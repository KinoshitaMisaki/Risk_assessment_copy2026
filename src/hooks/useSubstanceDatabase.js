// src/hooks/useSubstanceDatabase.js
import { useState, useCallback } from 'react';
import { CHEMICAL_DATABASE as defaultSubstances } from '../data/defaultSubstances';
import { parseSubstancesCSV } from '../utils/csvHelper';

export const useSubstanceDatabase = () => {
  const [substances, setSubstances] = useState(defaultSubstances);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  /**
   * CSVファイルから物質データベースを更新する
   * @param {File} file - ユーザーがアップロードしたCSVファイル
   */
  const updateDatabaseFromFile = useCallback(async (file) => {
    if (!file) return;

    setIsLoading(true);
    setError(null);

    try {
      const newSubstances = await parseSubstancesCSV(file);
      if (newSubstances.length === 0) {
        throw new Error("CSVファイルに有効なデータが含まれていないか、形式が正しくありません。");
      }
      setSubstances(newSubstances);
      // 成功メッセージはUI側で表示するため、ここでは件数を返す
      return newSubstances.length;
    } catch (err) {
      console.error("CSV Parse Error:", err);
      setError("データベースの更新に失敗しました。CSVの形式を確認してください。");
      return 0;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * CAS番号またはIDで物質を検索する
   * @param {string | number} identifier - CAS番号またはID
   * @returns {object | undefined} - 見つかった物質オブジェクト
   */
  const findSubstance = useCallback((identifier) => {
    if (!identifier) return undefined;

    const isCas = typeof identifier === 'string' && identifier.includes('-');

    if (isCas) {
        return substances.find(s => s.cas === identifier);
    }
    // 文字列でIDが渡される場合も考慮して `==` を使用
    return substances.find(s => s.id == identifier);
  }, [substances]);

  return {
    substances,
    updateDatabaseFromFile,
    findSubstance,
    isLoading,
    error,
  };
};
