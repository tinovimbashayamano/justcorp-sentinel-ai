export const RISK_ORDER = { critical: 4, high: 3, medium: 2, low: 1, unknown: 0 };
export function normalizeRisk(value) {
  const normalized = String(value ?? "unknown").trim().toLowerCase();
  return Object.hasOwn(RISK_ORDER, normalized) ? normalized : "unknown";
}
export function getFraudProbability(transaction) {
  return Number(transaction.fraud_probability ?? transaction.probability ?? transaction.fraud_score ?? 0);
}
export function formatProbability(transaction) {
  return new Intl.NumberFormat("en-US", { style: "percent", maximumFractionDigits: 1 }).format(getFraudProbability(transaction));
}
export function matchesTransactionSearch(transaction, query) {
  const q = String(query ?? "").trim().toLowerCase();
  if (!q) return true;
  return [transaction.transaction_id, transaction.customer_id, transaction.merchant, transaction.merchant_name, transaction.product_code, transaction.channel, transaction.device_type]
    .filter(Boolean).join(" ").toLowerCase().includes(q);
}
export function filterTransactions(transactions = [], { query = "", risk = "", minimumProbability = 0 } = {}) {
  return transactions.filter((transaction) => {
    if (!matchesTransactionSearch(transaction, query)) return false;
    if (risk && normalizeRisk(transaction.risk_band) !== normalizeRisk(risk)) return false;
    return getFraudProbability(transaction) >= Number(minimumProbability || 0);
  });
}
export function sortTransactions(transactions = [], { field = "created_at", direction = "desc" } = {}) {
  const multiplier = direction === "asc" ? 1 : -1;
  return [...transactions].sort((left, right) => {
    let a, b;
    switch (field) {
      case "probability": a = getFraudProbability(left); b = getFraudProbability(right); break;
      case "risk": a = RISK_ORDER[normalizeRisk(left.risk_band)]; b = RISK_ORDER[normalizeRisk(right.risk_band)]; break;
      case "amount": a = Number(left.transaction_amount ?? left.amount ?? 0); b = Number(right.transaction_amount ?? right.amount ?? 0); break;
      default: a = new Date(left.created_at ?? 0).getTime(); b = new Date(right.created_at ?? 0).getTime();
    }
    return (a - b) * multiplier;
  });
}
export function summarizeTransactions(transactions = []) {
  return transactions.reduce((summary, transaction) => {
    const risk = normalizeRisk(transaction.risk_band);
    summary.total += 1; summary[risk] += 1;
    if (transaction.prediction === 1 || transaction.is_fraud === true || getFraudProbability(transaction) >= 0.5) summary.flagged += 1;
    return summary;
  }, { total: 0, flagged: 0, critical: 0, high: 0, medium: 0, low: 0, unknown: 0 });
}
