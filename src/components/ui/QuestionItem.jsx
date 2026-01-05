// src/components/ui/QuestionItem.jsx
import React from 'react';

export const QuestionItem = ({ q, text, sub, children, compact = false, htmlFor }) => {
  return (
    <div className={compact ? "" : "border-l-4 border-slate-200 pl-4 py-1"}>
      <label htmlFor={htmlFor} className="flex items-baseline gap-2 mb-2">
        <span className="font-bold text-blue-600 text-sm">{q}</span>
        <span className="text-sm font-medium text-slate-700">{text}</span>
        {sub && <span className="text-xs text-slate-400">{sub}</span>}
      </label>
      <div>{children}</div>
    </div>
  );
};

export const Toggle = ({ value, onChange, labelOn = 'はい', labelOff = 'いいえ', isRisk = false }) => {
  const activeColor = isRisk ? 'bg-red-600' : 'bg-blue-600';

  return (
    <div className="flex items-center gap-2">
      <button
        type="button"
        onClick={() => onChange(true)}
        className={`px-4 py-1.5 rounded text-xs font-bold transition border ${value ? `${activeColor} text-white border-transparent shadow-sm` : 'bg-white text-slate-500 border-slate-200 hover:bg-slate-50'}`}
      >
        {labelOn}
      </button>
      <button
        type="button"
        onClick={() => onChange(false)}
        className={`px-4 py-1.5 rounded text-xs font-bold transition border ${!value ? 'bg-slate-500 text-white border-transparent shadow-sm' : 'bg-white text-slate-500 border-slate-200 hover:bg-slate-50'}`}
      >
        {labelOff}
      </button>
    </div>
  );
};
