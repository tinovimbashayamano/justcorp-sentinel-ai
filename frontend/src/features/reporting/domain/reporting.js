export const DEFAULT_FILTERS = {
  date_from: "",
  date_to: "",
  department: "all",
  risk_level: "all",
};

export function normalizeSummary(value = {}) {
  return {
    transactionsReviewed: Number(value.transactions_reviewed ?? 0),
    fraudCases: Number(value.fraud_cases ?? 0),
    fraudPrevented: Number(value.fraud_amount_prevented ?? 0),
    openInvestigations: Number(value.open_investigations ?? 0),
    closedInvestigations: Number(value.closed_investigations ?? 0),
    averageReviewHours: Number(value.average_review_hours ?? 0),
    highRiskAlerts: Number(value.high_risk_alerts ?? 0),
    precision: Number(value.precision ?? 0),
    recall: Number(value.recall ?? 0),
  };
}

export function normalizeRiskDistribution(items = []) {
  const totals = { critical: 0, high: 0, medium: 0, low: 0 };

  for (const item of items) {
    const key = String(item.risk_level ?? item.label ?? "").toLowerCase();
    if (Object.prototype.hasOwnProperty.call(totals, key)) {
      totals[key] += Number(item.count ?? item.value ?? 0);
    }
  }

  return Object.entries(totals).map(([riskLevel, count]) => ({
    riskLevel,
    count,
  }));
}

export function normalizeCompliance(value = {}) {
  return [
    ["Audit log coverage", value.audit_log_coverage],
    ["Explainability coverage", value.explainability_coverage],
    ["Case documentation", value.case_documentation_completeness],
    ["MFA compliance", value.mfa_compliance],
    ["Access review", value.access_review_status],
    ["Data retention", value.data_retention_compliance],
  ].map(([label, raw]) => {
    const score = Number(raw ?? 0);
    return {
      label,
      value: score,
      status: score >= 90 ? "compliant" : score >= 70 ? "attention" : "non_compliant",
    };
  });
}

export function buildTrendSeries(items = []) {
  return [...items]
    .map((item) => ({
      date: item.date,
      alerts: Number(item.alerts ?? 0),
      confirmedFraud: Number(item.confirmed_fraud ?? 0),
      fraudAmount: Number(item.fraud_amount ?? 0),
    }))
    .sort((a, b) => new Date(a.date ?? 0) - new Date(b.date ?? 0));
}

export function sortCases(items = []) {
  return [...items].sort(
    (a, b) => new Date(b.opened_at ?? 0) - new Date(a.opened_at ?? 0)
  );
}

export function sortAnalysts(items = []) {
  return [...items].sort(
    (a, b) => Number(b.cases_completed ?? 0) - Number(a.cases_completed ?? 0)
  );
}

export function calculateResolutionRate(summary = {}) {
  const open = Number(summary.openInvestigations ?? 0);
  const closed = Number(summary.closedInvestigations ?? 0);
  return open + closed ? Math.round((closed / (open + closed)) * 100) : 0;
}
