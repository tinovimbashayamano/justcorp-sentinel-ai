import { useEffect, useState } from "react";
import { useLocation } from "react-router";

import ContributionTable from "../components/ContributionTable";
import GlobalImportanceTable from "../components/GlobalImportanceTable";
import PlotCard from "../components/PlotCard";
import ReportExportActions from "../components/ReportExportActions";
import RiskSummaryCard from "../components/RiskSummaryCard";
import StatusBanner from "../components/StatusBanner";
import TransactionExplanationForm from "../components/TransactionExplanationForm";
import { useExplainabilityWorkspace } from "../hooks/useExplainabilityWorkspace";
import "../styles/explainability-workspace.css";

export default function ExplainabilityWorkspace() {
  const location = useLocation();
  const routedTransactionId =
    location.state?.transactionId || "";
  const {
    data,
    loading,
    error,
    loadHealth,
    loadGlobal,
    explainTransaction,
    exportReport,
  } = useExplainabilityWorkspace();
  const [lastPayload, setLastPayload] = useState(null);

  useEffect(() => {
    Promise.allSettled([
      loadHealth(),
      loadGlobal(20),
    ]);
  }, [loadHealth, loadGlobal]);

  async function handleExplain(payload) {
    setLastPayload(payload);
    try {
      await explainTransaction(payload);
    } catch {
      // The hook exposes the normalized request error.
    }
  }

  return (
    <main className="explainability-workspace">
      <header className="workspace-header">
        <div>
          <p className="eyebrow">
            JustCorp Sentinel AI
          </p>
          <h1>
            Explainability Investigation Workspace
          </h1>
          <p>
            Review local SHAP drivers, compare global
            model behaviour, and export audit-ready
            investigation reports.
          </p>
        </div>
        <button type="button" onClick={loadHealth}>
          Refresh status
        </button>
      </header>

      <StatusBanner
        health={data.health}
        error={error}
      />

      <div className="workspace-grid workspace-grid--two">
        <TransactionExplanationForm
          initialTransactionId={routedTransactionId}
          onSubmit={handleExplain}
          loading={
            loading.local ||
            loading.waterfall ||
            loading.force
          }
        />
        <RiskSummaryCard explanation={data.local} />
      </div>

      <div className="workspace-grid workspace-grid--two">
        <PlotCard
          title="Waterfall contribution plot"
          description={
            "Shows which features pushed the transaction " +
            "toward or away from fraud."
          }
          plot={data.waterfall}
          loading={loading.waterfall}
        />
        <PlotCard
          title="Cumulative explanation path"
          description={
            "Shows how the model output changes as " +
            "feature contributions are added."
          }
          plot={data.force}
          loading={loading.force}
        />
      </div>

      <ContributionTable points={data.local?.points} />

      <div className="workspace-grid workspace-grid--two">
        <PlotCard
          title="Global SHAP summary"
          description={
            "Mean absolute SHAP values across the model " +
            "insight sample."
          }
          plot={data.globalSummary}
          loading={loading.globalSummary}
        />
        <GlobalImportanceTable insight={data.global} />
      </div>

      <ReportExportActions
        payload={lastPayload || {}}
        onExport={exportReport}
        disabled={
          !lastPayload ||
          loading["report-html"] ||
          loading["report-pdf"]
        }
      />
    </main>
  );
}
