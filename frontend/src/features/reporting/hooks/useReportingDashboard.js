import { useCallback, useMemo, useState } from "react";
import { reportingApi } from "../../../api/reportingDashboard";
import {
  DEFAULT_FILTERS,
  buildTrendSeries,
  normalizeCompliance,
  normalizeRiskDistribution,
  normalizeSummary,
  sortAnalysts,
  sortCases,
} from "../domain/reporting";

export function useReportingDashboard() {
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [state, setState] = useState({
    summary: {},
    trends: [],
    riskDistribution: [],
    cases: [],
    analysts: [],
    modelPerformance: {},
    compliance: {},
    auditEvidence: [],
    schedules: [],
  });
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState(null);

  const loadDashboard = useCallback(async (nextFilters = filters) => {
    setLoading(true);
    setError(null);

    try {
      const [
        summary,
        trends,
        riskDistribution,
        cases,
        analysts,
        modelPerformance,
        compliance,
        auditEvidence,
        schedules,
      ] = await Promise.all([
        reportingApi.executiveSummary(nextFilters),
        reportingApi.fraudTrends(nextFilters),
        reportingApi.riskDistribution(nextFilters),
        reportingApi.cases(nextFilters),
        reportingApi.analysts(nextFilters),
        reportingApi.modelPerformance(nextFilters),
        reportingApi.compliance(nextFilters),
        reportingApi.auditEvidence(nextFilters),
        reportingApi.schedules(),
      ]);

      const next = {
        summary: summary ?? {},
        trends: trends ?? [],
        riskDistribution: riskDistribution ?? [],
        cases: cases ?? [],
        analysts: analysts ?? [],
        modelPerformance: modelPerformance ?? {},
        compliance: compliance ?? {},
        auditEvidence: auditEvidence ?? [],
        schedules: schedules ?? [],
      };

      setFilters(nextFilters);
      setState(next);
      return next;
    } catch (caught) {
      setError(caught);
      throw caught;
    } finally {
      setLoading(false);
    }
  }, [filters]);

  const downloadReport = useCallback(async (type, format) => {
    setExporting(true);
    try {
      const blob = await reportingApi.exportReport({ type, format, filters });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `${type}.${format}`;
      anchor.click();
      URL.revokeObjectURL(url);
    } finally {
      setExporting(false);
    }
  }, [filters]);

  const addSchedule = useCallback(async (payload) => {
    const created = await reportingApi.createSchedule(payload);
    setState((current) => ({
      ...current,
      schedules: [...current.schedules, created],
    }));
    return created;
  }, []);

  const removeSchedule = useCallback(async (id) => {
    await reportingApi.deleteSchedule(id);
    setState((current) => ({
      ...current,
      schedules: current.schedules.filter((item) => item.id !== id),
    }));
  }, []);

  return {
    filters,
    loading,
    exporting,
    error,
    loadDashboard,
    downloadReport,
    addSchedule,
    removeSchedule,
    schedules: state.schedules,
    auditEvidence: state.auditEvidence,
    modelPerformance: state.modelPerformance,
    summary: useMemo(() => normalizeSummary(state.summary), [state.summary]),
    trends: useMemo(() => buildTrendSeries(state.trends), [state.trends]),
    riskDistribution: useMemo(
      () => normalizeRiskDistribution(state.riskDistribution),
      [state.riskDistribution]
    ),
    cases: useMemo(() => sortCases(state.cases), [state.cases]),
    analysts: useMemo(() => sortAnalysts(state.analysts), [state.analysts]),
    compliance: useMemo(
      () => normalizeCompliance(state.compliance),
      [state.compliance]
    ),
  };
}
