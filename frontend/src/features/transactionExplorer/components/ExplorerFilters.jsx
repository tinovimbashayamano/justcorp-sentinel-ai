export default function ExplorerFilters({ filters, sort, onFiltersChange, onSortChange, onClear }) {
  const field = (label, key, type = "text", extra = {}) => (
    <label>{label}<input type={type} value={filters[key]} onChange={(e) => onFiltersChange({ [key]: e.target.value })} {...extra} /></label>
  );

  return (
    <section className="explorer-panel">
      <div className="explorer-header"><div><p>Advanced search</p><h2>Transaction criteria</h2></div><button onClick={onClear}>Clear</button></div>
      <div className="explorer-filters">
        {field("Search", "query")}
        <label>Risk<select value={filters.risk} onChange={(e) => onFiltersChange({ risk: e.target.value })}>
          <option value="">All</option><option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option>
        </select></label>
        {field("Merchant", "merchant")}
        {field("Customer", "customerId")}
        {field("Min probability", "minimumProbability", "number", { min: 0, max: 1, step: .05 })}
        {field("Max probability", "maximumProbability", "number", { min: 0, max: 1, step: .05 })}
        {field("Min amount", "minimumAmount", "number", { min: 0 })}
        {field("Max amount", "maximumAmount", "number", { min: 0 })}
        {field("Date from", "dateFrom", "date")}
        {field("Date to", "dateTo", "date")}
        <label>Sort<select value={sort.field} onChange={(e) => onSortChange({ ...sort, field: e.target.value })}>
          <option value="created_at">Created</option><option value="amount">Amount</option><option value="probability">Probability</option><option value="risk">Risk</option><option value="merchant">Merchant</option>
        </select></label>
        <label>Direction<select value={sort.direction} onChange={(e) => onSortChange({ ...sort, direction: e.target.value })}>
          <option value="desc">Descending</option><option value="asc">Ascending</option>
        </select></label>
      </div>
    </section>
  );
}
