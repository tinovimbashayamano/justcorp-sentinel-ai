import { httpClient } from "./httpClient";

const SOURCE_CACHE_MS = 1200;
let cachedAt = 0;
let cachedPromise = null;

function listItems(value) {
  if (Array.isArray(value)) return value;
  if (Array.isArray(value?.items)) return value.items;
  if (Array.isArray(value?.features)) return value.features;
  return [];
}

async function optionalGet(path, config) {
  try {
    const { data } = await httpClient.get(path, config);
    return data;
  } catch {
    return null;
  }
}

function algorithmFromModelName(value) {
  const name = String(value || "").toLowerCase();
  if (name.includes("lightgbm")) return "LightGBM";
  if (name.includes("xgboost")) return "XGBoost";
  if (name.includes("random_forest")) return "Random Forest";
  return "Production classifier";
}

function runtimeVersion(health) {
  return (
    import.meta.env.VITE_MODEL_VERSION ||
    health.model_version ||
    "runtime"
  );
}

function normalizeAuditEvent(item) {
  return {
    id: item.id,
    action: item.action,
    description: [
      item.resource_type,
      item.resource_id,
      item.status,
    ]
      .filter(Boolean)
      .join(" / "),
    actor: item.actor_username || "System",
    timestamp: item.created_at,
  };
}

function buildDashboard({
  health,
  insights,
  featurePayload,
  scores,
  audit,
  profile,
}) {
  const modelName =
    health.model_name || insights.model || "fraud_detection_model";
  const version = runtimeVersion(health);
  const owner =
    profile.full_name || profile.username || "JustCorp ML Operations";
  const isReady = ["ready", "healthy", "active"].includes(
    String(health.status || "").toLowerCase(),
  );
  const model = {
    id: modelName,
    name: modelName,
    version,
    algorithm: algorithmFromModelName(modelName),
    status: isReady ? "Production" : "Failed",
    environment: import.meta.env.MODE || "development",
    roc_auc: null,
    pr_auc: null,
    accuracy: null,
    precision: null,
    recall: null,
    f1_score: null,
    false_positive_rate: null,
    false_negative_rate: null,
    average_latency_ms: null,
    prediction_volume: scores.length,
    training_date: null,
    deployed_date: null,
    owner,
    updated_at: null,
    fraud_threshold: health.fraud_threshold ?? null,
    expected_feature_count:
      health.expected_feature_count ?? insights.feature_count ?? null,
  };

  const featureItems = listItems(featurePayload);
  const generatedAt = featurePayload?.generated_at || null;
  const featureDrift = featureItems.map((item) => ({
    feature_name: item.feature,
    feature_type: "Model feature",
    baseline_distribution: null,
    current_distribution: null,
    metric: "Not calculated",
    drift_score: null,
    warning_threshold: null,
    critical_threshold: null,
    status: "Insufficient Data",
    last_evaluated: generatedAt || "Not evaluated",
    importance: item.importance,
  }));

  const governanceEvents = listItems(audit)
    .filter((item) =>
      [item.action, item.resource_type].some((value) =>
        String(value || "").toLowerCase().includes("model"),
      ),
    )
    .map(normalizeAuditEvent);

  const datasetAvailable = Boolean(insights.samples_used);
  const datasets = insights.status
    ? [
        {
          id: "model-insight-baseline",
          name: "Fraud model insight baseline",
          version: "runtime",
          source: "Processed modeling dataset",
          record_count: insights.samples_used ?? 0,
          feature_count:
            insights.feature_count ?? health.expected_feature_count ?? 0,
          target_distribution: "Not exposed",
          created_date: null,
          validation_status: datasetAvailable ? "Available" : "Unknown",
          preprocessing_pipeline: "Production model pipeline",
          parent_dataset: null,
          data_owner: "JustCorp Data Operations",
        },
      ]
    : [];

  const deployment = {
    id: `runtime-${modelName}`,
    model_name: modelName,
    version,
    environment: model.environment,
    action: "Runtime model discovered",
    status: isReady ? "Active" : "Unavailable",
    deployed_by: "Not recorded",
    timestamp: "Not recorded",
  };

  return {
    summary: {
      registered_models: 1,
      production_models: isReady ? 1 : 0,
      pending_approvals: null,
      models_with_drift: null,
      failed_training_runs: null,
      active_experiments: null,
      latest_deployment: null,
      champion_model: isReady ? modelName : null,
    },
    models: [model],
    performance: {
      roc_auc: null,
      pr_auc: null,
      accuracy: null,
      precision: null,
      recall: null,
      f1_score: null,
      false_positive_rate: null,
      false_negative_rate: null,
      average_latency_ms: null,
      prediction_volume: scores.length,
      fraud_threshold: health.fraud_threshold ?? null,
    },
    drift: {
      overall_status: "Insufficient Data",
      data_drift: null,
      prediction_drift: null,
      concept_drift: null,
      class_distribution_drift: null,
      missing_value_drift: null,
      confidence_score_drift: null,
      evaluated_at: null,
    },
    featureDrift,
    modelCard: {
      intended_use:
        "Fraud-risk scoring and prioritization for financial transactions.",
      out_of_scope_use:
        "The model output is not a final fraud determination and requires human review.",
      training_data:
        "Processed fraud modeling data; a versioned training lineage record is not exposed.",
      evaluation_data:
        "No versioned evaluation dataset is available through the current API.",
      performance:
        "Validated performance metrics are not exposed by the current backend.",
      limitations:
        "Drift, fairness, and post-deployment outcome metrics require dedicated telemetry.",
      bias_considerations:
        "Bias evaluation evidence is not available through the current API.",
      explainability_method: "SHAP-based local and global explanations.",
      monitoring_requirements:
        "Monitor prediction quality, input distributions, latency, and confirmed outcomes.",
      approval_history:
        "No authoritative model approval workflow is implemented.",
      responsible_owner: owner,
    },
    trainingRuns: [],
    datasets,
    deployments: [deployment],
    auditTrail: governanceEvents,
    championChallenger: {
      champion: isReady ? model : null,
      challengers: [],
      supported: false,
    },
    capabilities: {
      authoritative_registry: false,
      performance_metrics: false,
      drift_monitoring: false,
      lifecycle_history: false,
      governance_actions: false,
    },
  };
}

async function loadDashboard() {
  const now = Date.now();
  if (cachedPromise && now - cachedAt < SOURCE_CACHE_MS) {
    return cachedPromise;
  }

  cachedAt = now;
  cachedPromise = Promise.all([
    httpClient.get("/api/v1/fraud/health"),
    optionalGet("/api/v1/model-insights/health"),
    optionalGet("/api/v1/model-insights/features", {
      params: { limit: 200, sort: "importance" },
    }),
    optionalGet("/api/v1/fraud/scores", { params: { limit: 100 } }),
    optionalGet("/api/v1/audit-logs", { params: { limit: 200 } }),
    optionalGet("/api/v1/auth/me"),
  ]).then(
    ([
      healthResponse,
      insights,
      featurePayload,
      scores,
      audit,
      profile,
    ]) =>
      buildDashboard({
        health: healthResponse.data || {},
        insights: insights || {},
        featurePayload: featurePayload || {},
        scores: listItems(scores),
        audit: audit || {},
        profile: profile || {},
      }),
  );
  return cachedPromise;
}

function unavailableAction() {
  return Promise.reject(
    new Error(
      "Authoritative model-governance actions require backend governance endpoints.",
    ),
  );
}

export const modelGovernanceApi = {
  summary: () => loadDashboard().then((data) => data.summary),
  models: () => loadDashboard().then((data) => data.models),
  model: (id) =>
    loadDashboard().then(
      (data) =>
        data.models.find((item) => String(item.id) === String(id)) || null,
    ),
  performance: () => loadDashboard().then((data) => data.performance),
  drift: () => loadDashboard().then((data) => data.drift),
  featureDrift: () => loadDashboard().then((data) => data.featureDrift),
  modelCard: () => loadDashboard().then((data) => data.modelCard),
  trainingRuns: () => loadDashboard().then((data) => data.trainingRuns),
  datasets: () => loadDashboard().then((data) => data.datasets),
  deployments: () => loadDashboard().then((data) => data.deployments),
  auditTrail: () => loadDashboard().then((data) => data.auditTrail),
  championChallenger: () =>
    loadDashboard().then((data) => data.championChallenger),
  capabilities: () => loadDashboard().then((data) => data.capabilities),
  approve: unavailableAction,
  reject: unavailableAction,
  promote: unavailableAction,
  rollback: unavailableAction,
  archive: unavailableAction,
};
