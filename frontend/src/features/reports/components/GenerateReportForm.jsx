import { useMemo, useState } from "react";
import {
  REPORT_TYPES,
  createReportPayload,
  validateReportForm,
} from "../domain/reports";
import ReportTypeSelector from "./ReportTypeSelector";

const DEFAULT_FORM = {
  reportType: "",
  outputFormat: "",
  title: "",
  description: "",
  dateFrom: "",
  dateTo: "",
  caseId: "",
  transactionId: "",
  modelId: "",
  severity: "",
  includeCharts: true,
  includeExplanations: true,
  includeAuditMetadata: true,
};

export default function GenerateReportForm({ onGenerate, actionLoading }) {
  const [form, setForm] = useState(DEFAULT_FORM);
  const [errors, setErrors] = useState({});

  const selectedType = useMemo(
    () => REPORT_TYPES.find((type) => type.key === form.reportType),
    [form.reportType]
  );

  const update = (name, value) => {
    setForm((current) => ({
      ...current,
      [name]: value,
      ...(name === "reportType"
        ? {
            outputFormat:
              REPORT_TYPES.find((type) => type.key === value)
                ?.availableFormats[0] ?? "",
          }
        : {}),
    }));
  };

  const submit = async (event) => {
    event.preventDefault();
    const validation = validateReportForm(form);
    setErrors(validation);
    if (Object.keys(validation).length > 0) return;
    try {
      await onGenerate(createReportPayload(form));
      setForm(DEFAULT_FORM);
    } catch {
      // The dashboard renders the normalized API error from the report hook.
    }
  };

  return (
    <form className="report-form" onSubmit={submit}>
      <header className="report-panel-header">
        <div><p>New export</p><h2>Generate report</h2></div>
      </header>

      <ReportTypeSelector
        value={form.reportType}
        onChange={(value) => update("reportType", value)}
      />
      {errors.reportType ? <small className="field-error">{errors.reportType}</small> : null}
      {selectedType?.availableFormats.length === 0 ? (
        <p className="report-capability-note">
          Preview only: this report type still needs a backend generator.
        </p>
      ) : null}

      <div className="report-form-grid">
        <label>
          Report title
          <input
            value={form.title}
            onChange={(event) => update("title", event.target.value)}
            placeholder="July fraud investigation summary"
          />
          {errors.title ? <small className="field-error">{errors.title}</small> : null}
        </label>

        <label>
          Output format
          <select
            value={form.outputFormat}
            onChange={(event) => update("outputFormat", event.target.value)}
            disabled={!selectedType}
          >
            <option value="">Select format</option>
            {(selectedType?.availableFormats ?? []).map((format) => (
              <option key={format}>{format}</option>
            ))}
          </select>
          {errors.outputFormat ? <small className="field-error">{errors.outputFormat}</small> : null}
        </label>

        <label>
          Start date
          <input type="date" value={form.dateFrom}
            onChange={(event) => update("dateFrom", event.target.value)} />
        </label>

        <label>
          End date
          <input type="date" value={form.dateTo}
            onChange={(event) => update("dateTo", event.target.value)} />
          {errors.dateTo ? <small className="field-error">{errors.dateTo}</small> : null}
        </label>

        <label>
          Case ID
          <input value={form.caseId}
            onChange={(event) => update("caseId", event.target.value)}
            placeholder="Required for server generation" />
          {errors.caseId ? <small className="field-error">{errors.caseId}</small> : null}
        </label>

        <label>
          Transaction ID
          <input value={form.transactionId}
            onChange={(event) => update("transactionId", event.target.value)}
            placeholder="Optional" />
        </label>

        <label>
          Model ID
          <input value={form.modelId}
            onChange={(event) => update("modelId", event.target.value)}
            placeholder="Optional" />
        </label>

        <label>
          Severity
          <select value={form.severity}
            onChange={(event) => update("severity", event.target.value)}>
            <option value="">All severities</option>
            <option>Critical</option><option>High</option>
            <option>Medium</option><option>Low</option>
          </select>
        </label>
      </div>

      <label>
        Description
        <textarea rows="3" value={form.description}
          onChange={(event) => update("description", event.target.value)}
          placeholder="Purpose and intended audience." />
      </label>

      <div className="report-options">
        <label><input type="checkbox" checked={form.includeCharts}
          onChange={(event) => update("includeCharts", event.target.checked)} />
          Include charts</label>
        <label><input type="checkbox" checked={form.includeExplanations}
          onChange={(event) => update("includeExplanations", event.target.checked)} />
          Include model explanations</label>
        <label><input type="checkbox" checked={form.includeAuditMetadata}
          onChange={(event) => update("includeAuditMetadata", event.target.checked)} />
          Include audit metadata</label>
      </div>

      <button type="submit" disabled={actionLoading}>
        {actionLoading ? "Generating…" : "Generate report"}
      </button>
    </form>
  );
}
