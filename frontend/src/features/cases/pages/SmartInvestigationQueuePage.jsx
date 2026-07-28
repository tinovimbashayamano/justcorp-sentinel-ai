import {
  useEffect,
  useRef,
  useState,
} from "react";
import { useLocation } from "react-router";

import CaseEditor from "../components/CaseEditor";
import CaseExplainabilityLink from "../components/CaseExplainabilityLink";
import CaseQueueFilters from "../components/CaseQueueFilters";
import CaseSummary from "../components/CaseSummary";
import FraudAlertQueue from "../components/FraudAlertQueue";
import QueuePagination from "../components/QueuePagination";
import QueueSummaryCards from "../components/QueueSummaryCards";
import SmartCaseQueue from "../components/SmartCaseQueue";
import { useSmartCaseQueue } from "../hooks/useSmartCaseQueue";
import "../styles/smart-case-queue.css";

export default function SmartInvestigationQueuePage() {
  const location = useLocation();
  const routedScoreId =
    location.state?.fraudScoreRecordId ?? null;
  const handledRoutedScoreId = useRef(null);
  const {
    cases,
    scores,
    selectedCase,
    selectedScore,
    filters,
    sort,
    pageSize,
    pagination,
    summary,
    loading,
    error,
    loadQueue,
    selectCase,
    saveCase,
    openOrCreateCase,
    updateFilters,
    clearFilters,
    setSort,
    setPage,
    setPageSize,
  } = useSmartCaseQueue();

  const [notice, setNotice] = useState("");

  useEffect(() => {
    loadQueue().catch(() => undefined);
  }, [loadQueue]);

  useEffect(() => {
    if (
      routedScoreId == null ||
      handledRoutedScoreId.current === routedScoreId ||
      !scores.some(
        (score) =>
          String(score.id) === String(routedScoreId),
      )
    ) {
      return;
    }

    handledRoutedScoreId.current = routedScoreId;
    openOrCreateCase(routedScoreId)
      .then((result) => {
        setNotice(
          result.created
            ? "A new investigation case was created."
            : "The existing investigation case was opened.",
        );
      })
      .catch(() => {
        handledRoutedScoreId.current = null;
      });
  }, [openOrCreateCase, routedScoreId, scores]);

  async function handleInvestigate(scoreId) {
    try {
      const result = await openOrCreateCase(scoreId);
      setNotice(
        result.created
          ? "A new investigation case was created."
          : "The existing investigation case was opened."
      );
    } catch {
      setNotice("");
    }
  }

  async function handleSave(caseId, payload) {
    await saveCase(caseId, payload);
    setNotice("Case changes were saved.");
  }

  return (
    <main className="smart-investigation-page">
      <header className="case-workspace__header">
        <div>
          <p className="case-eyebrow">JustCorp Sentinel AI</p>
          <h1>Smart Investigation Queue</h1>
          <p>
            Convert fraud alerts into traceable investigations,
            prevent duplicate cases, and prioritize analyst work.
          </p>
        </div>
        <button type="button" onClick={loadQueue}>
          Refresh queue
        </button>
      </header>

      {error ? (
        <div className="case-error" role="alert">
          {error.message}
        </div>
      ) : null}

      {notice ? (
        <div className="case-notice" role="status">
          {notice}
        </div>
      ) : null}

      <QueueSummaryCards
        summary={summary}
        onStatusSelect={(status) =>
          updateFilters({ status })
        }
      />

      <FraudAlertQueue
        scores={scores}
        cases={cases}
        onInvestigate={handleInvestigate}
        loading={loading.createCase}
      />

      <CaseQueueFilters
        filters={filters}
        sort={sort}
        onFiltersChange={updateFilters}
        onSortChange={setSort}
        onClear={clearFilters}
      />

      <div className="smart-investigation-layout">
        <div>
          <SmartCaseQueue
            cases={pagination.items}
            scores={scores}
            selectedCaseId={selectedCase?.id}
            loading={loading.cases}
            onSelect={selectCase}
          />

          <QueuePagination
            pagination={pagination}
            pageSize={pageSize}
            onPageChange={setPage}
            onPageSizeChange={(size) => {
              setPageSize(size);
              setPage(1);
            }}
          />
        </div>

        <div className="case-main-column">
          <CaseSummary
            caseRecord={selectedCase}
            score={selectedScore}
          />

          <CaseEditor
            caseRecord={selectedCase}
            onSave={handleSave}
            loading={loading.saveCase}
          />

          <CaseExplainabilityLink
            caseRecord={selectedCase}
            score={selectedScore}
          />
        </div>
      </div>
    </main>
  );
}
