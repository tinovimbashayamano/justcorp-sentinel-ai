import { httpClient } from "./httpClient";

const BASE_PATH =
  "/api/v1/explainability-visualizations";

export async function getVisualizationHealth() {
  return (await httpClient.get(`${BASE_PATH}/health`)).data;
}

export async function getLocalVisualization(payload) {
  return (
    await httpClient.post(`${BASE_PATH}/local/data`, payload)
  ).data;
}

export async function getWaterfallPlot(payload) {
  return (
    await httpClient.post(
      `${BASE_PATH}/local/waterfall`,
      payload,
    )
  ).data;
}

export async function getForcePlot(payload) {
  return (
    await httpClient.post(
      `${BASE_PATH}/local/force`,
      payload,
    )
  ).data;
}

export async function getGlobalVisualization(limit = 20) {
  return (
    await httpClient.get(`${BASE_PATH}/global/data`, {
      params: { limit },
    })
  ).data;
}

export async function getGlobalSummaryPlot(limit = 20) {
  return (
    await httpClient.get(`${BASE_PATH}/global/summary`, {
      params: { limit },
    })
  ).data;
}

export async function getDependenceData(
  featureName,
  limit = 500,
) {
  const safeFeature = encodeURIComponent(featureName);
  return (
    await httpClient.get(
      `${BASE_PATH}/dependence/${safeFeature}`,
      { params: { limit } },
    )
  ).data;
}

export async function exportInvestigationReport(
  format,
  payload,
) {
  const normalized = String(format).toLowerCase();
  if (!["html", "pdf"].includes(normalized)) {
    throw new Error(
      "Report format must be 'html' or 'pdf'.",
    );
  }
  return (
    await httpClient.post(
      `${BASE_PATH}/reports/${normalized}`,
      payload,
    )
  ).data;
}
