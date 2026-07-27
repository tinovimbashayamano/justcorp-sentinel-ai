import {
  useCallback,
  useMemo,
  useState,
} from "react";

import {
  getFraudCase,
  listFraudCases,
  listFraudScores,
  updateFraudCase,
} from "../../../api/fraudCases";

const initialState = {
  cases: [],
  scores: [],
  selectedCase: null,
};

export function useCaseInvestigationWorkspace() {
  const [data, setData] = useState(initialState);
  const [loading, setLoading] = useState({});
  const [error, setError] = useState(null);

  const run = useCallback(async (key, operation) => {
    setLoading((current) => ({
      ...current,
      [key]: true,
    }));
    setError(null);
    try {
      return await operation();
    } catch (caught) {
      setError(caught);
      throw caught;
    } finally {
      setLoading((current) => ({
        ...current,
        [key]: false,
      }));
    }
  }, []);

  const loadWorkspace = useCallback(
    async ({
      caseLimit = 50,
      scoreLimit = 50,
    } = {}) => {
      const [cases, scores] = await Promise.all([
        run("cases", () =>
          listFraudCases({ limit: caseLimit }),
        ),
        run("scores", () =>
          listFraudScores({ limit: scoreLimit }),
        ),
      ]);
      setData((current) => ({
        ...current,
        cases,
        scores,
      }));
      return { cases, scores };
    },
    [run],
  );

  const selectCase = useCallback(
    async (caseId) => {
      const selectedCase = await run(
        "selectedCase",
        () => getFraudCase(caseId),
      );
      setData((current) => ({
        ...current,
        selectedCase,
      }));
      return selectedCase;
    },
    [run],
  );

  const saveCase = useCallback(
    async (caseId, payload) => {
      const updated = await run("saveCase", () =>
        updateFraudCase(caseId, payload),
      );
      setData((current) => ({
        ...current,
        selectedCase: updated,
        cases: current.cases.map((item) =>
          item.id === updated.id ? updated : item,
        ),
      }));
      return updated;
    },
    [run],
  );

  const selectedScore = useMemo(() => {
    if (!data.selectedCase) return null;
    return (
      data.scores.find(
        (score) =>
          score.id ===
          data.selectedCase.fraud_score_record_id,
      ) || null
    );
  }, [data.scores, data.selectedCase]);

  return {
    data,
    loading,
    error,
    selectedScore,
    loadWorkspace,
    selectCase,
    saveCase,
  };
}
