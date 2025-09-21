"""
Auto-Refine Filters Node (Phase 5 - S)

Adds targeted constraints to reduce overly large result sets using the
planning/decomposition context and architecture repository:

- Prefer adding architecture-safe label clauses (MMM) for planned services
- Apply severity threshold and HTTP status constraints if indicated
- Add content terms from query constraints
- Ensure a reasonable temporal window when missing

Strict behavior: only uses explicit data from state and repository;
no guessing or fallbacks. Clauses are composed with filter_components
(HHH–LLL) and MMM helper.
"""

import logging
from typing import Dict, Any, List, Tuple, Optional

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


class AutoRefineFiltersNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.AutoRefineFiltersNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            project_id = state.get("project_id") or ""
            if not project_id:
                raise ValueError("Missing project_id")

            # Start from current filter and components
            base_filter = state.get("logging_filter") or ""
            lines: List[str] = [l for l in base_filter.split("\n") if l.strip()]
            components: Dict[str, Any] = dict(state.get("logging_filter_components") or {})
            components.setdefault("s_refinements", [])

            changes: List[str] = []

            # Use filter_plan from K if present to target specific services
            stage_services: List[str] = []
            filter_plan = state.get("filter_plan") or []
            if isinstance(filter_plan, list) and filter_plan:
                # Take first stage (most constrained) services
                sids = filter_plan[0].get("services") or []
                stage_services = [sid for sid in sids if isinstance(sid, str) and sid]

            # Load registry for MMM label clauses
            reg = await project_architecture_service.get_service_registry(project_id)
            reg_idx: Dict[str, Dict[str, Any]] = {r.get("service_id"): r for r in reg or [] if r.get("service_id")}

            # MMM: add safe resource.labels constraints for planned services
            label_group: List[str] = []
            if stage_services:
                try:
                    from .. import architecture_specific_filters as mmm
                except Exception:
                    from app.services.agent.core import architecture_specific_filters as mmm
                label_group = mmm.build_label_clauses_for_services(stage_services, reg_idx)
                if label_group:
                    grp = fc.or_group(label_group)
                    for g in grp:
                        if g not in lines:
                            lines.append(g)
                    components["s_refinements"].append({"mmm_labels": label_group})
                    changes.append("added_mmm_labels")

            # Constraints from query decomposition (E)
            decomp = state.get("query_decomposition") or {}
            cons = decomp.get("constraints") or {}

            # Severity (JJJ)
            sev_clause, sev_info = fc.build_severity_clause([cons.get("severity")] if cons.get("severity") else [])
            if sev_clause:
                for c in sev_clause:
                    if c not in lines:
                        lines.append(c)
                components["severity"] = sev_info
                changes.append("added_severity")

            # HTTP status (JJJ) OR-grouped
            st_clauses, st_info = fc.build_http_status_clauses(cons.get("status") or [])
            if st_clauses:
                grp = fc.or_group(st_clauses)
                for g in grp:
                    if g not in lines:
                        lines.append(g)
                components["http_status"] = st_info.get("accepted", [])
                changes.append("added_status")

            # Content terms (KKK) OR-grouped
            kw = [str(k).strip() for k in (cons.get("keywords") or []) if str(k).strip()]
            if kw:
                cont, cont_info = fc.build_content_contains_clauses(kw)
                if cont:
                    grp = fc.or_group(cont)
                    for g in grp:
                        if g not in lines:
                            lines.append(g)
                    components.setdefault("extras", [])
                    for k in cont_info.get("accepted", []):
                        components["extras"].append({"contains": k})
                    changes.append("added_keywords")

            # Temporal window (III): if missing, narrow to '1h'
            if not any(l.startswith("timestamp>") or l.startswith("timestamp<") for l in lines):
                t_clauses, t_info = fc.build_temporal_clauses(window="1h")
                for t in t_clauses:
                    if t not in lines:
                        lines.append(t)
                components["time"] = t_info
                changes.append("added_temporal_window")

            # Build updated filter string
            new_filter = "\n".join(lines)

            history = list(state.get("refinement_history") or [])
            history.append({
                "type": "tighten",
                "changes": changes,
                "reason": "too_many_results",
            })

            updated = state.copy()
            updated.update({
                "current_step": "filters_refined",
                "logging_filter": new_filter,
                "logging_filter_components": components,
                "refinement_history": history,
            })
            return updated
        except Exception as e:
            updated = state.copy()
            updated.update({
                "current_step": "filters_refine_error",
                "error": f"Refinement failed: {e}",
            })
            return updated
