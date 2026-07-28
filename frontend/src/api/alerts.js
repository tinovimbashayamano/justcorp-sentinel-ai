import { httpClient } from "./httpClient";

export async function listFraudAlerts({ limit = 100 } = {}) {
  const { data } = await httpClient.get("/api/v1/fraud/scores", { params: { limit } });
  return data;
}
