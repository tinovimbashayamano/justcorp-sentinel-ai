import {
  ANALYST_DECISIONS,
  CASE_STATUSES,
  RISK_LEVELS,
} from "../domain/caseQueue";

export default function CaseQueueFilters({
  filters,
  sort,
  onFiltersChange,
  onSortChange,
  onClear,
}) {
  return (
    <section className="smart-filter-panel">
      <div className="smart-filter-panel__header">
        <div>
          <p className="case-eyebrow">Smart queue</p>
          <h2>Search and filter</h2>
        </div>
        <button type="button" onClick={onClear}>
          Clear
        </button>
      </div>

      <div className="smart-filter-grid">
        <label>
          Search
          <input
            value={filters.query}
            onChange={(event) =>
              onFiltersChange({ query: event.target.value })
            }
            placeholder="Transaction, customer, merchant, analyst…"
          />
        </label>

        <label>
          Status
          <select
            value={filters.status}
            onChange={(event) =>
              onFiltersChange({ status: event.target.value })
            }
          >
            <option value="">All statuses</option>
            {CASE_STATUSES.map((status) => (
              <option key={status} value={status}>
                {status.replaceAll("_", " ")}
              </option>
            ))}
          </select>
        </label>

        <label>
          Decision
          <select
            value={filters.decision}
            onChange={(event) =>
              onFiltersChange({ decision: event.target.value })
            }
          >
            <option value="">All decisions</option>
            {ANALYST_DECISIONS.map((decision) => (
              <option key={decision} value={decision}>
                {decision.replaceAll("_", " ")}
              </option>
            ))}
          </select>
        </label>

        <label>
          Risk
          <select
            value={filters.risk}
            onChange={(event) =>
              onFiltersChange({ risk: event.target.value })
            }
          >
            <option value="">All risk levels</option>
            {RISK_LEVELS.map((risk) => (
              <option key={risk} value={risk}>
                {risk}
              </option>
            ))}
          </select>
        </label>

        <label>
          Analyst
          <input
            value={filters.analyst}
            onChange={(event) =>
              onFiltersChange({ analyst: event.target.value })
            }
            placeholder="Exact analyst name"
          />
        </label>

        <label>
          Minimum probability
          <input
            type="number"
            min="0"
            max="1"
            step="0.05"
            value={filters.minimumProbability}
            onChange={(event) =>
              onFiltersChange({
                minimumProbability: event.target.value,
              })
            }
          />
        </label>

        <label>
          Date from
          <input
            type="date"
            value={filters.dateFrom}
            onChange={(event) =>
              onFiltersChange({ dateFrom: event.target.value })
            }
          />
        </label>

        <label>
          Date to
          <input
            type="date"
            value={filters.dateTo}
            onChange={(event) =>
              onFiltersChange({ dateTo: event.target.value })
            }
          />
        </label>

        <label>
          Sort by
          <select
            value={sort.field}
            onChange={(event) =>
              onSortChange({
                ...sort,
                field: event.target.value,
              })
            }
          >
            <option value="updated_at">Last updated</option>
            <option value="created_at">Created date</option>
            <option value="probability">Fraud probability</option>
            <option value="risk">Risk level</option>
            <option value="status">Status</option>
          </select>
        </label>

        <label>
          Direction
          <select
            value={sort.direction}
            onChange={(event) =>
              onSortChange({
                ...sort,
                direction: event.target.value,
              })
            }
          >
            <option value="desc">Descending</option>
            <option value="asc">Ascending</option>
          </select>
        </label>
      </div>
    </section>
  );
}
