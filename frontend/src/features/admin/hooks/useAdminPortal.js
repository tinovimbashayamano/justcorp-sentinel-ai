import {
  useCallback,
  useMemo,
  useState,
} from "react";

import {
  ADMIN_CAPABILITIES,
  createAdminUser,
  getAdminAuditLog,
  getAdminOverview,
  getAdminPermissions,
  getAdminRoles,
  getAdminUsers,
  updateAdminUser,
} from "../../../api/adminPortal";
import {
  buildPermissionMatrix,
  calculateAdminStatistics,
  normalizeUsers,
  sortAuditEvents,
} from "../domain/admin";

const INITIAL_STATE = {
  overview: {},
  currentUser: null,
  users: [],
  roles: [],
  permissions: [],
  teams: [],
  sessions: [],
  apiKeys: [],
  settings: {},
  audit: [],
  capabilities: ADMIN_CAPABILITIES,
};

export function useAdminPortal() {
  const [state, setState] = useState(INITIAL_STATE);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const loadPortal = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [
        overview,
        users,
        roles,
        permissions,
        audit,
      ] = await Promise.all([
        getAdminOverview(),
        getAdminUsers(),
        getAdminRoles(),
        getAdminPermissions(),
        getAdminAuditLog(),
      ]);
      const next = {
        ...INITIAL_STATE,
        overview,
        currentUser: overview.currentUser ?? null,
        capabilities:
          overview.capabilities ?? ADMIN_CAPABILITIES,
        users: users ?? [],
        roles: roles ?? [],
        permissions: permissions ?? [],
        audit: audit ?? [],
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

  const createUser = useCallback(
    (payload) =>
      runSave(async () => {
        const created = await createAdminUser(payload);
        setState((current) => ({
          ...current,
          users: [...current.users, created],
        }));
        return created;
      }),
    [runSave],
  );

  const updateUser = useCallback(
    (id, payload) =>
      runSave(async () => {
        const updated = await updateAdminUser(
          id,
          payload,
        );
        setState((current) => ({
          ...current,
          users: current.users.map((user) =>
            user.id === id
              ? { ...user, ...updated }
              : user,
          ),
        }));
        return updated;
      }),
    [runSave],
  );

  const users = useMemo(
    () => normalizeUsers(state.users),
    [state.users],
  );
  const audit = useMemo(
    () => sortAuditEvents(state.audit),
    [state.audit],
  );
  const permissionMatrix = useMemo(
    () =>
      buildPermissionMatrix(
        state.roles,
        state.permissions,
      ),
    [state.roles, state.permissions],
  );
  const statistics = useMemo(
    () =>
      calculateAdminStatistics({
        users,
        roles: state.roles,
        sessions: state.sessions,
        apiKeys: state.apiKeys,
      }),
    [
      users,
      state.roles,
      state.sessions,
      state.apiKeys,
    ],
  );

  return {
    ...state,
    users,
    audit,
    permissionMatrix,
    statistics,
    loading,
    saving,
    error,
    loadPortal,
    createUser,
    updateUser,
  };
}
