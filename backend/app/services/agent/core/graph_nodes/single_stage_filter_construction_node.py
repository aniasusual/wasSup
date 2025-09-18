"""
Single-Stage Filter Construction Node (Phase 2 - M)

Takes the basic filter produced by the DirectFilterConstructionNode (D)
and strengthens it with a few practical additions in a single pass:

- HTTP status filters from extracted entities
- Resource label guesses from free-form resource identifiers
- Additional text/json contains from resource identifiers when labels are unknown

This node intentionally avoids architecture-specific knowledge (reserved for N).
"""

import logging
from typing import Dict, Any, List, Optional

try:
    from .....models.agent import AgentState, WorkflowConfig
except ImportError:
    import sys, os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
    from app.models.agent import AgentState, WorkflowConfig


logger = logging.getLogger(__name__)


class SingleStageFilterConstructionNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.SingleStageFilterConstructionNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            base_filter = state.get("logging_filter") or ""
            extracted = state.get("extracted_entities") or {}

            new_lines: List[str] = []
            components = dict(state.get("logging_filter_components") or {})
            components.setdefault("http_status", [])
            components.setdefault("identifiers", [])

            # A) HTTP status codes
            http_status = extracted.get("http_status_codes") or []
            status_vals: List[str] = []
            for s in http_status:
                s_str = str(s).strip()
                if not s_str:
                    continue
                # Allow forms like 500, 5xx
                if s_str.endswith("xx") and len(s_str) == 3 and s_str[0].isdigit():
                    # Range 5xx -> 500..599
                    hundreds = int(s_str[0])
                    new_lines.append(f"(httpRequest.status>={(hundreds*100)} AND httpRequest.status<={hundreds*100+99})")
                    status_vals.append(s_str)
                elif s_str.isdigit():
                    new_lines.append(f"httpRequest.status={s_str}")
                    status_vals.append(s_str)
            if status_vals:
                components["http_status"] = status_vals

            # B) Resource identifier hints
            # Try to turn identifier text into resource.labels.<key>="value" or fallback contains
            identifiers = extracted.get("resource_identifiers") or []
            id_added = []
            for ident in identifiers[:5]:
                if not isinstance(ident, str):
                    continue
                ident = ident.strip()
                if not ident:
                    continue
                # Heuristic: if contains '=', treat as key=value
                if '=' in ident and not any(c in ident for c in ' "\'\t'):
                    k, v = ident.split('=', 1)
                    k = k.strip().strip('.').replace('..', '.')
                    v = v.strip(' "')
                    if k and v:
                        # Prefer resource.labels.<k>
                        new_lines.append(f"resource.labels.{k}=\"{v}\"")
                        id_added.append({"label": k, "value": v})
                        continue
                # Fallback to global full-text contains for the identifier
                kv = ident.replace('"', '\\"')
                new_lines.append(f'"{kv}"')
                id_added.append({"contains": ident})
            if id_added:
                components["identifiers"] = id_added

            # Merge with base filter (avoid duplicate empty lines)
            flines: List[str] = [l for l in (base_filter.split("\n") if base_filter else []) if l.strip()]
            for nl in new_lines:
                if nl not in flines:
                    flines.append(nl)
            new_filter = "\n".join(flines)

            updated = state.copy()
            updated.update({
                "current_step": "single_stage_filter_constructed",
                "logging_filter": new_filter,
                "logging_filter_components": components,
            })
            self.logger.info("Single-stage filter constructed")
            return updated
        except Exception as e:
            self.logger.error(f"SingleStageFilterConstructionNode error: {e}")
            updated = state.copy()
            updated.update({
                "current_step": "single_stage_filter_error",
                "error": f"Single-stage filter construction failed: {e}",
            })
            return updated
