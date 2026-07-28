import { describe, expect, it } from "vitest";
import { buildAlertTimeline, classifyAlertSeverity, enrichAlerts, filterAlerts, paginateAlerts, sortAlerts, summarizeAlerts, updateAlertState } from "../domain/alertCenter";
const raw=[{id:1,transaction_id:"TX-1",fraud_probability:.95,merchant:"Store A",created_at:"2026-07-27T10:00:00Z"},{id:2,transaction_id:"TX-2",fraud_probability:.45,merchant:"Store B",created_at:"2026-07-26T10:00:00Z"}];
describe("alert center domain",()=>{
  it("classifies severity",()=>{expect(classifyAlertSeverity(raw[0])).toBe("critical");expect(classifyAlertSeverity(raw[1])).toBe("medium")});
  it("enriches local state",()=>{const x=enrichAlerts(raw,{1:{alert_status:"acknowledged"}});expect(x[0].alert_status).toBe("acknowledged");expect(x[1].alert_status).toBe("unread")});
  it("filters alerts",()=>{expect(filterAlerts(enrichAlerts(raw),{query:"Store A",severity:"critical"})).toHaveLength(1)});
  it("sorts by probability",()=>{expect(sortAlerts(enrichAlerts(raw),{field:"probability",direction:"desc"})[0].id).toBe(1)});
  it("summarizes alerts",()=>{const s=summarizeAlerts(enrichAlerts(raw));expect(s.total).toBe(2);expect(s.unread).toBe(2);expect(s.critical).toBe(1)});
  it("updates workflow state",()=>{const s=updateAlertState({},1,"investigating","Tino");expect(s[1].alert_status).toBe("investigating");expect(s[1].acknowledged_at).toBeTruthy();expect(s[1].assigned_analyst).toBe("Tino")});
  it("updates unread notification counts",()=>{
    const state=updateAlertState({},1,"acknowledged");
    const summary=summarizeAlerts(enrichAlerts(raw,state));
    expect(summary.unread).toBe(1);
    expect(summary.acknowledged).toBe(1);
  });
  it("paginates the prioritized feed",()=>{
    const page=paginateAlerts([1,2,3,4,5],2,2);
    expect(page.items).toEqual([3,4]);
    expect(page.totalPages).toBe(3);
  });
  it("builds timeline",()=>{expect(buildAlertTimeline(enrichAlerts(raw)[0])).toHaveLength(5)});
});
