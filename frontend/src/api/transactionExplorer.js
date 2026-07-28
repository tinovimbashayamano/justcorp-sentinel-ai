import { httpClient } from "./httpClient";

export async function searchTransactions({ limit = 100, offset = 0 } = {}) {
  const { data } = await httpClient.get("/api/v1/fraud/scores", {
    params: { limit, offset },
  });
  return data;
}
