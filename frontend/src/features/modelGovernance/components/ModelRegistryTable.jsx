import {
  MODEL_STATUSES,
  normalizeMetric,
  statusClass,
} from "../domain/modelGovernance";

export default function ModelRegistryTable({
  models,
  filters,
  setFilters,
  onSelect,
  selectedId,
}) {
  return (
    <section className="governance-panel">
      <header className="panel-header">
        <div>
          <p>Registry</p>
          <h2>Model registry</h2>
        </div>
        <div className="registry-filters">
          <input
            aria-label="Search models"
            placeholder="Search models"
            value={filters.search}
            onChange={(event) =>
              setFilters((current) => ({
                ...current,
                search: event.target.value,
              }))
            }
          />
          <select
            aria-label="Filter by status"
            value={filters.status}
            onChange={(event) =>
              setFilters((current) => ({
                ...current,
                status: event.target.value,
              }))
            }
          >
            <option>All</option>
            {MODEL_STATUSES.map((status) => (
              <option key={status}>{status}</option>
            ))}
          </select>
        </div>
      </header>

      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Model</th>
              <th>Version</th>
              <th>Algorithm</th>
              <th>Status</th>
              <th>Environment</th>
              <th>ROC-AUC</th>
              <th>PR-AUC</th>
              <th>Recall</th>
              <th>Owner</th>
            </tr>
          </thead>
          <tbody>
            {models.length ? models.map((model) => (
              <tr
                key={model.id}
                className={selectedId === model.id ? "selected-row" : ""}
                onClick={() => onSelect(model.id)}
              >
                <td>{model.name}</td>
                <td>{model.version}</td>
                <td>{model.algorithm}</td>
                <td>
                  <span className={statusClass(model.status)}>
                    {model.status}
                  </span>
                </td>
                <td>{model.environment}</td>
                <td>{normalizeMetric(model.roc_auc)}</td>
                <td>{normalizeMetric(model.pr_auc)}</td>
                <td>{normalizeMetric(model.recall)}</td>
                <td>{model.owner}</td>
              </tr>
            )) : (
              <tr>
                <td colSpan="9">No model records are available.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
