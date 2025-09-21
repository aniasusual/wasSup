"""
Multi-Stage Filter Planning Node (Phase 4 - K)

Generates a filter planning blueprint for each stage of the investigation
based on:
  - investigation_plan (from J)
  - query_decomposition constraints/goals (from E)
  - performance_baselines (AAA) and failure_patterns (BBB)

This node does NOT build concrete Logging filter strings (that is L's job).
It outputs a structured `filter_plan` that L/other nodes can translate
using filter components (HHH–LLL, MMM).
"""

import logging
from typing import Dict, Any, List, Optional

try:
    from .....models.agent import AgentState, WorkflowConfig
    from ....project_architecture_service import project_architecture_service
except ImportError:
    import sys, os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
    from app.models.agent import AgentState, WorkflowConfig
    from app.services.project_architecture_service import project_architecture_service


logger = logging.getLogger(__name__)


class MultiStageFilterPlanningNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.MultiStageFilterPlanningNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            project_id = state.get("project_id") or ""
            if not project_id:
                raise ValueError("Missing project_id")

            plan: List[Dict[str, Any]] = list(state.get("investigation_plan") or [])
            if not plan:
                raise ValueError("Missing investigation_plan from dependency strategy")

            decomp = state.get("query_decomposition") or {}
            constraints = decomp.get("constraints") or {}
            # Gather repository guidance
            baselines = await project_architecture_service.get_performance_baselines(project_id)
            failures = await project_architecture_service.get_failure_patterns(project_id)

            # Index guidance by service_id for quick lookups
            bl_idx: Dict[str, Dict[str, Any]] = {}
            for b in baselines or []:
                sid = b.get("service_id")
                if sid:
                    bl_idx[sid] = b
            fp_idx: Dict[str, List[Dict[str, Any]]] = {}
            for p in failures or []:
                for sid in p.get("services") or []:
                    fp_idx.setdefault(sid, []).append(p)

            # Build per-stage blueprint using minimal, strict rules
            filter_plan: List[Dict[str, Any]] = []
            for stage in plan:
                services = list(stage.get("services") or [])
                if not services:
                    continue

                # Start with global constraints from E (if any)
                stage_plan: Dict[str, Any] = {
                    "stage": stage.get("stage"),
                    "services": services,
                    "rationale": stage.get("rationale"),
                    "temporal_window": None,  # e.g., '1h', '24h' (string for III)
                    "severity_threshold": None,  # e.g., 'ERROR' (string for JJJ)
                    "status_codes": [],  # e.g., ['5xx','500'] (JJJ)
                    "content_terms": [],  # e.g., ['timeout','UNAUTHENTICATED'] (KKK)
                    "notes": [],
                }

                # Apply user/decomp constraints when present
                if isinstance(constraints.get("time"), str):
                    stage_plan["temporal_window"] = constraints["time"].strip()
                if isinstance(constraints.get("severity"), str):
                    stage_plan["severity_threshold"] = constraints["severity"].strip().upper()
                if isinstance(constraints.get("status"), list):
                    stage_plan["status_codes"] = [str(s).strip() for s in constraints["status"] if str(s).strip()]
                if isinstance(constraints.get("keywords"), list):
                    stage_plan["content_terms"] = [str(k).strip() for k in constraints["keywords"] if str(k).strip()]

                # Incorporate repository guidance per service
                # - If baseline shows non-trivial error_rate, ensure severity >= WARNING
                # - If patterns exist for a service, include their signals as content_terms
                sev = stage_plan["severity_threshold"]
                for sid in services:
                    b = bl_idx.get(sid)
                    if b and isinstance(b.get("error_rate_pct"), (int, float)) and b.get("error_rate_pct", 0) > 1:
                        if not sev or sev not in ("WARNING", "ERROR", "CRITICAL", "ALERT", "EMERGENCY"):
                            sev = "WARNING"
                    for p in fp_idx.get(sid, []):
                        for sig in p.get("signals") or []:
                            if isinstance(sig, str) and sig.strip():
                                if sig not in stage_plan["content_terms"]:
                                    stage_plan["content_terms"].append(sig.strip())
                if sev:
                    stage_plan["severity_threshold"] = sev

                # Default temporal window if missing and baselines exist
                if not stage_plan["temporal_window"]:
                    # choose a conservative default window for the plan
                    stage_plan["temporal_window"] = "1h"

                filter_plan.append(stage_plan)

            updated = state.copy()
            tr = updated.get("tool_results") or {}
            tr.update({
                "filter_planning": {"stages": len(filter_plan)}
            })
            updated.update({
                "current_step": "filter_planning_complete",
                "filter_plan": filter_plan,
                "tool_results": tr,
            })
            return updated
        except Exception as e:
            self.logger.error(f"MultiStageFilterPlanningNode error: {e}")
            updated = state.copy()
            updated.update({
                "current_step": "filter_planning_error",
                "error": f"Filter planning failed: {e}",
            })
            return updated

