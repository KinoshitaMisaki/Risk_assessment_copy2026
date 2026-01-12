# -*- coding: utf-8 -*-
from data import CHEMICAL_DATABASE, OPTIONS

def get_risk_level(rcr):
    """Determines the inhalation risk level based on the RCR value."""
    if rcr < 0.1: return { 'val': 'I', 'color': 'bg-green-100 text-green-800', 'msg': '現状維持' }
    if rcr < 0.5: return { 'val': 'II', 'color': 'bg-yellow-100 text-yellow-800', 'msg': '要管理' }
    if rcr < 1.0: return { 'val': 'III', 'color': 'bg-orange-100 text-orange-800', 'msg': '改善検討' }
    return { 'val': 'IV', 'color': 'bg-red-100 text-red-800', 'msg': '直ちに改善' }

def calculate_volatility_score(chem, form):
    """
    Calculates the volatility/dispersibility score based on boiling point (bp) and physical form.
    Score: 1 (High) to 3 (Low).
    """
    if form == 'gas' or (chem.get('property') == 'gas'):
        return 1 # High

    if form == 'powder':
        # This can be refined based on particle size, but for now, we'll use a medium default.
        return 2 # Medium

    # Default to liquid if not specified
    if 'bp' in chem:
        if chem['bp'] < 50:
            return 1 # High
        elif 50 <= chem['bp'] < 150:
            return 2 # Medium
        else: # bp >= 150
            return 3 # Low

    return 3 # Default to low if no boiling point data

def calculate_inhalation_risk(form_data):
    """
    Calculates the inhalation risk based on user inputs.
    """
    # 1. Get selected chemical
    chem_id = int(form_data.get('substance_id'))
    chem = next((c for c in CHEMICAL_DATABASE if c['id'] == chem_id), None)
    if not chem or 'oel' not in chem:
        return { 'error': 'Selected chemical not found or missing OEL.' }

    # 2. Get user inputs from form
    concentration = float(form_data.get('concentration', 100))
    form = form_data.get('form', 'liquid') # Use the new form input, default to liquid
    q1_amount_val = int(form_data.get('q1_amount', 3))
    q2_spray = form_data.get('q2_spray') == 'true' # Check for spray application
    q4_ventilation = float(form_data.get('q4_ventilation', 1))
    q5_time = float(form_data.get('q5_time', 1))

    # 3. Determine Volatility/Dispersibility Score
    volatility_score = calculate_volatility_score(chem, form)

    # 4. Estimate Base Concentration
    volatility_multiplier = {1: 10, 2: 1, 3: 0.1}.get(volatility_score, 1)

    amount_score = next((opt['score'] for opt in OPTIONS['amount'] if opt['val'] == q1_amount_val), 50)

    base_concentration = amount_score * volatility_multiplier * (concentration / 100)

    # 5. Apply Correction Factors
    # Apply 10x penalty if it's a spray task
    if q2_spray:
        base_concentration *= 10

    corrected_exposure = base_concentration * q4_ventilation * q5_time

    # 6. Calculate RCR
    rcr = corrected_exposure / chem['oel'] if chem['oel'] > 0 else float('inf')

    # 7. Determine Risk Level
    level = get_risk_level(rcr)

    return {
        'chem': chem,
        'conc': f"{corrected_exposure:.2f}",
        'rcr': f"{rcr:.2f}",
        'level': level
    }
