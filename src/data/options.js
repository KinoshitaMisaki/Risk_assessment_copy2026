// src/data/options.js

export const OPTIONS = {
  amount: [
    { val: 1, label: '大量 (トン単位)' },
    { val: 2, label: '中量 (ドラム缶/一斗缶)' },
    { val: 3, label: '少量 (リットル単位)' },
    { val: 4, label: '微量 (試験管/フラスコ)' },
    { val: 5, label: '極微量' },
  ],
  ventilation: [
    { val: 0.01, label: '密閉設備 (完全囲い込み)' },
    { val: 0.1, label: '局所排気装置 (包囲型)' },
    { val: 0.5, label: '局所排気装置 (外付け型)' },
    { val: 1, label: '全体換気 (良好)' },
    { val: 10, label: '自然換気/換気なし' },
  ],
  time: [
    { val: 0.1, label: '短時間 (1時間未満)' },
    { val: 0.5, label: '半日程度 (1-4時間)' },
    { val: 1, label: '通常 (4-8時間)' },
    { val: 2, label: '長時間 (残業含む)' },
  ],
  frequency: [
    { val: 1, label: '毎日 (週1回以上)' },
    { val: 0.2, label: 'たまに (週1回未満)' },
  ],
  skinArea: [
    { val: 1, label: '両手・前腕 (広範囲)' },
    { val: 0.1, label: '片手・指先 (局所的)' },
    { val: 0, label: '接触なし' },
  ]
};
