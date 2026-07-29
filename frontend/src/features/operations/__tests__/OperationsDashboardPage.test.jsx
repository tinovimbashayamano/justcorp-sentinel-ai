import { render,screen } from "@testing-library/react";
import { describe,expect,it,vi } from "vitest";
import OperationsDashboardPage from "../pages/OperationsDashboardPage";

vi.mock("../hooks/useOperationsDashboard",()=>({useOperationsDashboard:()=>({
filters:{environment:"all",time_range:"24h",log_level:"all",service:"all",search:""},
loading:false,error:null,loadDashboard:vi.fn().mockResolvedValue({}),
summary:{status:"healthy",uptime:.999,errorRate:.01,averageLatency:82,throughput:120,activeUsers:8,databaseConnections:4,queueBacklog:0},
services:[],resources:[],jobs:[],incidents:[],logs:[],apiPerformance:{},deployment:{}
})}));

describe("OperationsDashboardPage",()=>{
  it("renders operations sections",()=>{
    render(<OperationsDashboardPage/>);
    expect(screen.getByRole("heading",{name:/System health and operations/i})).toBeInTheDocument();
    expect(screen.getByRole("heading",{name:/Service status/i})).toBeInTheDocument();
    expect(screen.getByRole("heading",{name:/Background jobs/i})).toBeInTheDocument();
    expect(screen.getByRole("heading",{name:/Application logs/i})).toBeInTheDocument();
  });
});
