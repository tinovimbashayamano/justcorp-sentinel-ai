import { REPORT_TYPES } from "../domain/reports";

export default function ReportTypeSelector({ value, onChange }) {
  return (
    <section className="report-type-grid" aria-label="Report types">
      {REPORT_TYPES.map((type) => (
        <button
          type="button"
          key={type.key}
          className={value === type.key ? "selected" : ""}
          onClick={() => onChange(type.key)}
        >
          <strong>{type.label}</strong>
          <span>{type.description}</span>
          <small>Planned: {type.formats.join(" · ")}</small>
          <small className={type.availableFormats.length ? "available" : "unavailable"}>
            {type.availableFormats.length
              ? `Available now: ${type.availableFormats.join(" · ")}`
              : "Backend generator unavailable"}
          </small>
        </button>
      ))}
    </section>
  );
}
