import { useEffect, useState } from "react";
import { useModelGovernance } from "../hooks/useModelGovernance";
import ModelSummaryCards from "../components/ModelSummaryCards";
import ModelRegistryTable from "../components/ModelRegistryTable";
import {
  ChampionChallengerPanel,
  DatasetLineagePanel,
  DeploymentHistoryTable,
  DriftMonitoringPanel,
  FeatureDriftTable,
  GovernanceAuditTrail,
  ModelApprovalPanel,
  ModelCardPanel,
  ModelPerformancePanel,
  TrainingRunsTable,
} from "../components/GovernancePanels";
import "../styles/modelGovernance.css";

const TABS = ["Overview", "Monitoring", "Lifecycle", "Lineage", "Governance"];

export default function ModelGovernancePage() {
  const governance = useModelGovernance();
  const [tab, setTab] = useState("Overview");

  useEffect(() => {
    governance.load().catch(() => undefined);
  }, [governance.load]);

  return (
    <main className="model-governance-page">
      <header className="governance-hero">
        <div>
          <p>JustCorp Sentinel AI</p>
          <h1>Enterprise MLOps and model governance</h1>
          <span>
            Review runtime model health, evidence, lineage and governance
            readiness.
          </span>
        </div>
        <div className="champion-banner">
          <span>Current champion</span>
          <strong>{governance.champion ? `${governance.champion.name} ${governance.champion.version}` : "Not assigned"}</strong>
        </div>
      </header>

      <ModelSummaryCards summary={governance.summary} />

      <nav className="governance-tabs" aria-label="Governance sections">
        {TABS.map((item) => (
          <button key={item} className={tab === item ? "active" : ""} onClick={() => setTab(item)}>{item}</button>
        ))}
      </nav>

      {!governance.capabilities?.authoritative_registry ? (
        <div className="governance-capability-note">
          This is a read-only governance snapshot built from the current fraud
          model and model-insight APIs. Version registration, drift telemetry,
          approvals, promotion and rollback require dedicated backend
          governance services.
        </div>
      ) : null}

      {governance.error ? <div className="governance-error" role="alert">{governance.error.message}</div> : null}

      {governance.loading ? (
        <section className="governance-panel">Loading model governance...</section>
      ) : (
        <>
          {tab === "Overview" && (
            <>
              <ModelRegistryTable
                models={governance.visibleModels}
                filters={governance.filters}
                setFilters={governance.setFilters}
                onSelect={governance.loadModelDetails}
                selectedId={governance.selectedModel?.id}
              />
              <div className="governance-two-column">
                <ModelPerformancePanel performance={governance.performance} />
                <DriftMonitoringPanel drift={governance.drift} />
              </div>
              <ChampionChallengerPanel
                champion={governance.champion}
                challengers={governance.championChallenger?.challengers ?? []}
                onPromote={governance.promote}
                actionsEnabled={Boolean(
                  governance.capabilities?.governance_actions
                )}
              />
            </>
          )}

          {tab === "Monitoring" && (
            <>
              <div className="governance-two-column">
                <ModelPerformancePanel performance={governance.performance} />
                <DriftMonitoringPanel drift={governance.drift} />
              </div>
              <FeatureDriftTable features={governance.featureDrift} />
            </>
          )}

          {tab === "Lifecycle" && (
            <>
              <TrainingRunsTable runs={governance.trainingRuns} />
              <DeploymentHistoryTable deployments={governance.deployments} />
            </>
          )}

          {tab === "Lineage" && <DatasetLineagePanel datasets={governance.datasets} />}

          {tab === "Governance" && (
            <>
              <div className="governance-two-column">
                <ModelApprovalPanel
                  model={governance.selectedModel}
                  onApprove={governance.approve}
                  onReject={governance.reject}
                  onRollback={governance.rollback}
                  actionLoading={governance.actionLoading}
                  actionsEnabled={Boolean(
                    governance.capabilities?.governance_actions
                  )}
                />
                <ModelCardPanel card={governance.modelCard} />
              </div>
              <GovernanceAuditTrail events={governance.auditTrail} />
            </>
          )}
        </>
      )}

      {governance.detailLoading || governance.actionLoading ? (
        <div className="governance-progress">
          {governance.actionLoading ? "Applying governance action..." : "Loading model details..."}
        </div>
      ) : null}
    </main>
  );
}
