import { ALERT_SEVERITIES, ALERT_STATUSES } from "../domain/alertCenter";
export default function AlertFilters({ filters, sort, onFiltersChange, onSortChange, onClear }) {
  return <section className="alert-filter-panel">
    <div className="alert-panel-header"><div><p className="alert-eyebrow">Alert controls</p><h2>Search and filter</h2></div><button type="button" onClick={onClear}>Clear</button></div>
    <div className="alert-filter-grid">
      <label>Search<input value={filters.query} onChange={(e)=>onFiltersChange({query:e.target.value})} placeholder="Transaction, customer, merchant…" /></label>
      <label>Severity<select value={filters.severity} onChange={(e)=>onFiltersChange({severity:e.target.value})}><option value="">All severities</option>{ALERT_SEVERITIES.map(x=><option key={x} value={x}>{x}</option>)}</select></label>
      <label>Status<select value={filters.status} onChange={(e)=>onFiltersChange({status:e.target.value})}><option value="">All statuses</option>{ALERT_STATUSES.map(x=><option key={x} value={x}>{x}</option>)}</select></label>
      <label>Analyst<input value={filters.analyst} onChange={(e)=>onFiltersChange({analyst:e.target.value})} placeholder="Exact analyst" /></label>
      <label>Minimum probability<input type="number" min="0" max="1" step="0.05" value={filters.minimumProbability} onChange={(e)=>onFiltersChange({minimumProbability:e.target.value})} /></label>
      <label>Sort by<select value={sort.field} onChange={(e)=>onSortChange({...sort,field:e.target.value})}><option value="priority">Priority</option><option value="probability">Probability</option><option value="severity">Severity</option><option value="created_at">Created date</option></select></label>
      <label>Direction<select value={sort.direction} onChange={(e)=>onSortChange({...sort,direction:e.target.value})}><option value="desc">Descending</option><option value="asc">Ascending</option></select></label>
    </div>
  </section>;
}
