"""
Context-Enhanced Filter Builder (Phase 4 - L)

Converts the multi-stage filter planning blueprint (from K) into concrete
Google Cloud Logging filter strings using the filter component helpers
(HHH–LLL) and service metadata from the repository (XX).

Behavior:
- For each stage in `filter_plan`, build an AND-group of clauses:
  resource.type (+labels when available), temporal window, severity threshold,
  http status codes (OR-grouped), and content terms (OR-grouped).
- Combine stages as an OR-group of stage AND-groups.

Outputs:
- state.logging_filter (string)
- state.logging_filter_components (structured breakdown)
- current_step: "context_enhanced_filter_built"
"""

import logging
from typing import Dict, Any, List, Optional, Tuple

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


class ContextEnhancedFilterBuilderNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.ContextEnhancedFilterBuilderNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            project_id = state.get("project_id") or ""
            if not project_id:
                raise ValueError("Missing project_id")

            filter_plan: List[Dict[str, Any]] = list(state.get("filter_plan") or [])
            if not filter_plan:
                raise ValueError("Missing filter_plan from planning step")

            # Load service registry to resolve service_id -> resource_type / labels
            registry = await project_architecture_service.get_service_registry(project_id)
            reg_idx: Dict[str, Dict[str, Any]] = {r.get("service_id"): r for r in registry or [] if r.get("service_id")}

            stage_groups: List[str] = []
            components: Dict[str, Any] = {"stages": []}

            for stage in filter_plan:
                sids: List[str] = stage.get("services") or []
                if not sids:
                    continue

                # HHH: resource types and labels
                res_types: List[str] = []
                label_pairs: List[Tuple[str, str]] = []
                for sid in sids:
                    r = reg_idx.get(sid) or {}
                    rt = r.get("resource_type")
                    if rt and rt not in res_types:
                        res_types.append(rt)
                    # Labels in registry can hint at resource.labels for specific services
                    labels = r.get("resource_labels") or {}
                    name = r.get("name") or None  # not guaranteed
                    # Only add safe, known labels directly if present
                    for lk, lv in labels.items():
                        # The build_resource_type_clauses helper accepts service_names (type,name) hints; labels we keep separately
                        pass

                # Build resource type OR group
                rt_clauses, rt_info = fc.build_resource_type_clauses(resource_types=res_types, service_names=None)

                # MMM: architecture-specific label clauses from registry labels
                try:
                    from .. import architecture_specific_filters as mmm
                except Exception:
                    from app.services.agent.core import architecture_specific_filters as mmm
                label_clauses = mmm.build_label_clauses_for_services(sids, reg_idx)
                if label_clauses:
                    label_clauses = fc.or_group(label_clauses)

                # III: temporal window
                t_clauses: List[str] = []
                t_info: Dict[str, Any] = {}
                if stage.get("temporal_window"):
                    tw = str(stage.get("temporal_window")).strip()
                    t_clauses, t_info = fc.build_temporal_clauses(window=tw)

                # JJJ: severity + status codes
                sev_clauses, sev_info = fc.build_severity_clause([stage.get("severity_threshold")] if stage.get("severity_threshold") else [])
                http_clauses, http_info = fc.build_http_status_clauses(stage.get("status_codes") or [])
                if http_clauses:
                    http_clauses = fc.or_group(http_clauses)

                # KKK: content terms (quoted) OR-grouped
                content_clauses, content_info = fc.build_content_contains_clauses(stage.get("content_terms") or [], max_items=None)
                if content_clauses:
                    content_clauses = fc.or_group(content_clauses)

                # AND all parts for this stage, skipping empties
                and_parts: List[str] = []
                for part in [rt_clauses, label_clauses, t_clauses, sev_clauses, http_clauses, content_clauses]:
                    if not part:
                        continue
                    if isinstance(part, list):
                        and_parts.extend([p for p in part if p])
                stage_group = fc.and_group(and_parts)
                if stage_group:
                    stage_groups.extend(stage_group)

                # Collect components per stage for diagnostics/UI
                components["stages"].append({
                    "services": sids,
                    "resource_types": rt_info.get("resource_types", []),
                    "mmm_labels": label_clauses or None,
                    "temporal": t_info or None,
                    "severity": sev_info or None,
                    "status": http_info or None,
                    "content": content_info or None,
                })

            # OR all stage groups together as final filter
            final_groups = fc.or_group(stage_groups)
            filter_str = "\n".join(final_groups) if final_groups else ""

            updated = state.copy()
            updated.update({
                "current_step": "context_enhanced_filter_built",
                "logging_filter": filter_str,
                "logging_filter_components": components,
                "order_by": state.get("order_by") or "timestamp desc",
            })
            self.logger.info("Context-enhanced filter built")
            return updated
        except Exception as e:
            self.logger.error(f"ContextEnhancedFilterBuilderNode error: {e}")
            updated = state.copy()
            updated.update({
                "current_step": "context_enhanced_filter_build_error",
                "error": f"Context-enhanced filter builder failed: {e}",
            })
            return updated
