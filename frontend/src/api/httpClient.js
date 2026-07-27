import axios from "axios";

const DEFAULT_TIMEOUT_MS = 30_000;

let accessTokenProvider = () =>
  window.localStorage.getItem("access_token") ||
  window.localStorage.getItem("accessToken") ||
  null;

export function configureAccessTokenProvider(provider) {
  if (typeof provider !== "function") {
    throw new TypeError(
      "Access token provider must be a function.",
    );
  }
  accessTokenProvider = provider;
}

export const httpClient = axios.create({
  baseURL:
    import.meta.env.VITE_API_BASE_URL ||
    "http://localhost:8000",
  timeout: DEFAULT_TIMEOUT_MS,
  headers: {
    Accept: "application/json",
    "Content-Type": "application/json",
  },
});

httpClient.interceptors.request.use((config) => {
  const token = accessTokenProvider();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

httpClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const normalized = new Error(
      typeof error?.response?.data?.detail === "string"
        ? error.response.data.detail
        : error.message || "Request failed.",
    );
    normalized.status = error?.response?.status;
    normalized.response = error?.response;
    normalized.cause = error;
    return Promise.reject(normalized);
  },
);
