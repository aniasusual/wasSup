"""
Filter Validation & Optimization Node (Phase 2 - O)

Validates and optimizes the accumulated Logging filter string:
- Deduplicate and normalize lines
- Merge multiple resource.type lines into a single ( ... OR ... ) group
- Remove empty/invalid clauses
- Ensure a sane default order_by (if not present upstream)
Outputs the optimized filter back into state.logging_filter and an
optimization report in state.logging_filter_optimization.
"""

import logging
import re
from typing import Dict, Any, List, Optional

try:
    from .....models.agent import AgentState, WorkflowConfig
except ImportError:
    import sys, os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
    from app.models.agent import AgentState, WorkflowConfig


logger = logging.getLogger(__name__)


class FilterValidationOptimizationNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.FilterValidationOptimizationNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            raw = state.get("logging_filter") or ""
            lines = [l.strip() for l in raw.split("\n") if l.strip()]
            before_count = len(lines)

            # Deduplicate
            deduped: List[str] = []
            seen = set()
            for l in lines:
                if l not in seen:
                    deduped.append(l)
                    seen.add(l)

            # Extract resource.type clauses and merge
            rt_pat = re.compile(r'^resource\.type=\"([^\"]+)\"$')
            resource_types: List[str] = []
            others: List[str] = []
            for l in deduped:
                m = rt_pat.match(l)
                if m:
                    resource_types.append(m.group(1))
                else:
                    others.append(l)
            resource_types = list(dict.fromkeys(resource_types))  # preserve order, unique
            if len(resource_types) == 1:
                merged_rt = [f'resource.type="{resource_types[0]}"']
            elif len(resource_types) > 1:
                merged_rt = ["(" + " OR ".join([f'resource.type="{rt}"' for rt in resource_types]) + ")"]
            else:
                merged_rt = []

            # Remove empty parens or dup parens
            def valid_clause(s: str) -> bool:
                if s == "()":
                    return False
                return True

            final_lines = [l for l in (merged_rt + others) if valid_clause(l)]

            # Normalize multiple spaces around operators
            norm_lines = [re.sub(r'\s+', ' ', l).strip() for l in final_lines]

            after_count = len(norm_lines)
            optimized_filter = "\n".join(norm_lines)

            # Update order_by default if missing in state
            order_by = state.get("order_by") or "timestamp desc"

            report = {
                "line_count_before": before_count,
                "line_count_after": after_count,
                "merged_resource_types": resource_types,
                "changed": optimized_filter != raw,
            }

            updated = state.copy()
            updated.update({
                "current_step": "filter_optimized",
                "logging_filter": optimized_filter,
                "order_by": order_by,
                "logging_filter_optimization": report,
            })
            self.logger.info("Filter validated and optimized")
            return updated
        except Exception as e:
            self.logger.error(f"FilterValidationOptimizationNode error: {e}")
            updated = state.copy()
            updated.update({
                "current_step": "filter_optimization_error",
                "error": f"Filter optimization failed: {e}",
            })
            return updated

