export const DEFAULT_SETTINGS = {
  theme: "system",
  accent_color: "blue",
  density: "comfortable",
  language: "en",
  timezone: "browser",
  date_format: "DD/MM/YYYY",
  number_format: "en-US",
  landing_page: "/",
};

export const DEFAULT_NOTIFICATION_SETTINGS = {
  email: true,
  sms: false,
  push: true,
  in_app: true,
  frequency: "immediate",
};

export function normalizeSettings(value = {}) {
  return { ...DEFAULT_SETTINGS, ...value };
}

export function normalizeNotificationSettings(value = {}) {
  return { ...DEFAULT_NOTIFICATION_SETTINGS, ...value };
}

export function sortNotifications(items = []) {
  return [...items].sort(
    (a, b) => new Date(b.timestamp ?? 0) - new Date(a.timestamp ?? 0)
  );
}

export function notificationSeverity(value) {
  const severity = String(value || "normal").toLowerCase();
  if (["critical", "high", "medium", "low"].includes(severity)) {
    return severity;
  }
  return "normal";
}

export function unreadCount(items = []) {
  return items.filter((item) => !item.read && !item.archived).length;
}

export function activeSessions(items = []) {
  return items.filter((item) => !item.revoked);
}

export function toggleFavorite(items = [], id) {
  return items.includes(id)
    ? items.filter((item) => item !== id)
    : [...items, id];
}

export function filterActivity(items = [], search = "") {
  const query = search.trim().toLowerCase();
  if (!query) return items;

  return items.filter((item) =>
    [item.action, item.description, item.ip_address, item.device].some(
      (value) => String(value ?? "").toLowerCase().includes(query)
    )
  );
}
