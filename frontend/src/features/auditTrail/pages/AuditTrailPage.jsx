import { useEffect } from "react";
import { useAuditTrail } from "../hooks/useAuditTrail";
import AuditSummaryCards from "../components/AuditSummaryCards";
import {
  AuditPresetFilters,
  AuditFilters,
  AuditEventTable,
  AuditEventDetails,
  AuditGovernancePanels,
  AuditPagination,
} from "../components/AuditWorkspace";
import "../styles/auditTrail.css";

const EXPORT_FORMATS = [
  { format: "PDF", label: "Print / PDF", supported: true },
  { format: "XLSX", label: "Export XLSX", supported: false },
  { format: "CSV", label: "Export CSV", supported: true },
  { format: "JSON", label: "Export JSON", supported: true },
];

export default function AuditTrailPage() {
  const audit = useAuditTrail();

  useEffect(() => {
    audit.load().catch(() => undefined);
  }, [audit.load]);

  return (
    <main className="audit-page">
      <header className="audit-hero">
        <div>
          <p>JustCorp Sentinel AI</p>
          <h1>Enterprise audit trail</h1>
          <span>Search, verify and export security and business activity.</span>
        </div>
        <div className="audit-export-actions">
          {EXPORT_FORMATS.map(({ format, label, supported }) => (
            <button
              type="button"
              key={format}
              disabled={
                audit.actionLoading ||
                !supported
              }
              title={
                supported
                  ? undefined
                  : `${format} export needs backend support`
              }
              onClick={() => audit.exportEvents(format)}
            >
              {label}
            </button>
          ))}
          <span className="audit-capability-note">
            XLSX export, hash verification and retention enforcement require
            backend support. Browser exports are not server-audited yet.
          </span>
        </div>
      </header>

      <AuditSummaryCards summary={audit.summary} />
      <AuditPresetFilters
        setFilters={audit.setFilters}
        apiPresets={audit.lookups.presets}
      />
      <AuditFilters
        filters={audit.filters}
        setFilters={audit.setFilters}
        lookups={audit.lookups}
        onApply={audit.load}
      />

      {audit.error ? (
        <div className="audit-error" role="alert">
          {audit.error.message}
        </div>
      ) : null}

      <AuditGovernancePanels
        integrity={audit.integrity}
        retention={audit.retention}
        canVerifyIntegrity={Boolean(audit.canVerifyIntegrity)}
      />

      {audit.loading ? (
        <section className="audit-panel">Loading audit events…</section>
      ) : (
        <div className="audit-main-grid">
          <div>
            <AuditEventTable
              events={audit.events}
              selectedEvent={audit.selectedEvent}
              onSelect={audit.selectEvent}
            />
            <AuditPagination
              pagination={audit.pagination}
              filters={audit.filters}
              setFilters={audit.setFilters}
              onPageChange={audit.load}
            />
          </div>
          <AuditEventDetails
            event={audit.selectedEvent}
            changes={audit.changes}
            detailLoading={audit.detailLoading}
            actionLoading={audit.actionLoading}
            onVerify={audit.verifyEvent}
            canVerify={Boolean(audit.canVerifyIntegrity)}
          />
        </div>
      )}

      {audit.actionLoading ? (
        <div className="audit-progress">Processing audit request…</div>
      ) : null}
    </main>
  );
}
