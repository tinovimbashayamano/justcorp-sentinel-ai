import {
  useEffect,
  useMemo,
  useState,
} from "react";

import { useAdminPortal } from "../hooks/useAdminPortal";
import "../styles/admin.css";

const NAV_ITEMS = [
  ["overview", "dashboard", "Dashboard", "Dashboard"],
  ["users", "users", "User Management", "Users"],
  ["roles", "shield", "Role Management", "Roles"],
  [
    "permissions",
    "grid",
    "Permission Matrix",
    "Permissions",
  ],
  ["teams", "teams", "Team Management", "Teams"],
  [
    "sessions",
    "monitor",
    "Session Management",
    "Sessions",
  ],
  ["api_keys", "key", "API Keys", "API keys"],
  [
    "settings",
    "lock",
    "Security Settings",
    "Settings",
  ],
  [
    "system",
    "settings",
    "System Settings",
    "System settings",
  ],
  [
    "organization",
    "building",
    "Organization Profile",
    "Organization",
  ],
  [
    "audit",
    "audit",
    "Audit Administration",
    "Audit",
  ],
];

const ROLE_OPTIONS = [
  ["admin", "Administrator"],
  ["fraud_analyst", "Fraud analyst"],
  ["auditor", "Auditor"],
  ["viewer", "Viewer"],
];

const EMPTY_USER_FORM = {
  username: "",
  full_name: "",
  email: "",
  password: "",
  role: "viewer",
};

function AdminIcon({
  name,
  size = 18,
}) {
  return (
    <svg
      aria-hidden="true"
      className="admin-icon"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {name === "dashboard" ? (
        <>
          <rect x="3" y="3" width="7" height="7" rx="1" />
          <rect x="14" y="3" width="7" height="7" rx="1" />
          <rect x="3" y="14" width="7" height="7" rx="1" />
          <rect x="14" y="14" width="7" height="7" rx="1" />
        </>
      ) : null}
      {name === "users" || name === "teams" ? (
        <>
          <circle cx="9" cy="8" r="3" />
          <path d="M3.5 19c.7-3.2 2.5-5 5.5-5s4.8 1.8 5.5 5" />
          <path d="M16 5.5a3 3 0 0 1 0 5.8M16.5 14c2.3.4 3.7 2 4 4.2" />
        </>
      ) : null}
      {name === "shield" ? (
        <>
          <path d="M12 3 20 6v5c0 5-3.2 8.2-8 10-4.8-1.8-8-5-8-10V6l8-3Z" />
          <path d="m9.5 12 1.7 1.7 3.6-4" />
        </>
      ) : null}
      {name === "grid" ? (
        <>
          <path d="M4 4h16v16H4zM4 10h16M10 4v16" />
        </>
      ) : null}
      {name === "monitor" ? (
        <>
          <rect x="3" y="4" width="18" height="13" rx="2" />
          <path d="M8 21h8M12 17v4" />
        </>
      ) : null}
      {name === "key" ? (
        <>
          <circle cx="8" cy="15" r="4" />
          <path d="m11 12 8-8M16 7l2 2M14 9l2 2" />
        </>
      ) : null}
      {name === "lock" ? (
        <>
          <rect x="4" y="10" width="16" height="11" rx="2" />
          <path d="M8 10V7a4 4 0 0 1 8 0v3M12 14v3" />
        </>
      ) : null}
      {name === "settings" ? (
        <>
          <circle cx="12" cy="12" r="3" />
          <path d="M19 12a7 7 0 0 0-.1-1l2-1.6-2-3.4-2.5 1a8 8 0 0 0-1.8-1L14.2 3h-4.4l-.4 3a8 8 0 0 0-1.8 1L5.1 6l-2 3.4L5 11a7 7 0 0 0 0 2l-2 1.6L5.1 18l2.5-1a8 8 0 0 0 1.8 1l.4 3h4.4l.4-3a8 8 0 0 0 1.8-1l2.5 1 2-3.4L19 13a7 7 0 0 0 .1-1Z" />
        </>
      ) : null}
      {name === "building" ? (
        <>
          <path d="M5 21V4h10v17M15 9h4v12M3 21h18" />
          <path d="M8 8h4M8 12h4M8 16h4" />
        </>
      ) : null}
      {name === "audit" ? (
        <>
          <path d="M8 4h8M9 2h6v4H9z" />
          <path d="M6 4H5v17h14V4h-1M8 11h8M8 15h8" />
        </>
      ) : null}
      {name === "menu" ? (
        <path d="M4 6h16M4 12h16M4 18h16" />
      ) : null}
      {name === "bell" ? (
        <>
          <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9" />
          <path d="M10 21h4" />
        </>
      ) : null}
      {name === "help" ? (
        <>
          <circle cx="12" cy="12" r="9" />
          <path d="M9.7 9a2.4 2.4 0 1 1 3.3 2.2c-1 .5-1 1.2-1 2M12 17h.01" />
        </>
      ) : null}
      {name === "search" ? (
        <>
          <circle cx="10.5" cy="10.5" r="6.5" />
          <path d="m16 16 4 4" />
        </>
      ) : null}
      {name === "plus" ? (
        <path d="M12 5v14M5 12h14" />
      ) : null}
      {name === "arrow" ? (
        <path d="m9 18 6-6-6-6" />
      ) : null}
    </svg>
  );
}

function initials(value) {
  return String(value || "Admin User")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}

function readable(value) {
  return String(value ?? "-").replaceAll("_", " ");
}

function roleLabel(role) {
  return (
    ROLE_OPTIONS.find(([value]) => value === role)?.[1] ??
    readable(role)
  );
}

function UserAvatar({ user, index = 0 }) {
  return (
    <span
      className={`admin-avatar admin-avatar--${index % 5}`}
    >
      {initials(user.name || user.username)}
    </span>
  );
}

function CreateUserForm({
  portal,
  onClose,
}) {
  const [form, setForm] = useState(EMPTY_USER_FORM);

  function update(name, value) {
    setForm((current) => ({
      ...current,
      [name]: value,
    }));
  }

  async function submit(event) {
    event.preventDefault();
    try {
      const created = await portal.createUser(form);
      if (created) onClose();
    } catch {
      // The hook exposes the normalized API error in the page alert.
    }
  }

  return (
    <form
      className="admin-create-user"
      onSubmit={submit}
    >
      <div className="admin-create-user__heading">
        <div>
          <strong>Create enterprise user</strong>
          <span>
            A temporary password is required by the current
            authentication API.
          </span>
        </div>
        <button type="button" onClick={onClose}>
          Cancel
        </button>
      </div>
      <div className="admin-create-user__fields">
        <input
          aria-label="Username"
          placeholder="Username"
          minLength="3"
          value={form.username}
          onChange={(event) =>
            update("username", event.target.value)
          }
          required
        />
        <input
          aria-label="Full name"
          placeholder="Full name"
          value={form.full_name}
          onChange={(event) =>
            update("full_name", event.target.value)
          }
        />
        <input
          aria-label="Email"
          type="email"
          placeholder="Email"
          value={form.email}
          onChange={(event) =>
            update("email", event.target.value)
          }
          required
        />
        <input
          aria-label="Temporary password"
          type="password"
          placeholder="Temporary password"
          minLength="12"
          value={form.password}
          onChange={(event) =>
            update("password", event.target.value)
          }
          required
        />
        <select
          aria-label="Initial role"
          value={form.role}
          onChange={(event) =>
            update("role", event.target.value)
          }
        >
          {ROLE_OPTIONS.map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
        <button
          className="admin-primary-button"
          disabled={
            portal.saving ||
            !form.username.trim() ||
            !form.email.trim() ||
            form.password.length < 12
          }
        >
          Create user
        </button>
      </div>
      <small>
        Use at least 12 characters with uppercase, lowercase,
        numeric, and special characters.
      </small>
    </form>
  );
}

function UserPanel({ portal }) {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("all");
  const [showCreate, setShowCreate] = useState(false);

  const users = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return portal.users.filter((user) => {
      const matchesQuery =
        !normalizedQuery ||
        [
          user.name,
          user.username,
          user.email,
          user.role,
        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase()
          .includes(normalizedQuery);
      const matchesStatus =
        status === "all" || user.status === status;
      return matchesQuery && matchesStatus;
    });
  }, [portal.users, query, status]);

  return (
    <section className="admin-card admin-user-panel">
      <div className="admin-card__title-row">
        <div>
          <h2>User Management</h2>
          <span>
            Manage access, roles, and account status
          </span>
        </div>
        <button
          className="admin-primary-button"
          type="button"
          onClick={() => setShowCreate((current) => !current)}
        >
          <AdminIcon name="plus" size={16} />
          Create User
        </button>
      </div>

      <div className="admin-user-toolbar">
        <label className="admin-search">
          <AdminIcon name="search" size={17} />
          <input
            aria-label="Search users"
            placeholder="Search users by name, email or role..."
            value={query}
            onChange={(event) =>
              setQuery(event.target.value)
            }
          />
        </label>
        <select
          aria-label="Filter user status"
          value={status}
          onChange={(event) =>
            setStatus(event.target.value)
          }
        >
          <option value="all">All Status</option>
          <option value="active">Active</option>
          <option value="disabled">Inactive</option>
        </select>
      </div>

      {showCreate ? (
        <CreateUserForm
          portal={portal}
          onClose={() => setShowCreate(false)}
        />
      ) : null}

      <div className="admin-table-scroll">
        <table className="admin-user-table">
          <thead>
            <tr>
              <th>User</th>
              <th>Role</th>
              <th>Department</th>
              <th>Status</th>
              <th>Last login</th>
              <th>MFA</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user, index) => {
              const isCurrentUser =
                user.id === portal.currentUser?.id;
              return (
                <tr key={user.id}>
                  <td>
                    <div className="admin-user-identity">
                      <UserAvatar
                        user={user}
                        index={index}
                      />
                      <div>
                        <strong>{user.name}</strong>
                        <span>{user.email}</span>
                      </div>
                    </div>
                  </td>
                  <td>
                    <select
                      className={`admin-role-select admin-role-select--${user.role}`}
                      aria-label={`Role for ${user.name}`}
                      value={user.role}
                      disabled={
                        portal.saving || isCurrentUser
                      }
                      onChange={(event) =>
                        portal
                          .updateUser(user.id, {
                            role: event.target.value,
                          })
                          .catch(() => undefined)
                      }
                    >
                      {ROLE_OPTIONS.map(
                        ([value, label]) => (
                          <option
                            key={value}
                            value={value}
                          >
                            {label}
                          </option>
                        ),
                      )}
                    </select>
                  </td>
                  <td>
                    {user.department || "Not tracked"}
                  </td>
                  <td>
                    <span
                      className={`admin-status admin-status--${user.status}`}
                    >
                      {readable(user.status)}
                    </span>
                  </td>
                  <td>
                    {user.lastLogin
                      ? new Date(
                          user.lastLogin,
                        ).toLocaleString()
                      : "Not tracked"}
                  </td>
                  <td>
                    <span
                      className={
                        user.mfaEnabled
                          ? "admin-mfa admin-mfa--on"
                          : "admin-mfa"
                      }
                      title={
                        user.mfaEnabled == null
                          ? "MFA data is not tracked"
                          : undefined
                      }
                    >
                      {user.mfaEnabled == null
                        ? "-"
                        : user.mfaEnabled
                          ? "Yes"
                          : "No"}
                    </span>
                  </td>
                  <td>
                    <button
                      className="admin-text-action"
                      type="button"
                      disabled={
                        portal.saving || isCurrentUser
                      }
                      onClick={() =>
                        portal
                          .updateUser(user.id, {
                            is_active:
                              user.status === "disabled",
                          })
                          .catch(() => undefined)
                      }
                    >
                      {user.status === "disabled"
                        ? "Enable"
                        : "Disable"}
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <footer className="admin-table-footer">
        <span>
          Showing {users.length ? 1 : 0} to {users.length} of{" "}
          {portal.users.length} users
        </span>
        <div className="admin-pagination" aria-label="Pagination">
          <button type="button" disabled>
            Previous
          </button>
          <button type="button" className="active">
            1
          </button>
          <button type="button" disabled>
            Next
          </button>
        </div>
      </footer>
    </section>
  );
}

function RoleMatrix({ portal, title = "Role & Permission Overview" }) {
  return (
    <section className="admin-card admin-role-panel">
      <div className="admin-card__title-row">
        <div>
          <h2>{title}</h2>
          <span>
            Permissions are enforced by backend role policy
          </span>
        </div>
        <span className="admin-readonly-badge">
          Read only
        </span>
      </div>
      <div className="admin-table-scroll">
        <table className="admin-permission-table">
          <thead>
            <tr>
              <th>Role</th>
              <th>Users</th>
              {portal.permissions.map((permission) => (
                <th key={permission.id}>
                  {permission.display_name ??
                    permission.code}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {portal.permissionMatrix.map((role) => {
              const matchingRole = portal.roles.find(
                (item) => item.id === role.id,
              );
              const roleCode =
                matchingRole?.name ?? matchingRole?.id;
              const userCount = portal.users.filter(
                (user) => user.role === roleCode,
              ).length;

              return (
                <tr key={role.id}>
                  <td>
                    <strong>{role.name}</strong>
                  </td>
                  <td>{userCount}</td>
                  {portal.permissions.map((permission) => {
                    const code =
                      permission.code ?? permission.name;
                    const allowed = Boolean(
                      role.permissions[code],
                    );
                    return (
                      <td key={code}>
                        <span
                          className={
                            allowed
                              ? "admin-permission admin-permission--yes"
                              : "admin-permission admin-permission--no"
                          }
                          aria-label={`${role.name}: ${code}`}
                        >
                          {allowed ? "Yes" : "No"}
                        </span>
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function SessionsPanel({
  standalone = false,
  onOpen,
}) {
  return (
    <section
      className={`admin-card admin-side-card${
        standalone ? " admin-side-card--standalone" : ""
      }`}
    >
      <div className="admin-card__title-row">
        <div>
          <h2>Active Sessions</h2>
          <span>Live authentication activity</span>
        </div>
        {!standalone ? (
          <button
            className="admin-link-button"
            type="button"
            onClick={onOpen}
          >
            View All
          </button>
        ) : null}
      </div>
      <div className="admin-empty-state">
        <span className="admin-empty-state__icon">
          <AdminIcon name="monitor" size={22} />
        </span>
        <strong>Session telemetry is not connected</strong>
        <p>
          The current backend cannot list or terminate
          individual user sessions.
        </p>
      </div>
      <footer className="admin-card__footer">
        Backend endpoint required
      </footer>
    </section>
  );
}

function AuditPanel({
  portal,
  preview = false,
  onOpen,
}) {
  const events = preview
    ? portal.audit.slice(0, 5)
    : portal.audit;

  return (
    <section
      className={`admin-card admin-audit-panel${
        preview ? " admin-side-card" : ""
      }`}
    >
      <div className="admin-card__title-row">
        <div>
          <h2>
            {preview
              ? "Recent Audit Log"
              : "Administrative Audit Log"}
          </h2>
          <span>Immutable security events</span>
        </div>
        {preview ? (
          <button
            className="admin-link-button"
            type="button"
            onClick={onOpen}
          >
            View All
          </button>
        ) : null}
      </div>
      <div className="admin-table-scroll">
        <table
          className={
            preview
              ? "admin-audit-table admin-audit-table--preview"
              : "admin-audit-table"
          }
        >
          <thead>
            <tr>
              <th>Time</th>
              <th>Admin</th>
              <th>Action</th>
              {!preview ? (
                <>
                  <th>Resource</th>
                  <th>Resource ID</th>
                  <th>IP</th>
                  <th>Details</th>
                </>
              ) : (
                <th>Target</th>
              )}
            </tr>
          </thead>
          <tbody>
            {events.map((event) => (
              <tr key={event.id}>
                <td>
                  {event.timestamp
                    ? new Date(
                        event.timestamp,
                      ).toLocaleString()
                    : "-"}
                </td>
                <td>
                  <strong>{event.actor}</strong>
                </td>
                <td>{event.action}</td>
                {!preview ? (
                  <>
                    <td>{event.resource}</td>
                    <td>{event.resourceId}</td>
                    <td>{event.ipAddress}</td>
                    <td className="admin-details">
                      {event.details}
                    </td>
                  </>
                ) : (
                  <td>{event.resourceId}</td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {!events.length ? (
        <div className="admin-empty-state admin-empty-state--small">
          No administrative events recorded.
        </div>
      ) : null}
      {preview ? (
        <footer className="admin-card__footer">
          <button
            className="admin-link-button"
            type="button"
            onClick={onOpen}
          >
            View Full Audit Log
            <AdminIcon name="arrow" size={14} />
          </button>
        </footer>
      ) : null}
    </section>
  );
}

function KpiCards({ portal }) {
  const cards = [
    {
      label: "Total Users",
      value: portal.statistics.users,
      note: `${portal.statistics.activeUsers} active`,
      icon: "users",
      tone: "blue",
    },
    {
      label: "Active Sessions",
      value: portal.capabilities.sessions
        ? portal.statistics.activeSessions
        : "-",
      note: portal.capabilities.sessions
        ? "Live now"
        : "Backend required",
      icon: "shield",
      tone: "purple",
    },
    {
      label: "API Keys",
      value: portal.capabilities.apiKeys
        ? portal.statistics.activeApiKeys
        : "-",
      note: portal.capabilities.apiKeys
        ? "Active credentials"
        : "Backend required",
      icon: "key",
      tone: "green",
    },
    {
      label: "Roles",
      value: portal.statistics.roles,
      note: "Backend-defined policy",
      icon: "teams",
      tone: "orange",
    },
    {
      label: "Audit Events",
      value: portal.audit.length,
      note: "Latest 200 events",
      icon: "audit",
      tone: "cyan",
    },
  ];

  return (
    <section className="admin-kpi-grid" aria-label="Statistics">
      {cards.map((card) => (
        <article
          className={`admin-kpi admin-kpi--${card.tone}`}
          key={card.label}
        >
          <span className="admin-kpi__icon">
            <AdminIcon name={card.icon} size={24} />
          </span>
          <div>
            <span>{card.label}</span>
            <strong>{card.value}</strong>
            <small>{card.note}</small>
          </div>
        </article>
      ))}
    </section>
  );
}

function UnavailablePanel({
  title,
  message,
  icon,
}) {
  return (
    <section className="admin-card admin-unavailable-page">
      <span className="admin-empty-state__icon">
        <AdminIcon name={icon} size={26} />
      </span>
      <p>Backend capability required</p>
      <h2>{title}</h2>
      <div role="status">{message}</div>
      <span>
        The interface is reserved for this module and can be
        activated when its API is implemented.
      </span>
    </section>
  );
}

function Dashboard({
  portal,
  setSection,
}) {
  return (
    <>
      <KpiCards portal={portal} />
      <div className="admin-dashboard-grid">
        <div className="admin-dashboard-main">
          <UserPanel portal={portal} />
          <RoleMatrix portal={portal} />
        </div>
        <aside className="admin-dashboard-side">
          <SessionsPanel
            onOpen={() => setSection("sessions")}
          />
          <AuditPanel
            portal={portal}
            preview
            onOpen={() => setSection("audit")}
          />
        </aside>
      </div>
    </>
  );
}

function sectionUnavailable(section) {
  const details = {
    teams: [
      "Team Management",
      "Team records and membership endpoints are not present in the current backend.",
      "teams",
    ],
    api_keys: [
      "API Key Management",
      "API-key storage, generation, rotation, and revocation endpoints have not been implemented.",
      "key",
    ],
    settings: [
      "Security Settings",
      "MFA policy, password policy, lockout, and retention settings are deployment configuration today.",
      "lock",
    ],
    system: [
      "System Settings",
      "Branding, currency, notifications, model selection, and feature flags do not have persistence endpoints.",
      "settings",
    ],
    organization: [
      "Organization Profile",
      "Organization profile and logo storage endpoints have not been implemented.",
      "building",
    ],
  };
  return details[section];
}

export default function AdminPortalPage() {
  const portal = useAdminPortal();
  const [section, setSection] = useState("overview");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    portal.loadPortal().catch(() => undefined);
  }, [portal.loadPortal]);

  const currentUser = portal.currentUser ?? {};
  const currentName =
    currentUser.full_name ??
    currentUser.username ??
    "Admin User";
  const unavailable = sectionUnavailable(section);

  function selectSection(value) {
    setSection(value);
    setSidebarOpen(false);
  }

  return (
    <div className="admin-shell">
      {sidebarOpen ? (
        <button
          aria-label="Close navigation"
          className="admin-sidebar-backdrop"
          type="button"
          onClick={() => setSidebarOpen(false)}
        />
      ) : null}

      <aside
        className={`admin-sidebar${
          sidebarOpen ? " admin-sidebar--open" : ""
        }`}
      >
        <div className="admin-brand">
          <span className="admin-brand__mark">
            <AdminIcon name="shield" size={27} />
          </span>
          <strong>
            JUSTCORP
            <span>SENTINEL AI</span>
          </strong>
        </div>

        <div className="admin-sidebar__body">
          <p className="admin-sidebar__label">
            Administration
          </p>
          <nav aria-label="Administration navigation">
            {NAV_ITEMS.map(
              ([value, icon, label, ariaLabel]) => (
                <button
                  aria-label={ariaLabel}
                  className={
                    section === value
                      ? "admin-sidebar__item active"
                      : "admin-sidebar__item"
                  }
                  type="button"
                  key={value}
                  onClick={() => selectSection(value)}
                >
                  <AdminIcon name={icon} size={18} />
                  <span>{label}</span>
                </button>
              ),
            )}
          </nav>
        </div>

        <footer className="admin-sidebar__footer">
          <span>
            <i />
            All Systems Operational
          </span>
          <small>Version 1.0.0</small>
        </footer>
      </aside>

      <section className="admin-workspace">
        <header className="admin-topbar">
          <div className="admin-topbar__title">
            <button
              aria-label="Open navigation"
              className="admin-menu-button"
              type="button"
              onClick={() =>
                setSidebarOpen((current) => !current)
              }
            >
              <AdminIcon name="menu" size={22} />
            </button>
            <h1>Enterprise Administration Portal</h1>
          </div>
          <div className="admin-topbar__actions">
            <button
              className="admin-icon-button"
              type="button"
              aria-label="Administrative notifications"
            >
              <AdminIcon name="bell" size={20} />
              {portal.audit.length ? (
                <span>
                  {Math.min(portal.audit.length, 99)}
                </span>
              ) : null}
            </button>
            <button
              className="admin-icon-button"
              type="button"
              aria-label="Administration help"
            >
              <AdminIcon name="help" size={20} />
            </button>
            <div className="admin-profile">
              <span className="admin-profile__avatar">
                {initials(currentName)}
              </span>
              <div>
                <strong>{currentName}</strong>
                <span>Super Administrator</span>
              </div>
              <span aria-hidden="true">v</span>
            </div>
          </div>
        </header>

        <main className="admin-content">
          {portal.error ? (
            <div className="admin-error" role="alert">
              {portal.error.message}
            </div>
          ) : null}

          {portal.loading ? (
            <section className="admin-card admin-loading">
              Loading administration portal...
            </section>
          ) : (
            <>
              {section === "overview" ? (
                <Dashboard
                  portal={portal}
                  setSection={selectSection}
                />
              ) : null}
              {section === "users" ? (
                <UserPanel portal={portal} />
              ) : null}
              {section === "roles" ||
              section === "permissions" ? (
                <RoleMatrix
                  portal={portal}
                  title={
                    section === "permissions"
                      ? "Permission Matrix"
                      : "Role Management"
                  }
                />
              ) : null}
              {section === "sessions" ? (
                <SessionsPanel standalone />
              ) : null}
              {section === "audit" ? (
                <AuditPanel portal={portal} />
              ) : null}
              {unavailable ? (
                <UnavailablePanel
                  title={unavailable[0]}
                  message={unavailable[1]}
                  icon={unavailable[2]}
                />
              ) : null}
            </>
          )}
        </main>
      </section>
    </div>
  );
}
