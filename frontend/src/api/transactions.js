import { httpClient } from "./httpClient";
const FRAUD_BASE = "/api/v1/fraud";
export async function listTransactions({ limit = 100, offset = 0, risk, search } = {}) {
  const { data } = await httpClient.get(`${FRAUD_BASE}/scores`, {
    params: { limit, offset, risk: risk || undefined, search: search || undefined },
  });
  return data;
}
