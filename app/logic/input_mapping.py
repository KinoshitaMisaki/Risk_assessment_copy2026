# app/logic/input_mapping.py

# Mapping from descriptive Japanese text to internal numeric/boolean values.
# This allows users to fill the CSV with human-readable choices.

AMOUNT_LEVEL_MAP = {
    '大量 (1kL以上)': 1,
    '中量 (1L以上～1000L未満)': 2,
    '少量 (100mL以上～1000mL未満)': 3,
    '微量 (10mL以上～100mL未満)': 4,
    '極微量 (10mL未満)': 5,
}

BOOL_MAP_JA = {
    "はい": True,
    "いいえ": False,
}

VENTILATION_MAP = {
    '換気レベルA（特に換気のない部屋）': 4,
    '換気レベルB（全体換気）': 3,
    '換気レベルC（工業的な全体換気、屋外作業）': 1,
    '換気レベルD（外付け式局所排気装置）': 0.1,
    '換気レベルE（囲い式局所排気装置）': 0.01,
    '換気レベルF（密閉容器内での取扱い）': 0.001,
}

WORK_TIME_MAP = {
    '8時間超': 10,
    '7時間超～8時間以下': 8,
    '6時間超～7時間以下': 7,
    '5時間超～6時間以下': 6,
    '4時間超～5時間以下': 5,
    '3時間超～4時間以下': 4,
    '2時間超～3時間以下': 3,
    '1時間超～2時間以下': 2,
    '30分超～1時間以下': 1,
    '30分以下': 0.5,
}

FREQ_TYPE_MAP = {
    '週1回以上': 1,
    '週1回未満': 0,
}

VARIATION_MAP = {
    'ばく露濃度の変動が小さい作業': 4,
    'ばく露濃度の変動が大きい作業': 6,
}

SKIN_AREA_MAP = {
    '大きなコインのサイズ、小さな飛沫': 10,
    '片手の手のひら付着': 240,
    '両手の手のひらに付着': 480,
    '両手全体に付着': 960,
    '両手及び手首': 1500,
    '両手の肘から下全体': 1980,
}

GLOVE_TYPE_MAP = {
    "手袋を着用していない": 1,
    "取扱物質に関する情報のない手袋を使用している": 1,
    "耐透過性・耐浸透性の手袋の着用している": 0.2,
}

GLOVE_EDU_MAP = {
    "教育や訓練を行っていない": 1,
    "基本的な教育や訓練を行っている": 0.5,
    "十分な教育や訓練を行っている": 0.25,
}

PROCESS_TEMP_MAP = {
    '室温': 20,
    '室温以上': 50,
}

# A dictionary to hold all mappings for easy access in the preprocessing step
ALL_MAPPINGS = {
    'amount_level': AMOUNT_LEVEL_MAP,
    'spray_work': BOOL_MAP_JA,
    'area_high': BOOL_MAP_JA,
    'ventilation': VENTILATION_MAP,
    'work_time_daily': WORK_TIME_MAP,
    'freq_type': FREQ_TYPE_MAP,
    'exposure_variation': VARIATION_MAP,
    'skin_area': SKIN_AREA_MAP,
    'glove_type': GLOVE_TYPE_MAP,
    'glove_edu': GLOVE_EDU_MAP,
    'process_temp': PROCESS_TEMP_MAP,
    'ignition_source': BOOL_MAP_JA,
    'explosive_atm': BOOL_MAP_JA,
    'metal_contact': BOOL_MAP_JA,
    'water_contact': BOOL_MAP_JA,
}
