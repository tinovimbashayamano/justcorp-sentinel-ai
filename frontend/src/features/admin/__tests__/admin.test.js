import {
  describe,
  expect,
  it,
} from "vitest";

import {
  buildPermissionMatrix,
  calculateAdminStatistics,
  normalizeUsers,
  sortAuditEvents,
  sortSessions,
  validatePasswordPolicy,
} from "../domain/admin";

describe("admin domain", () => {
  it("normalizes and sorts users", () => {
    const users = normalizeUsers([
      {
        id: 2,
        username: "zara",
        full_name: "Zara",
        role: "auditor",
      },
      {
        id: 1,
        username: "alice",
        full_name: "Alice",
        role: "admin",
      },
    ]);

    expect(users[0]).toMatchObject({
      name: "Alice",
      username: "alice",
      role: "admin",
    });
  });

  it("marks unsupported user metadata as unavailable", () => {
    const [user] = normalizeUsers([
      {
        id: 1,
        username: "analyst",
        is_active: false,
      },
    ]);

    expect(user.status).toBe("disabled");
    expect(user.department).toBeNull();
    expect(user.mfaEnabled).toBeNull();
  });

  it("calculates supported statistics", () => {
    const result = calculateAdminStatistics({
      users: [
        { status: "active", mfaEnabled: true },
        { status: "disabled", mfaEnabled: false },
      ],
      roles: [{}, {}],
      sessions: [{ status: "active" }],
      apiKeys: [{ status: "active" }],
    });

    expect(result.activeUsers).toBe(1);
    expect(result.roles).toBe(2);
    expect(result.mfaCoverage).toBe(50);
  });

  it("does not invent MFA coverage", () => {
    const result = calculateAdminStatistics({
      users: [{ status: "active", mfaEnabled: null }],
    });

    expect(result.mfaCoverage).toBeNull();
  });

  it("builds the read-only permission matrix", () => {
    const result = buildPermissionMatrix(
      [
        {
          id: "viewer",
          name: "viewer",
          permissions: [
            "fraud.view",
            { code: "reports.export" },
          ],
        },
      ],
      [
        { code: "fraud.view" },
        { code: "fraud.edit" },
        { code: "reports.export" },
      ],
    );

    expect(result[0].permissions).toEqual({
      "fraud.view": true,
      "fraud.edit": false,
      "reports.export": true,
    });
  });

  it("sorts sessions newest first", () => {
    const sessions = sortSessions([
      { id: 1, login_at: "2026-07-27" },
      { id: 2, login_at: "2026-07-28" },
    ]);

    expect(sessions[0].id).toBe(2);
  });

  it("sorts audit events newest first", () => {
    const events = sortAuditEvents([
      { id: 1, created_at: "2026-07-27" },
      { id: 2, created_at: "2026-07-28" },
    ]);

    expect(events[0].id).toBe(2);
  });

  it("normalizes real backend audit fields", () => {
    const [event] = sortAuditEvents([
      {
        id: 1,
        actor_username: "admin",
        resource_type: "user",
        resource_id: "9",
        details: { new_role: "auditor" },
      },
    ]);

    expect(event.actor).toBe("admin");
    expect(event.resource).toBe("user");
    expect(event.details).toContain("auditor");
  });

  it("validates unsafe password policy values", () => {
    expect(
      validatePasswordPolicy({
        minimum_length: 6,
        max_login_attempts: 0,
        session_timeout_minutes: 2,
      }),
    ).toHaveLength(3);
  });

  it("accepts safe password policy values", () => {
    expect(
      validatePasswordPolicy({
        minimum_length: 12,
        max_login_attempts: 5,
        session_timeout_minutes: 30,
      }),
    ).toEqual([]);
  });
});
