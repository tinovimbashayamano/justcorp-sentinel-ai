import { useCallback, useEffect, useMemo, useState } from "react";
import { listFraudAlerts } from "../../../api/alerts";
import { enrichAlerts, filterAlerts, paginateAlerts, sortAlerts, summarizeAlerts, updateAlertState } from "../domain/alertCenter";

const STORAGE_KEY = "justcorp.alert-center-state";
const DEFAULT_FILTERS = { query: "", severity: "", status: "", analyst: "", minimumProbability: 0 };
const DEFAULT_SORT = { field: "priority", direction: "desc" };

function loadStoredState() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}"); } catch { return {}; }
}

export function useAlertCenter({
  refreshIntervalMs = 30000,
  enabled = true,
} = {}) {
  const [rawAlerts, setRawAlerts] = useState([]);
  const [stateById, setStateById] = useState(loadStoredState);
  const [selectedAlertId, setSelectedAlertId] = useState(null);
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [sort, setSort] = useState(DEFAULT_SORT);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadAlerts = useCallback(async () => {
    setLoading(true); setError(null);
    try { const result = await listFraudAlerts({ limit: 100 }); setRawAlerts(result); return result; }
    catch (err) { setError(err); throw err; } finally { setLoading(false); }
  }, []);

  useEffect(() => {
    if (!enabled) return undefined;
    loadAlerts().catch(() => undefined);
    if (!refreshIntervalMs) return undefined;
    const timer = window.setInterval(() => loadAlerts().catch(() => undefined), refreshIntervalMs);
    return () => window.clearInterval(timer);
  }, [enabled, loadAlerts, refreshIntervalMs]);

  useEffect(() => { localStorage.setItem(STORAGE_KEY, JSON.stringify(stateById)); }, [stateById]);

  const alerts = useMemo(() => enrichAlerts(rawAlerts, stateById), [rawAlerts, stateById]);
  const filteredAlerts = useMemo(() => sortAlerts(filterAlerts(alerts, filters), sort), [alerts, filters, sort]);
  const pagination = useMemo(
    () => paginateAlerts(filteredAlerts, page, pageSize),
    [filteredAlerts, page, pageSize],
  );
  const visibleAlerts = pagination.items;
  const summary = useMemo(() => summarizeAlerts(alerts), [alerts]);
  const selectedAlert = useMemo(() => alerts.find((a) => a.id === selectedAlertId) || null, [alerts, selectedAlertId]);

  const updateStatus = useCallback((alertId, status, analyst = null) => {
    setStateById((current) => updateAlertState(current, alertId, status, analyst));
  }, []);

  const setSelectedAlert = useCallback(
    (alert) => setSelectedAlertId(alert?.id ?? null),
    [],
  );

  const updateFilters = useCallback(
    (patch) => {
      setFilters((current) => ({
        ...current,
        ...patch,
      }));
      setPage(1);
    },
    [],
  );

  const clearFilters = useCallback(() => {
    setFilters(DEFAULT_FILTERS);
    setSort(DEFAULT_SORT);
    setPage(1);
  }, []);

  return {
    alerts, visibleAlerts, selectedAlert, filters, sort, summary, pagination, pageSize, loading, error, loadAlerts,
    setSelectedAlert,
    updateStatus,
    updateFilters,
    clearFilters,
    setSort,
    setPage,
    setPageSize,
  };
}
