export default function ContributionTable({
  points = [],
}) {
  return (
    <section className="panel">
      <div className="panel__header">
        <div>
          <p className="eyebrow">Decision drivers</p>
          <h2>Feature contributions</h2>
        </div>
      </div>
      {points.length === 0 ? (
        <p className="muted">
          No contribution data available.
        </p>
      ) : (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Feature</th>
                <th>Observed value</th>
                <th>SHAP value</th>
                <th>Direction</th>
              </tr>
            </thead>
            <tbody>
              {points.map((point, index) => (
                <tr
                  key={`${point.feature}-${point.shap_value}-${index}`}
                >
                  <td>{point.feature}</td>
                  <td>
                    {String(
                      point.feature_value ?? "—",
                    )}
                  </td>
                  <td>
                    {Number(point.shap_value).toFixed(6)}
                  </td>
                  <td>
                    <span
                      className={`direction direction--${point.direction}`}
                    >
                      {point.direction.replaceAll("_", " ")}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
