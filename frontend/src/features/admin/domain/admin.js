export function normalizeUsers(users = []) {
  return [...users]
    .map((user) => ({
      id: user.id,
      username: user.username ?? "",
      name:
        user.full_name ??
        user.name ??
        user.username ??
        "Unnamed user",
      email: user.email ?? "—",
      role:
        user.role?.value ??
        user.role_name ??
        user.role ??
        "viewer",
      department:
        user.department_name ??
        user.department ??
        null,
      status:
        user.status ??
        (user.is_active === false
          ? "disabled"
          : "active"),
      lastLogin:
        user.last_login_at ?? user.last_login ?? null,
      mfaEnabled:
        typeof user.mfa_enabled === "boolean"
          ? user.mfa_enabled
          : null,
      locked:
        typeof (user.is_locked ?? user.locked) ===
        "boolean"
          ? Boolean(user.is_locked ?? user.locked)
          : null,
    }))
    .sort((a, b) => a.name.localeCompare(b.name));
}

export function calculateAdminStatistics({
  users = [],
  roles = [],
  sessions = [],
  apiKeys = [],
} = {}) {
  const usersWithMfaData = users.filter(
    (user) =>
      typeof (user.mfaEnabled ?? user.mfa_enabled) ===
      "boolean",
  );
  const mfaEnabled = usersWithMfaData.filter(
    (user) => user.mfaEnabled ?? user.mfa_enabled,
  ).length;

  return {
    users: users.length,
    activeUsers: users.filter(
      (user) => user.status !== "disabled",
    ).length,
    roles: roles.length,
    activeSessions: sessions.filter(
      (session) => session.status !== "revoked",
    ).length,
    activeApiKeys: apiKeys.filter(
      (key) => key.status === "active",
    ).length,
    mfaCoverage: usersWithMfaData.length
      ? Math.round(
          (mfaEnabled / usersWithMfaData.length) * 100,
        )
      : null,
  };
}

export function buildPermissionMatrix(
  roles = [],
  permissions = [],
) {
  const codes = permissions.map(
    (permission) => permission.code ?? permission.name,
  );

  return roles.map((role) => {
    const assigned = new Set(
      (role.permissions ?? []).map((permission) =>
        typeof permission === "string"
          ? permission
          : permission.code ?? permission.name,
      ),
    );

    return {
      id: role.id,
      name:
        role.display_name ??
        role.name ??
        "Unnamed role",
      permissions: Object.fromEntries(
        codes.map((code) => [
          code,
          assigned.has(code),
        ]),
      ),
    };
  });
}

export function sortSessions(sessions = []) {
  return [...sessions].sort(
    (a, b) =>
      new Date(
        b.login_at ?? b.created_at ?? 0,
      ).getTime() -
      new Date(
        a.login_at ?? a.created_at ?? 0,
      ).getTime(),
  );
}

function printableDetails(details) {
  if (!details) return "—";
  return typeof details === "string"
    ? details
    : JSON.stringify(details);
}

export function sortAuditEvents(events = []) {
  return [...events]
    .map((event) => ({
      id: event.id,
      timestamp: event.timestamp ?? event.created_at,
      actor:
        event.actor_username ??
        event.actor_name ??
        event.user_name ??
        event.actor ??
        "System",
      action:
        event.action ??
        event.event_type ??
        "Unknown action",
      resource:
        event.resource ??
        event.resource_type ??
        event.entity_type ??
        "—",
      resourceId:
        event.resource_id ?? event.entity_id ?? "—",
      ipAddress: event.ip_address ?? "—",
      details: printableDetails(
        event.details ?? event.description,
      ),
    }))
    .sort(
      (a, b) =>
        new Date(b.timestamp ?? 0).getTime() -
        new Date(a.timestamp ?? 0).getTime(),
    );
}

export function validatePasswordPolicy(settings = {}) {
  const errors = [];

  if ((settings.minimum_length ?? 0) < 8) {
    errors.push(
      "Minimum password length must be at least 8 characters.",
    );
  }
  if ((settings.max_login_attempts ?? 0) < 1) {
    errors.push(
      "Maximum login attempts must be at least 1.",
    );
  }
  if ((settings.session_timeout_minutes ?? 0) < 5) {
    errors.push(
      "Session timeout must be at least 5 minutes.",
    );
  }

  return errors;
}
