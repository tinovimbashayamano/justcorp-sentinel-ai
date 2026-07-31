import { lazy, Suspense } from "react";
import { Routes, Route } from "react-router";
import PageLoading from "../components/PageLoading";
const AuditTrailPage = lazy(() => import("../features/auditTrail/pages/AuditTrailPage"));
const ReportExportDashboard = lazy(() => import("../features/reports/pages/ReportExportDashboard"));
const ModelGovernancePage = lazy(() => import("../features/modelGovernance/pages/ModelGovernancePage"));
const OperationsDashboardPage = lazy(() => import("../features/operations/pages/OperationsDashboardPage"));
const AdminPortalPage = lazy(() => import("../features/admin/pages/AdminPortalPage"));
const ExplainabilityWorkspace = lazy(() => import("../features/explainability/pages/ExplainabilityWorkspace"));
const InvestigationWorkspacePage = lazy(() => import("../features/investigationWorkspace/pages/InvestigationWorkspacePage"));
export default function LazyApplicationRoutes(){ return <Suspense fallback={<PageLoading/>}><Routes><Route path="/audit-trail" element={<AuditTrailPage/>}/><Route path="/reports/export" element={<ReportExportDashboard/>}/><Route path="/model-governance" element={<ModelGovernancePage/>}/><Route path="/operations" element={<OperationsDashboardPage/>}/><Route path="/admin" element={<AdminPortalPage/>}/><Route path="/fraud/explainability" element={<ExplainabilityWorkspace/>}/><Route path="/fraud/investigations/:caseId" element={<InvestigationWorkspacePage/>}/></Routes></Suspense>; }
