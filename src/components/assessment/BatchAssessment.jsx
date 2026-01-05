// src/components/assessment/BatchAssessment.jsx
import React, { useState, useMemo } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, Download, AlertTriangle, CheckCircle } from 'lucide-react';
import { parseTargetsCSV, exportResultsCSV } from '../../utils/csvHelper';
import {
  calculateInhalationRisk,
  calculateDermalRisk,
  calculateDangerRisk
} from '../../utils/riskLogic';

// Default conditions to use if a value is missing from the CSV
const DEFAULT_CONDITIONS = {
  q1_amount: 3,
  q2_spray: false,
  q4_ventilation: 1,
  q5_time: 1,
  q6_frequency: 1,
  q8_skinArea: 1,
  q9_gloves: false,
  q10_glovesEdu: false,
  q11_temp: 'room',
  q12_ignition: false,
  q13_explosion: false,
  q14_organic: false,
  q15_contact: false,
};


export const BatchAssessment = ({ findSubstance }) => {
  const [assessmentTargets, setAssessmentTargets] = useState([]);
  const [error, setError] = useState(null);

  const onDrop = async (acceptedFiles) => {
    setError(null);
    setAssessmentTargets([]);
    const file = acceptedFiles[0];
    if (!file) {
      setError("ファイルが選択されませんでした。");
      return;
    }
    try {
      const targets = await parseTargetsCSV(file);
       if (targets.length === 0) {
        setError("CSVファイルに有効なデータが含まれていません。");
        return;
      }
      setAssessmentTargets(targets);
    } catch (err) {
      setError("CSVファイルの解析に失敗しました。形式を確認してください。");
      console.error(err);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/csv': ['.csv'] },
    multiple: false,
  });

  const results = useMemo(() => {
    return assessmentTargets.map(target => {
      const substance = findSubstance(target.cas || target.name);
      if (!substance) {
        return {
          assessment: target,
          substance: null,
          error: "物質がDBに見つかりません。",
        };
      }

      // Merge parsed conditions with defaults
      const conditions = { ...DEFAULT_CONDITIONS, ...target.conditions };

      const basicInfo = { form: substance.property || 'liquid' };
      const substanceInfo = { concentration: target.concentration || 100 };

      return {
        assessment: target,
        substance,
        results: {
          inhalation: calculateInhalationRisk(substance, conditions, substanceInfo, basicInfo),
          dermal: calculateDermalRisk(substance, conditions),
          danger: calculateDangerRisk(substance, conditions),
        },
      };
    });
  }, [assessmentTargets, findSubstance]);

  return (
    <main className="max-w-7xl mx-auto p-4 md:p-6">
      <div {...getRootProps()} className={`border-4 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-slate-300 hover:border-blue-400'}`}>
        <input {...getInputProps()} />
        <Upload className="w-12 h-12 mx-auto text-slate-400 mb-4" />
        <h2 className="text-lg font-bold text-slate-700">一括判定用CSVファイルをアップロード</h2>
        <p className="text-sm text-slate-500">
          {isDragActive ? 'ここにファイルをドロップ' : 'ここをクリックするか、ファイルをドラッグ＆ドロップしてください'}
        </p>
      </div>

      {error && <div className="mt-4 p-4 bg-red-100 text-red-800 border border-red-200 rounded-lg">{error}</div>}

      {results.length > 0 && (
        <div className="mt-8 bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="px-4 py-3 border-b flex justify-between items-center">
            <h3 className="font-bold text-slate-700">一括判定結果 ({results.length}件)</h3>
            <button
              onClick={() => exportResultsCSV(results)}
              className="px-4 py-2 bg-green-600 text-white text-sm rounded-md hover:bg-green-500 flex items-center gap-2"
            >
              <Download className="w-4 h-4" />
              結果をダウンロード
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-slate-50 text-xs text-slate-500 uppercase">
                <tr>
                  <th className="px-4 py-3">物質名</th>
                  <th className="px-4 py-3 text-center">吸入</th>
                  <th className="px-4 py-3 text-center">経皮</th>
                  <th className="px-4 py-3 text-center">危険性</th>
                  <th className="px-4 py-3">備考</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {results.map((res, index) => (
                  <tr key={index} className={res.error ? 'bg-red-50' : 'hover:bg-slate-50'}>
                    <td className="px-4 py-3 font-medium">
                      {res.assessment.name || res.substance?.name || 'N/A'}
                      <span className="block text-xs text-slate-400">
                        CAS: {res.assessment.cas || res.substance?.cas || 'N/A'}
                      </span>
                    </td>
                    {res.error ? (
                      <td colSpan="4" className="px-4 py-3 text-red-600">
                        <div className="flex items-center gap-2">
                          <AlertTriangle className="w-4 h-4" />
                          {res.error}
                        </div>
                      </td>
                    ) : (
                      <>
                        <td className="px-4 py-3 text-center">
                          <span className={`px-2 py-1 text-xs font-bold rounded-full ${res.results.inhalation.level.color}`}>
                            {res.results.inhalation.level.val}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-center">
                          <span className={`px-2 py-1 text-xs font-bold rounded-full ${res.results.dermal.level.color}`}>
                            {res.results.dermal.level.val}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-center">
                          <span className={`px-2 py-1 text-xs font-bold rounded-full ${res.results.danger.level.color}`}>
                            {res.results.danger.level.val}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-green-600 text-xs">
                           <div className="flex items-center gap-2">
                             <CheckCircle className="w-4 h-4" />
                             正常に評価完了
                           </div>
                        </td>
                      </>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </main>
  );
};
