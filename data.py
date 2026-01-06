# -*- coding: utf-8 -*-

CHEMICAL_DATABASE = [
  {
    'id': 1,
    'cas': '108-88-3',
    'name': 'トルエン',
    'ghs': { 'flamLiq': 2, 'acuteToxInhale': 4, 'skinIrrit': 2, 'repr': 1, 'stotRe': 1 },
    'oel': 20,
    'bp': 110.6,
    'vp': 2900,
    'property': 'liquid'
  },
  {
    'id': 2,
    'cas': '67-64-1',
    'name': 'アセトン',
    'ghs': { 'flamLiq': 2, 'eyeIrrit': 2, 'stotSe': 3 },
    'oel': 500,
    'bp': 56,
    'vp': 24000,
    'property': 'liquid'
  },
  {
    'id': 3,
    'cas': '50-00-0',
    'name': 'ホルムアルデヒド',
    'ghs': { 'carc': 1, 'skinSens': 1, 'muta': 2 },
    'oel': 0.1,
    'bp': -19,
    'vp': 101300,
    'property': 'gas'
  },
  {
    'id': 4,
    'cas': '78-93-3',
    'name': 'メチルエチルケトン',
    'ghs': { 'flamLiq': 2, 'eyeIrrit': 2, 'stotSe': 3 },
    'oel': 200,
    'bp': 79.6,
    'vp': 10500,
    'property': 'liquid'
  },
  {
    'id': 5,
    'cas': '1330-20-7',
    'name': 'キシレン',
    'ghs': { 'flamLiq': 3, 'acuteToxInhale': 4, 'skinIrrit': 2, 'stotRe': 1 },
    'oel': 50,
    'bp': 138.5,
    'vp': 800,
    'property': 'liquid'
  }
]

OPTIONS = {
  'amount': [
    { 'val': 1, 'label': '大量 (トン単位)', 'score': 5000 },
    { 'val': 2, 'label': '中量 (ドラム缶/一斗缶)', 'score': 500 },
    { 'val': 3, 'label': '少量 (リットル単位)', 'score': 50 },
    { 'val': 4, 'label': '微量 (試験管/フラスコ)', 'score': 5 },
    { 'val': 5, 'label': '極微量', 'score': 0.5 },
  ],
  'ventilation': [
    { 'val': 0.01, 'label': '密閉設備 (完全囲い込み)' },
    { 'val': 0.1, 'label': '局所排気装置 (包囲型)' },
    { 'val': 0.5, 'label': '局所排気装置 (外付け型)' },
    { 'val': 1, 'label': '全体換気 (良好)' },
    { 'val': 10, 'label': '自然換気/換気なし' },
  ],
  'time': [
    { 'val': 0.1, 'label': '短時間 (1時間未満)' },
    { 'val': 0.5, 'label': '半日程度 (1-4時間)' },
    { 'val': 1, 'label': '通常 (4-8時間)' },
    { 'val': 2, 'label': '長時間 (残業含む)' },
  ],
  'frequency': [
    { 'val': 1, 'label': '毎日 (週1回以上)' },
    { 'val': 0.2, 'label': 'たまに (週1回未満)' },
  ],
  'skinArea': [
    { 'val': 1, 'label': '両手・前腕 (広範囲)' },
    { 'val': 0.1, 'label': '片手・指先 (局所的)' },
    { 'val': 0, 'label': '接触なし' },
  ]
}
