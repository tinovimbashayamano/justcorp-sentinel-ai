import {
  useCallback,
  useMemo,
  useState,
} from "react";

import {
  addInvestigationNote,
  addInvestigationTask,
  assignInvestigation,
  downloadInvestigationEvidence,
  getInvestigationWorkspace,
  updateInvestigationStatus,
  updateInvestigationTask,
} from "../../../api/investigationWorkspace";
import {
  buildSummary,
  buildTimeline,
  calculateTaskProgress,
  normalizeAudit,
  sortNewest,
} from "../domain/investigationWorkspace";

const INITIAL_WORKSPACE = {
  investigation: {},
  notes: [],
  evidence: [],
  tasks: [],
  analysts: [],
  timeline: [],
  activity_history: [],
  audit_log: [],
  current_user: null,
};

function readCurrentUserId(currentUser) {
  try {
    const user =
      currentUser ||
      JSON.parse(
        window.localStorage.getItem("user") || "null",
      );
    if (
      String(user?.role || "").toLowerCase() !==
      "fraud_analyst"
    ) {
      return null;
    }
    return user?.id ?? user?.user_id ?? null;
  } catch {
    return null;
  }
}

export function useInvestigationWorkspace(caseId) {
  const [workspace, setWorkspace] = useState(
    INITIAL_WORKSPACE,
  );
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

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

  const loadWorkspace = useCallback(async () => {
    if (!caseId) return null;
    setLoading(true);
    setError(null);
    try {
      const data = await getInvestigationWorkspace(caseId);
      const normalized = {
        ...INITIAL_WORKSPACE,
        ...data,
        investigation:
          data.investigation ?? data.case ?? data,
      };
      setWorkspace(normalized);
      return normalized;
    } catch (caught) {
      setError(caught);
      throw caught;
    } finally {
      setLoading(false);
    }
  }, [caseId]);

  const changeStatus = useCallback(
    (status) =>
      runSave(async () => {
        const updated = await updateInvestigationStatus(
          caseId,
          status,
        );
        setWorkspace((current) => ({
          ...current,
          investigation: {
            ...current.investigation,
            ...updated,
            status: updated.status ?? status,
            case_status:
              updated.case_status ?? status,
          },
        }));
        return updated;
      }),
    [caseId, runSave],
  );

  const changeAssignment = useCallback(
    (analystId) =>
      runSave(async () => {
        const updated = await assignInvestigation(
          caseId,
          analystId,
        );
        setWorkspace((current) => ({
          ...current,
          investigation: {
            ...current.investigation,
            ...updated,
            status:
              updated.status ??
              updated.case_status ??
              current.investigation.status,
            assigned_analyst_name:
              updated.assigned_to_username ||
              updated.assigned_to,
            assigned_analyst_id:
              updated.assigned_to_user_id || "",
          },
        }));
        return updated;
      }),
    [caseId, runSave],
  );

  const createNote = useCallback(
    async (content) => {
      const clean = String(content || "").trim();
      if (!clean) return null;

      return runSave(async () => {
        const note = await addInvestigationNote(
          caseId,
          clean,
        );
        setWorkspace((current) => ({
          ...current,
          notes: [note, ...current.notes],
        }));
        return note;
      });
    },
    [caseId, runSave],
  );

  const createTask = useCallback(
    async (title) => {
      const clean = String(title || "").trim();
      if (clean.length < 3) return null;

      return runSave(async () => {
        const task = await addInvestigationTask(
          caseId,
          clean,
          readCurrentUserId(workspace.current_user),
        );
        setWorkspace((current) => ({
          ...current,
          tasks: [...current.tasks, task],
        }));
        return task;
      });
    },
    [caseId, runSave, workspace.current_user],
  );

  const toggleTask = useCallback(
    async (task) => {
      if (task.completed) return task;

      return runSave(async () => {
        const updated = await updateInvestigationTask(
          caseId,
          task.id,
          {
            completed: true,
            currentStatus: task.status,
          },
        );
        setWorkspace((current) => ({
          ...current,
          tasks: current.tasks.map((item) =>
            item.id === task.id
              ? { ...item, ...updated }
              : item,
          ),
        }));
        return updated;
      });
    },
    [caseId, runSave],
  );

  const downloadEvidence = useCallback(
    (evidence) =>
      downloadInvestigationEvidence(caseId, evidence),
    [caseId],
  );

  const summary = useMemo(
    () => buildSummary(workspace.investigation),
    [workspace.investigation],
  );
  const timeline = useMemo(
    () => buildTimeline(workspace),
    [workspace],
  );
  const notes = useMemo(
    () => sortNewest(workspace.notes),
    [workspace.notes],
  );
  const evidence = useMemo(
    () => sortNewest(workspace.evidence, "uploaded_at"),
    [workspace.evidence],
  );
  const activityHistory = useMemo(
    () =>
      sortNewest(
        workspace.activity_history.length
          ? workspace.activity_history
          : workspace.timeline,
      ),
    [workspace.activity_history, workspace.timeline],
  );
  const taskProgress = useMemo(
    () => calculateTaskProgress(workspace.tasks),
    [workspace.tasks],
  );
  const auditLog = useMemo(
    () => normalizeAudit(workspace.audit_log),
    [workspace.audit_log],
  );

  return {
    workspace,
    summary,
    timeline,
    notes,
    evidence,
    tasks: workspace.tasks,
    analysts: workspace.analysts,
    activityHistory,
    taskProgress,
    auditLog,
    loading,
    saving,
    error,
    loadWorkspace,
    changeStatus,
    changeAssignment,
    createNote,
    createTask,
    toggleTask,
    downloadEvidence,
  };
}
