import { describe,expect,it } from "vitest";
import { deriveOverallStatus,filterLogs,formatMetric,normalizeResources,normalizeServices,normalizeSummary,sortIncidents,sortJobs } from "../domain/operations";

describe("operations domain",()=>{
  it("normalizes summary",()=>{const r=normalizeSummary({status:"healthy",api_uptime:.999,average_response_time_ms:82});expect(r.status).toBe("healthy");expect(r.averageLatency).toBe(82)});
  it("normalizes services",()=>{expect(normalizeServices([{name:"Backend",status:"Healthy"}])[0].status).toBe("healthy")});
  it("normalizes resources",()=>{expect(normalizeResources({cpu_usage:55})[0].value).toBe(55)});
  it("sorts incidents",()=>{expect(sortIncidents([{id:1,severity:"low"},{id:2,severity:"critical"}])[0].id).toBe(2)});
  it("sorts jobs",()=>{expect(sortJobs([{id:1,started_at:"2026-07-27"},{id:2,started_at:"2026-07-28"}])[0].id).toBe(2)});
  it("filters logs by level",()=>{expect(filterLogs([{id:1,level:"error"},{id:2,level:"information"}],{log_level:"error",service:"all",search:""})).toHaveLength(1)});
  it("filters logs by text",()=>{expect(filterLogs([{id:1,message:"Database timeout"}],{log_level:"all",service:"all",search:"database"})).toHaveLength(1)});
  it("derives critical status",()=>{expect(deriveOverallStatus([{status:"healthy"},{status:"critical"}])).toBe("critical")});
  it("keeps unavailable database connections explicit",()=>{expect(normalizeSummary({database_connections:null}).databaseConnections).toBeNull()});
  it("defaults missing service metadata",()=>{const service=normalizeServices([{}])[0];expect(service.name).toBe("Unknown service");expect(service.status).toBe("unknown")});
  it("filters services without case sensitivity",()=>{expect(filterLogs([{id:1,service:"Backend"}],{log_level:"all",service:"backend",search:""})).toHaveLength(1)});
  it("derives unknown status without services",()=>{expect(deriveOverallStatus([])).toBe("unknown")});
  it("formats unavailable metrics honestly",()=>{expect(formatMetric(null," ms")).toBe("Not reported")});
});
