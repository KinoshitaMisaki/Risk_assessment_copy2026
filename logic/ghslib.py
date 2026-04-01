# logic/ghslib.py
import pandas as pd

GHS_PHYSICAL_HAZARD_COLUMNS = {
    'GHS_Explosives': 'Explosives',
    'GHS_FlammableGases': 'FlammableGases',
    'GHS_FlammableAerosols': 'FlammableAerosols',
    'GHS_OxidizingGases': 'OxidizingGases',
    'GHS_GasesUnderPressure': 'GasesUnderPressure',
    'GHS_FlammableLiquids': 'FlammableLiquids',
    'GHS_FlammableSolids': 'FlammableSolids',
    'GHS_SelfReactiveSubstances': 'SelfReactiveSubstances',
    'GHS_PyrophoricLiquids': 'PyrophoricLiquids',
    'GHS_PyrophoricSolids': 'PyrophoricSolids',
    'GHS_SelfHeatingSubstances': 'SelfHeatingSubstances',
    'GHS_SubstancesWhichInContactWithWaterEmitFlammableGases': 'SubstancesWhichInContactWithWaterEmitFlammableGases',
    'GHS_OxidizingLiquids': 'OxidizingLiquids',
    'GHS_OxidizingSolids': 'OxidizingSolids',
    'GHS_OrganicPeroxides': 'OrganicPeroxides',
    'GHS_CorrosiveToMetals': 'CorrosiveToMetals',
}

def parse_ghs_classifications(substance):
    """Parses the GHS columns from the substance data."""
    ghs_data = {}
    for col, name in GHS_PHYSICAL_HAZARD_COLUMNS.items():
        if col in substance and pd.notna(substance[col]):
            ghs_data[name] = substance[col]
    return ghs_data

def determine_physical_hazard_level(category, classification, amount_score):
    """Determinesthe hazard level for a single physical hazard category."""
    level = 0
    # Logic based on the specification's examples
    if category in ['Explosives', 'SelfReactiveSubstances', 'OrganicPeroxides']:
        if classification in ['区分A', '区分B', 'タイプA', 'タイプB']:
            level = 5
        elif classification in ['区分C', '区分D', 'タイプC', 'タイプD']:
            level = 4
        else:
            level = 3
    elif category in ['FlammableGases', 'FlammableAerosols', 'FlammableLiquids', 'FlammableSolids']:
        if classification in ['区分1', '区分2']:
            if amount_score >= 500: level = 5
            else: level = 4
        elif classification == '区分3':
            level = 3
    elif category in ['PyrophoricLiquids', 'PyrophoricSolids', 'SelfHeatingSubstances', 'SubstancesWhichInContactWithWaterEmitFlammableGases']:
        if classification == '区分1':
            level = 5
    elif category in ['OxidizingGases', 'OxidizingLiquids', 'OxidizingSolids']:
        if classification == '区分1':
            level = 5
    elif category == 'CorrosiveToMetals':
        if classification == '区分1':
            level = 3

    return level

def determine_physical_hazards(ghs_data, amount_score, safety_measures):
    """Determines the overall physical hazard risk level."""
    max_level = 0
    for category, classification in ghs_data.items():
        level = determine_physical_hazard_level(category, classification, amount_score)

        # Apply safety measure corrections
        if category in ['FlammableGases', 'FlammableLiquids'] and safety_measures['AntiFire_Q12']:
            level -= 1
        if category == 'Explosives' and safety_measures['AntiExplosion_Q13']:
            level -= 1

        if level > max_level:
            max_level = level

    return max(0, max_level) # Ensure level is not negative
