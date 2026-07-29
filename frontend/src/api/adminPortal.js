import { httpClient } from "./httpClient";

const ADMIN_USERS = "/api/v1/admin/users";

export const ADMIN_CAPABILITIES = Object.freeze({
  users: true,
  roles: true,
  permissions: true,
  audit: true,
  teams: false,
  sessions: false,
  apiKeys: false,
  settings: false,
  organization: false,
});

export const ADMIN_PERMISSIONS = Object.freeze([
  {
    id: "fraud.view",
    code: "fraud.view",
    display_name: "View fraud data",
  },
  {
    id: "fraud.investigate",
    code: "fraud.investigate",
    display_name: "Investigate cases",
  },
  {
    id: "reports.export",
    code: "reports.export",
    display_name: "Export reports",
  },
  {
    id: "audit.view",
    code: "audit.view",
    display_name: "View audit logs",
  },
  {
    id: "users.manage",
    code: "users.manage",
    display_name: "Manage users",
  },
]);

export const ADMIN_ROLES = Object.freeze([
  {
    id: "admin",
    name: "admin",
    display_name: "Administrator",
    permissions: ADMIN_PERMISSIONS.map(
      (permission) => permission.code,
    ),
  },
  {
    id: "fraud_analyst",
    name: "fraud_analyst",
    display_name: "Fraud analyst",
    permissions: [
      "fraud.view",
      "fraud.investigate",
      "reports.export",
    ],
  },
  {
    id: "auditor",
    name: "auditor",
    display_name: "Auditor",
    permissions: [
      "fraud.view",
      "reports.export",
      "audit.view",
    ],
  },
  {
    id: "viewer",
    name: "viewer",
    display_name: "Viewer",
    permissions: ["fraud.view"],
  },
]);

function cloneItems(items) {
  return items.map((item) => ({
    ...item,
    permissions: item.permissions
      ? [...item.permissions]
      : undefined,
  }));
}

export async function getAdminOverview() {
  const { data } = await httpClient.get("/api/v1/auth/me");
  return {
    currentUser: data,
    capabilities: ADMIN_CAPABILITIES,
  };
}

export async function getAdminUsers() {
  const { data } = await httpClient.get(ADMIN_USERS, {
    params: { limit: 100 },
  });
  return data;
}

export async function createAdminUser(payload) {
  const registrationPayload = {
    username: payload.username,
    email: payload.email,
    password: payload.password,
    full_name: payload.full_name || null,
  };
  const { data: created } = await httpClient.post(
    "/api/v1/auth/register",
    registrationPayload,
  );

  if (payload.role && payload.role !== "viewer") {
    try {
      const { data: withRole } = await httpClient.patch(
        `${ADMIN_USERS}/${created.id}/role`,
        { role: payload.role },
      );
      return withRole;
    } catch (error) {
      error.message =
        `User ${created.username} was created as a viewer, ` +
        `but role assignment failed: ${error.message}`;
      throw error;
    }
  }

  return created;
}

export async function updateAdminUser(id, payload) {
  let updated = null;

  if (payload.role) {
    const response = await httpClient.patch(
      `${ADMIN_USERS}/${id}/role`,
      { role: payload.role },
    );
    updated = response.data;
  }

  if (typeof payload.is_active === "boolean") {
    const response = await httpClient.patch(
      `${ADMIN_USERS}/${id}/status`,
      { is_active: payload.is_active },
    );
    updated = response.data;
  }

  if (!updated) {
    throw new Error(
      "Only role and activation changes are supported by the current backend.",
    );
  }

  return updated;
}

export async function getAdminRoles() {
  return cloneItems(ADMIN_ROLES);
}

export async function getAdminPermissions() {
  return cloneItems(ADMIN_PERMISSIONS);
}

export async function getAdminAuditLog() {
  const { data } = await httpClient.get(
    "/api/v1/audit-logs",
    { params: { limit: 200 } },
  );
  return data.items || [];
}
