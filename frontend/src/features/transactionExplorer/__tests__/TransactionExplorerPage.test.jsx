import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it, vi } from "vitest";
import TransactionExplorerPage from "../pages/TransactionExplorerPage";

vi.mock("../hooks/useTransactionExplorer", () => ({
  useTransactionExplorer: () => ({
    visibleTransactions: [], filters: { query:"",risk:"",minimumProbability:0,maximumProbability:1,minimumAmount:"",maximumAmount:"",merchant:"",customerId:"",dateFrom:"",dateTo:"" },
    sort:{field:"created_at",direction:"desc"},page:1,pageCount:1,totalResults:0,pageSize:25,selectedTransaction:null,comparison:[],savedSearches:[],
    summary:{total:0,flagged:0,critical:0,high:0,totalAmount:0},loading:false,error:null,
    loadTransactions:vi.fn().mockResolvedValue([]),updateFilters:vi.fn(),clearFilters:vi.fn(),setSort:vi.fn(),setPage:vi.fn(),setPageSize:vi.fn(),
    setSelectedTransaction:vi.fn(),toggleComparison:vi.fn(),setComparison:vi.fn(),saveSearch:vi.fn(),applySavedSearch:vi.fn(),deleteSavedSearch:vi.fn(),exportCsv:vi.fn(),
  }),
}));

describe("TransactionExplorerPage", () => {
  it("renders the explorer", () => {
    render(<MemoryRouter><TransactionExplorerPage /></MemoryRouter>);
    expect(screen.getByRole("heading", { name: /Transaction Search & Explorer/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Export CSV/i })).toBeInTheDocument();
  });
});
