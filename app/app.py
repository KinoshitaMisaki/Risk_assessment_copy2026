# app.py
import os
import pandas as pd
from flask import Flask, request, render_template, send_from_directory, flash, redirect, url_for
from werkzeug.utils import secure_filename
import numpy as np
import logging

from logic import calculator, physical_hazards, constants, input_mapping

# --- Configuration & Setup ---
UPLOAD_FOLDER = 'uploads'
DOWNLOAD_FOLDER = 'downloads'
ALLOWED_EXTENSIONS = {'csv'}
app = Flask(__name__)
app.config.from_mapping(UPLOAD_FOLDER=UPLOAD_FOLDER, DOWNLOAD_FOLDER=DOWNLOAD_FOLDER, SECRET_KEY='supersecretkey')

# --- Data Loading ---
df_substance = pd.DataFrame()
df_glove = pd.DataFrame()

# Mapping from Japanese CSV headers to internal English names
GHS_JP_TO_EN_MAP = {
    '爆発物': 'GHS_Explosives', '可燃性ガス': 'GHS_FlamGas', 'エアゾール': 'GHS_Aerosol',
    '酸化性ガス': 'GHS_OxGas', '高圧ガス': 'GHS_GasesUnderPressure', '引火性液体': 'GHS_FlamLiq',
    '可燃性固体': 'GHS_FlamSol', '自己反応性化学品': 'GHS_SelfReact', '自然発火性液体': 'GHS_PyrLiq',
    '自然発火性固体': 'GHS_PyrSol', '自己発熱性化学品': 'GHS_SelfHeat',
    '水反応可燃性化学品': 'GHS_WaterReact', '酸化性液体': 'GHS_OxLiq', '酸化性固体': 'GHS_OxSol',
    '有機過酸化物': 'GHS_OrgPerox', '金属腐食性化学品': 'GHS_MetCorr',
    '鈍性化爆発物': 'GHS_InertExplosives',
    # Columns for ACRmax calculation
    '急性毒性（経口）': 'GHS_AcuteTox_Oral',
    '急性毒性（経皮）': 'GHS_AcuteTox_Dermal',
    '急性毒性（吸入：ガス）': 'GHS_AcuteTox_Inhalation_Gas',
    '急性毒性（吸入：蒸気）': 'GHS_AcuteTox_Inhalation_Vapor',
    '急性毒性（吸入：粉塵、ミスト）': 'GHS_AcuteTox_Inhalation_Dust',
    '皮膚腐食性／刺激性': 'GHS_SkinCorrosion_Irritation',
    '眼に対する重篤な損傷性／眼刺激性': 'GHS_EyeDamage_Irritation',
    '呼吸器感作性': 'GHS_RespiratorySensitizer',
    '皮膚感作性': 'GHS_SkinSensitizer',
    '生殖細胞変異原性': 'GHS_GermCellMutagenicity',
    '発がん性': 'GHS_Carcinogenicity',
    '生殖毒性': 'GHS_ReproductiveToxicity',
    '特定標的臓器毒性（単回暴露）': 'GHS_STOT_Single',
    '特定標的臓器毒性（反復暴露）': 'GHS_STOT_Repeated',
}

COLUMN_JP_TO_EN_MAP = {
    '沸点': 'bp', '引火点': 'flash_point', '分子量': 'mw', '水／オクタノール分配係数（logKow）': 'log_kow',
    '値': 'vp_val', '単位': 'vp_unit',
    '値.1': 'water_sol_val', '単位.1': 'water_sol_unit',
    '性状\n液体:1、固体:2、気体:3': 'prop_type_raw'
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_databases():
    global df_substance, df_glove
    try:
        substance_path = os.path.join(os.path.dirname(__file__), 'data', 'SubstanceList.csv')
        df_substance = pd.read_csv(substance_path, encoding='cp932', header=3, low_memory=False)
        df_substance.set_index('CAS RN', inplace=True)

        glove_path = os.path.join(os.path.dirname(__file__), 'data', 'GloveData.csv')
        df_glove = pd.read_csv(glove_path, encoding='cp932')
        df_glove.set_index(df_glove.columns[0], inplace=True)
        print("Databases loaded successfully.")
    except Exception as e:
        print(f"Error loading databases: {e}")

# --- Calculation Pipeline ---

def preprocess_user_csv_text(df):
    for col, mapping in input_mapping.ALL_MAPPINGS.items():
        if col in df.columns:
            df[col] = df[col].map(mapping)
    return df

def rename_columns(df):
    """Renames Japanese columns to English equivalents for processing."""
    df.rename(columns={**GHS_JP_TO_EN_MAP, **COLUMN_JP_TO_EN_MAP}, inplace=True)
    return df

def run_pipeline(df):
    print("--- 1. After Merge ---")
    print(df.columns)
    print(df.head(1).to_string())
    print("-" * 20)

    df = preprocess_user_csv_text(df)

    print("--- 2. After Text-to-Numeric Mapping ---")
    print(df.columns)
    print(df.head(1).to_string())
    print("-" * 20)

    df = rename_columns(df)

    print("--- 3. After Renaming ---")
    print(df.columns)
    print(df.head(1).to_string())
    print("-" * 20)

    # Enforce string type for all GHS columns to prevent accessor errors
    ghs_cols = GHS_JP_TO_EN_MAP.values()
    for col in ghs_cols:
        if col in df.columns:
            df[col] = df[col].astype(str)

    df = preprocess_and_normalize(df)
    df = calculator.determine_properties_vectorized(df)
    df = calculator.calculate_acr_max_vectorized(df)
    df = calculator.select_oel_vectorized(df)

    df = calculator.calculate_inhalation_risk_vectorized(df)
    df = calculator.calculate_dermal_risk_vectorized(df)

    df = calculate_final_rcr_and_levels(df)

    phys_results = df.apply(physical_hazards.calculate_physical_hazards, axis=1, result_type='expand')
    df[['Phys_Score_Max', 'Risk_Level_Phys', 'Phys_Risk_Factors']] = phys_results

    return df

def preprocess_and_normalize(df):
    # Combine all columns that need to be numeric into a single list
    all_numeric_cols = [
        # User inputs
        'amount_level', 'concentration', 'work_time_daily', 'freq_val',
        'skin_area', 'glove_type', 'glove_edu', 'process_temp',
        # Substance data
        'bp', 'flash_point', 'mw', 'log_kow', 'vp_val', 'water_sol_val', 'prop_type_raw'
    ]
    for col in all_numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    df['vp_val_pa'] = df['vp_val'] * df['vp_unit'].map(constants.VP_CONVERSION).fillna(1)
    df['water_sol_mg_cm3'] = df['water_sol_val'] * df['water_sol_unit'].map(constants.WATER_SOL_CONVERSION).fillna(0)

    return df

def calculate_final_rcr_and_levels(df):
    oel_target = df['OEL_8h'].fillna(df['ACR_Max'])
    df['RCR_Inhalation'] = df['EpBandMax'] / oel_target
    df['Risk_Level_Inh'] = df['RCR_Inhalation'].apply(lambda x: calculator.get_risk_level(x, is_dermal=False))

    oel_target_st = df['OEL_ST']
    df['RCR_Inh_ST'] = df['EpBandMax_ST'] / oel_target_st
    df['Risk_Level_Inh_ST'] = df['RCR_Inh_ST'].apply(lambda x: calculator.get_risk_level(x, is_dermal=False))

    base = df['OEL_8h'].fillna(df['ACR_Max'])
    oel_dermal_liq = (df['mw'] / 24.45) * base * 0.75 * 10
    oel_dermal_sol = base * 0.75 * 10
    df['OEL_Dermal'] = np.where(df['prop_type'].isin([1, 3]), oel_dermal_liq, oel_dermal_sol)
    df['RCR_Dermal'] = df['Dermal_Abs'] / df['OEL_Dermal']
    df['Risk_Level_Derm'] = df['RCR_Dermal'].apply(lambda x: calculator.get_risk_level(x, is_dermal=True))

    # --- Total Risk Calculation ---
    df['RCR_Total'] = df['RCR_Inhalation'].fillna(0) + df['RCR_Dermal'].fillna(0)
    df['Risk_Level_Total'] = df['RCR_Total'].apply(lambda x: calculator.get_risk_level(x, is_dermal=True)) # Use dermal map as per VBA

    return df

# --- Flask Routes ---
@app.route('/', methods=['GET', 'POST'])
def upload_file_route():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file or not file.filename or not allowed_file(file.filename):
            flash('Invalid file. Please upload a CSV.')
            return redirect(request.url)

        filename = secure_filename(file.filename)
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(upload_path)

        try:
            user_df = pd.read_csv(upload_path, encoding='utf-8')
            # Add logging to inspect the initial dataframe
            logging.info("--- 1. After User CSV Load ---")
            logging.info(user_df.columns)
            logging.info(user_df.head())

            merged_df = user_df.merge(df_substance, left_on='CAS_RN', right_index=True, how='left')

            result_df = run_pipeline(merged_df)

            result_filename = f"result_{filename}"
            result_path = os.path.join(app.config['DOWNLOAD_FOLDER'], result_filename)
            os.makedirs(app.config['DOWNLOAD_FOLDER'], exist_ok=True)
            result_df.to_csv(result_path, index=False, encoding='shift_jisx0213')

            # --- Create Display DataFrame ---
            display_columns = {
                'CAS_RN': 'CAS RN',
                'Product_Name': '製品名',
                'Risk_Level_Inh': '吸入(8時間)',
                'Risk_Level_Inh_ST': '吸入(短時間)',
                'Risk_Level_Derm': '経皮吸収',
                'Risk_Level_Total': '合計(吸入+経皮)',
                'Risk_Level_Phys': '危険性(爆発,火災等)'
            }
            display_df = result_df[list(display_columns.keys())].copy()
            display_df.rename(columns=display_columns, inplace=True)

            # Convert dataframe to HTML table for display
            result_table = display_df.to_html(classes='table-auto w-full text-left whitespace-no-wrap', index=False)

            return render_template('result.html', result_table=result_table, filename=result_filename)

        except Exception as e:
            flash(f"An error occurred during processing: {e}")
            logging.error(f"Error processing file: {e}", exc_info=True)
            return redirect(request.url)

    return render_template('index.html')

@app.route('/download/<filename>')
def download_file(filename):
    """Route to download a file from the DOWNLOAD_FOLDER."""
    return send_from_directory(
        os.path.abspath(app.config['DOWNLOAD_FOLDER']),
        filename,
        as_attachment=True
    )

if __name__ == '__main__':
    load_databases()
    app.run(debug=True)
