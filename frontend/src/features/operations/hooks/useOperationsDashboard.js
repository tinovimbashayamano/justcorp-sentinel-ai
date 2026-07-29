import { useCallback, useMemo, useState } from "react";
import { operationsApi } from "../../../api/operationsDashboard";
import {
  DEFAULT_OPERATION_FILTERS,
  filterLogs,
  normalizeResources,
  normalizeServices,
  normalizeSummary,
  sortIncidents,
  sortJobs,
} from "../domain/operations";

export function useOperationsDashboard(){
  const [filters,setFilters]=useState(DEFAULT_OPERATION_FILTERS);
  const [state,setState]=useState({summary:{},services:[],apiPerformance:{},resources:{},database:{},jobs:[],incidents:[],logs:[],deployment:{},thresholds:{}});
  const [loading,setLoading]=useState(false);
  const [error,setError]=useState(null);

  const loadDashboard=useCallback(async(nextFilters=DEFAULT_OPERATION_FILTERS)=>{
    setLoading(true); setError(null);
    try{
      const [summary,services,apiPerformance,resources,database,jobs,incidents,logs,deployment,thresholds]=await Promise.all([
        operationsApi.summary(nextFilters),operationsApi.services(nextFilters),operationsApi.apiPerformance(nextFilters),
        operationsApi.resources(nextFilters),operationsApi.database(nextFilters),operationsApi.jobs(nextFilters),
        operationsApi.incidents(nextFilters),operationsApi.logs(nextFilters),operationsApi.deployment(nextFilters),
        operationsApi.thresholds()
      ]);
      const next={summary:summary??{},services:services??[],apiPerformance:apiPerformance??{},resources:resources??{},database:database??{},jobs:jobs??[],incidents:incidents??[],logs:logs??[],deployment:deployment??{},thresholds:thresholds??{}};
      setFilters(nextFilters); setState(next); return next;
    }catch(caught){setError(caught); throw caught}
    finally{setLoading(false)}
  },[]);

  const saveThresholds=useCallback(async payload=>{
    const updated=await operationsApi.updateThresholds(payload);
    setState(current=>({...current,thresholds:updated}));
    return updated;
  },[]);

  const addIncident=useCallback(async payload=>{
    const created=await operationsApi.createIncident(payload);
    setState(current=>({...current,incidents:[created,...current.incidents]}));
    return created;
  },[]);

  const updateIncident=useCallback(async(id,payload)=>{
    const updated=await operationsApi.updateIncident(id,payload);
    if(!updated)return null;
    setState(current=>({
      ...current,
      incidents:current.incidents.map(item=>
        String(item.id)===String(id)?updated:item
      ),
    }));
    return updated;
  },[]);

  return {
    filters,setFilters,loading,error,loadDashboard,saveThresholds,addIncident,updateIncident,
    summary:useMemo(()=>normalizeSummary(state.summary),[state.summary]),
    services:useMemo(()=>normalizeServices(state.services),[state.services]),
    resources:useMemo(()=>normalizeResources(state.resources),[state.resources]),
    jobs:useMemo(()=>sortJobs(state.jobs),[state.jobs]),
    incidents:useMemo(()=>sortIncidents(state.incidents),[state.incidents]),
    logs:useMemo(()=>filterLogs(state.logs,filters),[state.logs,filters]),
    apiPerformance:state.apiPerformance,database:state.database,deployment:state.deployment,thresholds:state.thresholds
  };
}
