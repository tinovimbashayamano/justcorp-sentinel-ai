export default function GlobalImportanceTable({
  insight,
}) {
  const features = insight?.features || [];

  return (
    <section className="panel">
      <div className="panel__header">
        <div>
          <p className="eyebrow">
            Global explainability
          </p>
          <h2>Model-wide feature importance</h2>
        </div>
        {insight ? (
          <span className="muted">
            {insight.samples} samples
          </span>
        ) : null}
      </div>
      {features.length === 0 ? (
        <p className="muted">
          Global model intelligence has not been loaded.
        </p>
      ) : (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Rank</th>
                <th>Feature</th>
                <th>Mean absolute SHAP</th>
              </tr>
            </thead>
            <tbody>
              {features.map((feature) => (
                <tr key={feature.feature}>
                  <td>{feature.rank}</td>
                  <td>{feature.feature}</td>
                  <td>
                    {Number(
                      feature.importance,
                    ).toFixed(6)}
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
