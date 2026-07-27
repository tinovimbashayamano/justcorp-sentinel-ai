import {
  useCallback,
  useMemo,
  useState,
} from "react";

import {
  exportInvestigationReport,
  getForcePlot,
  getGlobalSummaryPlot,
  getGlobalVisualization,
  getLocalVisualization,
  getVisualizationHealth,
  getWaterfallPlot,
} from "../../../api/explainabilityVisualizations";

const initialState = {
  health: null,
  local: null,
  waterfall: null,
  force: null,
  global: null,
  globalSummary: null,
};

export function useExplainabilityWorkspace() {
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
      const result = await operation();
      setData((current) => ({
        ...current,
        [key]: result,
      }));
      return result;
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

  const loadHealth = useCallback(
    () => run("health", getVisualizationHealth),
    [run],
  );

  const loadGlobal = useCallback(
    async (limit = 20) => {
      const [global, globalSummary] = await Promise.all([
        run("global", () =>
          getGlobalVisualization(limit),
        ),
        run("globalSummary", () =>
          getGlobalSummaryPlot(limit),
        ),
      ]);
      return { global, globalSummary };
    },
    [run],
  );

  const explainTransaction = useCallback(
    async (payload) => {
      const [local, waterfall, force] = await Promise.all([
        run("local", () =>
          getLocalVisualization(payload),
        ),
        run("waterfall", () =>
          getWaterfallPlot(payload),
        ),
        run("force", () => getForcePlot(payload)),
      ]);
      return { local, waterfall, force };
    },
    [run],
  );

  const exportReport = useCallback(
    (format, payload) =>
      run(`report-${format}`, () =>
        exportInvestigationReport(format, payload),
      ),
    [run],
  );

  const isBusy = useMemo(
    () => Object.values(loading).some(Boolean),
    [loading],
  );

  return {
    data,
    loading,
    error,
    isBusy,
    loadHealth,
    loadGlobal,
    explainTransaction,
    exportReport,
  };
}
