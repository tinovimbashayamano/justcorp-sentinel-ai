import { useState } from "react";
import {
  determineDriftState,
  driftClass,
  normalizeMetric,
} from "../domain/modelGovernance";

export function ModelPerformancePanel({ performance }) {
  const metrics = [
    ["ROC-AUC", performance.roc_auc],
    ["PR-AUC", performance.pr_auc],
    ["Accuracy", performance.accuracy],
    ["Precision", performance.precision],
    ["Recall", performance.recall],
    ["F1 score", performance.f1_score],
    ["False-positive rate", performance.false_positive_rate],
    ["False-negative rate", performance.false_negative_rate],
    ["Latency (ms)", performance.average_latency_ms],
    ["Prediction volume", performance.prediction_volume, "count"],
    ["Fraud threshold", performance.fraud_threshold],
  ];

  return (
    <section className="governance-panel">
      <header className="panel-header"><div><p>Quality</p><h2>Model performance</h2></div></header>
      <div className="metric-grid">
        {metrics.map(([label, value, format]) => (
          <article key={label}>
            <span>{label}</span>
            <strong>
              {format === "count"
                ? value ?? "Not reported"
                : normalizeMetric(value)}
            </strong>
          </article>
        ))}
      </div>
    </section>
  );
}

export function DriftMonitoringPanel({ drift }) {
  const items = [
    ["Data drift", drift.data_drift],
    ["Prediction drift", drift.prediction_drift],
    ["Concept drift", drift.concept_drift],
    ["Class distribution", drift.class_distribution_drift],
    ["Missing values", drift.missing_value_drift],
    ["Confidence scores", drift.confidence_score_drift],
  ];

  return (
    <section className="governance-panel">
      <header className="panel-header">
        <div><p>Monitoring</p><h2>Drift monitoring</h2></div>
        <span className={driftClass(drift.overall_status)}>{drift.overall_status ?? "Unknown"}</span>
      </header>
      <div className="drift-list">
        {items.map(([label, value]) => (
          <article key={label}><span>{label}</span><strong>{normalizeMetric(value)}</strong></article>
        ))}
      </div>
    </section>
  );
}

export function FeatureDriftTable({ features }) {
  return (
    <section className="governance-panel">
      <header className="panel-header"><div><p>Inputs</p><h2>Feature drift</h2></div></header>
      <div className="table-scroll">
        <table>
          <thead><tr><th>Feature</th><th>Type</th><th>Metric</th><th>Score</th><th>Threshold</th><th>Status</th><th>Evaluated</th></tr></thead>
          <tbody>
            {features.length ? features.map((feature) => {
              const status = feature.status ?? determineDriftState(
                feature.drift_score,
                feature.warning_threshold,
                feature.critical_threshold
              );
              return (
                <tr key={feature.feature_name}>
                  <td>{feature.feature_name}</td><td>{feature.feature_type}</td>
                  <td>{feature.metric}</td><td>{normalizeMetric(feature.drift_score)}</td>
                  <td>{normalizeMetric(feature.critical_threshold)}</td>
                  <td><span className={driftClass(status)}>{status}</span></td>
                  <td>{feature.last_evaluated}</td>
                </tr>
              );
            }) : (
              <tr>
                <td colSpan="7">
                  Feature drift telemetry is not available.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export function ChampionChallengerPanel({
  champion,
  challengers = [],
  onPromote,
  actionsEnabled = false,
}) {
  return (
    <section className="governance-panel">
      <header className="panel-header"><div><p>Experimentation</p><h2>Champion and challenger</h2></div></header>
      <div className="champion-grid">
        <article>
          <span>Champion</span>
          <strong>{champion ? `${champion.name} ${champion.version}` : "Not assigned"}</strong>
          <small>{champion ? `PR-AUC ${normalizeMetric(champion.pr_auc)}` : "No production model"}</small>
        </article>
        {challengers.map((model) => (
          <article key={model.id}>
            <span>Challenger</span>
            <strong>{model.name} {model.version}</strong>
          <small>PR-AUC {normalizeMetric(model.pr_auc)} / Traffic {model.traffic_allocation ?? 0}%</small>
            <button
              disabled={!actionsEnabled}
              onClick={() => onPromote(model.id)}
            >
              Promote
            </button>
          </article>
        ))}
      </div>
      {!actionsEnabled ? (
        <p className="governance-note">
          Promotion and traffic allocation require authoritative backend
          governance endpoints.
        </p>
      ) : null}
    </section>
  );
}

export function TrainingRunsTable({ runs }) {
  return (
    <section className="governance-panel">
      <header className="panel-header"><div><p>Pipeline</p><h2>Training runs</h2></div></header>
      <div className="table-scroll">
        <table>
          <thead><tr><th>Run</th><th>Model</th><th>Dataset</th><th>Algorithm</th><th>Status</th><th>Started</th><th>Duration</th><th>Triggered by</th></tr></thead>
          <tbody>{runs.length ? runs.map((run) => (
            <tr key={run.id}><td>{run.id}</td><td>{run.model_name}</td><td>{run.dataset_version}</td><td>{run.algorithm}</td><td>{run.status}</td><td>{run.started_at}</td><td>{run.duration}</td><td>{run.triggered_by}</td></tr>
          )) : (
            <tr><td colSpan="8">No training-run history is exposed.</td></tr>
          )}</tbody>
        </table>
      </div>
    </section>
  );
}

export function DeploymentHistoryTable({ deployments }) {
  return (
    <section className="governance-panel">
      <header className="panel-header"><div><p>Release management</p><h2>Deployment history</h2></div></header>
      <div className="table-scroll">
        <table>
          <thead><tr><th>Model</th><th>Version</th><th>Environment</th><th>Action</th><th>Status</th><th>Deployed by</th><th>Timestamp</th></tr></thead>
          <tbody>{deployments.length ? deployments.map((item) => (
            <tr key={item.id}><td>{item.model_name}</td><td>{item.version}</td><td>{item.environment}</td><td>{item.action}</td><td>{item.status}</td><td>{item.deployed_by}</td><td>{item.timestamp}</td></tr>
          )) : (
            <tr><td colSpan="7">No deployment history is exposed.</td></tr>
          )}</tbody>
        </table>
      </div>
    </section>
  );
}

export function DatasetLineagePanel({ datasets }) {
  return (
    <section className="governance-panel">
      <header className="panel-header"><div><p>Traceability</p><h2>Dataset lineage</h2></div></header>
      <div className="lineage-list">
        {datasets.length ? datasets.map((dataset) => (
          <article key={dataset.id}>
            <div><strong>{dataset.name} {dataset.version}</strong><span>{dataset.source}</span></div>
            <div><small>{dataset.record_count ?? 0} records</small><small>{dataset.feature_count ?? 0} features</small><small>{dataset.validation_status}</small></div>
          </article>
        )) : (
          <p className="governance-note">
            No versioned dataset lineage is exposed.
          </p>
        )}
      </div>
    </section>
  );
}

export function ModelApprovalPanel({
  model,
  onApprove,
  onReject,
  onRollback,
  actionLoading,
  actionsEnabled = false,
}) {
  const [comments, setComments] = useState("");
  if (!model) return null;

  return (
    <section className="governance-panel">
      <header className="panel-header"><div><p>Decision</p><h2>Approval workflow</h2></div></header>
      <p className="approval-model">{model.name} / {model.version} / {model.status}</p>
      <label>Review comments
        <textarea rows="4" value={comments} onChange={(event) => setComments(event.target.value)} placeholder="Record evidence, conditions or reasons." />
      </label>
      <div className="approval-actions">
        <button disabled={actionLoading || !actionsEnabled} onClick={() => onApprove(model.id, { comments })}>Approve</button>
        <button className="secondary" disabled={actionLoading || !actionsEnabled} onClick={() => onReject(model.id, { comments })}>Reject</button>
        <button className="danger" disabled={actionLoading || !actionsEnabled} onClick={() => onRollback(model.id, { reason: comments })}>Roll back</button>
      </div>
      {!actionsEnabled ? (
        <p className="governance-note">
          Approval and rollback controls are read-only until backend model
          governance persistence is implemented.
        </p>
      ) : null}
    </section>
  );
}

export function ModelCardPanel({ card }) {
  const sections = [
    ["Intended use", card.intended_use],
    ["Out-of-scope use", card.out_of_scope_use],
    ["Training data", card.training_data],
    ["Evaluation data", card.evaluation_data],
    ["Limitations", card.limitations],
    ["Bias considerations", card.bias_considerations],
    ["Explainability", card.explainability_method],
    ["Monitoring", card.monitoring_requirements],
    ["Approval history", card.approval_history],
    ["Responsible owner", card.responsible_owner],
  ];

  return (
    <section className="governance-panel">
      <header className="panel-header"><div><p>Documentation</p><h2>Model card</h2></div></header>
      <div className="model-card-sections">
        {sections.map(([title, value]) => (
          <article key={title}><strong>{title}</strong><p>{value || "Not documented"}</p></article>
        ))}
      </div>
    </section>
  );
}

export function GovernanceAuditTrail({ events }) {
  return (
    <section className="governance-panel">
      <header className="panel-header"><div><p>Evidence</p><h2>Governance audit trail</h2></div></header>
      <div className="audit-list">
        {events.length ? events.map((event) => (
          <article key={event.id}>
            <div><strong>{event.action}</strong><span>{event.description}</span></div>
            <div><small>{event.actor}</small><small>{event.timestamp}</small></div>
          </article>
        )) : (
          <p className="governance-note">
            No model-specific audit events are available.
          </p>
        )}
      </div>
    </section>
  );
}
