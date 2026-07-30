import { useCallback, useMemo, useState } from "react";
import { auditTrailApi } from "../../../api/auditTrailApi";
import {
  DEFAULT_FILTERS,
  buildAuditLookups,
  compareAuditChanges,
  filterAuditEvents,
  normalizeAuditCollection,
  normalizeAuditEvent,
  normalizeAuditSummary,
  paginateAuditEvents,
  summarizeAuditEvents,
} from "../domain/auditTrail";

export function useAuditTrail() {
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [events, setEvents] = useState([]);
  const [filteredEvents, setFilteredEvents] = useState([]);
  const [summary, setSummary] = useState({});
  const [pagination, setPagination] = useState({ page: 1, page_size: 25, total: 0, total_pages: 1 });
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [lookups, setLookups] = useState({ categories: [], actions: [], users: [], presets: [] });
  const [integrity, setIntegrity] = useState({});
  const [retention, setRetention] = useState({});
  const [loading, setLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async (nextFilters = filters) => {
    setLoading(true);
    setError(null);
    try {
      const [eventsResponse, integrityResponse, retentionResponse] =
        await Promise.all([
          auditTrailApi.events({ limit: 200 }),
          auditTrailApi.integrity(),
          auditTrailApi.retention(),
        ]);
      const allEvents = normalizeAuditCollection(eventsResponse)
        .items.map(normalizeAuditEvent);
      const filtered = filterAuditEvents(allEvents, nextFilters);
      const page = paginateAuditEvents(
        filtered,
        nextFilters.page,
        nextFilters.page_size,
      );
      setEvents(page.items);
      setFilteredEvents(filtered);
      setPagination({
        page: page.page,
        page_size: page.page_size,
        total: page.total,
        total_pages: page.total_pages,
      });
      setSummary(summarizeAuditEvents(filtered));
      setLookups(buildAuditLookups(allEvents));
      setIntegrity(integrityResponse);
      setRetention(retentionResponse);
    } catch (caught) {
      setError(caught);
      throw caught;
    } finally {
      setLoading(false);
    }
  }, [filters]);

  const selectEvent = useCallback(async (event) => {
    setSelectedEvent(event);
    setDetailLoading(false);
  }, []);

  const verifyEvent = useCallback(async (id) => {
    setActionLoading(true);
    try {
      const verified = await auditTrailApi.verify(id);
      setSelectedEvent((current) => current?.id === id ? { ...current, integrity: verified.integrity ?? verified } : current);
      return verified;
    } catch (caught) {
      setError(caught);
      return null;
    } finally {
      setActionLoading(false);
    }
  }, []);

  const exportEvents = useCallback(async (format) => {
    setActionLoading(true);
    try {
      await auditTrailApi.export(
        {
          format: format.toLowerCase(),
          filters,
          events: filteredEvents,
        },
        "audit-events",
      );
      return true;
    } catch (caught) {
      setError(caught);
      return false;
    } finally {
      setActionLoading(false);
    }
  }, [filteredEvents, filters]);

  const changes = useMemo(() => compareAuditChanges(selectedEvent?.before, selectedEvent?.after), [selectedEvent]);

  return {
    filters, setFilters, events, summary: normalizeAuditSummary(summary), pagination,
    selectedEvent, changes, lookups, integrity, retention, loading, detailLoading,
    actionLoading, error, load, selectEvent, verifyEvent, exportEvents,
    canVerifyIntegrity: Boolean(integrity.available),
    exportCapabilities: {
      PDF: true,
      XLSX: false,
      CSV: true,
      JSON: true,
    },
  };
}
