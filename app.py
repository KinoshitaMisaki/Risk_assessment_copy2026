import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, send_file
from werkzeug.utils import secure_filename
from logic import calculator, risk_assessment, input_mapping, constants
import uuid
from flask import session
import config
from io import StringIO

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER
app.secret_key = os.urandom(24)

results_cache = {}

# Load and preprocess master data at startup
def load_substance_db():
    """Loads and preprocesses the substance database from the CSV file."""

    # Define the column mapping based on the specification document
    column_mapping = {
        0: 'CAS_RN', 1: 'Name_JP', 2: 'Name_EN', 5: 'GHS_Explosives', 6: 'GHS_FlammableGases',
        7: 'GHS_FlammableAerosols', 8: 'GHS_OxidizingGases', 9: 'GHS_GasesUnderPressure', 10: 'GHS_FlammableLiquids',
        11: 'GHS_FlammableSolids', 12: 'GHS_SelfReactiveSubstances', 13: 'GHS_PyrophoricLiquids', 14: 'GHS_PyrophoricSolids',
        15: 'GHS_SelfHeatingSubstances', 16: 'GHS_SubstancesWhichInContactWithWaterEmitFlammableGases', 17: 'GHS_OxidizingLiquids',
        18: 'GHS_OxidizingSolids', 19: 'GHS_OrganicPeroxides', 20: 'GHS_CorrosiveToMetals', 21: 'GHS_DesensitizedExplosives',
        22: 'GHS_AcuteToxicityOral', 23: 'GHS_AcuteToxicityDermal', 24: 'GHS_AcuteToxicityInhalationGases',
        25: 'GHS_AcuteToxicityInhalationVapors', 26: 'GHS_AcuteToxicityInhalationDustsMists', 27: 'GHS_SkinCorrosionIrritation',
        28: 'GHS_SeriousEyeDamageIrritation', 29: 'GHS_RespiratorySensitization', 30: 'GHS_SkinSensitization',
        31: 'GHS_GermCellMutagenicity', 32: 'GHS_Carcinogenicity', 33: 'GHS_ReproductiveToxicity', 34: 'GHS_STOT_SingleExposure',
        35: 'GHS_STOT_RepeatedExposure', 36: 'GHS_AspirationHazard', 43: 'OEL_Std_8h_ppm', 44: 'OEL_Std_8h_mg',
        45: 'OEL_Std_Short_ppm', 46: 'OEL_Std_Short_mg', 49: 'OEL_JSOH_ppm', 50: 'OEL_JSOH_mg',
        51: 'OEL_JSOH_Ceiling_ppm', 52: 'OEL_JSOH_Ceiling_mg', 56: 'OEL_ACGIH_TWA_ppm', 57: 'OEL_ACGIH_TWA_mg',
        58: 'OEL_ACGIH_STEL_ppm', 59: 'OEL_ACGIH_STEL_mg', 65: 'OEL_DFG_MAK_ppm', 66: 'OEL_DFG_MAK_mg',
        71: 'Property_Type', 72: 'Mol_Weight', 73: 'Boiling_Point', 74: 'LogKow', 75: 'Flash_Point',
        76: 'Solubility_Val', 77: 'Solubility_Unit', 78: 'Vapor_Press_Val', 79: 'Vapor_Press_Unit',
        80: 'Regulation_Flag_1', 92: 'Regulation_Flag_13'
    }

    df = pd.read_csv(config.SUBSTANCE_DATA_PATH, encoding='shift_jis', header=None, skiprows=4, usecols=column_mapping.keys())
    df = df.rename(columns=column_mapping)
    df = df.set_index('CAS_RN')

    numeric_cols = [
        'OEL_Std_8h_ppm', 'OEL_Std_8h_mg', 'OEL_Std_Short_ppm', 'OEL_Std_Short_mg', 'OEL_JSOH_ppm', 'OEL_JSOH_mg',
        'OEL_JSOH_Ceiling_ppm', 'OEL_JSOH_Ceiling_mg', 'OEL_ACGIH_TWA_ppm', 'OEL_ACGIH_TWA_mg', 'OEL_ACGIH_STEL_ppm',
        'OEL_ACGIH_STEL_mg', 'OEL_DFG_MAK_ppm', 'OEL_DFG_MAK_mg', 'Mol_Weight', 'Boiling_Point', 'LogKow',
        'Flash_Point', 'Solubility_Val', 'Vapor_Press_Val'
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    return df

substance_db = load_substance_db()

@app.route('/')
def index():
    """Renders the main upload page."""
    return render_template('index.html')

def preprocess_user_csv(df):
    """
    Converts Japanese text selections in the user-uploaded CSV to their
    corresponding numeric or boolean values.
    """
    # Create a single copy to avoid SettingWithCopyWarning and data loss in loop
    df = df.copy()

    # Handle Product_Property mapping separately using constants.py
    if 'Product_Property' in df.columns:
        df.loc[:, 'Product_Property'] = df['Product_Property'].map(constants.PRODUCT_PROPERTY)

    # Process other columns using the general mapping file.
    for column, mapping in input_mapping.COLUMN_MAPPINGS.items():
        if column in df.columns:
            df.loc[:, column] = df[column].map(mapping)

    return df

def process_data(df):
    """Processes the uploaded data to perform risk assessment."""
    merged_df = pd.merge(df, substance_db, on='CAS_RN', how='left')

    # Ensure relevant columns are numeric after merge
    merged_df['Product_Property'] = pd.to_numeric(merged_df['Product_Property'], errors='coerce')
    merged_df['Property_Type'] = pd.to_numeric(merged_df['Property_Type'], errors='coerce')

    results = []
    for index, row in merged_df.iterrows():
        # Create a mutable copy of the row to modify it
        row = row.copy()

        # --- Pre-processing Step: Normalize Vapor Pressure to Pascals ---
        if pd.notna(row.get('Vapor_Press_Val')) and pd.notna(row.get('Vapor_Press_Unit')):
            row['Vapor_Press_Val'] = calculator.convert_to_pascals(
                row['Vapor_Press_Val'], row['Vapor_Press_Unit']
            )

        # Corrected logic for v3.2: User's 'Product_Property' overrides the database's 'Property_Type'
        if pd.notna(row['Product_Property']):
            row['Property_Type'] = row['Product_Property']

        # --- Calculations ---
        volatility_rank = calculator.determine_volatility_or_dustiness(row, row['Temp_Q11'])
        oel_8h, oel_short, oel_unit = calculator.select_oel(row)
        ep_band_8h, ep_band_short = calculator.calculate_exposure_bands(row, volatility_rank)

        risk_level_8h, risk_comment_8h = risk_assessment.assess_inhalation_risk(ep_band_8h, oel_8h)
        risk_level_short, risk_comment_short = risk_assessment.assess_inhalation_risk(ep_band_short, oel_short)

        dermal_absorption = calculator.calculate_dermal_absorption(row)
        risk_level_dermal, risk_comment_dermal = risk_assessment.assess_dermal_risk(
            dermal_absorption, oel_8h, row.get('OEL_Std_8h_mg'), row.get('Mol_Weight'), row.get('Property_Type')
        )

        risk_level_physical, risk_comment_physical = risk_assessment.assess_physical_risk(row)

        result_row = {
            'CAS_RN': row['CAS_RN'],
            'Name_JP': row['Name_JP'],
            'OEL_Used_Value': f"{oel_8h} ({oel_unit})",
            'EpBand_8h': ep_band_8h,
            'Risk_Inhalation_8h': risk_level_8h,
            'Risk_Comment_8h': risk_comment_8h,
            'EpBand_Short': ep_band_short,
            'Risk_Inhalation_Short': risk_level_short,
            'Risk_Comment_Short': risk_comment_short,
            'Risk_Dermal': risk_level_dermal,
            'Risk_Comment_Dermal': risk_comment_dermal,
            'Risk_Physical': risk_level_physical,
            'Risk_Comment_Physical': risk_comment_physical,
        }
        results.append(result_row)

    return results

@app.route('/process', methods=['POST'])
def process_csv():
    """Handles the CSV file upload and processing."""
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file:
        filename = secure_filename(file.filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Read CSV, ignoring comment lines starting with #
        user_df = pd.read_csv(filepath, comment='#')
        preprocessed_df = preprocess_user_csv(user_df)
        results = process_data(preprocessed_df)

        results_id = str(uuid.uuid4())
        results_cache[results_id] = results
        session['results_id'] = results_id

        return render_template('result.html', data=results)

@app.route('/download/template')
def download_template():
    """Serves the template CSV file for download."""
    return send_from_directory(
        os.path.dirname(config.TEMPLATE_CSV_PATH),
        os.path.basename(config.TEMPLATE_CSV_PATH),
        as_attachment=True
    )

@app.route('/download/results')
def download_results():
    """Serves the results as a CSV file for download."""
    results_id = session.get('results_id')
    if results_id and results_id in results_cache:
        df = pd.DataFrame(results_cache[results_id])
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
        csv_buffer.seek(0)

        return send_file(
            csv_buffer,
            mimetype='text/csv',
            as_attachment=True,
            download_name='risk_assessment_results.csv'
        )
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
