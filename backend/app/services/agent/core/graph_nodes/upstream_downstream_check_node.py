"""
Upstream/Downstream Check (Phase 5 - U1)

Translates discovered resources from U into concrete filter expansions:

- OR-in resource.type clauses for discovered `service_id`s (from XX)
- Add architecture-specific label clauses (MMM) when available
- Ensure a reasonable temporal window if none exists (e.g., 6h)

Strict behavior: only uses repository and discovered_resources; no guessing.
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


class UpstreamDownstreamCheckNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.UpstreamDownstreamCheckNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            project_id = state.get("project_id") or ""
            if not project_id:
                raise ValueError("Missing project_id")

            discovered = state.get("discovered_resources") or []
            if not isinstance(discovered, list) or not discovered:
                updated = state.copy()
                updated.update({
                    "current_step": "up_downstream_checked",
                    "up_downstream_checked": False,
                })
                return updated

            # Collect service_ids from discovery
            service_ids: List[str] = []
            for d in discovered:
                sid = (d or {}).get("service_id")
                if isinstance(sid, str) and sid and sid not in service_ids:
                    service_ids.append(sid)

            # Resolve resource types from registry (XX)
            registry = await project_architecture_service.get_service_registry(project_id)
            reg_idx: Dict[str, Dict[str, Any]] = {r.get("service_id"): r for r in registry or [] if r.get("service_id")}
            rtypes: List[str] = []
            for sid in service_ids:
                rt = (reg_idx.get(sid) or {}).get("resource_type")
                if rt and rt not in rtypes:
                    rtypes.append(rt)

            # Start from current filter
            base_filter = state.get("logging_filter") or ""
            lines: List[str] = [l for l in base_filter.split("\n") if l.strip()]
            components: Dict[str, Any] = dict(state.get("logging_filter_components") or {})
            components.setdefault("u1_expansions", {})

            # Add resource.type OR-group
            if rtypes:
                rt_clauses, rt_info = fc.build_resource_type_clauses(resource_types=rtypes)
                grp = fc.or_group(rt_clauses)
                for g in grp:
                    if g not in lines:
                        lines.append(g)
                components["u1_expansions"]["resource_types"] = rt_info.get("resource_types", [])

            # Add MMM label OR-group for these services
            try:
                from .. import architecture_specific_filters as mmm
            except Exception:
                from app.services.agent.core import architecture_specific_filters as mmm
            lbls = mmm.build_label_clauses_for_services(service_ids, reg_idx)
            if lbls:
                grp = fc.or_group(lbls)
                for g in grp:
                    if g not in lines:
                        lines.append(g)
                components["u1_expansions"]["mmm_labels"] = lbls

            # Ensure a temporal window if none is present (e.g., '6h' for discovery)
            if not any(l.startswith("timestamp>") or l.startswith("timestamp<") for l in lines):
                t_clauses, t_info = fc.build_temporal_clauses(window="6h")
                for t in t_clauses:
                    if t not in lines:
                        lines.append(t)
                components["time"] = t_info

            new_filter = "\n".join(lines)

            updated = state.copy()
            updated.update({
                "current_step": "up_downstream_checked",
                "up_downstream_checked": True,
                "logging_filter": new_filter,
                "logging_filter_components": components,
            })
            return updated
        except Exception as e:
            updated = state.copy()
            updated.update({
                "current_step": "up_downstream_check_error",
                "error": f"Upstream/Downstream check failed: {e}",
            })
            return updated
