# app/logic/constants.py

# 4.1.2 Unit Conversion Constants
WATER_SOL_CONVERSION = {
    "mg/L": 0.001,
    "g/100mL": 10,
    "g/L": 1,
    "mg/cm^3": 1,
}

VP_CONVERSION = {
    "Pa": 1,
    "kPa": 1000,
    "hPa": 100,
    "mPa": 0.001,
    "mmHg": 133.3,
    "Torr": 133.3,
}

# 4.5.2 Initial Exposure Concentration (Initial_EP) Matrices
# Liquids (ppm)
INITIAL_EP_LIQUID = {
    # Amount Level (row) x Volatility Rank (col)
    # Rows: 1:大, 2:中, 3:小, 4:微, 5:極
    # Cols: 1:高, 2:中, 3:低, 4:極低
    (1, 1): 5000, (1, 2): 500, (1, 3): 50, (1, 4): 5,
    (2, 1): 500,  (2, 2): 500, (2, 3): 50, (2, 4): 5,
    (3, 1): 50,   (3, 2): 50,  (3, 3): 5,  (3, 4): 0.5,
    (4, 1): 5,    (4, 2): 5,   (4, 3): 5,  (4, 4): 0.5,
    (5, 1): 0.5,  (5, 2): 5,   (5, 3): 0.5,(5, 4): 0.05,
}

# Solids (mg/m^3)
INITIAL_EP_SOLID = {
    # Amount Level: 1:Large, 2:Medium, 3:Small, 4:Trace, 5:Very Trace
    # Dustiness Rank: 1:High, 2:Medium, 3:Low
    (1, 1): 100, (1, 2): 100, (1, 3): 1,
    (2, 1): 10,  (2, 2): 10,  (2, 3): 1,
    (3, 1): 1,   (3, 2): 0.1, (3, 3): 0.1,
    (4, 1): 0.1, (4, 2): 0.1, (4, 3): 0.1,
    (5, 1): 0.1, (5, 2): 0.1, (5, 3): 0.01,
}

# 4.6.1 Dermal Assessment Constants
DERMAL_CONSTANTS = {
    "R": 8.314,      # Gas constant
    "T": 293,        # Temperature (K)
    "AirVel": 1080,  # Air velocity (m/h)
    "Visc": 0.054,   # Dynamic viscosity (m^2/h)
    "L": 0.1,        # Evaporation length (m)
}

# Risk Level Mapping
RISK_LEVEL_MAP = {
    (10, float('inf')): "IV",
    (1, 10): "III",
    (0.5, 1): "II-B",
    (0.1, 0.5): "II-A",
    (-float('inf'), 0.1): "I",
}

RISK_LEVEL_MAP_DERMAL = {
    (10, float('inf')): "IV",
    (1, 10): "III",
    (0.1, 1): "II",
    (-float('inf'), 0.1): "I",
}

RISK_LEVEL_MAP_PHYS = {
    4: "IV",
    5: "IV",
    3: "III",
    2: "II",
    1: "I",
}
