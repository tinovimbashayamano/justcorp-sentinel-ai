export default function AlertToolbar({
  summary,
  pagination,
  loading,
  onRefresh,
  onPageChange,
}) {
  return (
    <section
      className="alert-toolbar"
      aria-label="Alert feed status"
    >
      <div className="alert-toolbar__status">
        <span className="alert-toolbar__live">
          Live feed
        </span>
        <span>
          <strong>{summary.total || 0}</strong> alerts
        </span>
        <span>
          <strong>{summary.unread || 0}</strong> unread
        </span>
        <span>Refreshes every 30 seconds</span>
        {pagination ? (
          <span>
            Showing {pagination.startItem}–
            {pagination.endItem} of {pagination.totalItems}
          </span>
        ) : null}
      </div>
      <div className="alert-toolbar__actions">
        {pagination?.totalPages > 1 ? (
          <>
            <button
              type="button"
              disabled={pagination.page <= 1}
              onClick={() =>
                onPageChange(pagination.page - 1)
              }
            >
              Previous
            </button>
            <span>
              Page {pagination.page} of{" "}
              {pagination.totalPages}
            </span>
            <button
              type="button"
              disabled={
                pagination.page >= pagination.totalPages
              }
              onClick={() =>
                onPageChange(pagination.page + 1)
              }
            >
              Next
            </button>
          </>
        ) : null}
        <button
          type="button"
          onClick={onRefresh}
          disabled={loading}
        >
          {loading ? "Refreshing…" : "Refresh alerts"}
        </button>
      </div>
    </section>
  );
}
