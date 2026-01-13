# app/logic/calculator.py
import numpy as np
import pandas as pd
from . import constants

def determine_properties_vectorized(df):
    """Vectorized determination of property type and volatility rank."""
    df['prop_type'] = np.where((df['prop_type_raw'] == 2) & (df['vp_val_pa'] >= 0.5), 1, df['prop_type_raw'])

    conditions_bp = [df['bp'] < 50, (df['bp'] >= 50) & (df['bp'] < 150), df['bp'] >= 150]
    choices_bp = [1, 2, 3]
    base_rank = pd.Series(np.select(conditions_bp, choices_bp, default=2), index=df.index)
    base_rank = np.where((df['vp_val_pa'].notna()) & (df['vp_val_pa'] < 0.5), 4, base_rank)

    temp_adjusted_rank = base_rank - (df['process_temp'] >= 50).astype(int)
    liquid_rank = np.maximum(1, temp_adjusted_rank)

    df['volatility_rank'] = np.select(
        [df['prop_type'] == 1, df['prop_type'] == 3, df['prop_type'] == 2],
        [liquid_rank, 1, df.get('dustiness_level', 2)], default=2
    ).astype(int)
    return df

def calculate_acr_max_vectorized(df):
    """Calculates ACRmax based on GHS classifications using corrected English column names."""
    is_liquid = df['prop_type'].isin([1, 3])

    def check_ghs(col_name, keywords):
        if col_name not in df.columns: return pd.Series(False, index=df.index)
        pattern = '|'.join(keywords)
        return df[col_name].str.contains(pattern, na=False)

    # Combine multiple inhalation columns into one composite check
    inhalation_cols = ['GHS_AcuteTox_Inhalation_Gas', 'GHS_AcuteTox_Inhalation_Vapor', 'GHS_AcuteTox_Inhalation_Dust']
    inhalation_present = df[inhalation_cols].notna().any(axis=1)

    def check_inhalation(keywords):
        return (check_ghs('GHS_AcuteTox_Inhalation_Gas', keywords) |
                check_ghs('GHS_AcuteTox_Inhalation_Vapor', keywords) |
                check_ghs('GHS_AcuteTox_Inhalation_Dust', keywords))

    # HL5 Conditions
    cond_hl5 = (
        check_inhalation(['区分1']) |
        (check_ghs('GHS_AcuteTox_Oral', ['区分1']) & ~inhalation_present) |
        check_ghs('GHS_Carcinogenicity', ['区分1', '区分1A', '区分1B']) |
        check_ghs('GHS_GermCellMutagenicity', ['区分1', '区分1A', '区分1B'])
    )

    # HL4 Conditions
    cond_hl4 = (
        check_inhalation(['区分2']) |
        (check_ghs('GHS_AcuteTox_Oral', ['区分2']) & ~inhalation_present) |
        check_ghs('GHS_SkinCorrosion_Irritation', ['区分1A']) |
        check_ghs('GHS_RespiratorySensitizer', ['区分1', '区分1A', '区分1B']) |
        check_ghs('GHS_Carcinogenicity', ['区分2', '区分2A', '区分2B']) |
        check_ghs('GHS_GermCellMutagenicity', ['区分2', '区分2A', '区分2B']) |
        check_ghs('GHS_ReproductiveToxicity', ['区分1', '区分1A', '区分1B']) |
        check_ghs('GHS_STOT_Repeated', ['区分1'])
    )

    # HL3 Conditions
    cond_hl3 = (
        check_inhalation(['区分3']) |
        (check_ghs('GHS_AcuteTox_Oral', ['区分3']) & ~inhalation_present) |
        check_ghs('GHS_SkinCorrosion_Irritation', ['区分1B', '区分1C', '区分1']) |
        check_ghs('GHS_EyeDamage_Irritation', ['区分1']) |
        check_ghs('GHS_SkinSensitizer', ['区分1', '区分1A', '区分1B']) |
        check_ghs('GHS_ReproductiveToxicity', ['区分2']) |
        check_ghs('GHS_STOT_Single', ['区分1']) |
        check_ghs('GHS_STOT_Repeated', ['区分2'])
    )

    # HL2 Conditions
    cond_hl2 = (
        check_inhalation(['区分4']) |
        (check_ghs('GHS_AcuteTox_Oral', ['区分4']) & ~inhalation_present) |
        check_ghs('GHS_SkinCorrosion_Irritation', ['区分2']) |
        check_ghs('GHS_EyeDamage_Irritation', ['区分2', '区分2A', '区分2B']) |
        check_ghs('GHS_STOT_Single', ['区分2', '区分3'])
    )

    acr_choices_liquid = [0.05, 0.5, 5, 50, 500]
    acr_choices_solid = [0.001, 0.01, 0.1, 1, 10]

    conditions = [cond_hl5, cond_hl4, cond_hl3, cond_hl2]

    # Build the list of choices dynamically based on whether the substance is liquid or solid
    choices = [
        np.where(is_liquid, acr_choices_liquid[0], acr_choices_solid[0]), # HL5
        np.where(is_liquid, acr_choices_liquid[1], acr_choices_solid[1]), # HL4
        np.where(is_liquid, acr_choices_liquid[2], acr_choices_solid[2]), # HL3
        np.where(is_liquid, acr_choices_liquid[3], acr_choices_solid[3]), # HL2
    ]

    # Use np.select with the correctly structured choices list
    df['ACR_Max'] = np.select(
        conditions,
        choices,
        default=np.where(is_liquid, acr_choices_liquid[-1], acr_choices_solid[-1]) # HL1
    )

    return df

def select_oel_vectorized(df):
    """
    Selects OEL values based on priority, finding the first available valid value
    across multiple columns, exactly replicating the VBA logic in a robust way.
    """
    # Define columns in order of priority
    oel_8h_cols = ['濃度基準値', '日本産業衛生学会 許容濃度', 'ACGIH TLV-TWA', 'DFG MAK']
    oel_st_cols = ['濃度基準値(短時間)', '日本産業衛生学会 (天井値)', 'ACGIH TLV-STEL']

    # Initialize OEL columns with NaN
    df['OEL_8h'] = np.nan
    df['OEL_ST'] = np.nan

    # For 8h OEL, iterate through columns by priority and fill missing values
    for col in oel_8h_cols:
        if col in df.columns:
            # Coerce to numeric, turning non-numeric into NaN
            numeric_col = pd.to_numeric(df[col], errors='coerce')
            # Fill NaN in 'OEL_8h' with the first valid (positive) value from the current priority column
            df['OEL_8h'].fillna(numeric_col[numeric_col > 0], inplace=True)

    # For Short Term OEL, do the same
    for col in oel_st_cols:
        if col in df.columns:
            numeric_col = pd.to_numeric(df[col], errors='coerce')
            df['OEL_ST'].fillna(numeric_col[numeric_col > 0], inplace=True)

    # Fallback for OEL_ST, ensuring alignment with VBA logic
    df['OEL_ST'].fillna(df['OEL_8h'] * 3, inplace=True)
    df['OEL_ST'].fillna(df['ACR_Max'] * 3, inplace=True)
    return df

def calculate_inhalation_risk_vectorized(df):
    df['conc_coeff'] = pd.cut(df['concentration'], bins=[-1, 1, 5, 25, 101], labels=[0.1, 0.2, 0.6, 1], right=False).astype(float)
    df['spray_coeff'] = np.where(df['spray_work'], 10, 1)
    df['area_coeff'] = np.where((df['prop_type'] == 1) & (df['amount_level'].isin([1, 2])) & (df['area_high']), 10, 1)
    df['venti_coeff'] = df['ventilation']
    df.loc[(df['volatility_rank'] == 4) & (~df['spray_work']), 'venti_coeff'] = 1
    df['var_coeff'] = df['exposure_variation']

    # --- Time Coeff (time_coeff) - For 8h assessment (VBA logic recreation) ---
    # Replicating If...ElseIf...Else logic with np.select for correctness
    is_weekly = df['freq_type'] == 1
    is_not_weekly = df['freq_type'] == 0

    # Weekly conditions
    cond_weekly_10 = is_weekly & ((df['work_time_daily'] * df['freq_val'] > 40) | ((df['work_time_daily'] > 8) & (df['freq_val'] >= 3)))
    cond_weekly_01 = is_weekly & (df['work_time_daily'] * df['freq_val'] <= 4)

    # Not weekly conditions
    cond_not_weekly_1 = is_not_weekly & (df['work_time_daily'] * df['freq_val'] * 12 > 192)

    conditions = [
        cond_weekly_10,      # If this is true, use 10.0
        cond_weekly_01,      # Else if this is true, use 0.1
        is_weekly,           # Else if it's weekly, use 1.0 (the default for weekly)
        cond_not_weekly_1,   # If not weekly and this is true, use 1.0
        is_not_weekly        # Else if it's not weekly, use 0.1
    ]
    choices = [
        10.0,
        0.1,
        1.0,
        1.0,
        0.1
    ]

    df['time_coeff'] = np.select(conditions, choices, default=1.0)

    # Create MultiIndex for mapping
    multi_index = pd.MultiIndex.from_frame(df[['amount_level', 'volatility_rank']])

    # Map initial exposure values
    liq_map = pd.Series(constants.INITIAL_EP_LIQUID, name='initial_ep').rename_axis(['amount_level', 'volatility_rank'])
    sol_map = pd.Series(constants.INITIAL_EP_SOLID, name='initial_ep').rename_axis(['amount_level', 'volatility_rank'])

    df['initial_ep'] = np.nan
    df.loc[df['prop_type'] == 1, 'initial_ep'] = multi_index[df['prop_type'] == 1].map(liq_map)
    df.loc[df['prop_type'] == 2, 'initial_ep'] = multi_index[df['prop_type'] == 2].map(sol_map)
    df['initial_ep'].fillna(0, inplace=True)

    base_exp = df['initial_ep'] * df['conc_coeff'] * df['spray_coeff'] * df['area_coeff'] * df['venti_coeff']

    # Calculate final exposure and apply rounding and clipping
    ep_band_max = base_exp * df['time_coeff']
    ep_band_max_st = base_exp * df['var_coeff']

    # Special case for very low volatility
    ep_band_max_st = np.where((df['volatility_rank'] == 4) & (~df['spray_work']), ep_band_max, ep_band_max_st)

    # Round down to 2 significant figures
    df['EpBandMax'] = round_down_significant(pd.Series(ep_band_max, index=df.index), 2)
    df['EpBandMax_ST'] = round_down_significant(pd.Series(ep_band_max_st, index=df.index), 2)

    # Clipping final values
    df['EpBandMax'] = df['EpBandMax'].clip(lower=np.where(df['prop_type'] == 1, 0.005, 0.001), upper=5000)
    df['EpBandMax_ST'] = df['EpBandMax_ST'].clip(lower=np.where(df['prop_type'] == 1, 0.005, 0.001), upper=5000)

    return df

def calculate_dermal_risk_vectorized(df):
    log_kp_sc = -1.326 + 0.6097 * df['log_kow'] - 0.1786 * np.sqrt(df['mw'])
    kp_sc = 10**log_kp_sc
    k_pol = 0.0001519 / np.sqrt(df['mw'])
    k_aq = 2.5 / np.sqrt(df['mw'])
    df['kp'] = 1 / (1 / (kp_sc + k_pol) + 1 / k_aq)

    df['jmax'] = df['kp'] * df['water_sol_mg_cm3']
    c = constants.DERMAL_CONSTANTS
    diff = 0.06 * (76 / df['mw'])**0.5
    beta = (0.0111 * c['AirVel']**0.96 * diff**0.19) / (c['Visc']**0.15 * c['L']**0.04)
    evap_rate = (beta * df['vp_val_pa'] * df['mw']) / (c['R'] * c['T'] * 10)
    df['evap_rate'] = np.where(df['prop_type'] == 1, evap_rate, 0)

    # Correctly handle the numpy array returned by np.where before calling .fillna
    t_skin_raw = np.where(
        df['prop_type'] == 1,
        7 / (df['jmax'] + df['evap_rate']),
        3 / (df['jmax'] + df['evap_rate']) # Corrected for solids
    )
    t_skin = pd.Series(t_skin_raw, index=df.index).fillna(float('inf'))
    t_total = np.minimum(df['work_time_daily'] + t_skin, 10)
    glove_coeff = np.where(df['glove_type'] == 0.2, 0.2 * df['glove_edu'], 1.0)

    # Calculate final absorption and apply rounding
    dermal_abs = df['jmax'] * t_total * df['skin_area'] * glove_coeff
    df['Dermal_Abs'] = round_down_significant(dermal_abs, 2)

    return df

def round_down_significant(series, num_significant_figures=2):
    """
    Rounds down a pandas Series to a specified number of significant figures,
    perfectly replicating the VBA's `RoundDown(value, 2 - Int(Log(Abs(value))))` logic.
    """
    # Handle non-positive values, which cannot be logged
    is_positive = series > 0
    result = pd.Series(np.nan, index=series.index)

    positive_series = series[is_positive]
    if not positive_series.empty:
        # Calculate the number of decimal places for rounding down
        power = num_significant_figures - np.floor(np.log10(positive_series)) - 1
        # Calculate the factor to multiply by
        factor = 10 ** power
        # Round down and then divide by the factor
        result[is_positive] = np.floor(positive_series * factor) / factor

    # Handle zero and negative values separately
    result.fillna(0, inplace=True)
    return result

def get_risk_level(rcr, is_dermal=False):
    """Helper to find risk level from an RCR value."""
    if pd.isna(rcr) or rcr < 0:
        return "-"
    level_map = constants.RISK_LEVEL_MAP_DERMAL if is_dermal else constants.RISK_LEVEL_MAP
    for (lower, upper), level in level_map.items():
        if lower < rcr <= upper:
            return level
    return "I"
