import { comparisonRows } from "../domain/transactionExplorer";

export default function ComparisonPanel({ comparison, onClear }) {
  if (!comparison.length) return null;
  const rows = comparison.length === 2 ? comparisonRows(comparison[0], comparison[1]) : [];
  return (
    <section className="explorer-panel">
      <div className="explorer-header"><div><p>Comparison</p><h2>Transaction comparison</h2></div><button onClick={onClear}>Clear</button></div>
      {comparison.length < 2 ? <p>Select one more transaction.</p> :
        <div className="explorer-scroll"><table><thead><tr><th>Field</th><th>{comparison[0].transaction_id}</th><th>{comparison[1].transaction_id}</th></tr></thead>
        <tbody>{rows.map((row) => <tr key={row.label}><th>{row.label}</th><td>{String(row.left)}</td><td>{String(row.right)}</td></tr>)}</tbody></table></div>}
    </section>
  );
}
