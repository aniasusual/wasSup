"""
Direct Filter Construction Node (Phase 2 - D)

Builds a simple Google Cloud Logging filter from the current agent state.
This is the first step in the filter pipeline (D), prior to single-stage and
context-aware enhancements (M, N, O).
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

try:
    from .....models.agent import AgentState, WorkflowConfig
except ImportError:
    import sys, os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
    from app.models.agent import AgentState, WorkflowConfig


logger = logging.getLogger(__name__)


_SEVERITY_ORDER = [
    "DEFAULT",
    "DEBUG",
    "INFO",
    "NOTICE",
    "WARNING",
    "ERROR",
    "CRITICAL",
    "ALERT",
    "EMERGENCY",
]
_SEVERITY_INDEX = {s: i for i, s in enumerate(_SEVERITY_ORDER)}


class DirectFilterConstructionNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.DirectFilterConstructionNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            extracted = state.get("extracted_entities") or {}
            project_id = state.get("project_id") or ""

            filter_lines: List[str] = []
            components: Dict[str, Any] = {
                "resource_types": [],
                "severity": None,
                "time": None,
                "extras": [],
            }

            # 1) resource.type and label hints via Filter Components (HHH)
            try:
                from .. import filter_components as fc  # relative import within core
            except Exception:
                from app.services.agent.core import filter_components as fc

            candidate_types: List[str] = fc.derive_resource_types_from_state(state)
            # Resolve canonical resource types strictly via LLM (no local aliases)
            try:
                from ..llm_service import LLMService
            except Exception:
                from app.services.agent.core.llm_service import LLMService
            llm = LLMService()
            canonical_types: List[str] = []
            if candidate_types:
                # Raise if LLM unavailable as per instruction (no fallbacks)
                canonical_types = await fc.canonicalize_resource_types_via_llm(candidate_types, llm_service=llm)

            # Optional service name hints (type,name) derived from architecture context
            service_name_hints: List[tuple] = []
            arch = state.get("architecture_context") or {}
            for svc in arch.get("parsed_services", []) or []:
                if isinstance(svc, dict):
                    st = svc.get("type") or svc.get("name")
                    nm = svc.get("service_name") or svc.get("name")
                    if st and nm:
                        service_name_hints.append((st, nm))
            rt_clauses, rt_info = fc.build_resource_type_clauses(
                resource_types=canonical_types,
                service_names=service_name_hints,
            )
            if rt_clauses:
                filter_lines.extend(rt_clauses)
            components["resource_types"] = rt_info.get("resource_types", [])
            if rt_info.get("labels"):
                components.setdefault("context_labels", [])
                components["context_labels"].extend(rt_info["labels"]) 

            # 2) severity and http status (JJJ)
            sev_input: List[str] = list(extracted.get("severities") or [])
            if sev_input:
                sev_clause, sev_info = fc.build_severity_clause(sev_input)
                if sev_clause:
                    filter_lines.extend(sev_clause)
                    components["severity"] = {"threshold": sev_info.get("selected"), "provided": sev_info.get("provided")}
            http_input: List[str] = list(extracted.get("http_status_codes") or [])
            if http_input:
                http_clauses, http_info = fc.build_http_status_clauses(http_input)
                if http_clauses:
                    # Multiple status clauses should be OR-ed, not AND-ed
                    grouped = fc.or_group(http_clauses)
                    filter_lines.extend(grouped)
                    components.setdefault("http_status", [])
                    components["http_status"] = http_info.get("accepted", [])

            # 3) time from extracted time_indicators (III)
            time_inds = [str(t).strip() for t in (extracted.get("time_indicators") or []) if str(t).strip()]
            if time_inds:
                try:
                    t_clauses, t_info = fc.build_temporal_clauses_from_indicators(time_inds)
                    filter_lines.extend(t_clauses)
                    components["time"] = {"indicator": t_info.get("indicator"), "from": t_info.get("start_time")}
                except Exception as te:
                    # Strict behavior: if indicators are unsupported, surface an error
                    raise te

            # 4) extras: error patterns / keywords as text search (KKK)
            # Use global full-text search (quoted phrases) with a small cap
            keywords = (extracted.get("keywords") or []) + (extracted.get("error_patterns") or [])
            keywords = [k for k in keywords if isinstance(k, str) and k.strip()]
            if keywords:
                contains_clauses, contains_info = fc.build_content_contains_clauses(keywords, max_items=3)
                if contains_clauses:
                    # Content matches should be OR-ed to avoid over-constraining
                    grouped = fc.or_group(contains_clauses)
                    filter_lines.extend(grouped)
                    components.setdefault("extras", [])
                    for k in contains_info.get("accepted", []):
                        components["extras"].append({"contains": k})

            # Join lines (newline-separated for readability)
            filter_str = "\n".join(filter_lines)

            updated = state.copy()
            updated.update({
                "current_step": "direct_filter_constructed",
                "logging_filter": filter_str,
                "logging_filter_components": components,
                "order_by": "timestamp desc",
            })

            self.logger.info("Direct filter constructed")
            return updated
        except Exception as e:
            self.logger.error(f"DirectFilterConstructionNode error: {e}")
            updated = state.copy()
            updated.update({
                "current_step": "direct_filter_error",
                "error": f"Direct filter construction failed: {e}",
            })
            return updated

    def _simple_contains(self, keyword: str) -> str:
        # Deprecated in favor of filter_components.build_content_contains_clauses
        k = keyword.replace('"', '\\"')
        return f'"{k}"'
