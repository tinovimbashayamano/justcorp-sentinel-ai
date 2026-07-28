export const CASE_STATUSES = [
  "new",
  "open",
  "assigned",
  "investigating",
  "pending_customer",
  "escalated",
  "resolved",
  "under_review",
  "confirmed_fraud",
  "false_positive",
  "closed",
];

export const ANALYST_DECISIONS = [
  "pending",
  "confirmed_fraud",
  "false_positive",
  "needs_more_information",
];

export const RISK_LEVELS = ["high", "medium", "low"];

function normalize(value) {
  return String(value ?? "").trim().toLowerCase();
}

function getCaseScore(caseRecord, scoresById) {
  return scoresById.get(caseRecord.fraud_score_record_id) || null;
}

function getSearchText(caseRecord, score) {
  return [
    caseRecord.id,
    caseRecord.case_status,
    caseRecord.analyst_decision,
    caseRecord.reviewed_by,
    caseRecord.analyst_notes,
    score?.transaction_id,
    score?.customer_id,
    score?.merchant,
    score?.merchant_name,
    score?.risk_band,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
}

function numericProbability(score) {
  return Number(
    score?.fraud_probability ??
      score?.probability ??
      score?.fraud_score ??
      0
  );
}

function timestamp(caseRecord) {
  return new Date(
    caseRecord.updated_at ||
      caseRecord.created_at ||
      0
  ).getTime();
}

export function buildScoreMap(scores = []) {
  return new Map(scores.map((score) => [score.id, score]));
}

export function filterAndSortCases({
  cases = [],
  scores = [],
  filters,
  sort,
}) {
  const scoresById = buildScoreMap(scores);
  const query = normalize(filters.query);
  const minimumProbability = Number(filters.minimumProbability || 0);

  const filtered = cases.filter((caseRecord) => {
    const score = getCaseScore(caseRecord, scoresById);

    if (
      query &&
      !getSearchText(caseRecord, score).includes(query)
    ) {
      return false;
    }

    if (
      filters.status &&
      caseRecord.case_status !== filters.status
    ) {
      return false;
    }

    if (
      filters.decision &&
      caseRecord.analyst_decision !== filters.decision
    ) {
      return false;
    }

    if (
      filters.risk &&
      normalize(score?.risk_band) !== normalize(filters.risk)
    ) {
      return false;
    }

    if (
      filters.analyst &&
      normalize(caseRecord.reviewed_by) !== normalize(filters.analyst)
    ) {
      return false;
    }

    if (numericProbability(score) < minimumProbability) {
      return false;
    }

    if (filters.dateFrom) {
      const from = new Date(filters.dateFrom).getTime();
      if (timestamp(caseRecord) < from) return false;
    }

    if (filters.dateTo) {
      const to = new Date(`${filters.dateTo}T23:59:59.999`).getTime();
      if (timestamp(caseRecord) > to) return false;
    }

    return true;
  });

  const direction = sort.direction === "asc" ? 1 : -1;

  return [...filtered].sort((left, right) => {
    const leftScore = getCaseScore(left, scoresById);
    const rightScore = getCaseScore(right, scoresById);

    let a;
    let b;

    switch (sort.field) {
      case "probability":
        a = numericProbability(leftScore);
        b = numericProbability(rightScore);
        break;
      case "risk":
        a = RISK_LEVELS.indexOf(normalize(leftScore?.risk_band));
        b = RISK_LEVELS.indexOf(normalize(rightScore?.risk_band));
        break;
      case "status":
        a = normalize(left.case_status);
        b = normalize(right.case_status);
        break;
      case "created_at":
        a = new Date(left.created_at || 0).getTime();
        b = new Date(right.created_at || 0).getTime();
        break;
      case "updated_at":
      default:
        a = timestamp(left);
        b = timestamp(right);
        break;
    }

    if (typeof a === "string") {
      return a.localeCompare(b) * direction;
    }

    return (a - b) * direction;
  });
}

export function paginate(items, page, pageSize) {
  const totalItems = items.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  const safePage = Math.min(Math.max(1, page), totalPages);
  const start = (safePage - 1) * pageSize;

  return {
    items: items.slice(start, start + pageSize),
    page: safePage,
    pageSize,
    totalItems,
    totalPages,
  };
}

export function summarizeCases(cases = []) {
  const summary = {
    total: cases.length,
    new: 0,
    open: 0,
    assigned: 0,
    investigating: 0,
    pending_customer: 0,
    escalated: 0,
    resolved: 0,
    under_review: 0,
    confirmed_fraud: 0,
    false_positive: 0,
    closed: 0,
  };

  for (const item of cases) {
    if (Object.hasOwn(summary, item.case_status)) {
      summary[item.case_status] += 1;
    }
  }

  return summary;
}

export function findCaseForScore(cases = [], fraudScoreRecordId) {
  return (
    cases.find(
      (caseRecord) =>
        caseRecord.fraud_score_record_id === fraudScoreRecordId
    ) || null
  );
}

export function buildCaseCreationPayload(
  fraudScoreRecordId,
  defaults = {}
) {
  return {
    fraud_score_record_id: fraudScoreRecordId,
    case_status: defaults.case_status || "open",
    analyst_decision: defaults.analyst_decision || "pending",
    analyst_notes: defaults.analyst_notes || null,
    reviewed_by: defaults.reviewed_by || null,
  };
}
