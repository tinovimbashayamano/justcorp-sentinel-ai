import { useCallback, useMemo, useState } from "react";
import { modelGovernanceApi } from "../../../api/modelGovernanceApi";
import {
  filterModels,
  normalizeSummary,
  selectChampion,
  sortModels,
} from "../domain/modelGovernance";

export function useModelGovernance() {
  const [state, setState] = useState({
    summary: {},
    models: [],
    trainingRuns: [],
    datasets: [],
    deployments: [],
    auditTrail: [],
    championChallenger: {},
    selectedModel: null,
    performance: {},
    drift: {},
    featureDrift: [],
    modelCard: {},
    capabilities: {},
  });
  const [filters, setFilters] = useState({
    search: "",
    status: "All",
    sortKey: "updated_at",
    sortDirection: "desc",
  });
  const [loading, setLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadModelDetails = useCallback(async (id) => {
    if (!id) return;
    setDetailLoading(true);
    try {
      const [model, performance, drift, featureDrift, modelCard] =
        await Promise.all([
          modelGovernanceApi.model(id),
          modelGovernanceApi.performance(id),
          modelGovernanceApi.drift(id),
          modelGovernanceApi.featureDrift(id),
          modelGovernanceApi.modelCard(id),
        ]);

      setState((current) => ({
        ...current,
        selectedModel: model,
        performance: performance ?? {},
        drift: drift ?? {},
        featureDrift: featureDrift?.items ?? featureDrift ?? [],
        modelCard: modelCard ?? {},
      }));
    } finally {
      setDetailLoading(false);
    }
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [
        summary,
        models,
        trainingRuns,
        datasets,
        deployments,
        auditTrail,
        championChallenger,
        capabilities,
      ] = await Promise.all([
        modelGovernanceApi.summary(),
        modelGovernanceApi.models(),
        modelGovernanceApi.trainingRuns(),
        modelGovernanceApi.datasets(),
        modelGovernanceApi.deployments(),
        modelGovernanceApi.auditTrail(),
        modelGovernanceApi.championChallenger(),
        modelGovernanceApi.capabilities(),
      ]);

      const modelItems = models?.items ?? models ?? [];

      setState((current) => ({
        ...current,
        summary: summary ?? {},
        models: modelItems,
        trainingRuns: trainingRuns?.items ?? trainingRuns ?? [],
        datasets: datasets?.items ?? datasets ?? [],
        deployments: deployments?.items ?? deployments ?? [],
        auditTrail: auditTrail?.items ?? auditTrail ?? [],
        championChallenger: championChallenger ?? {},
        capabilities: capabilities ?? {},
        selectedModel: current.selectedModel ?? modelItems[0] ?? null,
      }));

      if (modelItems[0]) {
        await loadModelDetails(modelItems[0].id);
      }
    } catch (caught) {
      setError(caught);
      throw caught;
    } finally {
      setLoading(false);
    }
  }, [loadModelDetails]);

  const runAction = useCallback(
    async (action, id, payload = {}) => {
      if (!state.capabilities.governance_actions) {
        const unavailable = new Error(
          "Authoritative governance actions are unavailable until backend governance endpoints are added.",
        );
        setError(unavailable);
        throw unavailable;
      }
      setActionLoading(true);
      try {
        const result = await modelGovernanceApi[action](id, payload);
        await load();
        return result;
      } finally {
        setActionLoading(false);
      }
    },
    [load, state.capabilities.governance_actions]
  );

  const visibleModels = useMemo(() => {
    const filtered = filterModels(state.models, filters.search, filters.status);
    return sortModels(filtered, filters.sortKey, filters.sortDirection);
  }, [state.models, filters]);

  return {
    ...state,
    summary: normalizeSummary(state.summary),
    champion:
      state.championChallenger?.champion ?? selectChampion(state.models),
    visibleModels,
    filters,
    setFilters,
    loading,
    detailLoading,
    actionLoading,
    error,
    load,
    loadModelDetails,
    approve: (id, payload) => runAction("approve", id, payload),
    reject: (id, payload) => runAction("reject", id, payload),
    promote: (id, payload) => runAction("promote", id, payload),
    rollback: (id, payload) => runAction("rollback", id, payload),
    archive: (id) => runAction("archive", id),
  };
}
