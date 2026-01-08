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
        check_inhalation(['1']) |
        (check_ghs('GHS_AcuteTox_Oral', ['1']) & ~inhalation_present) |
        check_ghs('GHS_Carcinogenicity', ['1', '1A', '1B']) |
        check_ghs('GHS_GermCellMutagenicity', ['1', '1A', '1B'])
    )

    # HL4 Conditions
    cond_hl4 = (
        check_inhalation(['2']) |
        (check_ghs('GHS_AcuteTox_Oral', ['2']) & ~inhalation_present) |
        check_ghs('GHS_SkinCorrosion_Irritation', ['1A']) |
        check_ghs('GHS_RespiratorySensitizer', ['1', '1A', '1B']) |
        check_ghs('GHS_Carcinogenicity', ['2', '2A', '2B']) |
        check_ghs('GHS_GermCellMutagenicity', ['2', '2A', '2B']) |
        check_ghs('GHS_ReproductiveToxicity', ['1', '1A', '1B']) |
        check_ghs('GHS_STOT_Repeated', ['1'])
    )

    # HL3 Conditions
    cond_hl3 = (
        check_inhalation(['3']) |
        (check_ghs('GHS_AcuteTox_Oral', ['3']) & ~inhalation_present) |
        check_ghs('GHS_SkinCorrosion_Irritation', ['1', '1B', '1C']) |
        check_ghs('GHS_EyeDamage_Irritation', ['1']) |
        check_ghs('GHS_SkinSensitizer', ['1', '1A', '1B']) |
        check_ghs('GHS_ReproductiveToxicity', ['2']) |
        check_ghs('GHS_STOT_Single', ['1']) |
        check_ghs('GHS_STOT_Repeated', ['2'])
    )

    # HL2 Conditions
    cond_hl2 = (
        check_inhalation(['4']) |
        (check_ghs('GHS_AcuteTox_Oral', ['4']) & ~inhalation_present) |
        check_ghs('GHS_SkinCorrosion_Irritation', ['2']) |
        check_ghs('GHS_EyeDamage_Irritation', ['2']) |
        check_ghs('GHS_STOT_Single', ['2', '3'])
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
    """Selects OEL values based on priority."""
    oel_8h_cols = ['濃度基準値', '日本産業衛生学会 許容濃度', 'ACGIH TLV-TWA', 'DFG MAK']
    oel_st_cols = ['濃度基準値(短時間)', '日本産業衛生学会 (天井値)', 'ACGIH TLV-STEL']

    # Ensure columns exist, fill with NaN if not
    for col in oel_8h_cols + oel_st_cols:
        if col not in df.columns:
            df[col] = np.nan

    # Find the minimum available OEL for 8h and Short Term, replicating VBA logic
    df['OEL_8h'] = df[oel_8h_cols].min(axis=1)
    df['OEL_ST'] = df[oel_st_cols].min(axis=1)

    # Fallback for OEL_ST, ensuring alignment with VBA logic
    # First, try to fill with a direct calculation from an 8h value if one exists ('濃度基準値' is 'oelConcentrationStandard8Hour')
    df['OEL_ST'].fillna(df['濃度基準値'] * 3, inplace=True)
    # Then, use the calculated minimum 8h OEL
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

    weekly_cond = (df['freq_type'] == 1)
    work_hours_week = df['work_time_daily'] * df['freq_val']
    cond1 = weekly_cond & ((work_hours_week > 40) | ((df['work_time_daily'] > 8) & (df['freq_val'] >= 3)))
    cond2 = weekly_cond & (work_hours_week <= 4)
    df['time_coeff'] = np.select([cond1, cond2], [10, 0.1], default=1.0)

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

def round_down_significant(series, num_significant_figures):
    """
    Rounds down a pandas Series to a specified number of significant figures.
    Replicates VBA's `RoundDown(value, N - Int(Log(Abs(value))))`.
    """
    # Replace zero with a very small number to avoid log(0)
    series = series.replace(0, 1e-9)
    # Calculate the power of 10 for rounding
    power = num_significant_figures - np.floor(np.log10(np.abs(series))) - 1
    # Calculate the factor to multiply by
    factor = 10 ** power
    # Round down and then divide by the factor
    return np.floor(series * factor) / factor

def get_risk_level(rcr, is_dermal=False):
    """Helper to find risk level from an RCR value."""
    if pd.isna(rcr) or rcr < 0:
        return "-"
    level_map = constants.RISK_LEVEL_MAP_DERMAL if is_dermal else constants.RISK_LEVEL_MAP
    for (lower, upper), level in level_map.items():
        if lower < rcr <= upper:
            return level
    return "I"
