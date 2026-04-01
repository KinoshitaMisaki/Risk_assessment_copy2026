# logic/input_mapping.py

# Mapping from Japanese text to the numeric codes used in the logic.

AMOUNT_MAP = {
    '大量 (1kL以上)': 1,
    '中量 (1L以上～1000L未満)': 2,
    '少量 (100mL以上～1000mL未満)': 3,
    '微量 (10mL以上～100mL未満)': 4,
    '極微量 (10mL未満)': 5,
    '極微量（10mL未満）': 5 # Alias for full-width parenthesis from user example
}

SPRAY_MAP = {
    'はい': 10,
    'いいえ': 1
}

AREA_MAP = {
    'はい': 10,
    'いいえ': 1
}

VENTILATION_MAP = {
    '換気レベルA（特に換気のない部屋）': 4,
    '換気レベルB（全体換気）': 3,
    '換気レベルC（工業的な全体換気、屋外作業）': 1,
    '換気レベルD（外付け式局所排気装置）': 0.1,
    '換気レベルE（囲い式局所排気装置）': 0.01,
    '換気レベルF（密閉容器内での取扱い）': 0.001
}

TIME_MAP = {
    '8時間超': 10,
    '7時間超～8時間以下': 8,
    '6時間超～7時間以下': 7,
    '5時間超～6時間以下': 6,
    '4時間超～5時間以下': 5,
    '3時間超～4時間以下': 4,
    '2時間超～3時間以下': 3,
    '1時間超～2時間以下': 2,
    '30分超～1時間以下': 1,
    '30分以下': 0.5
}

FREQUENCY_MAP = {
    '週1回以上': 1,
    '週1回未満': 0
}

VARIATION_MAP = {
    'ばく露濃度の変動が大きい作業': 6,
    '変動が小さい': 4,
    'ばく露濃度の変動が小さい作業': 4 # Alias for common phrasing
}

SKIN_AREA_MAP = {
    '大きなコインサイズ': 10,
    '片手の手のひら付着': 240,
    '両手の手のひら': 480,
    '両手全体': 960,
    '両手及び手首': 1500,
    '両手の肘から下全体': 1980
}

GLOVE_MAP = {
    '着用していない / 情報のない手袋': 1,
    '耐透過性・耐浸透性の手袋の着用している': 0.2
}

EDUCATION_MAP = {
    '行っていない': 1,
    '基本的な教育': 0.5,
    '十分な教育や訓練を行っている': 0.25
}

TEMP_MAP = {
    '室温': 20,
    '室温以上': 50
}

BOOL_MAP = {
    'はい': True,
    'いいえ': False
}

# A dictionary to hold all mappings for easy access
COLUMN_MAPPINGS = {
    'Amount_Q1': AMOUNT_MAP,
    'Spray_Q2': SPRAY_MAP,
    'Area_Q3': AREA_MAP,
    'Ventilation_Q4': VENTILATION_MAP,
    'Time_Q5': TIME_MAP,
    'Frequency_Q6': FREQUENCY_MAP,
    'Variation_Q7': VARIATION_MAP,
    'SkinArea_Q8': SKIN_AREA_MAP,
    'Glove_Q9': GLOVE_MAP,
    'Education_Q10': EDUCATION_MAP,
    'Temp_Q11': TEMP_MAP,
    'AntiFire_Q12': BOOL_MAP,
    'AntiExplosion_Q13': BOOL_MAP,
    'AntiMetal_Q14': BOOL_MAP,
    'ContactWaterAir_Q15': BOOL_MAP
}
