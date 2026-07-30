import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import AuditTrailPage from "../pages/AuditTrailPage";

const selectEvent = vi.fn();
vi.mock("../hooks/useAuditTrail", () => ({
  useAuditTrail: () => ({
    filters: { search:"",user:"",role:"",action:"",category:"",module:"",resource_type:"",resource_id:"",outcome:"",severity:"",source_ip:"",integrity_status:"",correlation_id:"",session_id:"",date_from:"",date_to:"",relative_range:"",page:1,page_size:25 },
    setFilters: vi.fn(),
    events: [{ id:"event-1", timestamp:"2026-07-30T08:00:00Z", actor:{ email:"auditor@example.com" }, action:"case.status.updated", category:"investigation", module:"fraud_cases", resource_type:"fraud_case", resource_id:"case-1", outcome:"Success", severity:"Medium", source_ip:"192.0.2.1", integrity:{ status:"Verified" } }],
    summary: { total_events:1, security_events:0, failed_authentication_attempts:0, administrative_changes:0, high_risk_actions:0, export_download_events:0, unique_users:1, events_last_24_hours:1 },
    pagination: { page:1, page_size:25, total:1, total_pages:1 }, selectedEvent:null, changes:[], retention:{}, integrity:{ status:"Verified" },
    lookups:{ categories:[], actions:[], users:[], presets:[] }, loading:false, detailLoading:false, actionLoading:false, error:null,
    load:vi.fn().mockResolvedValue(undefined), selectEvent, verifyEvent:vi.fn(), exportEvents:vi.fn(),
  }),
}));

describe("AuditTrailPage", () => {
  it("renders the workspace", () => { render(<AuditTrailPage />); expect(screen.getByRole("heading", { name:/Enterprise audit trail/i })).toBeInTheDocument(); });
  it("selects an event", () => { render(<AuditTrailPage />); fireEvent.click(screen.getByText("case.status.updated")); expect(selectEvent).toHaveBeenCalled(); });
  it("renders exports", () => { render(<AuditTrailPage />); expect(screen.getByRole("button", { name:"Export JSON" })).toBeInTheDocument(); });
});
