export const DEFAULT_FILTERS = {
  query: "", risk: "", minimumProbability: 0, maximumProbability: 1,
  minimumAmount: "", maximumAmount: "", productCode: "", channel: "",
  merchant: "", customerId: "", dateFrom: "", dateTo: "",
};

export const DEFAULT_SORT = { field: "created_at", direction: "desc" };

const RISK_ORDER = { critical: 4, high: 3, medium: 2, low: 1, unknown: 0 };

export function probabilityOf(item) {
  return Number(item.fraud_probability ?? item.probability ?? item.fraud_score ?? 0);
}

export function amountOf(item) {
  return Number(item.transaction_amount ?? item.amount ?? item.TransactionAmt ?? 0);
}

export function riskOf(item) {
  const explicit = String(item.risk_band ?? "").toLowerCase();
  if (Object.hasOwn(RISK_ORDER, explicit)) return explicit;
  const p = probabilityOf(item);
  if (p >= 0.9) return "critical";
  if (p >= 0.7) return "high";
  if (p >= 0.4) return "medium";
  if (p > 0) return "low";
  return "unknown";
}

export function filterTransactions(items = [], filters = DEFAULT_FILTERS) {
  const q = String(filters.query ?? "").trim().toLowerCase();
  return items.filter((item) => {
    const searchable = [
      item.transaction_id, item.customer_id, item.merchant, item.merchant_name,
      item.product_code, item.channel, item.device_type, item.model_version,
    ].filter(Boolean).join(" ").toLowerCase();

    const p = probabilityOf(item);
    const amount = amountOf(item);
    const merchant = String(item.merchant_name ?? item.merchant ?? "").toLowerCase();
    const customer = String(item.customer_id ?? "").toLowerCase();
    const created = new Date(item.created_at ?? 0).getTime();

    if (q && !searchable.includes(q)) return false;
    if (filters.risk && riskOf(item) !== filters.risk) return false;
    if (p < Number(filters.minimumProbability || 0)) return false;
    if (p > Number(filters.maximumProbability ?? 1)) return false;
    if (filters.minimumAmount !== "" && amount < Number(filters.minimumAmount)) return false;
    if (filters.maximumAmount !== "" && amount > Number(filters.maximumAmount)) return false;
    if (filters.productCode && String(item.product_code ?? "") !== filters.productCode) return false;
    if (filters.channel && String(item.channel ?? "") !== filters.channel) return false;
    if (filters.merchant && !merchant.includes(String(filters.merchant).toLowerCase())) return false;
    if (filters.customerId && !customer.includes(String(filters.customerId).toLowerCase())) return false;
    if (filters.dateFrom && created < new Date(`${filters.dateFrom}T00:00:00`).getTime()) return false;
    if (filters.dateTo && created > new Date(`${filters.dateTo}T23:59:59.999`).getTime()) return false;
    return true;
  });
}

export function sortTransactions(items = [], sort = DEFAULT_SORT) {
  const multiplier = sort.direction === "asc" ? 1 : -1;
  return [...items].sort((a, b) => {
    if (sort.field === "merchant") {
      return String(a.merchant_name ?? a.merchant ?? "")
        .localeCompare(String(b.merchant_name ?? b.merchant ?? "")) * multiplier;
    }
    const value = (item) => {
      if (sort.field === "amount") return amountOf(item);
      if (sort.field === "probability") return probabilityOf(item);
      if (sort.field === "risk") return RISK_ORDER[riskOf(item)];
      return new Date(item.created_at ?? 0).getTime();
    };
    return (value(a) - value(b)) * multiplier;
  });
}

export function paginate(items = [], page = 1, pageSize = 25) {
  const size = Math.max(1, Number(pageSize) || 25);
  const pageCount = Math.max(1, Math.ceil(items.length / size));
  const currentPage = Math.min(Math.max(1, Number(page) || 1), pageCount);
  const start = (currentPage - 1) * size;
  return { items: items.slice(start, start + size), page: currentPage, pageCount, total: items.length };
}

export function summarize(items = []) {
  const result = {
    total: items.length, flagged: 0, critical: 0, high: 0, medium: 0,
    low: 0, unknown: 0, totalAmount: 0,
  };
  for (const item of items) {
    result[riskOf(item)] += 1;
    result.totalAmount += amountOf(item);
    if (item.prediction === 1 || item.is_fraud === true || probabilityOf(item) >= 0.5) result.flagged += 1;
  }
  return result;
}

export function comparisonRows(left, right) {
  if (!left || !right) return [];
  return [
    ["Transaction", left.transaction_id, right.transaction_id],
    ["Customer", left.customer_id, right.customer_id],
    ["Merchant", left.merchant_name ?? left.merchant, right.merchant_name ?? right.merchant],
    ["Amount", amountOf(left), amountOf(right)],
    ["Probability", probabilityOf(left), probabilityOf(right)],
    ["Risk", riskOf(left), riskOf(right)],
    ["Channel", left.channel, right.channel],
    ["Product", left.product_code, right.product_code],
  ].map(([label, a, b]) => ({ label, left: a ?? "—", right: b ?? "—" }));
}

export function toCsv(items = []) {
  const rows = items.map((item) => [
    item.transaction_id, item.customer_id, item.merchant_name ?? item.merchant,
    amountOf(item), item.currency ?? "USD", riskOf(item), probabilityOf(item),
    item.product_code, item.channel, item.model_version, item.created_at,
  ]);
  const escape = (value) => {
    const text = String(value ?? "");
    return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
  };
  return [
    "transaction_id,customer_id,merchant,amount,currency,risk,fraud_probability,product_code,channel,model_version,created_at",
    ...rows.map((row) => row.map(escape).join(",")),
  ].join("\n");
}
