import {
  useEffect,
  useState,
} from "react";
import {
  useLocation,
  useNavigate,
  useParams,
} from "react-router";

import {
  INVESTIGATION_STATUSES,
  canTransitionStatus,
} from "../domain/investigationWorkspace";
import { useInvestigationWorkspace } from "../hooks/useInvestigationWorkspace";
import "../styles/investigation-workspace.css";

function readable(value) {
  return String(value ?? "—").replaceAll("_", " ");
}

function fileSize(bytes) {
  const value = Number(bytes || 0);
  if (!value) return "Unknown size";
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) {
    return `${(value / 1024).toFixed(1)} KB`;
  }
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

export default function InvestigationWorkspacePage() {
  const { caseId: routeCaseId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const caseId = routeCaseId ?? location.state?.caseId;
  const investigationWorkspace =
    useInvestigationWorkspace(caseId);
  const [note, setNote] = useState("");
  const [task, setTask] = useState("");

  useEffect(() => {
    investigationWorkspace
      .loadWorkspace()
      .catch(() => undefined);
  }, [investigationWorkspace.loadWorkspace]);

  if (!caseId) {
    return (
      <main className="iw-page">
        <div className="iw-error">
          No investigation case selected.
        </div>
      </main>
    );
  }

  const {
    workspace,
    summary,
  } = investigationWorkspace;
  const scoreId =
    workspace.investigation.fraud_score_record_id;
  const transactionId =
    workspace.investigation.transaction_id;
  const summaryItems = [
    ["Status", readable(summary.status)],
    ["Priority", readable(summary.priority)],
    ["Risk", readable(summary.risk)],
    [
      "Fraud probability",
      new Intl.NumberFormat("en-US", {
        style: "percent",
        maximumFractionDigits: 1,
      }).format(summary.probability),
    ],
    [
      "Amount",
      new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: summary.currency,
      }).format(summary.amount),
    ],
    ["Merchant", summary.merchant],
    ["Customer", summary.customerId],
    ["Analyst", summary.assignedAnalyst],
    ["Due date", summary.dueDate || "—"],
    ["Decision", readable(summary.decision)],
    ["Model", summary.modelVersion],
    ["Device", summary.deviceType],
    ["Location", summary.location],
  ];

  function openTransaction() {
    navigate(`/fraud/transactions?scoreId=${scoreId}`, {
      state: {
        fraudScoreRecordId: scoreId,
        transactionId,
        caseId,
      },
    });
  }

  function openExplainability() {
    navigate(`/fraud/explainability?scoreId=${scoreId}`, {
      state: {
        fraudScoreRecordId: scoreId,
        transactionId,
        caseId,
      },
    });
  }

  return (
    <main className="iw-page">
      <header className="iw-header">
        <div>
          <p>Investigation workspace</p>
          <h1>Case {summary.caseId}</h1>
          <span>Transaction {summary.transactionId}</span>
        </div>
        <div className="iw-actions">
          <button
            type="button"
            onClick={openTransaction}
            disabled={!scoreId}
          >
            Open transaction
          </button>
          <button
            type="button"
            onClick={openExplainability}
            disabled={!scoreId}
          >
            Open explainability
          </button>
        </div>
      </header>

      {investigationWorkspace.error ? (
        <div className="iw-error" role="alert">
          {investigationWorkspace.error.message}
        </div>
      ) : null}

      {investigationWorkspace.loading ? (
        <div className="iw-panel">
          Loading investigation workspace…
        </div>
      ) : (
        <>
          <section className="iw-panel">
            <div className="iw-panel-header">
              <div>
                <p>Case summary</p>
                <h2>Investigation overview</h2>
              </div>
            </div>
            <div className="iw-summary">
              {summaryItems.map(([label, value]) => (
                <article key={label}>
                  <span>{label}</span>
                  <strong>{String(value)}</strong>
                </article>
              ))}
            </div>
          </section>

          <div className="iw-grid">
            <section className="iw-panel">
              <div className="iw-panel-header">
                <div>
                  <p>Workflow</p>
                  <h2>Status</h2>
                </div>
              </div>
              <select
                value={summary.status}
                disabled={investigationWorkspace.saving}
                onChange={(event) =>
                  investigationWorkspace.changeStatus(
                    event.target.value,
                  )
                }
              >
                {INVESTIGATION_STATUSES.map((status) => (
                  <option
                    key={status}
                    value={status}
                    disabled={
                      !canTransitionStatus(
                        summary.status,
                        status,
                      )
                    }
                  >
                    {readable(status)}
                  </option>
                ))}
              </select>
            </section>

            <section className="iw-panel">
              <div className="iw-panel-header">
                <div>
                  <p>Ownership</p>
                  <h2>Assignment</h2>
                </div>
              </div>
              <select
                value={summary.assignedAnalystId}
                disabled={
                  investigationWorkspace.saving ||
                  !investigationWorkspace.analysts.length
                }
                onChange={(event) =>
                  investigationWorkspace.changeAssignment(
                    event.target.value,
                  )
                }
              >
                <option value="">Unassigned</option>
                {investigationWorkspace.analysts.map(
                  (analyst) => (
                    <option
                      key={analyst.id}
                      value={analyst.id}
                    >
                      {analyst.full_name ||
                        analyst.name ||
                        analyst.email}
                    </option>
                  ),
                )}
              </select>
              {!investigationWorkspace.analysts.length ? (
                <p className="iw-muted">
                  Analyst assignment is available to
                  administrators.
                </p>
              ) : null}
            </section>
          </div>

          <div className="iw-grid">
            <section className="iw-panel">
              <div className="iw-panel-header">
                <div>
                  <p>Chronology</p>
                  <h2>Investigation timeline</h2>
                </div>
              </div>
              {investigationWorkspace.timeline.length ? (
                <ol className="iw-timeline">
                  {investigationWorkspace.timeline.map(
                    (event) => (
                      <li key={event.id}>
                        <strong>{event.title}</strong>
                        <time>
                          {new Date(
                            event.created_at,
                          ).toLocaleString()}
                        </time>
                        <p>{event.description}</p>
                        <small>By {event.actor}</small>
                      </li>
                    ),
                  )}
                </ol>
              ) : (
                <p>No timeline events.</p>
              )}
            </section>

            <section className="iw-panel">
              <div className="iw-panel-header">
                <div>
                  <p>Collaboration</p>
                  <h2>Analyst notes</h2>
                </div>
              </div>
              <form
                onSubmit={async (event) => {
                  event.preventDefault();
                  if (
                    await investigationWorkspace.createNote(
                      note,
                    )
                  ) {
                    setNote("");
                  }
                }}
              >
                <textarea
                  rows="4"
                  value={note}
                  onChange={(event) =>
                    setNote(event.target.value)
                  }
                  placeholder="Add investigation note using Markdown…"
                />
                <button
                  disabled={
                    !note.trim() ||
                    investigationWorkspace.saving
                  }
                >
                  Add note
                </button>
              </form>
              {investigationWorkspace.notes.map((item) => (
                <article className="iw-note" key={item.id}>
                  <strong>
                    {item.author_name ||
                      item.user_name ||
                      "Analyst"}
                  </strong>
                  <time>
                    {new Date(
                      item.created_at,
                    ).toLocaleString()}
                  </time>
                  <p className="iw-markdown">{item.content}</p>
                </article>
              ))}
            </section>
          </div>

          <div className="iw-grid">
            <section className="iw-panel">
              <div className="iw-panel-header">
                <div>
                  <p>Checklist</p>
                  <h2>Tasks</h2>
                </div>
                <strong>
                  {investigationWorkspace.taskProgress.completed}/
                  {investigationWorkspace.taskProgress.total}
                </strong>
              </div>
              <div className="iw-progress">
                <span
                  style={{
                    width: `${investigationWorkspace.taskProgress.percentage}%`,
                  }}
                />
              </div>
              <form
                onSubmit={async (event) => {
                  event.preventDefault();
                  if (
                    await investigationWorkspace.createTask(
                      task,
                    )
                  ) {
                    setTask("");
                  }
                }}
              >
                <input
                  value={task}
                  onChange={(event) =>
                    setTask(event.target.value)
                  }
                  placeholder="New task"
                />
                <button
                  disabled={
                    task.trim().length < 3 ||
                    investigationWorkspace.saving
                  }
                >
                  Add task
                </button>
              </form>
              {investigationWorkspace.tasks.map((item) => (
                <label className="iw-task" key={item.id}>
                  <input
                    type="checkbox"
                    checked={Boolean(item.completed)}
                    disabled={
                      item.completed ||
                      investigationWorkspace.saving
                    }
                    onChange={() =>
                      investigationWorkspace.toggleTask(item)
                    }
                  />
                  <span>{item.title}</span>
                </label>
              ))}
            </section>

            <section className="iw-panel">
              <div className="iw-panel-header">
                <div>
                  <p>Supporting material</p>
                  <h2>Evidence</h2>
                </div>
              </div>
              {investigationWorkspace.evidence.length ? (
                investigationWorkspace.evidence.map((item) => (
                  <article
                    className="iw-evidence"
                    key={item.id}
                  >
                    <div>
                      <strong>{item.filename || item.name}</strong>
                      <span>
                        {item.uploader || "Unknown uploader"} ·{" "}
                        {fileSize(item.size)} ·{" "}
                        {new Date(
                          item.uploaded_at,
                        ).toLocaleString()}
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={() =>
                        investigationWorkspace.downloadEvidence(
                          item,
                        )
                      }
                    >
                      Download
                    </button>
                  </article>
                ))
              ) : (
                <p>No evidence attached.</p>
              )}
            </section>
          </div>

          <section className="iw-panel">
            <div className="iw-panel-header">
              <div>
                <p>Activity</p>
                <h2>Activity history</h2>
              </div>
            </div>
            {(investigationWorkspace.activityHistory || [])
              .length ? (
              <ol className="iw-history">
                {investigationWorkspace.activityHistory.map(
                  (event) => (
                    <li key={event.id}>
                      <strong>
                        {readable(
                          event.event_type ||
                            event.title ||
                            event.action,
                        )}
                      </strong>
                      <span>
                        {event.actor_username ||
                          event.actor_name ||
                          "System"}
                      </span>
                      <time>
                        {new Date(
                          event.created_at,
                        ).toLocaleString()}
                      </time>
                    </li>
                  ),
                )}
              </ol>
            ) : (
              <p>No activity recorded.</p>
            )}
          </section>

          <section className="iw-panel">
            <div className="iw-panel-header">
              <div>
                <p>Compliance</p>
                <h2>Audit log</h2>
              </div>
            </div>
            <div className="iw-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>User</th>
                    <th>Action</th>
                    <th>Previous</th>
                    <th>New</th>
                    <th>IP address</th>
                  </tr>
                </thead>
                <tbody>
                  {investigationWorkspace.auditLog.map(
                    (entry) => (
                      <tr key={entry.id}>
                        <td>
                          {new Date(
                            entry.created_at,
                          ).toLocaleString()}
                        </td>
                        <td>{entry.user}</td>
                        <td>{entry.action}</td>
                        <td>
                          {String(entry.previousValue)}
                        </td>
                        <td>{String(entry.newValue)}</td>
                        <td>{entry.ipAddress}</td>
                      </tr>
                    ),
                  )}
                </tbody>
              </table>
            </div>
            {!investigationWorkspace.auditLog.length ? (
              <p className="iw-muted">
                Audit entries are available to administrators
                and auditors.
              </p>
            ) : null}
          </section>
        </>
      )}
    </main>
  );
}
