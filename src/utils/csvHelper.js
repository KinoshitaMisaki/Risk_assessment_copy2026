// src/utils/csvHelper.js
import Papa from 'papaparse';
import { OPTIONS } from '../data/options';

/**
 * SubstanceList.csv をパースして、アプリケーションで使える形式に変換する
 * (This function remains unchanged)
 */
export const parseSubstancesCSV = (file) => {
  return new Promise((resolve, reject) => {
    Papa.parse(file, {
      header: true,
      skipEmptyLines: true,
      complete: (results) => {
        try {
          const parsedData = results.data.map(row => {
            const oel =
              parseFloat(row['8時間']) ||
              parseFloat(row['許容濃度']) ||
              parseFloat(row['TWA']) ||
              parseFloat(row['MAK']) ||
              parseFloat(row['STEL']) ||
              null;
            const propertyMap = { '1': 'liquid', '2': 'powder', '3': 'gas' };
            return {
              id: parseInt(row['No'], 10),
              cas: row['CAS RN'],
              name: row['日本語名称'],
              enName: row['英語名称'],
              property: propertyMap[row['性状']] || 'liquid',
              mw: parseFloat(row['分子量']),
              bp: parseFloat(row['沸点']),
              vp: parseFloat(row['蒸気圧']),
              oel: oel,
              ghs: {
                flamLiq: parseInt(row['引火性液体'], 10) || null,
                acuteToxInhale: parseInt(row['急性毒性（吸入：蒸気）'], 10) || null,
                skinIrrit: parseInt(row['皮膚腐食性／刺激性'], 10) || null,
                skinSens: parseInt(row['呼吸器感作性又は皮膚感作性（皮膚感作性）'], 10) || null,
                carc: parseInt(row['発がん性'], 10) || null,
                repr: parseInt(row['生殖毒性'], 10) || null,
                stotRe: parseInt(row['特定標的臓器毒性（反復ばく露）'], 10) || null,
                eyeIrrit: parseInt(row['眼に対する重篤な損傷性／眼刺激性'], 10) || null,
                stotSe: parseInt(row['特定標的臓器毒性（単回ばく露）'], 10) || null,
                muta: parseInt(row['生殖細胞変異原性'], 10) || null,
              },
            };
          });
          resolve(parsedData.filter(item => item.id && item.name && item.cas));
        } catch (error) {
          reject(error);
        }
      },
      error: (error) => {
        reject(error);
      },
    });
  });
};

// --- New and Updated functions for Batch Assessment ---

// Helper to create a reverse map from label to value for faster lookups
const createReverseOptionMap = (optionsArray) => {
    const map = {};
    optionsArray.forEach(opt => {
        // Main label
        map[opt.label] = opt.val;
        // Also handle partial labels, e.g., "大量" instead of "大量 (トン単位)"
        const shortLabel = opt.label.split(' ')[0];
        if (shortLabel !== opt.label) {
            map[shortLabel] = opt.val;
        }
    });
    return map;
};

const reverseOptions = {
    amount: createReverseOptionMap(OPTIONS.amount),
    ventilation: createReverseOptionMap(OPTIONS.ventilation),
    time: createReverseOptionMap(OPTIONS.time),
    frequency: createReverseOptionMap(OPTIONS.frequency),
    skinArea: createReverseOptionMap(OPTIONS.skinArea),
};

const booleanMap = {
    'はい': true, 'yes': true, 'true': true, 'あり': true, '実施': true, '着用': true,
    'いいえ': false, 'no': false, 'false': false, 'なし': false, '未実施': false, '未着用': false,
};

const tempMap = {
    '高温': 'high',
    '常温': 'room',
};

/**
 * targets.csv (一括評価用ファイル) をパースし、値を内部形式に変換する
 * @param {File} file - アップロードされたCSVファイル
 * @returns {Promise<Array<object>>} - 評価対象オブジェクトの配列
 */
export const parseTargetsCSV = (file) => {
    // Map CSV column headers to internal state keys
    const conditionMapping = {
        '取扱量': 'q1_amount',
        'スプレー作業': 'q2_spray',
        '換気': 'q4_ventilation',
        '作業時間': 'q5_time',
        '頻度': 'q6_frequency',
        '接触面積': 'q8_skinArea',
        '手袋': 'q9_gloves',
        '手袋教育': 'q10_glovesEdu',
        '温度': 'q11_temp',
        '着火源対策': 'q12_ignition',
        '防爆対策': 'q13_explosion',
        '混触危険物': 'q14_organic',
        '空気水接触': 'q15_contact',
    };

    return new Promise((resolve, reject) => {
        Papa.parse(file, {
            header: true,
            skipEmptyLines: true,
            complete: (results) => {
                const parsedData = results.data.map(row => {
                    const target = {
                        cas: row['CAS RN'] || row['cas'],
                        name: row['物質名'] || row['name'],
                        concentration: parseFloat(row['含有率']) || 100,
                        conditions: {},
                    };

                    for (const [csvHeader, internalKey] of Object.entries(conditionMapping)) {
                        const rawValue = row[csvHeader]?.trim();
                        if (rawValue === undefined) continue;

                        let parsedValue;
                        if (internalKey in reverseOptions) {
                            parsedValue = reverseOptions[internalKey][rawValue];
                        } else if (internalKey === 'q11_temp') {
                            parsedValue = tempMap[rawValue] || 'room';
                        } else { // Boolean fields
                            parsedValue = booleanMap[rawValue.toLowerCase()] || false;
                        }

                        target.conditions[internalKey] = parsedValue;
                    }
                    return target;
                });
                resolve(parsedData);
            },
            error: (error) => reject(error),
        });
    });
};

/**
 * 一括評価の結果をCSV形式でダウンロードする
 * (This function remains unchanged)
 */
export const exportResultsCSV = (results) => {
  if (!results || results.length === 0) {
    alert("エクスポートするデータがありません。");
    return;
  }

  const formatedResults = results.map(res => ({
    'CAS RN': res.substance.cas,
    '物質名': res.substance.name,
    '含有率(%)': res.assessment.concentration,
    '推定ばく露濃度(ppm)': res.results.inhalation.conc,
    'RCR': res.results.inhalation.rcr,
    '吸入リスクレベル': res.results.inhalation.level.val,
    '経皮リスクスコア': res.results.dermal.score,
    '経皮リスクレベル': res.results.dermal.level.val,
    '危険性スコア': res.results.danger.score,
    '危険性レベル': res.results.danger.level.val,
  }));

  const csv = Papa.unparse(formatedResults);

  const blob = new Blob([`\uFEFF${csv}`], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);

  link.setAttribute('href', url);
  link.setAttribute('download', `risk_assessment_results_${new Date().toISOString().slice(0,10)}.csv`);
  link.style.visibility = 'hidden';

  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};
