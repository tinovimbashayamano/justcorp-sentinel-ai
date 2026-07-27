import { useState } from "react";

import { downloadBase64File } from "../utils/base64";

export default function ReportExportActions({
  payload,
  onExport,
  disabled,
}) {
  const [notes, setNotes] = useState("");
  const [caseId, setCaseId] = useState("");

  async function handleExport(format) {
    const result = await onExport(format, {
      ...payload,
      case_id: caseId ? Number(caseId) : null,
      analyst_notes: notes || null,
      include_global_context: true,
    });
    downloadBase64File({
      base64: result.content_base64,
      mediaType: result.media_type,
      filename: result.filename,
    });
  }

  return (
    <section className="panel">
      <div className="panel__header">
        <div>
          <p className="eyebrow">Audit-ready output</p>
          <h2>Investigation report</h2>
        </div>
      </div>
      <label>
        Case ID (optional)
        <input
          type="number"
          min="1"
          value={caseId}
          onChange={(event) =>
            setCaseId(event.target.value)
          }
        />
      </label>
      <label>
        Analyst notes
        <textarea
          rows="5"
          value={notes}
          onChange={(event) =>
            setNotes(event.target.value)
          }
          maxLength={5000}
        />
      </label>
      <div className="button-row">
        <button
          type="button"
          onClick={() => handleExport("html")}
          disabled={disabled}
        >
          Download HTML
        </button>
        <button
          type="button"
          onClick={() => handleExport("pdf")}
          disabled={disabled}
        >
          Download PDF
        </button>
      </div>
    </section>
  );
}
