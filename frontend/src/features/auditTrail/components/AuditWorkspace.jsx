import {
  AUDIT_PRESETS, applyPreset, calculatePageRange, eventActorLabel, formatAuditDate,
  integrityClass, outcomeClass, severityClass,
} from "../domain/auditTrail";

export function AuditPresetFilters({ setFilters, apiPresets = [] }) {
  const presets = apiPresets.length ? apiPresets : AUDIT_PRESETS;
  return <section className="audit-presets" aria-label="Audit filter presets">
    {presets.map((preset) => <button type="button" key={preset.key ?? preset.id ?? preset.label}
      onClick={() => setFilters((current) => applyPreset(current, preset))}>{preset.label}</button>)}
  </section>;
}

export function AuditFilters({ filters, setFilters, lookups, onApply }) {
  const update = (name, value) => setFilters((current) => ({ ...current, [name]: value, page: 1 }));
  return <section className="audit-panel">
    <header className="audit-panel-header"><div><p>Discovery</p><h2>Search and filters</h2></div>
      <button type="button" onClick={() => onApply(filters)}>Apply filters</button></header>
    <div className="audit-filter-grid">
      <label className="wide">Full-text search<input value={filters.search} onChange={(e) => update("search", e.target.value)} placeholder="User, action, resource or event ID" /></label>
      <label>User<select value={filters.user} onChange={(e) => update("user", e.target.value)}><option value="">All users</option>{lookups.users.map((u) => <option key={u.id ?? u.email} value={u.id ?? u.email}>{u.email ?? u.name ?? u.id}</option>)}</select></label>
      <label>Role<input value={filters.role} onChange={(e) => update("role", e.target.value)} /></label>
      <label>Action<select value={filters.action} onChange={(e) => update("action", e.target.value)}><option value="">All actions</option>{lookups.actions.map((a) => { const v = a.key ?? a.value ?? a; return <option key={v}>{v}</option>; })}</select></label>
      <label>Category<select value={filters.category} onChange={(e) => update("category", e.target.value)}><option value="">All categories</option>{lookups.categories.map((c) => { const v = c.key ?? c.value ?? c; return <option key={v}>{v}</option>; })}</select></label>
      <label>Module<input value={filters.module} onChange={(e) => update("module", e.target.value)} /></label>
      <label>Resource type<input value={filters.resource_type} onChange={(e) => update("resource_type", e.target.value)} /></label>
      <label>Resource ID<input value={filters.resource_id} onChange={(e) => update("resource_id", e.target.value)} /></label>
      <label>Outcome<select value={filters.outcome} onChange={(e) => update("outcome", e.target.value)}><option value="">All outcomes</option>{["Success","Failure","Denied","Warning","Partial","Unknown"].map((v) => <option key={v}>{v}</option>)}</select></label>
      <label>Severity<select value={filters.severity} onChange={(e) => update("severity", e.target.value)}><option value="">All severities</option>{["Informational","Low","Medium","High","Critical"].map((v) => <option key={v}>{v}</option>)}</select></label>
      <label>Integrity<select value={filters.integrity_status} onChange={(e) => update("integrity_status", e.target.value)}><option value="">All states</option>{["Verified","Unverified","Integrity Warning","Legacy Record"].map((v) => <option key={v}>{v}</option>)}</select></label>
      <label>Source IP<input value={filters.source_ip} onChange={(e) => update("source_ip", e.target.value)} /></label>
      <label>Correlation ID<input value={filters.correlation_id} onChange={(e) => update("correlation_id", e.target.value)} /></label>
      <label>Session ID<input value={filters.session_id} onChange={(e) => update("session_id", e.target.value)} /></label>
      <label>Start date<input type="datetime-local" value={filters.date_from} onChange={(e) => update("date_from", e.target.value)} /></label>
      <label>End date<input type="datetime-local" value={filters.date_to} onChange={(e) => update("date_to", e.target.value)} /></label>
      <label>Page size<select value={filters.page_size} onChange={(e) => update("page_size", Number(e.target.value))}><option value="25">25</option><option value="50">50</option><option value="100">100</option></select></label>
    </div>
  </section>;
}

export function AuditEventTable({ events, selectedEvent, onSelect }) {
  return <section className="audit-panel"><header className="audit-panel-header"><div><p>Evidence stream</p><h2>Audit events</h2></div></header>
    <div className="audit-table-scroll"><table><thead><tr><th>Timestamp</th><th>Event ID</th><th>User</th><th>Action</th><th>Category</th><th>Resource</th><th>Outcome</th><th>Severity</th><th>IP</th><th>Module</th><th>Integrity</th></tr></thead>
    <tbody>{events.map((event) => <tr key={event.id} className={selectedEvent?.id === event.id ? "selected" : ""} onClick={() => onSelect(event)}>
      <td>{formatAuditDate(event.timestamp ?? event.created_at)}</td><td>{event.id}</td><td>{eventActorLabel(event)}</td><td>{event.action}</td><td>{event.category}</td>
      <td>{event.resource_type}{event.resource_id ? ` · ${event.resource_id}` : ""}</td><td><span className={outcomeClass(event.outcome)}>{event.outcome}</span></td>
      <td><span className={severityClass(event.severity)}>{event.severity}</span></td><td>{event.source_ip ?? "—"}</td><td>{event.module ?? "—"}</td>
      <td><span className={integrityClass(event.integrity?.status ?? event.integrity_status)}>{event.integrity?.status ?? event.integrity_status ?? "Unverified"}</span></td>
    </tr>)}</tbody></table></div>{events.length === 0 ? <p className="audit-empty">No audit events match the filters.</p> : null}</section>;
}

export function AuditEventDetails({ event, changes, detailLoading, actionLoading, onVerify, canVerify }) {
  if (!event) return <aside className="audit-panel audit-details-empty">Select an audit event to inspect its full evidence record.</aside>;
  const status = event.integrity?.status ?? event.integrity_status ?? "Unverified";
  return <aside className="audit-panel audit-details">
    <header className="audit-panel-header"><div><p>Evidence detail</p><h2>{event.action}</h2></div><button type="button" disabled={actionLoading || !canVerify} title={canVerify ? undefined : "Backend hash verification is unavailable"} onClick={() => onVerify(event.id)}>{actionLoading ? "Verifying…" : canVerify ? "Verify integrity" : "Verification unavailable"}</button></header>
    {detailLoading ? <p>Loading complete event…</p> : null}
    <div className="audit-badges"><span className={outcomeClass(event.outcome)}>{event.outcome}</span><span className={severityClass(event.severity)}>{event.severity}</span><span className={integrityClass(status)}>{status}</span></div>
    {event.description ? <p>{event.description}</p> : null}
    <dl className="audit-metadata">
      {[ ["Event ID",event.id],["Timestamp",formatAuditDate(event.timestamp ?? event.created_at)],["User",eventActorLabel(event)],["Role",event.actor?.role ?? event.user_role],["Category",event.category],["Module",event.module],["Resource",`${event.resource_type ?? "—"} · ${event.resource_id ?? "—"}`],["Source IP",event.source_ip],["Session ID",event.session_id],["Correlation ID",event.correlation_id],["Request",`${event.request_method ?? "—"} ${event.request_path ?? ""}`],["Status code",event.status_code],["Retention expiration",formatAuditDate(event.retention_expires_at)] ].map(([label,value]) => <div key={label}><dt>{label}</dt><dd>{value ?? "—"}</dd></div>)}
    </dl>
    <section className="audit-subpanel"><h3>Integrity chain</h3><pre className="audit-json">{JSON.stringify(event.integrity ?? {}, null, 2)}</pre></section>
    <section className="audit-subpanel"><h3>Before-and-after comparison</h3>{changes.length ? <div className="audit-table-scroll"><table><thead><tr><th>Field</th><th>Before</th><th>After</th></tr></thead><tbody>{changes.map((c) => <tr key={c.field}><td>{c.field}</td><td><pre>{c.before}</pre></td><td><pre>{c.after}</pre></td></tr>)}</tbody></table></div> : <p>No changed values were recorded.</p>}</section>
    <section className="audit-subpanel"><h3>Additional metadata</h3><pre className="audit-json">{JSON.stringify(event.metadata ?? {}, null, 2)}</pre></section>
  </aside>;
}

export function AuditGovernancePanels({ integrity, retention }) {
  return <div className="audit-overview-grid"><section className="audit-panel"><header className="audit-panel-header"><div><p>Tamper evidence</p><h2>Integrity status</h2></div><span className={integrityClass(integrity.status ?? "Unavailable")}>{integrity.status ?? "Unavailable"}</span></header>{integrity.reason ? <p className="audit-unavailable">{integrity.reason}</p> : null}<dl className="audit-metadata"><div><dt>Verified events</dt><dd>{integrity.available ? integrity.verified_events ?? 0 : "Unavailable"}</dd></div><div><dt>Warnings</dt><dd>{integrity.available ? integrity.integrity_warnings ?? 0 : "Unavailable"}</dd></div><div><dt>Last verification</dt><dd>{integrity.last_verified_at ?? "—"}</dd></div><div><dt>Hash algorithm</dt><dd>{integrity.available ? integrity.hash_algorithm ?? "SHA-256" : "Not implemented"}</dd></div></dl></section>
    <section className="audit-panel"><header className="audit-panel-header"><div><p>Lifecycle governance</p><h2>Retention policy</h2></div></header>{retention.reason ? <p className="audit-unavailable">{retention.reason}</p> : null}<dl className="audit-metadata"><div><dt>Policy</dt><dd>{retention.policy_name ?? "Unavailable"}</dd></div><div><dt>Retention period</dt><dd>{retention.retention_period ?? "Unavailable"}</dd></div><div><dt>Legal hold</dt><dd>{retention.available ? retention.legal_hold_events ?? 0 : "Unavailable"}</dd></div><div><dt>Archived</dt><dd>{retention.available ? retention.archived_events ?? 0 : "Unavailable"}</dd></div><div><dt>Deletion pending</dt><dd>{retention.available ? retention.deletion_pending ?? 0 : "Unavailable"}</dd></div><div><dt>Storage</dt><dd>{retention.storage_location ?? "Unavailable"}</dd></div></dl></section></div>;
}

export function AuditPagination({ pagination, filters, setFilters, onPageChange }) {
  const { start, end } = calculatePageRange(pagination.page, pagination.page_size, pagination.total);
  const change = (page) => { const next = { ...filters, page }; setFilters(next); onPageChange(next); };
  return <footer className="audit-pagination"><span>Showing {start}–{end} of {pagination.total}</span><div><button type="button" disabled={pagination.page <= 1} onClick={() => change(pagination.page - 1)}>Previous</button><span>Page {pagination.page} of {pagination.total_pages}</span><button type="button" disabled={pagination.page >= pagination.total_pages} onClick={() => change(pagination.page + 1)}>Next</button></div></footer>;
}
