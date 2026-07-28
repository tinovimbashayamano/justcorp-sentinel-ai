import { useEffect, useState } from "react";

const STATUSES = [
  "new",
  "open",
  "assigned",
  "investigating",
  "pending_customer",
  "escalated",
  "resolved",
  "under_review",
  "confirmed_fraud",
  "false_positive",
  "closed",
];

const DECISIONS = [
  "pending",
  "confirmed_fraud",
  "false_positive",
  "needs_more_information",
];

export default function CaseEditor({
  caseRecord,
  onSave,
  loading,
}) {
  const [form, setForm] = useState({
    case_status: "open",
    analyst_decision: "pending",
    analyst_notes: "",
    reviewed_by: "",
  });

  useEffect(() => {
    if (!caseRecord) return;
    setForm({
      case_status: caseRecord.case_status,
      analyst_decision:
        caseRecord.analyst_decision || "pending",
      analyst_notes: caseRecord.analyst_notes || "",
      reviewed_by: caseRecord.reviewed_by || "",
    });
  }, [caseRecord]);

  if (!caseRecord) return null;

  function update(name, value) {
    setForm((current) => ({
      ...current,
      [name]: value,
    }));
  }

  function submit(event) {
    event.preventDefault();
    onSave(caseRecord.id, form);
  }

  return (
    <form
      className="case-panel case-editor"
      onSubmit={submit}
    >
      <div className="case-panel__header">
        <div>
          <p className="case-eyebrow">Human review</p>
          <h2>Update investigation</h2>
        </div>
      </div>

      <label>
        Case status
        <select
          value={form.case_status}
          onChange={(event) =>
            update("case_status", event.target.value)
          }
        >
          {STATUSES.map((status) => (
            <option key={status} value={status}>
              {status.replaceAll("_", " ")}
            </option>
          ))}
        </select>
      </label>

      <label>
        Analyst decision
        <select
          value={form.analyst_decision}
          onChange={(event) =>
            update(
              "analyst_decision",
              event.target.value,
            )
          }
        >
          {DECISIONS.map((decision) => (
            <option key={decision} value={decision}>
              {decision.replaceAll("_", " ")}
            </option>
          ))}
        </select>
      </label>

      <label>
        Reviewed by
        <input
          value={form.reviewed_by}
          onChange={(event) =>
            update("reviewed_by", event.target.value)
          }
          maxLength={255}
        />
      </label>

      <label>
        Investigation notes
        <textarea
          rows="8"
          value={form.analyst_notes}
          onChange={(event) =>
            update("analyst_notes", event.target.value)
          }
          maxLength={5000}
        />
      </label>

      <button type="submit" disabled={loading}>
        {loading ? "Saving…" : "Save investigation"}
      </button>
    </form>
  );
}
