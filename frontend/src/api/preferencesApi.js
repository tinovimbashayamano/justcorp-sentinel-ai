import { httpClient } from "./httpClient";

const AUTH_BASE = "/api/v1/auth";
const NOTIFICATION_BASE = "/api/v1/notifications";

const DEFAULT_SETTINGS = {
  theme: "system",
  accent_color: "blue",
  density: "comfortable",
  language: "en",
  timezone: "browser",
  date_format: "DD/MM/YYYY",
  number_format: "en-US",
  landing_page: "/",
};

const DEFAULT_NOTIFICATION_SETTINGS = {
  email: true,
  sms: false,
  push: true,
  in_app: true,
  frequency: "immediate",
};

function parseJson(value, fallback = null) {
  try {
    return JSON.parse(value) ?? fallback;
  } catch {
    return fallback;
  }
}

function tokenIdentity() {
  const storedUser = parseJson(window.localStorage.getItem("user"), {});
  const directIdentity =
    storedUser.id || storedUser.username || storedUser.email;
  if (directIdentity) return String(directIdentity);

  const token =
    window.localStorage.getItem("access_token") ||
    window.localStorage.getItem("accessToken");
  if (!token) return "anonymous";

  try {
    const payload = token.split(".")[1];
    const normalized = payload.replaceAll("-", "+").replaceAll("_", "/");
    const padded = normalized.padEnd(
      Math.ceil(normalized.length / 4) * 4,
      "=",
    );
    return String(parseJson(window.atob(padded), {})?.sub || "authenticated");
  } catch {
    return "authenticated";
  }
}

function storageKey(name) {
  return `sentinel.preferences.${tokenIdentity()}.${name}`;
}

function readPreference(name, fallback) {
  return parseJson(window.localStorage.getItem(storageKey(name)), fallback);
}

function writePreference(name, value) {
  window.localStorage.setItem(storageKey(name), JSON.stringify(value));
}

function listItems(value) {
  if (Array.isArray(value)) return value;
  if (Array.isArray(value?.items)) return value.items;
  return [];
}

async function optionalGet(path, config) {
  try {
    const { data } = await httpClient.get(path, config);
    return data;
  } catch {
    return null;
  }
}

function normalizeNotification(item) {
  return {
    ...item,
    timestamp: item.timestamp || item.created_at,
    severity: String(item.severity || item.priority || "normal").toLowerCase(),
    category: item.category || item.notification_type || "system",
    read: Boolean(item.read ?? item.is_read),
    archived: Boolean(item.archived ?? item.is_deleted),
  };
}

function describeUserAgent() {
  const userAgent = window.navigator.userAgent || "";
  const browser = userAgent.includes("Edg/")
    ? "Microsoft Edge"
    : userAgent.includes("Firefox/")
      ? "Firefox"
      : userAgent.includes("Chrome/")
        ? "Chrome"
        : userAgent.includes("Safari/")
          ? "Safari"
          : "Browser";
  const device = /Android|iPhone|iPad|Mobile/i.test(userAgent)
    ? "Mobile device"
    : "Desktop device";
  return { browser, device };
}

function currentSession() {
  const { browser, device } = describeUserAgent();
  return {
    id: "current-browser",
    device,
    browser,
    ip_address: "Not exposed",
    country: "Not exposed",
    last_activity: new Date().toISOString(),
    current: true,
    revoked: false,
  };
}

function mapActivity(item) {
  return {
    id: item.id,
    action: item.action || "Account activity",
    description: [
      item.resource_type,
      item.resource_id,
      item.status,
    ]
      .filter(Boolean)
      .join(" / "),
    ip_address: item.ip_address || null,
    device: item.user_agent || null,
    timestamp: item.created_at,
  };
}

export const preferencesApi = {
  profile: async () => {
    const { data } = await httpClient.get(`${AUTH_BASE}/me`);
    return {
      ...data,
      ...readPreference("profile", {}),
    };
  },
  updateProfile: (payload) => {
    const updated = {
      ...readPreference("profile", {}),
      ...payload,
    };
    writePreference("profile", updated);
    return Promise.resolve(updated);
  },
  settings: () =>
    Promise.resolve({
      ...DEFAULT_SETTINGS,
      ...readPreference("settings", {}),
    }),
  updateSettings: (payload) => {
    const updated = {
      ...DEFAULT_SETTINGS,
      ...readPreference("settings", {}),
      ...payload,
    };
    writePreference("settings", updated);
    return Promise.resolve(updated);
  },
  notifications: async () => {
    const { data } = await httpClient.get(NOTIFICATION_BASE, {
      params: { limit: 100 },
    });
    return {
      ...data,
      items: listItems(data).map(normalizeNotification),
      settings: {
        ...DEFAULT_NOTIFICATION_SETTINGS,
        ...readPreference("notification-settings", {}),
      },
    };
  },
  updateNotifications: (payload) => {
    const updated = {
      ...DEFAULT_NOTIFICATION_SETTINGS,
      ...readPreference("notification-settings", {}),
      ...payload,
    };
    writePreference("notification-settings", updated);
    return Promise.resolve(updated);
  },
  markNotificationRead: (id) =>
    httpClient
      .patch(`${NOTIFICATION_BASE}/${id}/read`)
      .then((response) => normalizeNotification(response.data)),
  markNotificationUnread: (id) =>
    httpClient
      .patch(`${NOTIFICATION_BASE}/${id}/unread`)
      .then((response) => normalizeNotification(response.data)),
  archiveNotification: (id) =>
    httpClient
      .delete(`${NOTIFICATION_BASE}/${id}`)
      .then((response) => normalizeNotification(response.data)),
  markAllNotificationsRead: () =>
    httpClient
      .patch(`${NOTIFICATION_BASE}/read-all`)
      .then((response) => response.data),
  sessions: () => Promise.resolve([currentSession()]),
  revokeSession: (id) => {
    if (id !== "current-browser") {
      return Promise.resolve({ id, revoked: true });
    }
    return httpClient
      .post(`${AUTH_BASE}/logout-all`)
      .then((response) => response.data);
  },
  devices: () => {
    const session = currentSession();
    return Promise.resolve([
      {
        id: session.id,
        device: session.device,
        browser: session.browser,
        last_seen: session.last_activity,
        current: true,
      },
    ]);
  },
  activity: async () => {
    const audit = await optionalGet("/api/v1/audit-logs", {
      params: { limit: 100 },
    });
    return listItems(audit).map(mapActivity);
  },
  favorites: () =>
    Promise.resolve(readPreference("favorites", [])),
  updateFavorites: (payload) => {
    const updated = Array.isArray(payload)
      ? payload
      : payload?.items || payload?.favorites || [];
    writePreference("favorites", updated);
    return Promise.resolve(updated);
  },
  savedFilters: () =>
    Promise.resolve(readPreference("saved-filters", [])),
  updateSavedFilters: (payload) => {
    const updated = Array.isArray(payload)
      ? payload
      : payload?.items || payload?.saved_filters || [];
    writePreference("saved-filters", updated);
    return Promise.resolve(updated);
  },
  changePassword: (payload) =>
    httpClient
      .post(`${AUTH_BASE}/change-password`, payload)
      .then((response) => response.data),
  logoutAll: () =>
    httpClient
      .post(`${AUTH_BASE}/logout-all`)
      .then((response) => {
        window.localStorage.removeItem("access_token");
        window.localStorage.removeItem("accessToken");
        window.localStorage.removeItem("refresh_token");
        window.localStorage.removeItem("refreshToken");
        return response.data;
      }),
};
