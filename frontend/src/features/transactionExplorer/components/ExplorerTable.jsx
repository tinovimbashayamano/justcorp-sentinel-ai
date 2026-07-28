import { amountOf, probabilityOf, riskOf } from "../domain/transactionExplorer";

export default function ExplorerTable({ transactions, comparison, loading, onSelect, onToggleComparison }) {
  const compared = new Set(comparison.map((item) => item.id));
  return (
    <section className="explorer-panel">
      <div className="explorer-header"><div><p>Search results</p><h2>Transactions</h2></div><span>{transactions.length} shown</span></div>
      {loading ? <p>Loading transactions…</p> : transactions.length === 0 ? <p>No matching transactions.</p> :
        <div className="explorer-scroll"><table><thead><tr>
          <th>Compare</th><th>Transaction</th><th>Customer</th><th>Merchant</th><th>Amount</th><th>Risk</th><th>Probability</th><th>Created</th>
        </tr></thead><tbody>{transactions.map((item) => <tr key={item.id}>
          <td><input aria-label={`Compare ${item.transaction_id || item.id}`} type="checkbox" checked={compared.has(item.id)} onChange={() => onToggleComparison(item)} /></td>
          <td><button className="explorer-link" onClick={() => onSelect(item)}>{item.transaction_id || `Score ${item.id}`}</button></td>
          <td>{item.customer_id || "—"}</td><td>{item.merchant_name || item.merchant || "—"}</td>
          <td>{new Intl.NumberFormat("en-US", { style: "currency", currency: item.currency || "USD" }).format(amountOf(item))}</td>
          <td><span className={`risk risk--${riskOf(item)}`}>{riskOf(item)}</span></td>
          <td>{new Intl.NumberFormat("en-US", { style: "percent", maximumFractionDigits: 1 }).format(probabilityOf(item))}</td>
          <td>{item.created_at ? new Date(item.created_at).toLocaleString() : "—"}</td>
        </tr>)}</tbody></table></div>}
    </section>
  );
}
