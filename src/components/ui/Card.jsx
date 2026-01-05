// src/components/ui/Card.jsx
import React from 'react';

export const Card = ({ children, className = '' }) => {
  return (
    <section className={`bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden ${className}`}>
      {children}
    </section>
  );
};

export const CardHeader = ({ icon, title, step }) => {
  return (
    <div className="bg-slate-100 px-4 py-3 border-b border-slate-200 flex items-center gap-3">
      {step && (
        <span className="bg-blue-600 text-white w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold">
          {step}
        </span>
      )}
      {icon}
      <h2 className="font-bold text-slate-700">{title}</h2>
    </div>
  );
};

export const CardContent = ({ children, className = '' }) => {
  return (
    <div className={`p-5 ${className}`}>
      {children}
    </div>
  );
};
