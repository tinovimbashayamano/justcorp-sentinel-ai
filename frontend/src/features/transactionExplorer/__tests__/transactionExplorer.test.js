import { describe, expect, it } from "vitest";
import { comparisonRows, filterTransactions, paginate, sortTransactions, summarize, toCsv } from "../domain/transactionExplorer";

const items = [
  { id: 1, transaction_id: "TX-1", customer_id: "C-1", merchant: "Store A", fraud_probability: .92, transaction_amount: 500, created_at: "2026-07-28T10:00:00Z" },
  { id: 2, transaction_id: "TX-2", customer_id: "C-2", merchant: "Store B", fraud_probability: .2, transaction_amount: 40, created_at: "2026-07-27T10:00:00Z" },
];

describe("transaction explorer domain", () => {
  it("filters transactions", () => expect(filterTransactions(items, { merchant: "Store A", minimumProbability: .8, maximumProbability: 1 })).toHaveLength(1));
  it("sorts by amount", () => expect(sortTransactions(items, { field: "amount", direction: "asc" })[0].id).toBe(2));
  it("paginates", () => expect(paginate(items, 1, 1).pageCount).toBe(2));
  it("summarizes", () => { const result = summarize(items); expect(result.flagged).toBe(1); expect(result.totalAmount).toBe(540); });
  it("compares", () => expect(comparisonRows(items[0], items[1]).length).toBeGreaterThan(5));
  it("exports csv", () => expect(toCsv(items)).toContain("TX-1"));
});
