import { useState } from "react";
import { formatDateTime, reportTypeLabel } from "../domain/reports";

const DEFAULT_SCHEDULE = {
  name: "",
  report_type: "executive_fraud_summary",
  output_format: "pdf",
  frequency: "monthly",
  delivery_time: "08:00",
  recipients: "",
};

export default function ScheduledReports({
  schedules,
  onCreate,
  onCancel,
  actionLoading,
}) {
  const [form, setForm] = useState(DEFAULT_SCHEDULE);

  const submit = async (event) => {
    event.preventDefault();
    await onCreate({
      ...form,
      recipients: form.recipients
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean),
    });
    setForm(DEFAULT_SCHEDULE);
  };

  return (
    <section className="report-panel">
      <header className="report-panel-header">
        <div>
          <p>Automation</p>
          <h2>Scheduled reports</h2>
          <span className="report-support-note">
            Saved in this browser; server-side execution is not available yet.
          </span>
        </div>
      </header>

      <form className="schedule-form" onSubmit={submit}>
        <input required placeholder="Schedule name" value={form.name}
          onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))} />
        <select value={form.report_type}
          onChange={(event) => setForm((current) => ({ ...current, report_type: event.target.value }))}>
          <option value="executive_fraud_summary">Executive Fraud Summary</option>
          <option value="audit_report">Audit Report</option>
          <option value="model_performance">Model Performance Report</option>
          <option value="operations_report">Operations Report</option>
        </select>
        <select value={form.frequency}
          onChange={(event) => setForm((current) => ({ ...current, frequency: event.target.value }))}>
          <option value="daily">Daily</option><option value="weekly">Weekly</option>
          <option value="monthly">Monthly</option><option value="quarterly">Quarterly</option>
        </select>
        <input type="time" value={form.delivery_time}
          onChange={(event) => setForm((current) => ({ ...current, delivery_time: event.target.value }))} />
        <input placeholder="recipient@example.com, manager@example.com"
          value={form.recipients}
          onChange={(event) => setForm((current) => ({ ...current, recipients: event.target.value }))} />
        <button disabled={actionLoading}>Create schedule</button>
      </form>

      <div className="schedule-list">
        {schedules.map((schedule) => (
          <article key={schedule.id}>
            <div><strong>{schedule.name}</strong><span>{reportTypeLabel(schedule.report_type)}</span></div>
            <div>
              <small>{schedule.frequency}</small>
              <small>Next run: {formatDateTime(schedule.next_run_at)}</small>
              <button type="button" className="danger" onClick={() => onCancel(schedule.id)}>
                Cancel
              </button>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
