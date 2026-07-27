export default function QueuePagination({
  pagination,
  pageSize,
  onPageChange,
  onPageSizeChange,
}) {
  return (
    <div className="queue-pagination">
      <span>
        Page {pagination.page} of {pagination.totalPages} ·{" "}
        {pagination.totalItems} cases
      </span>

      <div className="queue-pagination__actions">
        <label>
          Per page
          <select
            value={pageSize}
            onChange={(event) =>
              onPageSizeChange(Number(event.target.value))
            }
          >
            {[10, 20, 50].map((size) => (
              <option value={size} key={size}>
                {size}
              </option>
            ))}
          </select>
        </label>

        <button
          type="button"
          disabled={pagination.page <= 1}
          onClick={() => onPageChange(pagination.page - 1)}
        >
          Previous
        </button>
        <button
          type="button"
          disabled={
            pagination.page >= pagination.totalPages
          }
          onClick={() => onPageChange(pagination.page + 1)}
        >
          Next
        </button>
      </div>
    </div>
  );
}
