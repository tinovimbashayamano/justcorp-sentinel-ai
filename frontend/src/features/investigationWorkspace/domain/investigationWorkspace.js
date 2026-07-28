export const INVESTIGATION_STATUSES = [
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

export const ALLOWED_STATUS_TRANSITIONS = {
  new: ["assigned", "investigating", "closed"],
  open: ["new", "assigned", "investigating", "closed"],
  assigned: [
    "investigating",
    "pending_customer",
    "escalated",
    "closed",
  ],
  investigating: [
    "pending_customer",
    "escalated",
    "resolved",
    "closed",
  ],
  pending_customer: [
    "investigating",
    "escalated",
    "resolved",
    "closed",
  ],
  escalated: ["investigating", "resolved", "closed"],
  resolved: ["investigating", "closed"],
  under_review: ["investigating", "resolved", "closed"],
  confirmed_fraud: ["closed"],
  false_positive: ["closed"],
  closed: [],
};

export function canTransitionStatus(current, next) {
  return (
    current === next ||
    (ALLOWED_STATUS_TRANSITIONS[current] || []).includes(
      next,
    )
  );
}

export function sortNewest(
  items = [],
  dateKey = "created_at",
) {
  return [...items].sort(
    (a, b) =>
      new Date(b[dateKey] || 0).getTime() -
      new Date(a[dateKey] || 0).getTime(),
  );
}

export function calculateTaskProgress(tasks = []) {
  const completed = tasks.filter(
    (task) => task.completed,
  ).length;
  return {
    total: tasks.length,
    completed,
    percentage: tasks.length
      ? Math.round((completed / tasks.length) * 100)
      : 0,
  };
}

export function buildSummary(item = {}) {
  const probability = Number(
    item.fraud_probability ??
      item.probability ??
      item.fraud_score ??
      0,
  );
  const amount = Number(
    item.transaction_amount ?? item.amount ?? 0,
  );
  let risk = String(item.risk_band || "").toLowerCase();

  if (!risk) {
    if (probability >= 0.9) risk = "critical";
    else if (probability >= 0.7) risk = "high";
    else if (probability >= 0.4) risk = "medium";
    else if (probability > 0) risk = "low";
    else risk = "unknown";
  }

  return {
    caseId: item.case_id ?? item.id ?? "—",
    transactionId: item.transaction_id ?? "—",
    status: item.status ?? item.case_status ?? "new",
    priority: item.priority ?? risk,
    risk,
    probability,
    amount,
    currency: item.currency ?? "USD",
    merchant:
      item.merchant_name ??
      item.merchant ??
      "Unknown merchant",
    customerId: item.customer_id ?? "—",
    assignedAnalyst:
      item.assigned_analyst_name ??
      item.assigned_to_username ??
      item.assigned_to ??
      "Unassigned",
    assignedAnalystId:
      item.assigned_analyst_id ??
      item.assigned_to_user_id ??
      "",
    dueDate: item.due_date ?? null,
    modelVersion:
      item.model_version ?? item.model_name ?? "—",
    deviceType: item.device_type ?? "—",
    location: item.location ?? item.ip_country ?? "—",
    decision: item.analyst_decision ?? "pending",
  };
}

function printableDetails(value) {
  if (!value) return "";
  return typeof value === "string"
    ? value
    : JSON.stringify(value);
}

export function buildTimeline(workspace = {}) {
  const events = [
    ...(workspace.timeline || []),
    ...(workspace.activity_history || []),
  ];
  const uniqueEvents = new Map();

  events.forEach((event, index) => {
    const normalized = {
      id: event.id ?? `${event.created_at}-${index}`,
      title:
        event.title ??
        event.action ??
        event.event_type ??
        event.type ??
        "Investigation activity",
      description: printableDetails(
        event.description ?? event.details,
      ),
      actor:
        event.actor_name ??
        event.actor_username ??
        event.user_name ??
        event.actor ??
        "System",
      created_at:
        event.created_at ??
        event.timestamp ??
        new Date().toISOString(),
    };
    const key = `${normalized.id}-${normalized.title}-${normalized.created_at}`;
    uniqueEvents.set(key, normalized);
  });

  return sortNewest([...uniqueEvents.values()]);
}

export function normalizeAudit(entries = []) {
  return sortNewest(
    entries.map((entry, index) => {
      const changes = entry.details?.changed_fields || {};
      const previousValues = Object.fromEntries(
        Object.entries(changes).map(([field, value]) => [
          field,
          value.old,
        ]),
      );
      const newValues = Object.fromEntries(
        Object.entries(changes).map(([field, value]) => [
          field,
          value.new,
        ]),
      );

      return {
        id: entry.id ?? `${entry.timestamp}-${index}`,
        created_at:
          entry.timestamp ??
          entry.created_at ??
          new Date().toISOString(),
        user:
          entry.user_name ??
          entry.actor_username ??
          entry.actor_name ??
          entry.user ??
          "System",
        action:
          entry.action ??
          entry.event_type ??
          "Unknown action",
        previousValue:
          entry.previous_value ??
          entry.old_value ??
          (Object.keys(previousValues).length
            ? JSON.stringify(previousValues)
            : "—"),
        newValue:
          entry.new_value ??
          entry.current_value ??
          (Object.keys(newValues).length
            ? JSON.stringify(newValues)
            : "—"),
        ipAddress: entry.ip_address ?? "—",
      };
    }),
  );
}
