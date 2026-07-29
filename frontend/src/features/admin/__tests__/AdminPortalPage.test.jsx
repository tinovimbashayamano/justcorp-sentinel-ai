import {
  fireEvent,
  render,
  screen,
} from "@testing-library/react";
import {
  describe,
  expect,
  it,
  vi,
} from "vitest";

import AdminPortalPage from "../pages/AdminPortalPage";

const portal = vi.hoisted(() => ({
  overview: {},
  currentUser: { id: 1, role: "admin" },
  users: [
    {
      id: 2,
      username: "analyst",
      name: "Ada Analyst",
      email: "ada@example.com",
      role: "fraud_analyst",
      department: null,
      status: "active",
      lastLogin: null,
      mfaEnabled: null,
      locked: null,
    },
  ],
  roles: [
    {
      id: "admin",
      display_name: "Administrator",
    },
  ],
  permissions: [
    {
      id: "users.manage",
      code: "users.manage",
      display_name: "Manage users",
    },
  ],
  teams: [],
  sessions: [],
  apiKeys: [],
  settings: {},
  audit: [
    {
      id: 1,
      timestamp: "2026-07-28T10:00:00Z",
      actor: "admin",
      action: "admin.user.role_update",
      resource: "user",
      resourceId: "2",
      ipAddress: "127.0.0.1",
      details: "{\"new_role\":\"fraud_analyst\"}",
    },
  ],
  capabilities: {
    users: true,
    roles: true,
    permissions: true,
    audit: true,
    teams: false,
    sessions: false,
    apiKeys: false,
    settings: false,
    organization: false,
  },
  permissionMatrix: [
    {
      id: "admin",
      name: "Administrator",
      permissions: { "users.manage": true },
    },
  ],
  statistics: {
    users: 1,
    activeUsers: 1,
    roles: 4,
    activeSessions: 0,
    activeApiKeys: 0,
    mfaCoverage: null,
  },
  loading: false,
  saving: false,
  error: null,
  loadPortal: vi.fn().mockResolvedValue({}),
  createUser: vi.fn(),
  updateUser: vi.fn(),
}));

vi.mock("../hooks/useAdminPortal", () => ({
  useAdminPortal: () => portal,
}));

describe("AdminPortalPage", () => {
  it("renders supported administration features", () => {
    render(<AdminPortalPage />);

    expect(
      screen.getByRole("heading", {
        name: /Enterprise administration/i,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: /User management/i,
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("Ada Analyst")).toBeInTheDocument();
    expect(
      screen.getAllByText("Not tracked"),
    ).not.toHaveLength(0);
  });

  it("renders the read-only role matrix", () => {
    render(<AdminPortalPage />);

    fireEvent.click(
      screen.getByRole("button", { name: "Roles" }),
    );

    expect(
      screen.getByRole("heading", {
        name: /Role management/i,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Administrator"),
    ).toBeInTheDocument();
  });

  it("labels unavailable modules and renders audit data", () => {
    render(<AdminPortalPage />);

    fireEvent.click(
      screen.getByRole("button", { name: "Sessions" }),
    );
    expect(
      screen.getByText(/cannot list or terminate/i),
    ).toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("button", { name: "Audit" }),
    );
    expect(
      screen.getByText("admin.user.role_update"),
    ).toBeInTheDocument();
    expect(screen.getByText("127.0.0.1")).toBeInTheDocument();
  });
});
