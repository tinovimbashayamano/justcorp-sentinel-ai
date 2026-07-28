import { useCallback, useMemo, useState } from "react";
import { listTransactions } from "../../../api/transactions";
import { filterTransactions, sortTransactions, summarizeTransactions } from "../domain/transactionMonitoring";
const DEFAULT_FILTERS = { query: "", risk: "", minimumProbability: 0 };
const DEFAULT_SORT = { field: "created_at", direction: "desc" };
export function useTransactionMonitoring() {
  const [transactions, setTransactions] = useState([]);
  const [selectedTransaction, setSelectedTransaction] = useState(null);
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [sort, setSort] = useState(DEFAULT_SORT);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const loadTransactions = useCallback(async () => {
    setLoading(true); setError(null);
    try { const result = await listTransactions({ limit: 100 }); setTransactions(result); return result; }
    catch (caught) { setError(caught); throw caught; }
    finally { setLoading(false); }
  }, []);
  const visibleTransactions = useMemo(() => sortTransactions(filterTransactions(transactions, filters), sort), [transactions, filters, sort]);
  const summary = useMemo(() => summarizeTransactions(transactions), [transactions]);
  const updateFilters = useCallback((patch) => setFilters((current) => ({ ...current, ...patch })), []);
  const clearFilters = useCallback(() => { setFilters(DEFAULT_FILTERS); setSort(DEFAULT_SORT); }, []);
  return { transactions, visibleTransactions, selectedTransaction, filters, sort, summary, loading, error, loadTransactions, setSelectedTransaction, updateFilters, clearFilters, setSort };
}
