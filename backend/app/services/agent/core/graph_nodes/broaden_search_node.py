"""
Broaden Search Node (Phase 5 - T)

Relaxes constraints to increase the result set when too few results are
returned. This node performs safe broadening steps using repository data
and planned services:

- Expand temporal window to a larger recent period (e.g., 24h)
- Lower severity threshold (e.g., to WARNING)
- OR-in additional services from the investigation plan (resource.type)

Strict behavior: only uses explicit plan and repository data; no fallback
guessing. Clauses are assembled using filter components (HHH–LLL).
"""

import logging
from typing import Dict, Any, List

try:
    from .....models.agent import AgentState, WorkflowConfig
    from ....project_architecture_service import project_architecture_service
    from .. import filter_components as fc
except ImportError:
    import sys, os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
    from app.models.agent import AgentState, WorkflowConfig
    from app.services.project_architecture_service import project_architecture_service
    from app.services.agent.core import filter_components as fc


logger = logging.getLogger(__name__)


class BroadenSearchNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.BroadenSearchNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            project_id = state.get("project_id") or ""
            if not project_id:
                raise ValueError("Missing project_id")

            base_filter = state.get("logging_filter") or ""
            lines: List[str] = [l for l in base_filter.split("\n") if l.strip()]
            components: Dict[str, Any] = dict(state.get("logging_filter_components") or {})
            components.setdefault("t_broadenings", [])
            changes: List[str] = []

            # 1) Expand temporal window to 24h (replace any existing timestamp/>= lines)
            new_lines: List[str] = []
            for l in lines:
                if l.startswith("timestamp>") or l.startswith("timestamp<"):
                    continue
                new_lines.append(l)
            t_clauses, t_info = fc.build_temporal_clauses(window="24h")
            for t in t_clauses:
                if t not in new_lines:
                    new_lines.append(t)
            components["time"] = t_info
            changes.append("expanded_temporal_window_24h")

            # 2) Lower severity threshold to WARNING
            # Remove any existing severity>= lines and add WARNING
            lines2: List[str] = []
            for l in new_lines:
                if l.startswith("severity>="):
                    continue
                lines2.append(l)
            sev_clause, sev_info = fc.build_severity_clause(["WARNING"])
            for c in sev_clause:
                if c not in lines2:
                    lines2.append(c)
            components["severity"] = sev_info
            changes.append("lowered_severity_to_WARNING")

            # 3) OR-in resource types for all services in investigation_plan (if present)
            filter_plan = state.get("filter_plan") or []
            all_services: List[str] = []
            if isinstance(filter_plan, list) and filter_plan:
                for st in filter_plan:
                    for sid in (st.get("services") or []):
                        if isinstance(sid, str) and sid and sid not in all_services:
                            all_services.append(sid)

            if all_services:
                registry = await project_architecture_service.get_service_registry(project_id)
                reg_idx: Dict[str, Dict[str, Any]] = {r.get("service_id"): r for r in registry or [] if r.get("service_id")}
                rtypes: List[str] = []
                for sid in all_services:
                    rt = (reg_idx.get(sid) or {}).get("resource_type")
                    if rt and rt not in rtypes:
                        rtypes.append(rt)
                if rtypes:
                    rt_clauses, rt_info = fc.build_resource_type_clauses(resource_types=rtypes)
                    # Wrap as OR group and append
                    grp = fc.or_group(rt_clauses)
                    for g in grp:
                        if g not in lines2:
                            lines2.append(g)
                    components.setdefault("broadened_services", rtypes)
                    changes.append("added_resource_types_from_plan")

            new_filter = "\n".join(lines2)

            history = list(state.get("refinement_history") or [])
            history.append({
                "type": "broaden",
                "changes": changes,
                "reason": "too_few_results",
            })
            updated = state.copy()
            updated.update({
                "current_step": "search_broadened",
                "logging_filter": new_filter,
                "logging_filter_components": components,
                "refinement_history": history,
            })
            return updated
        except Exception as e:
            updated = state.copy()
            updated.update({
                "current_step": "search_broaden_error",
                "error": f"Broaden search failed: {e}",
            })
            return updated
