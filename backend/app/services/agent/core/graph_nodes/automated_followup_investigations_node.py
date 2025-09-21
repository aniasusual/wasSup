"""
Automated Follow-up Investigations (Phase 6 - X)

Transforms cross-service triggers into concrete investigation tasks that
subsequent nodes (X1–X3) will enrich. Also propagates contextual
information such as time windows and anomaly types.
"""

import logging
from typing import Any, Dict, List, Optional, Set

try:
    from .....models.agent import AgentState, WorkflowConfig
except ImportError:
    import sys
    import os

    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
    from app.models.agent import AgentState, WorkflowConfig


logger = logging.getLogger(__name__)


class AutomatedFollowupInvestigationsNode:
    """Plans automated follow-up investigations based on triggers (node X)."""

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.AutomatedFollowupInvestigationsNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            triggers: List[Dict[str, Any]] = list(state.get("cross_service_triggers") or [])
            findings: List[Dict[str, Any]] = list(state.get("correlation_findings") or [])
            anomalies: List[Dict[str, Any]] = list(state.get("anomalies") or [])
            global_signals: Dict[str, Any] = state.get("global_correlation_signals") or {}

            spike_hours = list(global_signals.get("spike_hours") or [])
            anomaly_types = list(global_signals.get("anomaly_types") or [])

            followups: List[Dict[str, Any]] = []
            seen_keys: Set[str] = set()
            seeds: List[str] = list(dict.fromkeys(state.get("followup_seed_services") or []))

            def add_followup(payload: Dict[str, Any]) -> None:
                key = f"{payload.get('service')}|{payload.get('action')}"
                if key in seen_keys:
                    return
                seen_keys.add(key)
                followups.append(payload)

            # Convert triggers directly into actionable follow-ups
            for idx, trigger in enumerate(triggers, start=1):
                service = trigger.get("service")
                if not service:
                    continue
                action = self._map_action(trigger.get("signals") or [])
                payload = {
                    "id": f"auto-{idx}",
                    "service": service,
                    "priority": trigger.get("priority") or "medium",
                    "action": action,
                    "signals": trigger.get("signals") or [],
                    "time_focus": trigger.get("time_windows") or spike_hours[:2],
                    "notes": trigger.get("reason"),
                    "recommended_next": trigger.get("recommended_action"),
                }
                add_followup(payload)
                if service not in seeds:
                    seeds.append(service)

            # Flow-path correlations spawn dependency tracing tasks
            path_findings = [f for f in findings if f.get("type") == "flow_path_correlation"]
            for idx, path in enumerate(path_findings, start=len(followups) + 1):
                services = path.get("services") or []
                if len(services) < 2:
                    continue
                primary = services[0]
                payload = {
                    "id": f"path-{idx}",
                    "service": primary,
                    "priority": "high",
                    "action": "trace_multi_hop_path",
                    "signals": ["correlation:flow_path"],
                    "time_focus": spike_hours[:2],
                    "notes": f"Flow path {path.get('path_id') or 'sequence'} spans {len(services)} services",
                    "related_services": services,
                }
                add_followup(payload)
                for svc in services:
                    if svc not in seeds:
                        seeds.append(svc)

            # Significant anomalies merit dedicated deep dives
            for idx, anomaly in enumerate(anomalies, start=len(followups) + 1):
                priority = "high" if anomaly.get("type") in {"latency", "error_rate"} else "medium"
                target_service = seeds[0] if seeds else None
                payload = {
                    "id": f"anomaly-{idx}",
                    "service": target_service,
                    "priority": priority,
                    "action": "deep_dive_anomaly",
                    "signals": [f"anomaly:{anomaly.get('type')}"] if anomaly.get("type") else [],
                    "time_focus": spike_hours[:2],
                    "notes": anomaly.get("note"),
                }
                add_followup(payload)

            followup_context = {
                "spike_hours": spike_hours[:3],
                "anomaly_types": anomaly_types,
                "path_count": len(path_findings),
            }

            analysis = state.get("analysis") or ""
            lines: List[str] = ["", "SECTION: Automated Follow-up Investigations"]
            if followups:
                top = ", ".join(
                    [f"{f['service'] or 'global'}->{f['action']}" for f in followups[:3]]
                )
                lines.append(f"  - Generated tasks: {len(followups)}")
                lines.append(f"  - Top tasks: {top}")
            else:
                lines.append("  - Outcome: automated follow-up tasks not generated")
            if spike_hours:
                lines.append(f"  - Focus hours: {', '.join(spike_hours[:2])}")
            if anomaly_types:
                lines.append(f"  - Anomaly focus: {', '.join(anomaly_types)}")

            new_analysis = (analysis + "\n" + "\n".join(lines)).strip()

            updated = state.copy()
            tr = dict(updated.get("tool_results") or {})
            tr.update({"phase6_followups": {"count": len(followups)}})
            updated.update({
                "current_step": "automated_followup_planned",
                "analysis": new_analysis,
                "auto_followup_investigations": followups,
                "followup_service_seeds": seeds,
                "followup_context": followup_context,
                "tool_results": tr,
            })
            return updated
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error(f"AutomatedFollowupInvestigationsNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "automated_followup_error",
                "error": f"Automated follow-up planning failed: {exc}",
            })
            return updated

    def _map_action(self, signals: List[str]) -> str:
        if any(sig.startswith("correlation:flow_path") for sig in signals):
            return "trace_multi_hop_path"
        if any(sig.startswith("correlation:error_neighbor") for sig in signals):
            return "inspect_neighbor_services"
        if any(sig.startswith("metric:") for sig in signals):
            return "compare_against_baselines"
        if any(sig.startswith("anomaly:") for sig in signals):
            return "deep_dive_anomaly"
        return "expand_log_scope"
