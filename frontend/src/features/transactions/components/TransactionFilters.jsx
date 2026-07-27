export default function TransactionFilters({ filters, sort, onFiltersChange, onSortChange, onClear }) {
  return <section className="transaction-filter-panel"><div className="transaction-panel-header"><div><p className="transaction-eyebrow">Monitoring controls</p><h2>Search and prioritize</h2></div><button type="button" onClick={onClear}>Clear</button></div><div className="transaction-filter-grid">
    <label>Search<input value={filters.query} onChange={(e)=>onFiltersChange({query:e.target.value})} placeholder="Transaction, customer, merchant…" /></label>
    <label>Risk<select value={filters.risk} onChange={(e)=>onFiltersChange({risk:e.target.value})}><option value="">All risks</option><option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option></select></label>
    <label>Minimum probability<input type="number" min="0" max="1" step="0.05" value={filters.minimumProbability} onChange={(e)=>onFiltersChange({minimumProbability:e.target.value})}/></label>
    <label>Sort by<select value={sort.field} onChange={(e)=>onSortChange({...sort,field:e.target.value})}><option value="created_at">Latest</option><option value="probability">Probability</option><option value="risk">Risk</option><option value="amount">Amount</option></select></label>
    <label>Direction<select value={sort.direction} onChange={(e)=>onSortChange({...sort,direction:e.target.value})}><option value="desc">Descending</option><option value="asc">Ascending</option></select></label>
  </div></section>;
}
