# logic/risk_assessment.py
import pandas as pd
from logic import ghslib, constants

def assess_inhalation_risk(exposure, oel):
    """Assesses the inhalation risk and provides a risk level and comment."""
    if oel is None or oel == 0 or exposure is None:
        return '－', '評価不能'

    rcr = exposure / oel

    if rcr > 10:
        return 'IV', '直ちに改善が必要'
    elif rcr > 1:
        return 'III', '改善が必要'
    elif rcr > 0.5:
        return 'II-B', '改善が望ましい'
    elif rcr > 0.1:
        return 'II-A', '現状維持（注意）'
    else:
        return 'I', 'リスクは低い'

def assess_dermal_risk(dermal_absorption, oel_8h_ppm, oel_8h_mg, mol_weight, property_type):
    """Assesses the dermal risk by calculating a dermal OEL and comparing it."""

    if dermal_absorption is None:
        return '－', '評価不能'

    oel_dermal = None
    if property_type in [1, 3] and pd.notna(oel_8h_ppm): # Liquid or Gas
        oel_dermal = (mol_weight / 24.45) * oel_8h_ppm * 10 * 0.75
    elif property_type == 2 and pd.notna(oel_8h_mg): # Solid
        oel_dermal = oel_8h_mg * 10 * 0.75

    if oel_dermal is None or oel_dermal == 0:
        return '－', '評価不能'

    ratio = dermal_absorption / oel_dermal

    if ratio > 1:
        return 'IV', '改善が必要'
    elif ratio > 0.5:
        return 'III', '改善が望ましい'
    elif ratio > 0.1:
        return 'II', '現状維持（注意）'
    else:
        return 'I', 'リスクは低い'

def assess_physical_risk(row):
    """Assesses the physical risk based on GHS data and safety measures."""
    ghs_data = ghslib.parse_ghs_classifications(row)
    if not ghs_data:
        return '－', '評価不能'

    amount_score = constants.AMOUNT_SCORE[row['Amount_Q1']]
    safety_measures = {
        'AntiFire_Q12': row['AntiFire_Q12'],
        'AntiExplosion_Q13': row['AntiExplosion_Q13']
    }

    hazard_level = ghslib.determine_physical_hazards(ghs_data, amount_score, safety_measures)

    if hazard_level >= 4:
        return 'IV', '改善が必要'
    elif hazard_level >= 3:
        return 'III', '改善が望ましい'
    elif hazard_level >= 2:
        return 'II', '現状維持（注意）'
    else:
        return 'I', 'リスクは低い'
