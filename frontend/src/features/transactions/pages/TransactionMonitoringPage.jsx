import {
  useEffect,
  useRef,
} from "react";
import {
  useLocation,
  useNavigate,
} from "react-router";

import RiskDistributionBars from "../components/RiskDistributionBars";
import TransactionDetailDrawer from "../components/TransactionDetailDrawer";
import TransactionFilters from "../components/TransactionFilters";
import TransactionKpiCards from "../components/TransactionKpiCards";
import TransactionTable from "../components/TransactionTable";
import { useTransactionMonitoring } from "../hooks/useTransactionMonitoring";
import "../styles/transaction-monitoring.css";

export default function TransactionMonitoringPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const state = useTransactionMonitoring();
  const handledScoreId = useRef(null);
  const scoreId =
    location.state?.fraudScoreRecordId ??
    new URLSearchParams(location.search).get("scoreId");

  useEffect(() => {
    state.loadTransactions().catch(() => undefined);
  }, [state.loadTransactions]);

  useEffect(() => {
    if (
      scoreId == null ||
      handledScoreId.current === scoreId
    ) {
      return;
    }

    const transaction = (state.transactions || []).find(
      (item) => String(item.id) === String(scoreId),
    );
    if (transaction) {
      handledScoreId.current = scoreId;
      state.setSelectedTransaction(transaction);
    }
  }, [
    scoreId,
    state.setSelectedTransaction,
    state.transactions,
  ]);

  function investigate(transaction) {
    navigate("/fraud/investigations", {
      state: {
        fraudScoreRecordId: transaction.id,
        transactionId: transaction.transaction_id,
      },
    });
  }

  function explain(transaction) {
    navigate(
      `/fraud/explainability?scoreId=${transaction.id}`,
      {
        state: {
          fraudScoreRecordId: transaction.id,
          transactionId: transaction.transaction_id,
        },
      },
    );
  }

  return (
    <main className="transaction-monitoring-page">
      <header className="transaction-page-header">
        <div>
          <p className="transaction-eyebrow">
            JustCorp Sentinel AI
          </p>
          <h1>Transaction Monitoring</h1>
          <p>
            Review scored transactions, prioritize high-risk
            activity, and move directly into investigation or
            explainability.
          </p>
        </div>
        <button
          type="button"
          onClick={state.loadTransactions}
        >
          Refresh
        </button>
      </header>

      {state.error ? (
        <div className="transaction-error" role="alert">
          {state.error.message}
        </div>
      ) : null}

      <TransactionKpiCards
        summary={state.summary}
        onRiskSelect={(risk) =>
          state.updateFilters({ risk })
        }
      />
      <div className="transaction-dashboard-grid">
        <RiskDistributionBars
          summary={state.summary}
          onSelect={(risk) =>
            state.updateFilters({ risk })
          }
        />
        <TransactionFilters
          filters={state.filters}
          sort={state.sort}
          onFiltersChange={state.updateFilters}
          onSortChange={state.setSort}
          onClear={state.clearFilters}
        />
      </div>
      <TransactionTable
        transactions={state.visibleTransactions}
        selectedId={state.selectedTransaction?.id}
        loading={state.loading}
        onSelect={state.setSelectedTransaction}
      />
      <TransactionDetailDrawer
        transaction={state.selectedTransaction}
        onClose={() => state.setSelectedTransaction(null)}
        onInvestigate={investigate}
        onExplain={explain}
      />
    </main>
  );
}
