import { useMemo, useState } from "react";

const DEFAULT_FEATURES = JSON.stringify(
  {
    TransactionAmt: 250,
    ProductCD: "W",
    card1: 13926,
  },
  null,
  2,
);

export default function TransactionExplanationForm({
  onSubmit,
  loading,
}) {
  const [transactionId, setTransactionId] = useState(
    "demo-transaction-001",
  );
  const [topFeatures, setTopFeatures] = useState(10);
  const [featureText, setFeatureText] =
    useState(DEFAULT_FEATURES);
  const [validationError, setValidationError] =
    useState("");

  const parsedFeatures = useMemo(() => {
    try {
      return JSON.parse(featureText);
    } catch {
      return null;
    }
  }, [featureText]);

  function handleSubmit(event) {
    event.preventDefault();
    if (!transactionId.trim()) {
      setValidationError(
        "Transaction ID is required.",
      );
      return;
    }
    if (
      !parsedFeatures ||
      Array.isArray(parsedFeatures)
    ) {
      setValidationError(
        "Features must be a valid JSON object.",
      );
      return;
    }

    setValidationError("");
    onSubmit({
      transaction_id: transactionId.trim(),
      features: parsedFeatures,
      top_features: Number(topFeatures),
    });
  }

  return (
    <form
      className="panel form-panel"
      onSubmit={handleSubmit}
    >
      <div className="panel__header">
        <div>
          <p className="eyebrow">
            Investigation input
          </p>
          <h2>Explain a transaction</h2>
        </div>
      </div>
      <label>
        Transaction ID
        <input
          value={transactionId}
          onChange={(event) =>
            setTransactionId(event.target.value)
          }
          maxLength={128}
          required
        />
      </label>
      <label>
        Top features
        <input
          type="number"
          min="1"
          max="30"
          value={topFeatures}
          onChange={(event) =>
            setTopFeatures(event.target.value)
          }
        />
      </label>
      <label>
        Transaction features (JSON)
        <textarea
          rows="14"
          value={featureText}
          onChange={(event) =>
            setFeatureText(event.target.value)
          }
          spellCheck="false"
        />
      </label>
      {validationError ? (
        <p className="form-error" role="alert">
          {validationError}
        </p>
      ) : null}
      <button type="submit" disabled={loading}>
        {loading
          ? "Generating explanation…"
          : "Generate explanation"}
      </button>
    </form>
  );
}
