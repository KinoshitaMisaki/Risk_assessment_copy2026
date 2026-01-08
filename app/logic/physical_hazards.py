# app/logic/physical_hazards.py
import numpy as np
from .constants import RISK_LEVEL_MAP_PHYS

# GHS_COLUMN_MAP will be created in app.py and columns will be renamed before calling this
def _get_basic_score(amount_level, scores):
    """Helper to get score from amount level based on a mapping."""
    if not isinstance(scores, dict):
        return scores
    return scores.get(amount_level, 1)

def _find_class(ghs_string, class_map):
    """Helper to find the first matching class in the GHS string."""
    if pd.isna(ghs_string):
        return None
    for key in class_map.keys():
        if key in ghs_string:
            return key
    return None

# --- Reduction Logic Functions ---
def no_reduction(row): return 0

def ignition_explosive_reduction(row):
    if row['ignition_source'] and row['explosive_atm']: return 2
    if row['ignition_source'] or row['explosive_atm']: return 1
    return 0

def flam_sol_reduction(row):
    has_dustiness = row['volatility_rank'] in [1, 2]
    q12 = row['ignition_source']
    q13 = row['explosive_atm']

    if q12 and q13 and has_dustiness: return 3
    if (q12 and q13) or (q12 and has_dustiness) or (q13 and has_dustiness): return 2
    if q12 or q13 or has_dustiness: return 1
    return 0

def air_water_contact_reduction(row):
    return 2 if not row['water_contact'] else 0 # Q15 is "contact", so False is safe

def self_heat_reduction(row):
    return 1 if not row['water_contact'] else 0

def water_react_reduction(row):
    if not row['water_contact'] and row['ignition_source']: return 2
    if not row['water_contact'] or row['ignition_source']: return 1
    return 0

def metal_contact_reduction(row):
    return 1 if not row['metal_contact'] else 0

# --- Hazard Calculation Functions ---
HAZARD_CALCULATORS = []
def hazard_calculator(func):
    """Decorator to register hazard calculation functions."""
    HAZARD_CALCULATORS.append(func)
    return func

@hazard_calculator
def explosives(row):
    scores = {"不安定爆発物": 5, "1.1": 5, "1.2": 5, "1.3": 5, "1.4": {1:5, 2:5, 3:5, 4:4, 5:3}, "1.5": {1:4, 2:4, 3:4, 4:3, 5:2}, "1.6": {1:4, 2:4, 3:4, 4:3, 5:2}}
    cls = _find_class(row.get('GHS_Explosives'), scores)
    if not cls: return 0, ""
    score = _get_basic_score(row['amount_level'], scores[cls])
    return max(1, score - ignition_explosive_reduction(row)), f"爆発物 {cls}"

@hazard_calculator
def flam_gas(row):
    scores = {"1A": {1:5, 2:5, 3:4, 4:3, 5:2}, "1B": {1:5, 2:5, 3:4, 4:3, 5:2}, "2": {1:4, 2:3, 3:2, 4:2, 5:2}}
    cls = _find_class(row.get('GHS_FlamGas'), scores)
    if not cls: return 0, ""
    score = _get_basic_score(row['amount_level'], scores[cls])
    return max(1, score - ignition_explosive_reduction(row)), f"引火性ガス {cls}"

@hazard_calculator
def aerosol(row):
    scores = {"1": {1:5, 2:5, 3:4, 4:3, 5:2}, "2": {1:4, 2:3, 3:2, 4:2, 5:2}, "3": {1:3, 2:2, 3:2, 4:2, 5:1}}
    cls = _find_class(row.get('GHS_Aerosol'), scores)
    if not cls: return 0, ""
    score = _get_basic_score(row['amount_level'], scores[cls])
    return max(1, score - ignition_explosive_reduction(row)), f"エアゾール {cls}"

@hazard_calculator
def ox_gas(row):
    scores = {"1": {1:5, 2:4, 3:3, 4:2, 5:2}}
    cls = _find_class(row.get('GHS_OxGas'), scores)
    if not cls: return 0, ""
    return _get_basic_score(row['amount_level'], scores[cls]), f"酸化性ガス {cls}"

@hazard_calculator
def pressure_gas(row):
    scores = {"": {1:2, 2:2, 3:2, 4:1, 5:1}} # Any classification triggers this
    cls = row.get('GHS_GasesUnderPressure')
    if pd.isna(cls) or cls in ["-", "分類対象外", "区分なし"]: return 0, ""
    return _get_basic_score(row['amount_level'], scores[""]), f"高圧ガス {cls}"

@hazard_calculator
def flam_liq(row):
    ghs_class = row.get('GHS_FlamLiq')
    if pd.isna(ghs_class) or ghs_class in ["-", "分類対象外", "区分なし"]: return 0, ""
    if row['process_temp'] >= 50 and row['flash_point'] < row['process_temp']:
        score = 5
    else:
        scores = {"1": {1:5, 2:5, 3:4, 4:3, 5:2}, "2": {1:5, 2:5, 3:4, 4:3, 5:2}, "3": {1:4, 2:3, 3:2, 4:2, 5:2}, "4": {1:3, 2:2, 3:2, 4:2, 5:1}}
        cls = _find_class(ghs_class, scores)
        if not cls: return 0, ""
        score = _get_basic_score(row['amount_level'], scores[cls])
    return max(1, score - ignition_explosive_reduction(row)), f"引火性液体 {ghs_class}"

@hazard_calculator
def flam_sol(row):
    scores = {"1": {1:5, 2:5, 3:4, 4:3, 5:2}, "2": {1:4, 2:3, 3:2, 4:2, 5:2}}
    cls = _find_class(row.get('GHS_FlamSol'), scores)
    if not cls: return 0, ""
    score = _get_basic_score(row['amount_level'], scores[cls])
    return max(1, score - flam_sol_reduction(row)), f"可燃性固体 {cls}"

@hazard_calculator
def self_react(row):
    scores = {"A": 5, "B": 5, "C": {1:5, 2:5, 3:4, 4:3, 5:2}, "D": {1:5, 2:5, 3:4, 4:3, 5:2}, "E": {1:4, 2:3, 3:2, 4:2, 5:2}, "F": {1:4, 2:3, 3:2, 4:2, 5:2}, "G": {1:3, 2:2, 3:2, 4:2, 5:1}}
    cls = _find_class(row.get('GHS_SelfReact'), scores)
    if not cls: return 0, ""
    return _get_basic_score(row['amount_level'], scores[cls]), f"自己反応性化学品 {cls}"

@hazard_calculator
def pyr_liq(row):
    scores = {"1": 5}
    cls = _find_class(row.get('GHS_PyrLiq'), scores)
    if not cls: return 0, ""
    score = _get_basic_score(row['amount_level'], scores[cls])
    return max(1, score - air_water_contact_reduction(row)), f"自然発火性液体 {cls}"

@hazard_calculator
def pyr_sol(row):
    scores = {"1": 5}
    cls = _find_class(row.get('GHS_PyrSol'), scores)
    if not cls: return 0, ""
    score = _get_basic_score(row['amount_level'], scores[cls])
    return max(1, score - air_water_contact_reduction(row)), f"自然発火性固体 {cls}"

@hazard_calculator
def self_heat(row):
    scores = {"1": {1:5, 2:5, 3:4, 4:3, 5:2}, "2": {1:4, 2:3, 3:2, 4:2, 5:2}}
    cls = _find_class(row.get('GHS_SelfHeat'), scores)
    if not cls: return 0, ""
    score = _get_basic_score(row['amount_level'], scores[cls])
    return max(1, score - self_heat_reduction(row)), f"自己発熱性化学品 {cls}"

@hazard_calculator
def water_react(row):
    scores = {"1": 5, "2": {1:5, 2:5, 3:4, 4:4, 5:3}, "3": {1:5, 2:4, 3:3, 4:3, 5:2}}
    cls = _find_class(row.get('GHS_WaterReact'), scores)
    if not cls: return 0, ""
    score = _get_basic_score(row['amount_level'], scores[cls])
    return max(1, score - water_react_reduction(row)), f"水反応可燃性化学品 {cls}"

@hazard_calculator
def ox_liq(row):
    scores = {"1": {1:5, 2:4, 3:3, 4:2, 5:2}, "2": {1:4, 2:3, 3:2, 4:2, 5:2}, "3": {1:3, 2:2, 3:2, 4:2, 5:1}}
    cls = _find_class(row.get('GHS_OxLiq'), scores)
    if not cls: return 0, ""
    score = _get_basic_score(row['amount_level'], scores[cls])
    return max(1, score - metal_contact_reduction(row)), f"酸化性液体 {cls}"

@hazard_calculator
def ox_sol(row):
    scores = {"1": {1:5, 2:4, 3:3, 4:2, 5:2}, "2": {1:4, 2:3, 3:2, 4:2, 5:2}, "3": {1:3, 2:2, 3:2, 4:2, 5:1}}
    cls = _find_class(row.get('GHS_OxSol'), scores)
    if not cls: return 0, ""
    score = _get_basic_score(row['amount_level'], scores[cls])
    return max(1, score - metal_contact_reduction(row)), f"酸化性固体 {cls}"

@hazard_calculator
def org_perox(row):
    scores = {"A": 5, "B": 5, "C": {1:5, 2:5, 3:4, 4:3, 5:2}, "D": {1:5, 2:5, 3:4, 4:3, 5:2}, "E": {1:4, 2:3, 3:2, 4:2, 5:2}, "F": {1:4, 2:3, 3:2, 4:2, 5:2}, "G": {1:3, 2:2, 3:2, 4:2, 5:1}}
    cls = _find_class(row.get('GHS_OrgPerox'), scores)
    if not cls: return 0, ""
    return _get_basic_score(row['amount_level'], scores[cls]), f"有機過酸化物 {cls}"

@hazard_calculator
def met_corr(row):
    scores = {"1": 2}
    cls = _find_class(row.get('GHS_MetCorr'), scores)
    if not cls: return 0, ""
    return _get_basic_score(row['amount_level'], scores[cls]), f"金属腐食性 {cls}"

# This is a guess for "鈍性化爆発物". If the column name is different, it needs to be updated.
@hazard_calculator
def inert_expl(row):
    scores = {"": 5}
    cls = row.get('GHS_InertExplosives')
    if pd.isna(cls) or cls in ["-", "分類対象外", "区分なし"]: return 0, ""
    return 5, f"鈍性化爆発物 {cls}"

# --- Main Calculation Function ---
def calculate_physical_hazards(row):
    if not row.get('target_phys', False):
        return 0, "I", "評価対象外"

    all_scores = [func(row) for func in HAZARD_CALCULATORS]

    valid_scores = [(s, r) for s, r in all_scores if s > 0]

    if not valid_scores:
        return 0, "I", "危険性なし"

    max_score, best_reason = max(valid_scores, key=lambda item: item[0])

    final_score = int(np.ceil(max_score))
    risk_level = RISK_LEVEL_MAP_PHYS.get(final_score, "I")

    return final_score, risk_level, best_reason
