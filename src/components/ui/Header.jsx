// src/components/ui/Header.jsx
import React from 'react';
import { Beaker, Upload, FileSpreadsheet } from 'lucide-react';

export const Header = ({ onShowBatch, onShowIndividual, onUpdateDB }) => {
  return (
    <header className="bg-blue-800 text-white p-4 shadow-lg sticky top-0 z-20">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Beaker className="w-8 h-8" />
          <div>
            <h1 className="text-xl font-bold">CREATE-SIMPLE Web</h1>
            <p className="text-xs opacity-80">Chemical Risk Assessment Support Tool</p>
          </div>
        </div>
        <nav className="flex items-center gap-2">
           <button
            onClick={onShowIndividual}
            className="text-sm bg-blue-700 hover:bg-blue-600 px-3 py-2 rounded-md transition-colors flex items-center gap-2"
          >
            個別評価
          </button>
          <button
            onClick={onShowBatch}
            className="text-sm bg-blue-700 hover:bg-blue-600 px-3 py-2 rounded-md transition-colors flex items-center gap-2"
          >
            <FileSpreadsheet className="w-4 h-4" />
            一括判定 (CSV)
          </button>
          <label className="text-sm bg-teal-600 hover:bg-teal-500 px-3 py-2 rounded-md transition-colors flex items-center gap-2 cursor-pointer">
            <Upload className="w-4 h-4" />
            物質DB更新
            <input type="file" accept=".csv" className="hidden" onChange={onUpdateDB} />
          </label>
        </nav>
      </div>
    </header>
  );
};
