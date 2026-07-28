import { useCallback, useMemo, useState } from "react";
import { searchTransactions } from "../../../api/transactionExplorer";
import {
  DEFAULT_FILTERS, DEFAULT_SORT, filterTransactions, sortTransactions,
  paginate, summarize, toCsv,
} from "../domain/transactionExplorer";

const KEY = "justcorp.transaction-explorer.saved-searches";

function storedSearches() {
  try { return JSON.parse(localStorage.getItem(KEY) || "[]"); }
  catch { return []; }
}

export function useTransactionExplorer() {
  const [transactions, setTransactions] = useState([]);
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [sort, setSort] = useState(DEFAULT_SORT);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [selected, setSelected] = useState(null);
  const [comparison, setComparison] = useState([]);
  const [savedSearches, setSavedSearches] = useState(storedSearches);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadTransactions = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const result = await searchTransactions();
      setTransactions(result);
      return result;
    } catch (caught) {
      setError(caught); throw caught;
    } finally { setLoading(false); }
  }, []);

  const filtered = useMemo(() => filterTransactions(transactions, filters), [transactions, filters]);
  const sorted = useMemo(() => sortTransactions(filtered, sort), [filtered, sort]);
  const paging = useMemo(() => paginate(sorted, page, pageSize), [sorted, page, pageSize]);
  const summary = useMemo(() => summarize(filtered), [filtered]);

  const updateFilters = useCallback((patch) => {
    setFilters((current) => ({ ...current, ...patch }));
    setPage(1);
  }, []);

  const clearFilters = useCallback(() => {
    setFilters(DEFAULT_FILTERS); setSort(DEFAULT_SORT); setPage(1);
  }, []);

  const toggleComparison = useCallback((item) => {
    setComparison((current) => {
      if (current.some((candidate) => candidate.id === item.id)) {
        return current.filter((candidate) => candidate.id !== item.id);
      }
      return current.length >= 2 ? [current[1], item] : [...current, item];
    });
  }, []);

  const saveSearch = useCallback((name) => {
    const clean = String(name ?? "").trim();
    if (!clean) return false;
    const next = [
      ...savedSearches.filter((item) => item.name.toLowerCase() !== clean.toLowerCase()),
      { id: crypto.randomUUID(), name: clean, filters, sort, createdAt: new Date().toISOString() },
    ];
    setSavedSearches(next); localStorage.setItem(KEY, JSON.stringify(next));
    return true;
  }, [filters, savedSearches, sort]);

  const applySavedSearch = useCallback((item) => {
    setFilters({ ...DEFAULT_FILTERS, ...item.filters });
    setSort({ ...DEFAULT_SORT, ...item.sort });
    setPage(1);
  }, []);

  const deleteSavedSearch = useCallback((id) => {
    const next = savedSearches.filter((item) => item.id !== id);
    setSavedSearches(next); localStorage.setItem(KEY, JSON.stringify(next));
  }, [savedSearches]);

  const exportCsv = useCallback(() => {
    const blob = new Blob([toCsv(sorted)], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `transaction-search-${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(link); link.click(); link.remove(); URL.revokeObjectURL(url);
  }, [sorted]);

  return {
    visibleTransactions: paging.items, filters, sort, page: paging.page,
    pageCount: paging.pageCount, totalResults: paging.total, pageSize,
    selectedTransaction: selected, comparison, savedSearches, summary,
    loading, error, loadTransactions, updateFilters, clearFilters, setSort,
    setPage, setPageSize, setSelectedTransaction: setSelected,
    toggleComparison, setComparison, saveSearch, applySavedSearch,
    deleteSavedSearch, exportCsv,
  };
}
