import { useEffect, useState } from "react";
import { usePreferences } from "../hooks/usePreferences";
import { toggleFavorite } from "../domain/preferences";
import "../styles/preferences.css";

const TABS = [
  "Notifications",
  "Appearance",
  "Workspace",
  "Security",
  "Sessions",
  "Activity",
  "Account",
];

const FAVORITE_REPORTS = [
  ["executive", "Executive reports"],
  ["compliance", "Compliance reports"],
  ["analyst", "Analyst reports"],
  ["fraud-trends", "Fraud trend reports"],
];

export default function PreferencesPage() {
  const preferences = usePreferences();
  const [tab, setTab] = useState("Notifications");
  const [settings, setSettings] = useState(preferences.settings);
  const [notificationSettings, setNotificationSettings] = useState(
    preferences.notificationSettings
  );
  const [activitySearch, setActivitySearch] = useState("");
  const [passwords, setPasswords] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  });

  useEffect(() => {
    preferences.load().catch(() => undefined);
  }, [preferences.load]);

  useEffect(() => {
    setSettings(preferences.settings);
    setNotificationSettings(preferences.notificationSettings);
  }, [preferences.settings, preferences.notificationSettings]);

  return (
    <main className="preferences-page">
      <header className="preferences-header">
        <p>JustCorp Sentinel AI</p>
        <h1>User preferences and notification center</h1>
        <span>
          Personalize your workspace, alerts, appearance, security and sessions.
        </span>
      </header>

      <nav className="preferences-tabs" aria-label="Preference sections">
        {TABS.map((item) => (
          <button
            key={item}
            className={tab === item ? "active" : ""}
            onClick={() => setTab(item)}
          >
            {item}
            {item === "Notifications" && preferences.unread
              ? ` (${preferences.unread})`
              : ""}
          </button>
        ))}
      </nav>

      {preferences.error ? (
        <div className="preferences-error" role="alert">
          {preferences.error.message}
        </div>
      ) : null}

      {preferences.loading ? (
        <section className="preferences-panel">Loading preferences...</section>
      ) : (
        <>
          {tab === "Notifications" && (
            <div className="preferences-grid">
              <section className="preferences-panel">
                <header>
                  <p>Inbox</p>
                  <h2>Notification center</h2>
                  {preferences.unread ? (
                    <button
                      type="button"
                      onClick={() => preferences.markAllNotificationsRead()}
                    >
                      Mark all read
                    </button>
                  ) : null}
                </header>
                <div className="notification-list">
                  {preferences.notifications.length ? (
                    preferences.notifications.map((item) => (
                      <article
                        key={item.id}
                        className={item.read ? "" : "unread"}
                      >
                        <div>
                          <strong>{item.title}</strong>
                          <span>{item.message}</span>
                          <small>{item.timestamp}</small>
                        </div>
                        <div className="notification-actions">
                          <span className={`severity-${item.severity}`}>
                            {item.category}
                          </span>
                          <button
                            type="button"
                            onClick={() =>
                              item.read
                                ? preferences.markNotificationUnread(item.id)
                                : preferences.markNotificationRead(item.id)
                            }
                          >
                            {item.read ? "Mark unread" : "Mark read"}
                          </button>
                          <button
                            type="button"
                            onClick={() =>
                              preferences.archiveNotification(item.id)
                            }
                          >
                            Archive
                          </button>
                        </div>
                      </article>
                    ))
                  ) : (
                    <p className="preferences-empty">
                      No notifications are available.
                    </p>
                  )}
                </div>
              </section>

              <section className="preferences-panel">
                <header>
                  <p>Delivery</p>
                  <h2>Notification settings</h2>
                </header>

                {["email", "sms", "push", "in_app"].map((channel) => (
                  <label className="preference-toggle" key={channel}>
                    <span>{channel.replace("_", " ")}</span>
                    <input
                      type="checkbox"
                      checked={Boolean(notificationSettings[channel])}
                      onChange={(event) =>
                        setNotificationSettings({
                          ...notificationSettings,
                          [channel]: event.target.checked,
                        })
                      }
                    />
                  </label>
                ))}

                <label>
                  Delivery frequency
                  <select
                    value={notificationSettings.frequency}
                    onChange={(event) =>
                      setNotificationSettings({
                        ...notificationSettings,
                        frequency: event.target.value,
                      })
                    }
                  >
                    <option value="immediate">Immediate</option>
                    <option value="hourly">Hourly digest</option>
                    <option value="daily">Daily digest</option>
                    <option value="weekly">Weekly digest</option>
                  </select>
                </label>

                <button
                  onClick={() =>
                    preferences.saveNotifications(notificationSettings)
                  }
                >
                  Save notification settings
                </button>
              </section>
            </div>
          )}

          {tab === "Appearance" && (
            <section className="preferences-panel">
              <header>
                <p>Personalization</p>
                <h2>Appearance settings</h2>
              </header>
              <div className="preferences-form">
                <label>
                  Theme
                  <select
                    value={settings.theme}
                    onChange={(event) =>
                      setSettings({ ...settings, theme: event.target.value })
                    }
                  >
                    <option value="light">Light</option>
                    <option value="dark">Dark</option>
                    <option value="system">System</option>
                  </select>
                </label>

                <label>
                  Accent color
                  <select
                    value={settings.accent_color}
                    onChange={(event) =>
                      setSettings({
                        ...settings,
                        accent_color: event.target.value,
                      })
                    }
                  >
                    <option value="blue">Blue</option>
                    <option value="green">Green</option>
                    <option value="purple">Purple</option>
                    <option value="orange">Orange</option>
                  </select>
                </label>

                <label>
                  Density
                  <select
                    value={settings.density}
                    onChange={(event) =>
                      setSettings({ ...settings, density: event.target.value })
                    }
                  >
                    <option value="compact">Compact</option>
                    <option value="comfortable">Comfortable</option>
                    <option value="spacious">Spacious</option>
                  </select>
                </label>
              </div>
              <button onClick={() => preferences.saveSettings(settings)}>
                Save appearance
              </button>
            </section>
          )}

          {tab === "Workspace" && (
            <section className="preferences-panel">
              <header>
                <p>Workspace</p>
                <h2>Dashboard preferences</h2>
              </header>
              <div className="preferences-form">
                <label>
                  Landing page
                  <select
                    value={settings.landing_page}
                    onChange={(event) =>
                      setSettings({
                        ...settings,
                        landing_page: event.target.value,
                      })
                    }
                  >
                    <option value="/">Home</option>
                    <option value="/fraud/alerts">Fraud alerts</option>
                    <option value="/fraud/cases">Investigation queue</option>
                    <option value="/reports">Reports</option>
                  </select>
                </label>

                <label>
                  Language
                  <select
                    value={settings.language}
                    onChange={(event) =>
                      setSettings({
                        ...settings,
                        language: event.target.value,
                      })
                    }
                  >
                    <option value="en">English</option>
                  </select>
                </label>

                <label>
                  Time zone
                  <select
                    value={settings.timezone}
                    onChange={(event) =>
                      setSettings({
                        ...settings,
                        timezone: event.target.value,
                      })
                    }
                  >
                    <option value="browser">Local browser</option>
                    <option value="organization">Organization default</option>
                    <option value="UTC">UTC</option>
                  </select>
                </label>

                <label>
                  Date format
                  <select
                    value={settings.date_format}
                    onChange={(event) =>
                      setSettings({
                        ...settings,
                        date_format: event.target.value,
                      })
                    }
                  >
                    <option value="DD/MM/YYYY">DD/MM/YYYY</option>
                    <option value="MM/DD/YYYY">MM/DD/YYYY</option>
                    <option value="YYYY-MM-DD">YYYY-MM-DD</option>
                  </select>
                </label>
              </div>
              <button onClick={() => preferences.saveSettings(settings)}>
                Save workspace settings
              </button>

              <div className="preference-subsection">
                <h3>Favorite reports</h3>
                <div className="favorite-report-grid">
                  {FAVORITE_REPORTS.map(([id, label]) => (
                    <label className="preference-toggle" key={id}>
                      <span>{label}</span>
                      <input
                        type="checkbox"
                        checked={preferences.favorites.includes(id)}
                        onChange={() =>
                          preferences.saveFavorites(
                            toggleFavorite(preferences.favorites, id),
                          )
                        }
                      />
                    </label>
                  ))}
                </div>
              </div>

              <div className="preference-subsection">
                <h3>Saved filters</h3>
                {preferences.savedFilters.length ? (
                  <ul>
                    {preferences.savedFilters.map((filter, index) => (
                      <li key={filter.id || filter.name || index}>
                        {filter.name || filter.label || "Saved filter"}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="preferences-empty">
                    Saved investigation, transaction, reporting and alert
                    filters will appear here.
                  </p>
                )}
              </div>
            </section>
          )}

          {tab === "Security" && (
            <section className="preferences-panel">
              <header>
                <p>Account protection</p>
                <h2>Security settings</h2>
              </header>
              <div className="security-actions">
                <form
                  className="password-form"
                  onSubmit={async (event) => {
                    event.preventDefault();
                    if (passwords.new_password !== passwords.confirm_password) {
                      return;
                    }
                    await preferences.changePassword({
                      current_password: passwords.current_password,
                      new_password: passwords.new_password,
                    });
                    setPasswords({
                      current_password: "",
                      new_password: "",
                      confirm_password: "",
                    });
                  }}
                >
                  <h3>Change password</h3>
                  <label>
                    Current password
                    <input
                      type="password"
                      value={passwords.current_password}
                      onChange={(event) =>
                        setPasswords({
                          ...passwords,
                          current_password: event.target.value,
                        })
                      }
                      required
                    />
                  </label>
                  <label>
                    New password
                    <input
                      type="password"
                      minLength="12"
                      value={passwords.new_password}
                      onChange={(event) =>
                        setPasswords({
                          ...passwords,
                          new_password: event.target.value,
                        })
                      }
                      required
                    />
                  </label>
                  <label>
                    Confirm new password
                    <input
                      type="password"
                      minLength="12"
                      value={passwords.confirm_password}
                      onChange={(event) =>
                        setPasswords({
                          ...passwords,
                          confirm_password: event.target.value,
                        })
                      }
                      required
                    />
                  </label>
                  {passwords.confirm_password &&
                  passwords.new_password !== passwords.confirm_password ? (
                    <span className="preference-validation">
                      Password confirmation does not match.
                    </span>
                  ) : null}
                  <button type="submit">Change password</button>
                </form>

                <article>
                  <div>
                    <strong>Multi-factor authentication</strong>
                    <span>
                      MFA enrollment requires a future backend endpoint.
                    </span>
                  </div>
                  <button type="button" disabled>
                    Not available
                  </button>
                </article>
                <article>
                  <div>
                    <strong>Recovery codes</strong>
                    <span>
                      Recovery codes become available after MFA support.
                    </span>
                  </div>
                  <button type="button" disabled>
                    Not available
                  </button>
                </article>
                <article>
                  <div>
                    <strong>Sign out all devices</strong>
                    <span>Revoke every refresh session for this account.</span>
                  </div>
                  <button
                    type="button"
                    onClick={async () => {
                      await preferences.logoutAll();
                      window.location.assign("/");
                    }}
                  >
                    Sign out all
                  </button>
                </article>
              </div>
              {preferences.securityMessage ? (
                <div className="preferences-success" role="status">
                  {preferences.securityMessage}
                </div>
              ) : null}
            </section>
          )}

          {tab === "Sessions" && (
            <section className="preferences-panel">
              <header>
                <p>Access</p>
                <h2>Active sessions</h2>
              </header>
              <div className="preferences-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Device</th>
                      <th>Browser</th>
                      <th>IP address</th>
                      <th>Country</th>
                      <th>Last activity</th>
                      <th>Current</th>
                      <th />
                    </tr>
                  </thead>
                  <tbody>
                    {preferences.sessions.length ? (
                      preferences.sessions.map((session) => (
                        <tr key={session.id}>
                          <td>{session.device}</td>
                          <td>{session.browser}</td>
                          <td>{session.ip_address}</td>
                          <td>{session.country}</td>
                          <td>{session.last_activity}</td>
                          <td>{session.current ? "Yes" : "No"}</td>
                          <td>
                            {!session.current && (
                              <button
                                onClick={() =>
                                  preferences.revokeSession(session.id)
                                }
                              >
                                Revoke
                              </button>
                            )}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan="7">No active sessions reported.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
              <div className="preference-subsection">
                <h3>Connected devices</h3>
                <div className="device-list">
                  {preferences.devices.length ? (
                    preferences.devices.map((device) => (
                      <article key={device.id}>
                        <strong>{device.device}</strong>
                        <span>{device.browser}</span>
                        <small>{device.last_seen}</small>
                      </article>
                    ))
                  ) : (
                    <p className="preferences-empty">
                      No connected devices reported.
                    </p>
                  )}
                </div>
              </div>
            </section>
          )}

          {tab === "Activity" && (
            <section className="preferences-panel">
              <header>
                <p>Audit</p>
                <h2>Activity history</h2>
              </header>

              <input
                className="activity-search"
                placeholder="Search activity"
                value={activitySearch}
                onChange={(event) => setActivitySearch(event.target.value)}
              />

              <div className="activity-list">
                {preferences.searchActivity(activitySearch).length ? (
                  preferences.searchActivity(activitySearch).map((item) => (
                    <article key={item.id}>
                      <div>
                        <strong>{item.action}</strong>
                        <span>{item.description}</span>
                      </div>
                      <small>{item.timestamp}</small>
                    </article>
                  ))
                ) : (
                  <p className="preferences-empty">
                    No accessible activity records match this search.
                  </p>
                )}
              </div>
            </section>
          )}

          {tab === "Account" && (
            <section className="preferences-panel">
              <header>
                <p>Profile</p>
                <h2>Account profile</h2>
              </header>
              <dl className="profile-details">
                <div>
                  <dt>Name</dt>
                  <dd>{preferences.profile.full_name || "Not provided"}</dd>
                </div>
                <div>
                  <dt>Username</dt>
                  <dd>{preferences.profile.username || "Not reported"}</dd>
                </div>
                <div>
                  <dt>Email</dt>
                  <dd>{preferences.profile.email || "Not reported"}</dd>
                </div>
                <div>
                  <dt>Role</dt>
                  <dd>{preferences.profile.role || "Not reported"}</dd>
                </div>
              </dl>
            </section>
          )}
        </>
      )}

      {preferences.saving ? (
        <div className="preferences-saving">Saving changes...</div>
      ) : null}
    </main>
  );
}
