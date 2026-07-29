import { useCallback, useEffect, useMemo, useState } from "react";
import { preferencesApi } from "../../../api/preferencesApi";
import {
  activeSessions,
  filterActivity,
  normalizeNotificationSettings,
  normalizeSettings,
  sortNotifications,
  unreadCount,
} from "../domain/preferences";

const INITIAL_STATE = {
  profile: {},
  settings: {},
  notifications: [],
  notificationSettings: {},
  sessions: [],
  devices: [],
  activity: [],
  favorites: [],
  savedFilters: [],
};

function applyAppearance(settings) {
  const root = document.documentElement;
  root.dataset.theme = settings.theme || "system";
  root.dataset.accent = settings.accent_color || "blue";
  root.dataset.density = settings.density || "comfortable";
}

export function usePreferences() {
  const [state, setState] = useState(INITIAL_STATE);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [securityMessage, setSecurityMessage] = useState("");

  useEffect(() => {
    applyAppearance(normalizeSettings(state.settings));
  }, [state.settings]);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [
        profile,
        settings,
        notificationResponse,
        sessions,
        devices,
        activity,
        favorites,
        savedFilters,
      ] = await Promise.all([
        preferencesApi.profile(),
        preferencesApi.settings(),
        preferencesApi.notifications(),
        preferencesApi.sessions(),
        preferencesApi.devices(),
        preferencesApi.activity(),
        preferencesApi.favorites(),
        preferencesApi.savedFilters(),
      ]);

      const next = {
        profile: profile ?? {},
        settings: settings ?? {},
        notifications: notificationResponse?.items ?? [],
        notificationSettings: notificationResponse?.settings ?? {},
        sessions: sessions ?? [],
        devices: devices ?? [],
        activity: activity ?? [],
        favorites: favorites ?? [],
        savedFilters: savedFilters ?? [],
      };
      setState(next);
      return next;
    } catch (caught) {
      setError(caught);
      throw caught;
    } finally {
      setLoading(false);
    }
  }, []);

  const runSave = useCallback(async (operation) => {
    setSaving(true);
    setError(null);
    try {
      return await operation();
    } catch (caught) {
      setError(caught);
      throw caught;
    } finally {
      setSaving(false);
    }
  }, []);

  const saveSettings = useCallback(
    (payload) =>
      runSave(async () => {
        const updated = await preferencesApi.updateSettings(payload);
        setState((current) => ({ ...current, settings: updated }));
        return updated;
      }),
    [runSave],
  );

  const saveNotifications = useCallback(
    (payload) =>
      runSave(async () => {
        const updated = await preferencesApi.updateNotifications(payload);
        setState((current) => ({
          ...current,
          notificationSettings: updated,
        }));
        return updated;
      }),
    [runSave],
  );

  const updateNotification = useCallback(
    async (id, action) => {
      const updated = await action(id);
      setState((current) => ({
        ...current,
        notifications: current.notifications.map((item) =>
          String(item.id) === String(id) ? updated : item,
        ),
      }));
      return updated;
    },
    [],
  );

  const markNotificationRead = useCallback(
    (id) => updateNotification(id, preferencesApi.markNotificationRead),
    [updateNotification],
  );

  const markNotificationUnread = useCallback(
    (id) => updateNotification(id, preferencesApi.markNotificationUnread),
    [updateNotification],
  );

  const archiveNotification = useCallback(
    (id) => updateNotification(id, preferencesApi.archiveNotification),
    [updateNotification],
  );

  const markAllNotificationsRead = useCallback(
    () =>
      runSave(async () => {
        const result = await preferencesApi.markAllNotificationsRead();
        setState((current) => ({
          ...current,
          notifications: current.notifications.map((item) => ({
            ...item,
            read: true,
            is_read: true,
          })),
        }));
        return result;
      }),
    [runSave],
  );

  const revokeSession = useCallback(async (id) => {
    await preferencesApi.revokeSession(id);
    setState((current) => ({
      ...current,
      sessions: current.sessions.map((session) =>
        String(session.id) === String(id)
          ? { ...session, revoked: true }
          : session,
      ),
    }));
  }, []);

  const saveFavorites = useCallback(
    (items) =>
      runSave(async () => {
        const updated = await preferencesApi.updateFavorites(items);
        setState((current) => ({ ...current, favorites: updated }));
        return updated;
      }),
    [runSave],
  );

  const saveSavedFilters = useCallback(
    (items) =>
      runSave(async () => {
        const updated = await preferencesApi.updateSavedFilters(items);
        setState((current) => ({ ...current, savedFilters: updated }));
        return updated;
      }),
    [runSave],
  );

  const changePassword = useCallback(
    (payload) =>
      runSave(async () => {
        const result = await preferencesApi.changePassword(payload);
        setSecurityMessage(result.message || "Password changed.");
        return result;
      }),
    [runSave],
  );

  const logoutAll = useCallback(
    () =>
      runSave(async () => {
        const result = await preferencesApi.logoutAll();
        setSecurityMessage(result.message || "All sessions signed out.");
        return result;
      }),
    [runSave],
  );

  return {
    ...state,
    loading,
    saving,
    error,
    securityMessage,
    load,
    saveSettings,
    saveNotifications,
    markNotificationRead,
    markNotificationUnread,
    archiveNotification,
    markAllNotificationsRead,
    revokeSession,
    saveFavorites,
    saveSavedFilters,
    changePassword,
    logoutAll,
    settings: useMemo(
      () => normalizeSettings(state.settings),
      [state.settings],
    ),
    notificationSettings: useMemo(
      () => normalizeNotificationSettings(state.notificationSettings),
      [state.notificationSettings],
    ),
    notifications: useMemo(
      () => sortNotifications(state.notifications).filter(
        (item) => !item.archived,
      ),
      [state.notifications],
    ),
    unread: useMemo(
      () => unreadCount(state.notifications),
      [state.notifications],
    ),
    sessions: useMemo(
      () => activeSessions(state.sessions),
      [state.sessions],
    ),
    searchActivity: (search) => filterActivity(state.activity, search),
  };
}
