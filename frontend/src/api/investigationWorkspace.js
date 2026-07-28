import { httpClient } from "./httpClient";

const FRAUD_CASES = "/api/v1/fraud/cases";
const CASES = "/api/v1/cases";
const TASKS = "/api/v1/fraud-cases";

function fulfilled(result, fallback) {
  return result.status === "fulfilled"
    ? result.value
    : fallback;
}

function listItems(result) {
  const value = fulfilled(result, null);
  return value?.data?.items || value?.data || [];
}

function normalizeTask(task) {
  return {
    ...task,
    completed: task.status === "completed",
  };
}

function normalizeEvidence(caseId, evidence) {
  return {
    ...evidence,
    filename:
      evidence.original_filename ||
      evidence.filename ||
      evidence.name,
    uploaded_at:
      evidence.created_at || evidence.uploaded_at,
    uploader:
      evidence.uploader_username || evidence.uploader,
    size:
      evidence.file_size_bytes ?? evidence.size,
    download_url: `${CASES}/${caseId}/evidence/${evidence.id}/download`,
  };
}

function normalizeComment(comment) {
  return {
    ...comment,
    author_name:
      comment.author_username ||
      comment.author_name ||
      comment.user_name,
  };
}

function normalizeHistory(entry) {
  const details = entry.details;
  return {
    ...entry,
    title:
      entry.title ||
      entry.event_type ||
      entry.action ||
      "Investigation activity",
    description:
      typeof details === "string"
        ? details
        : details
          ? JSON.stringify(details)
          : "",
    actor_name:
      entry.actor_username ||
      entry.actor_name ||
      entry.user_name,
  };
}

function normalizeAnalyst(analyst) {
  return {
    ...analyst,
    id: analyst.analyst_id ?? analyst.id,
    name:
      analyst.full_name ||
      analyst.username ||
      analyst.name,
  };
}

function auditBelongsToCase(entry, caseId) {
  const directCaseResource = new Set([
    "fraud_case",
    "fraud_case_review",
  ]);

  return (
    (directCaseResource.has(entry.resource_type) &&
      String(entry.resource_id) === String(caseId)) ||
    String(entry.details?.case_id) === String(caseId)
  );
}

export async function getInvestigationWorkspace(caseId) {
  const requests = await Promise.allSettled([
    httpClient.get(`${FRAUD_CASES}/${caseId}`),
    httpClient.get(`${CASES}/${caseId}/comments`, {
      params: { limit: 100 },
    }),
    httpClient.get(`${CASES}/${caseId}/evidence`, {
      params: { limit: 100 },
    }),
    httpClient.get(`${TASKS}/${caseId}/tasks`, {
      params: { limit: 100 },
    }),
    httpClient.get(`/api/v1/cases/${caseId}/timeline`),
    httpClient.get(`${CASES}/assignments/workload`),
    httpClient.get("/api/v1/audit-logs", {
      params: { limit: 200 },
    }),
    httpClient.get("/api/v1/fraud/scores", {
      params: { limit: 100 },
    }),
    httpClient.get("/api/v1/auth/me"),
  ]);

  const caseResponse = fulfilled(requests[0], null);
  if (!caseResponse) {
    throw requests[0].reason;
  }

  const caseRecord = caseResponse.data;
  const scores = listItems(requests[7]);
  const score =
    scores.find(
      (item) =>
        item.id === caseRecord.fraud_score_record_id,
    ) || {};
  const history = listItems(requests[4]).map(
    normalizeHistory,
  );
  const auditLog = listItems(requests[6]).filter(
    (entry) => auditBelongsToCase(entry, caseId),
  );

  return {
    investigation: {
      ...score,
      ...caseRecord,
      case_id: caseRecord.id,
      fraud_score_record_id:
        caseRecord.fraud_score_record_id,
      transaction_id:
        score.transaction_id ||
        caseRecord.transaction_id,
      status: caseRecord.case_status,
      assigned_analyst_name:
        caseRecord.assigned_to_username ||
        caseRecord.assigned_to,
      assigned_analyst_id:
        caseRecord.assigned_to_user_id || "",
    },
    notes: listItems(requests[1]).map(normalizeComment),
    evidence: listItems(requests[2]).map((item) =>
      normalizeEvidence(caseId, item),
    ),
    tasks: listItems(requests[3]).map(normalizeTask),
    analysts: listItems(requests[5]).map(normalizeAnalyst),
    timeline: history,
    activity_history: history,
    audit_log: auditLog,
    current_user: fulfilled(requests[8], null)?.data ?? null,
  };
}

export async function updateInvestigationStatus(
  caseId,
  status,
) {
  const { data } = await httpClient.patch(
    `${FRAUD_CASES}/${caseId}`,
    { case_status: status },
  );
  return {
    ...data,
    status: data.case_status,
  };
}

export async function assignInvestigation(
  caseId,
  analystId,
) {
  if (!analystId) {
    const { data } = await httpClient.delete(
      `${CASES}/${caseId}/assignment`,
    );
    if (data.case_status === "assigned") {
      return updateInvestigationStatus(caseId, "new");
    }
    return {
      ...data,
      status: data.case_status,
    };
  }

  const { data } = await httpClient.patch(
    `${CASES}/${caseId}/assignment`,
    {
      assigned_to_user_id: Number(analystId),
    },
  );
  if (["open", "new"].includes(data.case_status)) {
    return updateInvestigationStatus(caseId, "assigned");
  }
  return {
    ...data,
    status: data.case_status,
  };
}

export async function addInvestigationNote(
  caseId,
  content,
) {
  const { data } = await httpClient.post(
    `${CASES}/${caseId}/comments`,
    {
      content,
      visibility: "internal",
    },
  );
  return normalizeComment(data);
}

export async function addInvestigationTask(
  caseId,
  title,
  assignedToUserId = null,
) {
  const { data } = await httpClient.post(
    `${TASKS}/${caseId}/tasks`,
    {
      title,
      ...(assignedToUserId
        ? {
            assigned_to_user_id: Number(
              assignedToUserId,
            ),
          }
        : {}),
    },
  );
  return normalizeTask(data);
}

export async function updateInvestigationTask(
  caseId,
  taskId,
  patch,
) {
  if (patch.completed) {
    if (patch.currentStatus !== "in_progress") {
      await httpClient.patch(
        `${TASKS}/${caseId}/tasks/${taskId}/status`,
        {
          status: "in_progress",
          reason: "Started from investigation workspace",
        },
      );
    }
    const { data } = await httpClient.post(
      `${TASKS}/${caseId}/tasks/${taskId}/complete`,
      {
        completion_note:
          "Completed from investigation workspace",
      },
    );
    return normalizeTask(data);
  }

  throw new Error(
    "Completed investigation tasks are immutable.",
  );
}

export async function downloadInvestigationEvidence(
  caseId,
  evidence,
) {
  const response = await httpClient.get(
    `${CASES}/${caseId}/evidence/${evidence.id}/download`,
    { responseType: "blob" },
  );
  const url = URL.createObjectURL(response.data);
  const link = document.createElement("a");
  link.href = url;
  link.download =
    evidence.filename ||
    evidence.original_filename ||
    `evidence-${evidence.id}`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
