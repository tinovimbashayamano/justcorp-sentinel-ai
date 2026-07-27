import { useCallback, useMemo, useState } from "react";

import {
  createFraudCase,
  getFraudCase,
  listFraudCases,
  listFraudScores,
  updateFraudCase,
} from "../../../api/fraudCases";
import {
  buildCaseCreationPayload,
  filterAndSortCases,
  findCaseForScore,
  paginate,
  summarizeCases,
} from "../domain/caseQueue";

const DEFAULT_FILTERS = {
  query: "",
  status: "",
  decision: "",
  risk: "",
  analyst: "",
  minimumProbability: 0,
  dateFrom: "",
  dateTo: "",
};

const DEFAULT_SORT = {
  field: "updated_at",
  direction: "desc",
};

export function useSmartCaseQueue() {
  const [cases, setCases] = useState([]);
  const [scores, setScores] = useState([]);
  const [selectedCase, setSelectedCase] = useState(null);
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [sort, setSort] = useState(DEFAULT_SORT);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [loading, setLoading] = useState({});
  const [error, setError] = useState(null);

  const run = useCallback(async (key, operation) => {
    setLoading((current) => ({ ...current, [key]: true }));
    setError(null);

    try {
      return await operation();
    } catch (caught) {
      setError(caught);
      throw caught;
    } finally {
      setLoading((current) => ({ ...current, [key]: false }));
    }
  }, []);

  const loadQueue = useCallback(async () => {
    const [caseRecords, scoreRecords] = await Promise.all([
      run("cases", () => listFraudCases({ limit: 100 })),
      run("scores", () => listFraudScores({ limit: 100 })),
    ]);

    setCases(caseRecords);
    setScores(scoreRecords);

    return { cases: caseRecords, scores: scoreRecords };
  }, [run]);

  const selectCase = useCallback(
    async (caseId) => {
      const result = await run("selectedCase", () =>
        getFraudCase(caseId)
      );
      setSelectedCase(result);
      return result;
    },
    [run]
  );

  const saveCase = useCallback(
    async (caseId, payload) => {
      const updated = await run("saveCase", () =>
        updateFraudCase(caseId, payload)
      );

      setCases((current) =>
        current.map((item) =>
          item.id === updated.id ? updated : item
        )
      );
      setSelectedCase(updated);

      return updated;
    },
    [run]
  );

  const openOrCreateCase = useCallback(
    async (fraudScoreRecordId, defaults = {}) => {
      const existing = findCaseForScore(cases, fraudScoreRecordId);

      if (existing) {
        await selectCase(existing.id);
        return {
          caseRecord: existing,
          created: false,
        };
      }

      const payload = buildCaseCreationPayload(
        fraudScoreRecordId,
        defaults
      );

      const created = await run("createCase", () =>
        createFraudCase(payload)
      );

      setCases((current) => [created, ...current]);
      setSelectedCase(created);

      return {
        caseRecord: created,
        created: true,
      };
    },
    [cases, run, selectCase]
  );

  const updateFilters = useCallback((patch) => {
    setFilters((current) => ({ ...current, ...patch }));
    setPage(1);
  }, []);

  const clearFilters = useCallback(() => {
    setFilters(DEFAULT_FILTERS);
    setSort(DEFAULT_SORT);
    setPage(1);
  }, []);

  const filteredCases = useMemo(
    () =>
      filterAndSortCases({
        cases,
        scores,
        filters,
        sort,
      }),
    [cases, scores, filters, sort]
  );

  const pagination = useMemo(
    () => paginate(filteredCases, page, pageSize),
    [filteredCases, page, pageSize]
  );

  const summary = useMemo(
    () => summarizeCases(cases),
    [cases]
  );

  const selectedScore = useMemo(() => {
    if (!selectedCase) return null;

    return (
      scores.find(
        (score) =>
          score.id === selectedCase.fraud_score_record_id
      ) || null
    );
  }, [scores, selectedCase]);

  return {
    cases,
    scores,
    selectedCase,
    selectedScore,
    filters,
    sort,
    pageSize,
    pagination,
    summary,
    loading,
    error,
    loadQueue,
    selectCase,
    saveCase,
    openOrCreateCase,
    updateFilters,
    clearFilters,
    setSort,
    setPage,
    setPageSize,
  };
}
