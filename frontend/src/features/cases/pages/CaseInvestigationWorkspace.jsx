import { useEffect } from "react";

import CaseEditor from "../components/CaseEditor";
import CaseExplainabilityLink from "../components/CaseExplainabilityLink";
import CaseQueue from "../components/CaseQueue";
import CaseSummary from "../components/CaseSummary";
import { useCaseInvestigationWorkspace } from "../hooks/useCaseInvestigationWorkspace";
import "../styles/case-investigation.css";

export default function CaseInvestigationWorkspace() {
  const {
    data,
    loading,
    error,
    selectedScore,
    loadWorkspace,
    selectCase,
    saveCase,
  } = useCaseInvestigationWorkspace();

  useEffect(() => {
    loadWorkspace().catch(() => undefined);
  }, [loadWorkspace]);

  async function handleSave(caseId, payload) {
    await saveCase(caseId, payload);
  }

  return (
    <main className="case-workspace">
      <header className="case-workspace__header">
        <div>
          <p className="case-eyebrow">
            JustCorp Sentinel AI
          </p>
          <h1>
            Fraud Case Investigation Workspace
          </h1>
          <p>
            Review scored transactions, document analyst
            decisions, and preserve a clear audit trail.
          </p>
        </div>
        <button
          type="button"
          onClick={() =>
            loadWorkspace().catch(() => undefined)
          }
        >
          Refresh queue
        </button>
      </header>

      {error ? (
        <div className="case-error" role="alert">
          {error.message}
        </div>
      ) : null}

      <div className="case-layout">
        <CaseQueue
          cases={data.cases}
          selectedCaseId={data.selectedCase?.id}
          onSelect={selectCase}
          loading={loading.cases}
        />

        <div className="case-main-column">
          <CaseSummary
            caseRecord={data.selectedCase}
            score={selectedScore}
          />

          <CaseEditor
            caseRecord={data.selectedCase}
            onSave={handleSave}
            loading={loading.saveCase}
          />

          <CaseExplainabilityLink
            caseRecord={data.selectedCase}
            score={selectedScore}
          />
        </div>
      </div>
    </main>
  );
}
