# logic/calculator.py

import math
import pandas as pd
from logic import constants

def round_down_to_2_sig_figs(n):
    """Rounds a number down to 2 significant figures."""
    if n == 0:
        return 0
    # Calculate the power of 10 to shift the decimal point
    power = -math.floor(math.log10(abs(n))) + 1
    factor = 10 ** power
    return math.floor(n * factor) / factor

# GHS Hazard Level Mapping for ACR Max Calculation
GHS_HAZARD_LEVELS = {
    'GHS_AcuteToxicityOral': {'区分1': 5, '区分2': 4, '区分3': 3, '区分4': 2},
    'GHS_AcuteToxicityDermal': {'区分1': 5, '区分2': 4, '区分3': 3, '区分4': 2},
    'GHS_AcuteToxicityInhalation': {'区分1': 5, '区分2': 4, '区分3': 3, '区分4': 2},
    'GHS_SkinCorrosionIrritation': {'区分1': 4},
    'GHS_SeriousEyeDamageIrritation': {'区分1': 4},
    'GHS_RespiratorySensitization': {'区分1': 5},
    'GHS_SkinSensitization': {'区分1': 4},
    'GHS_GermCellMutagenicity': {'区分1': 5, '区分2': 4},
    'GHS_Carcinogenicity': {'区分1': 5, '区分2': 4},
    'GHS_ReproductiveToxicity': {'区分1': 5, '区分2': 4},
    'GHS_SpecificTargetOrganToxicitySE': {'区分1': 5, '区分2': 4},
    'GHS_SpecificTargetOrganToxicityRE': {'区分1': 5, '区分2': 4},
    'GHS_AspirationHazard': {'区分1': 4},
    # Default to HL1
    'DEFAULT': 1
}


def convert_to_pascals(value, unit):
    """Converts vapor pressure to Pascals."""
    if unit == 'kPa':
        return value * 1000
    elif unit == 'hPa':
        return value * 100
    elif unit in ['mmHg', 'Torr']:
        return value * 133.3
    return value  # Assume Pa if no unit is specified

def determine_volatility_or_dustiness(substance, temp_q11):
    """Determines the volatility or dustiness rank (1-4)."""

    # Gas
    if substance['Property_Type'] == 3:
        return 1 # Treat as highly volatile

    # Solid
    if substance['Property_Type'] == 2:
        # If vapor pressure is high, treat as liquid
        if 'Vapor_Press_Val' in substance and substance['Vapor_Press_Val'] >= 0.5:
             pass # Fall through to liquid logic
        else:
            return 2 # Default to medium dustiness

    # Liquid or solid treated as liquid
    boiling_point = substance.get('Boiling_Point')
    if pd.isna(boiling_point):
        return 3 # Default to low volatility if boiling point is unknown

    rank = 3 # Default to low揮発性
    if boiling_point < 50:
        rank = 1
    elif boiling_point < 150:
        rank = 2

    # Correction by vapor pressure
    if 'Vapor_Press_Val' in substance and substance['Vapor_Press_Val'] < 0.5:
        rank = 4

    # Temperature correction
    if temp_q11 == 50 and rank > 1: # 50 corresponds to "室温以上"
        rank -= 1

    return rank

def select_oel(substance):
    """Selects the appropriate 8-hour and short-term OELs."""
    is_gas_or_liquid = substance['Property_Type'] in [1, 3]

    # Select 8-hour OEL
    oel_8h_cols_ppm = ['OEL_Std_8h_ppm', 'OEL_JSOH_ppm', 'OEL_ACGIH_TWA_ppm', 'OEL_DFG_MAK_ppm']
    oel_8h_cols_mg = ['OEL_Std_8h_mg', 'OEL_JSOH_mg', 'OEL_ACGIH_TWA_mg', 'OEL_DFG_MAK_mg']

    selected_oel_8h = None
    oel_unit = None

    if is_gas_or_liquid:
        for col in oel_8h_cols_ppm:
            if col in substance and pd.notna(substance[col]) and substance[col] > 0:
                selected_oel_8h = substance[col]
                oel_unit = 'ppm'
                break
    else: # Solid
        for col in oel_8h_cols_mg:
            if col in substance and pd.notna(substance[col]) and substance[col] > 0:
                selected_oel_8h = substance[col]
                oel_unit = 'mg/m3'
                break

    # Fallback to ACR Max if no OEL is found
    if selected_oel_8h is None:
        selected_oel_8h, oel_unit = calculate_acr_max(substance)

    # Select Short-term OEL
    oel_short_cols_ppm = ['OEL_Std_Short_ppm', 'OEL_JSOH_Ceiling_ppm', 'OEL_ACGIH_STEL_ppm']
    oel_short_cols_mg = ['OEL_Std_Short_mg', 'OEL_JSOH_Ceiling_mg', 'OEL_ACGIH_STEL_mg']

    selected_oel_short = None
    if is_gas_or_liquid:
        for col in oel_short_cols_ppm:
            if col in substance and pd.notna(substance[col]) and substance[col] > 0:
                selected_oel_short = substance[col]
                break
    else: # Solid
        for col in oel_short_cols_mg:
            if col in substance and pd.notna(substance[col]) and substance[col] > 0:
                selected_oel_short = substance[col]
                break

    # Fallback for short-term OEL
    if selected_oel_short is None and selected_oel_8h is not None:
        selected_oel_short = selected_oel_8h * 3

    return selected_oel_8h, selected_oel_short, oel_unit

def calculate_acr_max(substance):
    """Calculates the fallback OEL (ACR Max) based on GHS classifications."""

    max_hl = GHS_HAZARD_LEVELS['DEFAULT']

    for ghs_col, levels in GHS_HAZARD_LEVELS.items():
        if ghs_col != 'DEFAULT' and ghs_col in substance and pd.notna(substance[ghs_col]):
            classification = substance[ghs_col]
            if classification in levels:
                hl = levels[classification]
                if hl > max_hl:
                    max_hl = hl

    is_gas_or_liquid = substance['Property_Type'] in [1, 3]

    if is_gas_or_liquid:
        if max_hl == 5: return 0.05, 'ppm'
        if max_hl == 4: return 0.5, 'ppm'
        if max_hl == 3: return 5, 'ppm'
        if max_hl == 2: return 50, 'ppm'
        return 500, 'ppm' # HL1
    else: # Solid
        if max_hl == 5: return 0.001, 'mg/m3'
        if max_hl == 4: return 0.01, 'mg/m3'
        if max_hl == 3: return 0.1, 'mg/m3'
        if max_hl == 2: return 1, 'mg/m3'
        return 10, 'mg/m3' # HL1

def calculate_exposure_bands(row, volatility_rank):
    """Estimates the 8-hour and short-term exposure bands (EpBandMax)."""

    # Step 1: Determine InitialEpBand
    amount_score = constants.AMOUNT_SCORE[row['Amount_Q1']]
    is_gas_or_liquid = row['Property_Type'] in [1, 3]

    initial_ep_band = 0
    if is_gas_or_liquid:
        if volatility_rank == 1: # High
            if amount_score >= 500: initial_ep_band = 5000
            elif amount_score >= 50: initial_ep_band = 500
            else: initial_ep_band = 50
        elif volatility_rank == 2: # Medium
            if amount_score >= 500: initial_ep_band = 500
            elif amount_score >= 50: initial_ep_band = 50
            else: initial_ep_band = 5
        elif volatility_rank == 3: # Low
            if amount_score >= 500: initial_ep_band = 50
            elif amount_score >= 5: initial_ep_band = 5
            else: initial_ep_band = 0.5
        elif volatility_rank == 4: # Very Low
            if amount_score >= 500: initial_ep_band = 5
            elif amount_score >= 0.5: initial_ep_band = 0.5
            else: initial_ep_band = 0.05
    else: # Solid
        # Simplified from VBA logic
        if amount_score >= 5000: initial_ep_band = 100
        elif amount_score >= 500: initial_ep_band = 10
        elif amount_score >= 50: initial_ep_band = 1
        else: initial_ep_band = 0.1

    # Step 2: Calculate Coefficients
    concentration = row.get('Concentration', 100)
    if concentration >= 25: conc_coeff = 1.0
    elif concentration >= 5: conc_coeff = 0.6
    elif concentration >= 1: conc_coeff = 0.2
    else: conc_coeff = 0.1

    spray_coeff = constants.SPRAY_SCORE.get(row['Spray_Q2'] == 10, 1) # Assuming 10 is True

    area_coeff = 1
    if is_gas_or_liquid and amount_score >= 500:
        area_coeff = constants.AREA_SCORE.get(row['Area_Q3'] == 10, 1)

    ventilation_coeff = constants.VENTILATION_SCORE[row['Ventilation_Q4']]
    if volatility_rank == 4 and ventilation_coeff > 1:
        ventilation_coeff = 1

    apf_coeff = 1 # Fixed value

    # Step 3: Time/Frequency Correction (TimeCoeff) - Corrected for v3.2
    time_coeff = 1.0
    daily_hours = row['Time_Q5']
    frequency_is_weekly_or_more = (row['Frequency_Q6'] == 1)

    if frequency_is_weekly_or_more:
        # --- Logic for '週1回以上' (Weekly or more) ---
        days_per_week = row.get('Frequency_Days', 0)
        if pd.isna(days_per_week):
            days_per_week = 0

        weekly_hours = daily_hours * days_per_week

        if weekly_hours > 40 or (daily_hours > 8 and days_per_week >= 3):
            time_coeff = 10
        elif weekly_hours <= 4:
            time_coeff = 0.1
        else:
            time_coeff = 1.0
    else:
        # --- Logic for '週1回未満' (Less than weekly) ---
        annual_events = row.get('Frequency_Events', 0)
        if pd.isna(annual_events):
            annual_events = 0

        yearly_hours = daily_hours * annual_events

        if yearly_hours > 192:
            time_coeff = 1.0
        else:
            time_coeff = 0.1

    # Step 4: Calculate EpBandMax (8-hour)
    ep_band_max_8h = initial_ep_band * conc_coeff * spray_coeff * area_coeff * ventilation_coeff * time_coeff * apf_coeff

    # Final processing for 8h
    if is_gas_or_liquid:
        ep_band_max_8h = max(0.005, min(ep_band_max_8h, 5000))
    else:
        ep_band_max_8h = max(0.001, ep_band_max_8h)

    # Truncate to 2 significant figures
    if ep_band_max_8h > 0:
        ep_band_max_8h = round_down_to_2_sig_figs(ep_band_max_8h)

    # Step 5: Calculate EpBandMax (Short-term)
    variation_coeff = constants.VARIATION_SCORE[row['Variation_Q7']]
    ep_band_max_short = initial_ep_band * conc_coeff * spray_coeff * area_coeff * ventilation_coeff * variation_coeff * apf_coeff

    if is_gas_or_liquid:
        ep_band_max_short = max(0.005, min(ep_band_max_short, 5000))
    else:
        ep_band_max_short = max(0.001, ep_band_max_short)

    if ep_band_max_short > 0:
        ep_band_max_short = round_down_to_2_sig_figs(ep_band_max_short)


    return ep_band_max_8h, ep_band_max_short

def calculate_dermal_absorption(row):
    """
    Calculates the estimated dermal absorption amount.
    This is a simplified version of the VBA logic.
    """
    mol_weight = row.get('Mol_Weight')
    log_kow = row.get('LogKow')
    solubility = row.get('Solubility_Val') # Assuming g/L for simplicity

    if pd.isna(mol_weight) or pd.isna(log_kow) or pd.isna(solubility):
        return None # Cannot calculate without essential data

    # Full Absorption Rate calculation based on VBA logic
    # This is a complex formula, and I will replicate it as closely as possible.
    log_Kow = row.get('LogKow', 0)
    MW = row.get('Mol_Weight', 0)
    VP = row.get('Vapor_Press_Val', 0)
    WS = row.get('Solubility_Val', 0)

    # Full implementation based on the VBA logic
    flux = 10 ** (-0.0053 * (MW**2) + 0.015 * MW - 0.25 * log_Kow - 2.8)
    if VP > 0 and WS > 0:
        permeability_coefficient = (0.00000024 * VP) / (0.00000024 * VP + 0.0000006 * WS)
        absorption_rate = flux * permeability_coefficient
    else:
        absorption_rate = flux

    total_exposure_hours = row['Time_Q5']
    skin_area = constants.SKIN_AREA_VAL[row['SkinArea_Q8']]
    glove_coeff = constants.GLOVE_SCORE[row['Glove_Q9']]

    # Apply education coefficient if a protective glove is used
    if glove_coeff < 1:
        glove_coeff *= constants.EDUCATION_SCORE[row['Education_Q10']]

    dermal_absorption = absorption_rate * total_exposure_hours * skin_area * glove_coeff

    return dermal_absorption
