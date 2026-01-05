// src/App.jsx
import React, { useState } from 'react';
import { Toaster, toast } from 'sonner';

import { useSubstanceDatabase } from './hooks/useSubstanceDatabase';
import { Header } from './components/ui/Header';
import { IndividualAssessment } from './components/assessment/IndividualAssessment';
import { BatchAssessment } from './components/assessment/BatchAssessment';

export default function App() {
  const [viewMode, setViewMode] = useState('individual'); // 'individual' or 'batch'
  const {
    substances,
    updateDatabaseFromFile,
    findSubstance,
    isLoading,
    error
  } = useSubstanceDatabase();

  const handleUpdateDB = async (event) => {
    const file = event.target.files[0];
    if (file) {
      const count = await updateDatabaseFromFile(file);
      if (count > 0) {
        toast.success(`物質データベースが更新されました。${count}件の物質が読み込まれました。`);
      } else {
        toast.error("データベースの更新に失敗しました。");
      }
      // Clear the file input so the same file can be uploaded again
      event.target.value = null;
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 font-sans">
      <Toaster position="top-right" richColors />
      <Header
        onShowIndividual={() => setViewMode('individual')}
        onShowBatch={() => setViewMode('batch')}
        onUpdateDB={handleUpdateDB}
      />

      {isLoading && (
        <div className="fixed inset-0 bg-white/70 z-50 flex items-center justify-center">
          <p className="text-lg font-bold">データベースを更新中...</p>
        </div>
      )}

      {error && toast.error(error) /* Display DB errors as toasts */}

      {viewMode === 'individual' ? (
        <IndividualAssessment substanceDB={substances} />
      ) : (
        <BatchAssessment findSubstance={findSubstance} />
      )}
    </div>
  );
}
