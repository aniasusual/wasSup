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

            # 1) resource.type from extracted services (keys like "resource.type=cloud_run_revision")
            services = extracted.get("services") or {}
            resource_types: List[str] = []
            for key in services.keys():
                if key.startswith("resource.type="):
                    rtype = key.split("=", 1)[1]
                    if rtype:
                        resource_types.append(rtype)
            # If user provided services list in state, include those too
            user_services = state.get("services") or []
            for s in user_services:
                if s and s not in resource_types:
                    resource_types.append(s)
            # Deduplicate and build OR lines if multiple
            resource_types = list(dict.fromkeys(resource_types))
            if len(resource_types) == 1:
                filter_lines.append(f"resource.type=\"{resource_types[0]}\"")
            elif len(resource_types) > 1:
                ors = " OR ".join([f"resource.type=\"{rt}\"" for rt in resource_types])
                filter_lines.append(f"({ors})")
            components["resource_types"] = resource_types

            # 2) severity from extracted
            severities: List[str] = (extracted.get("severities") or [])
            severities = [s.upper() for s in severities if isinstance(s, str)]
            severities = [s for s in severities if s in _SEVERITY_INDEX]
            if severities:
                # Choose least severe (broadest) among provided → severity>=that
                min_sev = min(severities, key=lambda s: _SEVERITY_INDEX[s])
                filter_lines.append(f"severity>={min_sev}")
                components["severity"] = {"threshold": min_sev, "provided": severities}

            # 3) time from extracted time_indicators
            time_indicator = None
            for ti in (extracted.get("time_indicators") or []):
                t = str(ti).lower().strip()
                if t:
                    time_indicator = t
                    break
            if time_indicator:
                start_ts = self._time_indicator_to_start(time_indicator)
                if start_ts:
                    filter_lines.append(f"timestamp>\"{start_ts}\"")
                    components["time"] = {"indicator": time_indicator, "from": start_ts}

            # 4) extras: error patterns / keywords as text search (simple contains)
            # Use unified full-text search to avoid invalid nested field matches.
            keywords = (extracted.get("keywords") or []) + (extracted.get("error_patterns") or [])
            keywords = [k for k in keywords if isinstance(k, str) and k.strip()]
            # Only add a couple to avoid overconstraining
            for k in keywords[:3]:
                filter_lines.append(f"{self._simple_contains(k)}")
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

    def _time_indicator_to_start(self, indicator: str) -> Optional[str]:
        now = datetime.utcnow()
        if indicator in ("last_hour", "recent"):
            start = now - timedelta(hours=1)
        elif indicator in ("last_day", "24h"):
            start = now - timedelta(days=1)
        elif indicator in ("last_7_days", "7d"):
            start = now - timedelta(days=7)
        else:
            return None
        return start.isoformat() + "Z"

    def _simple_contains(self, keyword: str) -> str:
        # Escaping quotes inside keyword for safety
        k = keyword.replace('"', '\\"')
        # Use two common payload fields for a basic text match
        # Use global full-text search (quoted phrase) across payloads and fields
        return f'"{k}"'
