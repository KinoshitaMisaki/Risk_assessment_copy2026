// src/utils/riskLogic.js

/**
 * GHS有害性クラスの判定
 * @param {object} ghs - 物質のGHSデータ
 * @returns {object} - 各有害性クラスのレベル
 */
const getHazardClass = (ghs) => {
  // 経皮毒性のクラスを判定 (皮膚腐食性/刺激性, 皮膚感作性)
  const isSkinHazardous = (ghs?.skinIrrit && ghs.skinIrrit <= 2) || (ghs?.skinSens && ghs.skinSens === 1);

  // 発がん性
  const isCarcinogenic = ghs?.carc && ghs.carc <= 1;

  // 引火性
  const flamLevel = ghs?.flamLiq || 4; // 未定義は最も安全な区分4とする

  return { isSkinHazardous, isCarcinogenic, flamLevel };
};

/**
 * 揮発性・飛散性スコアを計算
 * @param {object} substance - 選択された化学物質
 * @param {string} form - 物理的形状 ('liquid', 'powder', 'gas')
 * @returns {number} - 1: 高, 2: 中, 3: 低
 */
const getVolatilityScore = (substance, form) => {
  if (form === 'gas' || (substance && substance.bp < 50)) {
    return 1; // 高揮発性
  }
  if (substance && substance.bp >= 50 && substance.bp < 150) {
    return 2; // 中揮発性
  }
  if (substance && substance.bp >= 150) {
    return 3; // 低揮発性
  }
  // 粉体も同様のロジックで飛散性を判定
  if (form === 'powder') {
    // ここでは粉体の物性データがないため、仮で中飛散性とする
    return 2;
  }
  return 2; // デフォルトは中揮発性
};


// 基本濃度推定のためのテーブル
// キー: 揮発性スコア (1:高, 2:中, 3:低)
// 値: 取扱量に応じた濃度 (q1_amount: 1-5に対応)
const BASE_CONCENTRATION_TABLE = {
  1: [5000, 500, 50, 5, 0.5],    // 高揮発性
  2: [500, 50, 5, 0.5, 0.05],   // 中揮発性
  3: [50, 5, 0.5, 0.05, 0.005], // 低揮発性
};

/**
 * 吸入リスクを計算
 * @param {object} substance - 物質情報
 * @param {object} conditions - 作業条件
 * @param {object} substanceInfo - ユーザーが入力した物質情報(含有率など)
 * @returns {object} - 計算結果 (推定濃度, RCR, レベル)
 */
export const calculateInhalationRisk = (substance, conditions, substanceInfo, basicInfo) => {
  if (!substance || !substance.oel) {
    return { conc: 0, rcr: 0, level: getInhalationRiskLevel(0) };
  }

  const volatilityScore = getVolatilityScore(substance, basicInfo.form);

  // q1_amountは1から始まるので、インデックスに変換
  const amountIndex = conditions.q1_amount - 1;
  let baseConc = BASE_CONCENTRATION_TABLE[volatilityScore][amountIndex] || 0;

  // 温度補正: 高温なら基本濃度を3倍
  if (conditions.q11_temp === 'high') {
    baseConc *= 3;
  }

  // 含有率で補正
  let predictedExposure = baseConc * (substanceInfo.concentration / 100);

  // 作業条件で補正
  predictedExposure *= conditions.q4_ventilation; // 換気
  predictedExposure *= conditions.q5_time;         // 時間
  predictedExposure *= conditions.q6_frequency;    // 頻度

  // スプレー作業なら10倍
  if (conditions.q2_spray) {
    predictedExposure *= 10;
  }

  // RCR (リスク比) の計算
  const rcr = predictedExposure / substance.oel;

  return {
    conc: predictedExposure.toFixed(2),
    rcr: rcr.toFixed(2),
    level: getInhalationRiskLevel(rcr),
  };
};

/**
 * 経皮リスクを計算
 * @param {object} substance - 物質情報
 * @param {object} conditions - 作業条件
 * @returns {object} - 計算結果 (スコア, レベル)
 */
export const calculateDermalRisk = (substance, conditions) => {
  if (!substance) {
    return { score: 0, level: getDermalRiskLevel(0) };
  }

  const { isSkinHazardous } = getHazardClass(substance.ghs);

  // 有害性係数 (GHS区分に基づく)
  const hazardFactor = isSkinHazardous ? 10 : 1; // 有害なら10倍

  // 対策係数 (手袋と教育)
  let protectionFactor = 1.0;
  if (conditions.q9_gloves) protectionFactor *= 0.1; // 適切な手袋でリスク1/10
  if (conditions.q10_glovesEdu) protectionFactor *= 0.8; // 教育で20%低減

  // スコア計算: 接触面積(係数) * 有害性係数 * 対策係数
  const score = conditions.q8_skinArea * hazardFactor * protectionFactor;

  return {
    score: score.toFixed(1),
    level: getDermalRiskLevel(score),
  };
};

/**
 * 危険性リスクを計算
 * @param {object} substance - 物質情報
 * @param {object} conditions - 作業条件
 * @returns {object} - 計算結果 (スコア, レベル)
 */
export const calculateDangerRisk = (substance, conditions) => {
  if (!substance) {
    return { score: 0, level: getDangerLevel(0) };
  }

  const { flamLevel } = getHazardClass(substance.ghs);

  // 物質の危険性スコア (引火性GHSに基づく)
  let score = 0;
  if (flamLevel <= 2) score = 10; // 区分1, 2は高リスク
  else if (flamLevel === 3) score = 5; // 区分3は中リスク
  else score = 1; // 区分4は低リスク

  // 対策による減点
  if (conditions.q12_ignition) score -= 3; // 着火源対策
  if (conditions.q13_explosion) score -= 3; // 防爆対策

  // 環境要因による加点
  if (conditions.q14_organic) score += 2; // 混触危険物
  if (conditions.q15_contact) score += 2; // 空気/水との接触

  // スコアは1未満にならない
  const finalScore = Math.max(1, score);

  return {
    score: finalScore,
    level: getDangerLevel(finalScore),
  };
};


// --- リスクレベル判定ヘルパー ---

export const getInhalationRiskLevel = (rcr) => {
  if (rcr < 0.1) return { val: 'I', color: 'bg-green-100 text-green-800', msg: 'リスクは許容範囲内です。現状の管理を維持してください。' };
  if (rcr < 0.5) return { val: 'II', color: 'bg-yellow-100 text-yellow-800', msg: '許容範囲内ですが、管理状況の継続的な確認が必要です。' };
  if (rcr < 1.0) return { val: 'III', color: 'bg-orange-100 text-orange-800', msg: 'リスクが高い可能性があります。対策の検討を推奨します。' };
  return { val: 'IV', color: 'bg-red-100 text-red-800', msg: 'リスクが許容範囲を超えています。直ちに改善策を実施してください。' };
};

export const getDermalRiskLevel = (score) => {
  if (score < 1) return { val: 'I', color: 'bg-green-100 text-green-800', msg: 'リスクは低いです。' };
  if (score < 5) return { val: 'II', color: 'bg-yellow-100 text-yellow-800', msg: '保護具の着用を検討してください。' };
  if (score < 10) return { val: 'III', color: 'bg-orange-100 text-orange-800', msg: '適切な保護手袋の着用が必要です。' };
  return { val: 'IV', color: 'bg-red-100 text-red-800', msg: '皮膚への接触を避けるための抜本的な対策が必要です。' };
};

export const getDangerLevel = (score) => {
  if (score <= 3) return { val: '低', color: 'bg-green-100 text-green-800', msg: '危険性は低いです。' };
  if (score <= 6) return { val: '中', color: 'bg-yellow-100 text-yellow-800', msg: '着火源対策など、基本的な対策を徹底してください。' };
  return { val: '高', color: 'bg-red-100 text-red-800', msg: '爆発・火災のリスクが高いです。専門家による評価と対策を推奨します。' };
};
