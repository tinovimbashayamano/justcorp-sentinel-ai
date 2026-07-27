import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it, vi } from "vitest";
import TransactionMonitoringPage from "../pages/TransactionMonitoringPage";
vi.mock("../hooks/useTransactionMonitoring",()=>({useTransactionMonitoring:()=>({visibleTransactions:[],selectedTransaction:null,filters:{query:"",risk:"",minimumProbability:0},sort:{field:"created_at",direction:"desc"},summary:{total:0,flagged:0,critical:0,high:0,medium:0,low:0,unknown:0},loading:false,error:null,loadTransactions:vi.fn().mockResolvedValue([]),setSelectedTransaction:vi.fn(),updateFilters:vi.fn(),clearFilters:vi.fn(),setSort:vi.fn()})}));
describe("TransactionMonitoringPage",()=>{it("renders the monitoring workspace",()=>{render(<MemoryRouter><TransactionMonitoringPage/></MemoryRouter>);expect(screen.getByRole("heading",{name:/Transaction Monitoring/i})).toBeInTheDocument();expect(screen.getByRole("heading",{name:/Monitored transactions/i})).toBeInTheDocument()})});
