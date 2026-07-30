import { useCallback, useMemo, useState } from "react";
import { reportExportApi } from "../../../api/reportExportApi";
import {
  filterReports,
  normalizeCollection,
  normalizeReport,
  summarizeReports,
} from "../domain/reports";

export function useReportExports() {
  const [state, setState] = useState({
    summary: {},
    reports: [],
    history: [],
    templates: [],
    types: [],
    scheduled: [],
    selectedReport: null,
  });
  const [filters, setFilters] = useState({
    search: "",
    status: "All",
    format: "All",
  });
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [reports, history, templates, types, scheduled] = await Promise.all([
        reportExportApi.list(),
        reportExportApi.history(),
        reportExportApi.templates(),
        reportExportApi.types(),
        reportExportApi.scheduled(),
      ]);

      const normalizedReports = normalizeCollection(reports).map(normalizeReport);
      const normalizedSchedules = normalizeCollection(scheduled);
      setState((current) => ({
        ...current,
        reports: normalizedReports,
        history: normalizeCollection(history).map(normalizeReport),
        templates: normalizeCollection(templates),
        types: normalizeCollection(types),
        scheduled: normalizedSchedules,
        summary: summarizeReports(
          normalizedReports,
          normalizedSchedules.length,
        ),
      }));
    } catch (caught) {
      setError(caught);
      throw caught;
    } finally {
      setLoading(false);
    }
  }, []);

  const generate = useCallback(async (payload) => {
    setActionLoading(true);
    setError(null);
    try {
      const created = normalizeReport(
        await reportExportApi.generate(payload),
      );
      setState((current) => ({
        ...current,
        reports: [created, ...current.reports],
        history: [created, ...current.history],
        selectedReport: created,
        summary: summarizeReports(
          [created, ...current.reports],
          current.scheduled.length,
        ),
      }));
      return created;
    } catch (caught) {
      setError(caught);
      throw caught;
    } finally {
      setActionLoading(false);
    }
  }, []);

  const remove = useCallback(async (id) => {
    setActionLoading(true);
    try {
      await reportExportApi.remove(id);
      setState((current) => ({
        ...current,
        reports: current.reports.filter((item) => item.id !== id),
        history: current.history.filter((item) => item.id !== id),
        selectedReport:
          current.selectedReport?.id === id ? null : current.selectedReport,
        summary: summarizeReports(
          current.reports.filter((item) => item.id !== id),
          current.scheduled.length,
        ),
      }));
    } finally {
      setActionLoading(false);
    }
  }, []);

  const schedule = useCallback(async (payload) => {
    setActionLoading(true);
    try {
      const created = await reportExportApi.schedule(payload);
      setState((current) => ({
        ...current,
        scheduled: [created, ...current.scheduled],
        summary: summarizeReports(
          current.reports,
          current.scheduled.length + 1,
        ),
      }));
      return created;
    } finally {
      setActionLoading(false);
    }
  }, []);

  const cancelSchedule = useCallback(async (id) => {
    setActionLoading(true);
    try {
      await reportExportApi.cancelSchedule(id);
      setState((current) => ({
        ...current,
        scheduled: current.scheduled.filter((item) => item.id !== id),
        summary: summarizeReports(
          current.reports,
          current.scheduled.filter((item) => item.id !== id).length,
        ),
      }));
    } finally {
      setActionLoading(false);
    }
  }, []);

  const visibleReports = useMemo(
    () => filterReports(state.reports, filters),
    [state.reports, filters]
  );

  return {
    ...state,
    summary: state.summary,
    visibleReports,
    filters,
    setFilters,
    loading,
    actionLoading,
    error,
    load,
    generate,
    remove,
    schedule,
    cancelSchedule,
    download: reportExportApi.download,
    selectReport: (report) =>
      setState((current) => ({ ...current, selectedReport: report })),
  };
}
