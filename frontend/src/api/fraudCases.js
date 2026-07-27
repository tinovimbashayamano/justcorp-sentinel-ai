import { httpClient } from "./httpClient";

const FRAUD_BASE = "/api/v1/fraud";

export async function listFraudCases({
  limit = 50,
} = {}) {
  const { data } = await httpClient.get(
    `${FRAUD_BASE}/cases`,
    {
      params: { limit },
    },
  );
  return data;
}

export async function getFraudCase(caseId) {
  const { data } = await httpClient.get(
    `${FRAUD_BASE}/cases/${caseId}`,
  );
  return data;
}

export async function createFraudCase(payload) {
  const { data } = await httpClient.post(
    `${FRAUD_BASE}/cases`,
    payload,
  );
  return data;
}

export async function updateFraudCase(
  caseId,
  payload,
) {
  const { data } = await httpClient.patch(
    `${FRAUD_BASE}/cases/${caseId}`,
    payload,
  );
  return data;
}

export async function listFraudScores({
  limit = 50,
} = {}) {
  const { data } = await httpClient.get(
    `${FRAUD_BASE}/scores`,
    {
      params: { limit },
    },
  );
  return data;
}
