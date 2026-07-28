import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import ExplorerFilters from "../components/ExplorerFilters";
import ExplorerTable from "../components/ExplorerTable";
import ComparisonPanel from "../components/ComparisonPanel";
import {
  amountOf,
  probabilityOf,
  riskOf,
} from "../domain/transactionExplorer";
import { useTransactionExplorer } from "../hooks/useTransactionExplorer";
import "../styles/transaction-explorer.css";

export default function TransactionExplorerPage() {
  const navigate = useNavigate();
  const [savedName, setSavedName] = useState("");
  const explorer = useTransactionExplorer();

  useEffect(() => { explorer.loadTransactions().catch(() => undefined); }, [explorer.loadTransactions]);

  return (
    <main className="transaction-explorer">
      <header className="explorer-page-header">
        <div><p>JustCorp Sentinel AI</p><h1>Transaction Search & Explorer</h1><span>Search, compare, save and export scored transactions.</span></div>
        <div><button onClick={explorer.exportCsv}>Export CSV</button><button onClick={explorer.loadTransactions}>Refresh</button></div>
      </header>

      {explorer.error ? <div className="explorer-error">{explorer.error.message}</div> : null}

      <section className="explorer-summary">
        <article><span>Results</span><strong>{explorer.summary.total}</strong></article>
        <article><span>Flagged</span><strong>{explorer.summary.flagged}</strong></article>
        <article><span>Critical</span><strong>{explorer.summary.critical}</strong></article>
        <article><span>High</span><strong>{explorer.summary.high}</strong></article>
        <article><span>Total amount</span><strong>{new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(explorer.summary.totalAmount)}</strong></article>
      </section>

      <ExplorerFilters filters={explorer.filters} sort={explorer.sort} onFiltersChange={explorer.updateFilters} onSortChange={explorer.setSort} onClear={explorer.clearFilters} />

      <section className="explorer-panel saved-searches">
        <div className="explorer-header"><div><p>Saved searches</p><h2>Reusable analyst views</h2></div></div>
        <form onSubmit={(e) => { e.preventDefault(); if (explorer.saveSearch(savedName)) setSavedName(""); }}>
          <input aria-label="Saved search name" value={savedName} onChange={(e) => setSavedName(e.target.value)} placeholder="Search name" />
          <button type="submit">Save current search</button>
        </form>
        <div>{explorer.savedSearches.map((item) => <span className="saved-chip" key={item.id}>
          <button onClick={() => explorer.applySavedSearch(item)}>{item.name}</button>
          <button aria-label={`Delete ${item.name}`} onClick={() => explorer.deleteSavedSearch(item.id)}>×</button>
        </span>)}</div>
      </section>

      <ComparisonPanel comparison={explorer.comparison} onClear={() => explorer.setComparison([])} />

      <ExplorerTable transactions={explorer.visibleTransactions} comparison={explorer.comparison} loading={explorer.loading} onSelect={explorer.setSelectedTransaction} onToggleComparison={explorer.toggleComparison} />

      <section className="explorer-pagination">
        <span>Page {explorer.page} of {explorer.pageCount} · {explorer.totalResults} results</span>
        <div><button disabled={explorer.page <= 1} onClick={() => explorer.setPage(explorer.page - 1)}>Previous</button>
        <button disabled={explorer.page >= explorer.pageCount} onClick={() => explorer.setPage(explorer.page + 1)}>Next</button></div>
      </section>

      {explorer.selectedTransaction ? <aside className="explorer-drawer" aria-label="Transaction details">
        <div className="explorer-header"><h2>{explorer.selectedTransaction.transaction_id || `Score ${explorer.selectedTransaction.id}`}</h2><button onClick={() => explorer.setSelectedTransaction(null)}>Close</button></div>
        <p>{explorer.selectedTransaction.merchant_name || explorer.selectedTransaction.merchant || "Unknown merchant"}</p>
        <div className="explorer-detail-grid">
          <div><span>Customer</span><strong>{explorer.selectedTransaction.customer_id || "—"}</strong></div>
          <div><span>Amount</span><strong>{new Intl.NumberFormat("en-US", { style: "currency", currency: explorer.selectedTransaction.currency || "USD" }).format(amountOf(explorer.selectedTransaction))}</strong></div>
          <div><span>Risk</span><strong>{riskOf(explorer.selectedTransaction)}</strong></div>
          <div><span>Fraud probability</span><strong>{new Intl.NumberFormat("en-US", { style: "percent", maximumFractionDigits: 1 }).format(probabilityOf(explorer.selectedTransaction))}</strong></div>
          <div><span>Model</span><strong>{explorer.selectedTransaction.model_version || explorer.selectedTransaction.model_name || "—"}</strong></div>
          <div><span>Created</span><strong>{explorer.selectedTransaction.created_at ? new Date(explorer.selectedTransaction.created_at).toLocaleString() : "—"}</strong></div>
        </div>
        <div className="drawer-actions">
          <button onClick={() => navigate("/fraud/investigations", { state: { fraudScoreRecordId: explorer.selectedTransaction.id, transactionId: explorer.selectedTransaction.transaction_id } })}>Investigate</button>
          <button onClick={() => navigate(`/fraud/explainability?scoreId=${explorer.selectedTransaction.id}`, { state: { fraudScoreRecordId: explorer.selectedTransaction.id, transactionId: explorer.selectedTransaction.transaction_id } })}>Explain</button>
          <button onClick={() => navigate(`/fraud/transactions?scoreId=${explorer.selectedTransaction.id}`, { state: { fraudScoreRecordId: explorer.selectedTransaction.id, transactionId: explorer.selectedTransaction.transaction_id } })}>Open monitoring</button>
        </div>
      </aside> : null}
    </main>
  );
}
