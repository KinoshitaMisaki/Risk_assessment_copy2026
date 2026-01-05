// src/components/assessment/IndividualAssessment.jsx
import React, { useState, useMemo } from 'react';
import { Wind, User, AlertTriangle, Activity, Droplet, Zap, Save } from 'lucide-react';

import {
  calculateInhalationRisk,
  calculateDermalRisk,
  calculateDangerRisk
} from '../../utils/riskLogic';
import { OPTIONS } from '../../data/options';

import { Card, CardHeader, CardContent } from '../ui/Card';
import { QuestionItem, Toggle } from '../ui/QuestionItem';
import { CloudIcon } from '../ui/CloudIcon';

const RiskResultCard = ({ result }) => {
    if (!result || !result.chem) {
      return (
        <div className="p-10 text-center text-slate-400">
          <Activity className="w-12 h-12 mx-auto mb-3 opacity-20" />
          <p className="text-sm">左側の情報を入力すると<br/>判定結果が表示されます。</p>
        </div>
      );
    }

    return (
      <div className="divide-y divide-slate-100">
        <div className="p-4 bg-blue-50 text-sm">
          <p className="font-bold text-blue-900">{result.chem.name}</p>
          <p className="text-blue-700 text-xs mt-1">
            CAS: {result.chem.cas} | 許容濃度: {result.chem.oel || 'N/A'} ppm
          </p>
        </div>

        {result.inhalation && (
          <div className="p-5">
            <h3 className="text-sm font-bold text-slate-600 mb-3 flex items-center gap-2">
              <Wind className="w-4 h-4 text-blue-500" /> 吸入リスク
            </h3>
            <div className="flex items-center justify-between mb-4">
              <div className={`px-4 py-2 rounded-lg font-bold text-2xl ${result.inhalation.level.color} border border-current`}>
                {result.inhalation.level.val}
              </div>
              <div className="text-right">
                <p className="text-xs text-slate-500">推定ばく露濃度</p>
                <p className="text-lg font-mono font-bold">{result.inhalation.conc} <span className="text-xs font-normal text-slate-500">ppm</span></p>
              </div>
            </div>
            <div className="text-xs text-slate-600 bg-slate-50 p-2 rounded">
              <span className="font-bold">判定: </span> {result.inhalation.level.msg}
              <br />
              <span className="text-slate-400">(リスク比: {result.inhalation.rcr})</span>
            </div>
          </div>
        )}

        {result.dermal && (
          <div className="p-5 bg-slate-50/30">
            <h3 className="text-sm font-bold text-slate-600 mb-3 flex items-center gap-2">
              <User className="w-4 h-4 text-purple-500" /> 経皮吸収リスク
            </h3>
            <div className="flex items-center gap-4">
              <div className={`px-3 py-1 rounded font-bold text-lg ${result.dermal.level.color} border border-current`}>
                {result.dermal.level.val}
              </div>
              <p className="text-xs text-slate-500">{result.dermal.level.msg}</p>
            </div>
          </div>
        )}

        {result.danger && (
          <div className="p-5">
            <h3 className="text-sm font-bold text-slate-600 mb-3 flex items-center gap-2">
              <Zap className="w-4 h-4 text-orange-500" /> 危険性 (爆発・火災)
            </h3>
            <div className="flex items-center gap-4">
              <div className={`px-3 py-1 rounded font-bold text-lg ${result.danger.level.color} border border-current`}>
                {result.danger.level.val}
              </div>
              <p className="text-xs text-slate-500">{result.danger.level.msg}</p>
            </div>
          </div>
        )}

        <div className="p-5 bg-slate-50">
          <button className="w-full bg-blue-700 hover:bg-blue-600 text-white py-3 rounded-lg font-bold flex items-center justify-center gap-2 shadow transition">
            <Save className="w-4 h-4" /> レポート保存・PDF出力
          </button>
        </div>
      </div>
    );
};

export const IndividualAssessment = ({ substanceDB }) => {
    // --- State Management ---
    const [basicInfo, setBasicInfo] = useState({
      title: '洗浄作業のリスク評価', place: '第1工場 洗浄室', productName: '洗浄剤A',
      targets: { inhalation: true, dermal: true, danger: true },
      form: 'liquid',
    });
    const [substance, setSubstance] = useState({ id: '', concentration: 100 });
    const [conditions, setConditions] = useState({
      q1_amount: 3, q2_spray: false, q3_area: false, q4_ventilation: 1,
      q5_time: 1, q6_frequency: 1, q7_variation: 'medium', q8_skinArea: 1,
      q9_gloves: false, q10_glovesEdu: false, q11_temp: 'room', q12_ignition: false,
      q13_explosion: false, q14_organic: false, q15_contact: false,
    });

    // --- Handlers ---
    const handleBasicChange = (key, val) => setBasicInfo(prev => ({ ...prev, [key]: val }));
    const handleTargetChange = (key) => setBasicInfo(prev => ({ ...prev, targets: { ...prev.targets, [key]: !prev.targets[key] } }));
    const handleCondChange = (key, val) => setConditions(prev => ({ ...prev, [key]: val }));

    // --- Calculation Logic using useMemo to avoid cascading renders ---
    const result = useMemo(() => {
      const selectedSubstance = substanceDB.find(s => s.id == substance.id);

      if (!selectedSubstance) {
        return null;
      }

      const newResult = { chem: selectedSubstance };
      if (basicInfo.targets.inhalation) {
        newResult.inhalation = calculateInhalationRisk(selectedSubstance, conditions, substance, basicInfo);
      }
      if (basicInfo.targets.dermal) {
        newResult.dermal = calculateDermalRisk(selectedSubstance, conditions);
      }
      if (basicInfo.targets.danger) {
        newResult.danger = calculateDangerRisk(selectedSubstance, conditions);
      }
      return newResult;

    }, [basicInfo, substance, conditions, substanceDB]);

    return (
      <main className="max-w-7xl mx-auto p-4 md:p-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* === Left Column: Input Area === */}
        <div className="lg:col-span-7 space-y-6">
            <Card>
                <CardHeader step="1" title="対象製品の基本情報" />
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="text-xs font-bold text-slate-500 block mb-1">タイトル</label>
                            <input type="text" className="w-full p-2 border rounded text-sm" placeholder="例: 洗浄作業のリスク評価"
                            value={basicInfo.title} onChange={(e) => handleBasicChange('title', e.target.value)} />
                        </div>
                        <div>
                            <label className="text-xs font-bold text-slate-500 block mb-1">実施場所</label>
                            <input type="text" className="w-full p-2 border rounded text-sm" placeholder="例: 第1工場 洗浄室"
                            value={basicInfo.place} onChange={(e) => handleBasicChange('place', e.target.value)} />
                        </div>
                        <div className="md:col-span-2">
                            <label className="text-xs font-bold text-slate-500 block mb-1">製品名等</label>
                            <input type="text" className="w-full p-2 border rounded text-sm" placeholder="製品名を入力"
                            value={basicInfo.productName} onChange={(e) => handleBasicChange('productName', e.target.value)} />
                        </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 mt-4 border-t border-dashed border-slate-200">
                        <div>
                            <label className="text-xs font-bold text-slate-500 block mb-2">評価対象</label>
                            <div className="flex flex-wrap gap-3">
                                {Object.keys(basicInfo.targets).map(key => (
                                <label key={key} className={`flex items-center gap-2 px-3 py-2 rounded-md border cursor-pointer text-sm transition ${basicInfo.targets[key] ? 'bg-blue-50 border-blue-400 text-blue-800' : 'bg-white border-slate-200'}`}>
                                    <input type="checkbox" checked={basicInfo.targets[key]} onChange={() => handleTargetChange(key)} className="accent-blue-600" />
                                    {key === 'inhalation' ? '吸入' : key === 'dermal' ? '経皮' : '危険性'}
                                </label>
                                ))}
                            </div>
                        </div>
                        <div>
                            <label className="text-xs font-bold text-slate-500 block mb-2">性状</label>
                            <div className="flex gap-3">
                                {[
                                    { id: 'liquid', label: '液体', icon: Droplet },
                                    { id: 'powder', label: '粉体', icon: Wind },
                                    { id: 'gas', label: '気体', icon: CloudIcon }
                                ].map(type => (
                                    <button key={type.id} onClick={() => handleBasicChange('form', type.id)}
                                    className={`flex items-center gap-1.5 px-3 py-2 rounded-md border text-sm transition ${basicInfo.form === type.id ? 'bg-blue-600 text-white border-blue-600' : 'hover:bg-slate-50'}`}>
                                    <type.icon className="w-4 h-4" /> {type.label}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>

            <Card>
                <CardHeader step="2" title="取扱い物質情報" />
                <CardContent>
                    <div className="flex flex-col md:flex-row gap-4 items-start">
                    <div className="flex-1 w-full">
                        <label className="text-xs font-bold text-slate-500 block mb-1" htmlFor="substance-select">物質選択 (DB検索)</label>
                        <select
                        id="substance-select"
                        value={substance.id}
                        onChange={(e) => setSubstance({ ...substance, id: e.target.value })}
                        className="w-full p-2 border border-slate-300 rounded focus:ring-2 focus:ring-blue-500 bg-white"
                        >
                        <option value="">物質を選択してください...</option>
                        {substanceDB.map(c => (
                            <option key={c.id} value={c.id}>{c.name} (CAS: {c.cas})</option>
                        ))}
                        </select>
                    </div>
                    <div className="w-full md:w-32">
                        <label className="text-xs font-bold text-slate-500 block mb-1" htmlFor="concentration-input">含有率 (wt%)</label>
                        <input type="number" min="0" max="100"
                        id="concentration-input"
                        value={substance.concentration} onChange={(e) => setSubstance({ ...substance, concentration: Number(e.target.value) })}
                        className="w-full p-2 border border-slate-300 rounded text-right"
                        />
                    </div>
                    </div>
                    {substance.id && result && result.chem && (
                    <div className="mt-3 p-3 bg-blue-50 text-blue-800 text-xs rounded border border-blue-100 flex gap-4">
                        <span>許容濃度: <strong>{result.chem.oel || 'N/A'} ppm</strong></span>
                        <span>沸点: <strong>{result.chem.bp || 'N/A'} °C</strong></span>
                    </div>
                    )}
                </CardContent>
            </Card>

            <Card>
                <CardHeader step="3" title="作業内容に関する質問" />
                <div className="divide-y divide-slate-100">
                    <CardContent className="space-y-6">
                        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2"><Wind className="w-4 h-4" /> ばく露・吸入要因</h3>
                        <QuestionItem q="Q1" text="製品の取扱量はどのくらいですか。" htmlFor="q1-amount">
                            <select id="q1-amount" value={conditions.q1_amount} onChange={(e) => handleCondChange('q1_amount', Number(e.target.value))} className="w-full p-2 border rounded text-sm bg-slate-50">
                            {OPTIONS.amount.map(opt => <option key={opt.val} value={opt.val}>{opt.label}</option>)}
                            </select>
                        </QuestionItem>
                        <QuestionItem q="Q2" text="スプレー作業など飛散しやすい作業ですか。"><Toggle value={conditions.q2_spray} onChange={(v) => handleCondChange('q2_spray', v)} /></QuestionItem>
                        <QuestionItem q="Q4" text="作業場の換気状況はどのくらいですか。" htmlFor="q4-ventilation">
                            <select id="q4-ventilation" value={conditions.q4_ventilation} onChange={(e) => handleCondChange('q4_ventilation', Number(e.target.value))} className="w-full p-2 border rounded text-sm bg-slate-50">
                            {OPTIONS.ventilation.map(opt => <option key={opt.val} value={opt.val}>{opt.label}</option>)}
                            </select>
                        </QuestionItem>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <QuestionItem q="Q5" text="1日の作業時間" htmlFor="q5-time">
                                <select id="q5-time" value={conditions.q5_time} onChange={(e) => handleCondChange('q5_time', Number(e.target.value))} className="w-full p-2 border rounded text-sm bg-slate-50">
                                {OPTIONS.time.map(opt => <option key={opt.val} value={opt.val}>{opt.label}</option>)}
                                </select>
                            </QuestionItem>
                            <QuestionItem q="Q6" text="取扱頻度" htmlFor="q6-frequency">
                                <select id="q6-frequency" value={conditions.q6_frequency} onChange={(e) => handleCondChange('q6_frequency', Number(e.target.value))} className="w-full p-2 border rounded text-sm bg-slate-50">
                                {OPTIONS.frequency.map(opt => <option key={opt.val} value={opt.val}>{opt.label}</option>)}
                                </select>
                            </QuestionItem>
                        </div>
                    </CardContent>
                    <CardContent className="space-y-6 bg-slate-50/50">
                        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2"><User className="w-4 h-4" /> 経皮・接触要因</h3>
                        <QuestionItem q="Q8" text="皮膚に接触する面積はどれぐらいですか。" htmlFor="q8-skin-area">
                            <select id="q8-skin-area" value={conditions.q8_skinArea} onChange={(e) => handleCondChange('q8_skinArea', Number(e.target.value))} className="w-full p-2 border rounded text-sm bg-white">
                            {OPTIONS.skinArea.map(opt => <option key={opt.val} value={opt.val}>{opt.label}</option>)}
                            </select>
                        </QuestionItem>
                        <div className="flex gap-6">
                            <QuestionItem q="Q9" text="適切な手袋着用" compact><Toggle value={conditions.q9_gloves} onChange={(v) => handleCondChange('q9_gloves', v)} labelOn="着用" labelOff="未着用" /></QuestionItem>
                            <QuestionItem q="Q10" text="手袋使用の教育" compact><Toggle value={conditions.q10_glovesEdu} onChange={(v) => handleCondChange('q10_glovesEdu', v)} labelOn="実施" labelOff="未実施" /></QuestionItem>
                        </div>
                    </CardContent>
                    <CardContent className="space-y-6">
                        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2"><AlertTriangle className="w-4 h-4" /> 危険性・爆発火災要因</h3>
                        <QuestionItem q="Q11" text="取扱温度はどのくらいですか。">
                            <div className="flex gap-2">
                                <button onClick={() => handleCondChange('q11_temp', 'room')} className={`flex-1 py-1 px-3 rounded text-sm border ${conditions.q11_temp === 'room' ? 'bg-blue-100 border-blue-300 text-blue-800' : 'bg-white'}`}>常温</button>
                                <button onClick={() => handleCondChange('q11_temp', 'high')} className={`flex-1 py-1 px-3 rounded text-sm border ${conditions.q11_temp === 'high' ? 'bg-red-100 border-red-300 text-red-800' : 'bg-white'}`}>高温</button>
                            </div>
                        </QuestionItem>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <QuestionItem q="Q12" text="着火源の除去対策"><Toggle value={conditions.q12_ignition} onChange={(v) => handleCondChange('q12_ignition', v)} labelOn="実施" labelOff="未実施" /></QuestionItem>
                            <QuestionItem q="Q13" text="防爆対策の実施"><Toggle value={conditions.q13_explosion} onChange={(v) => handleCondChange('q13_explosion', v)} labelOn="実施" labelOff="未実施" /></QuestionItem>
                            <QuestionItem q="Q14" text="混触危険物の近傍取扱"><Toggle value={conditions.q14_organic} onChange={(v) => handleCondChange('q14_organic', v)} labelOn="あり" labelOff="なし" isRisk /></QuestionItem>
                            <QuestionItem q="Q15" text="空気・水との接触可能性"><Toggle value={conditions.q15_contact} onChange={(v) => handleCondChange('q15_contact', v)} labelOn="あり" labelOff="なし" isRisk /></QuestionItem>
                        </div>
                    </CardContent>
                </div>
            </Card>
        </div>

        {/* === Right Column: Result Area === */}
        <div className="lg:col-span-5">
            <div className="sticky top-20">
                <Card>
                    <CardHeader step="4" title="リスク判定結果"/>
                    <RiskResultCard result={result} />
                </Card>
            </div>
        </div>
      </main>
    );
  };
