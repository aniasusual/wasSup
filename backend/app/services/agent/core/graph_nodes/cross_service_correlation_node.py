"""
Cross-Service Correlation Triggers (Phase 6 - W)

Combines signals from previous analysis nodes (V1–V5) and the
architecture context repository to highlight services that warrant
cross-service investigation. Produces trigger objects consumed by the
automated follow-up stage.
"""

import logging
from collections import Counter
from typing import Any, Dict, List, Optional, Set

try:
    from .....models.agent import AgentState, WorkflowConfig
    from ....project_architecture_service import project_architecture_service
except ImportError:
    import sys
    import os

    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
    from app.models.agent import AgentState, WorkflowConfig
    from app.services.project_architecture_service import project_architecture_service


logger = logging.getLogger(__name__)


class CrossServiceCorrelationNode:
    """Generates cross-service investigation triggers (graph node W)."""

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.CrossServiceCorrelationNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            project_id = state.get("project_id") or ""
            relevant_logs: List[Dict[str, Any]] = list(state.get("relevant_logs") or [])
            findings: List[Dict[str, Any]] = list(state.get("correlation_findings") or [])
            temporal: Dict[str, Any] = state.get("temporal_trends") or {}
            anomalies: List[Dict[str, Any]] = list(state.get("anomalies") or [])
            error_clusters: List[Dict[str, Any]] = list(state.get("error_clusters") or [])
            perf_metrics: Dict[str, Any] = state.get("performance_metrics") or {}
            filter_plan: List[Dict[str, Any]] = list(state.get("filter_plan") or [])

            # Aggregate service signals from logs
            service_counts: Counter[str] = Counter()
            total_logs = len(relevant_logs)
            for entry in relevant_logs:
                svc = self._extract_service(entry)
                if svc:
                    service_counts[svc] += 1

            # Include planned services to avoid losing coverage
            plan_seeds: Set[str] = set()
            for stage in filter_plan:
                for sid in stage.get("services") or []:
                    if isinstance(sid, str) and sid:
                        plan_seeds.add(sid)

            # Collect architecture knowledge: failure patterns help score triggers
            failure_patterns_map: Dict[str, List[str]] = {}
            if project_id:
                try:
                    patterns = await project_architecture_service.get_failure_patterns(project_id)
                    for pattern in patterns or []:
                        sid = pattern.get("service_id") or pattern.get("service")
                        if not sid:
                            continue
                        failure_patterns_map.setdefault(sid, []).append(
                            pattern.get("pattern")
                            or pattern.get("name")
                            or pattern.get("description")
                            or "historical incident"
                        )
                except Exception as fetch_err:  # pragma: no cover - defensive
                    self.logger.debug(f"Failure patterns unavailable: {fetch_err}")

            spikes = [s for s in (temporal.get("spikes") or []) if isinstance(s, dict)]
            spike_hours = [s.get("hour") for s in spikes if s.get("hour")]
            anomaly_types = sorted({a.get("type") for a in anomalies if a.get("type")})

            weight_map: Counter[str] = Counter()
            signal_map: Dict[str, Set[str]] = {}

            for finding in findings:
                services = finding.get("services") or []
                strength = finding.get("strength") or 0.5
                ftype = finding.get("type") or "correlation"
                for svc in services:
                    if not svc:
                        continue
                    weight_map[svc] += max(0.1, float(strength))
                    signal_map.setdefault(svc, set()).add(f"correlation:{ftype}")

            for svc, count in service_counts.items():
                if total_logs:
                    weight_map[svc] += count / total_logs
                else:
                    weight_map[svc] += 0.1
                signal_map.setdefault(svc, set()).add(f"volume:{count}")

            for svc in plan_seeds:
                weight_map[svc] += 0.1
                signal_map.setdefault(svc, set()).add("plan:seed")

            if anomaly_types:
                for svc in set(weight_map.keys()) | set(service_counts.keys()) or plan_seeds:
                    signal_map.setdefault(svc, set()).update({f"anomaly:{atype}" for atype in anomaly_types})
                    weight_map[svc] += 0.1 * len(anomaly_types)

            if perf_metrics.get("error_rate_pct") and perf_metrics.get("error_rate_pct") > 5.0:
                for svc in weight_map:
                    signal_map.setdefault(svc, set()).add("metric:elevated_error_rate")

            triggers: List[Dict[str, Any]] = []
            if weight_map:
                for svc, score in weight_map.most_common(7):
                    signals = sorted(signal_map.get(svc, set()))
                    priority = self._infer_priority(score, signals)
                    reason_parts: List[str] = []
                    if any(sig.startswith("correlation:flow_path") for sig in signals):
                        reason_parts.append("flow path correlations highlight multi-hop impact")
                    if any(sig.startswith("correlation:error_neighbor") for sig in signals):
                        reason_parts.append("neighboring services share error patterns")
                    if any(sig.startswith("anomaly:") for sig in signals):
                        reason_parts.append("anomalies detected in upstream analysis")
                    if not reason_parts:
                        reason_parts.append("service appears prominently across analysis signals")

                    patterns = failure_patterns_map.get(svc) or []
                    if patterns:
                        reason_parts.append(f"historical issues: {patterns[0]}")

                    action = self._suggest_action(signals)
                    trigger = {
                        "service": svc,
                        "score": round(float(score), 2),
                        "priority": priority,
                        "signals": signals,
                        "time_windows": spike_hours[:3],
                        "recommended_action": action,
                        "reason": "; ".join(reason_parts),
                    }
                    triggers.append(trigger)

            # Construct context for downstream nodes
            followup_seeds = list(dict.fromkeys([t.get("service") for t in triggers if t.get("service")]))
            if not followup_seeds:
                followup_seeds = list(plan_seeds) or list(service_counts.keys())[:3]

            global_context = {
                "spike_hours": spike_hours[:5],
                "anomaly_types": anomaly_types,
                "error_cluster_count": len(error_clusters),
                "total_services_observed": len(service_counts),
            }

            analysis = state.get("analysis") or ""
            lines: List[str] = ["", "SECTION: Cross-Service Correlation"]
            if triggers:
                top_services = ", ".join([f"{t['service']} {t['priority']}" for t in triggers[:3]])
                lines.append(f"  - Flagged services: {len(triggers)}")
                lines.append(f"  - Top services: {top_services}")
            else:
                lines.append("  - Outcome: cross-service triggers not generated")
            if spike_hours:
                lines.append(f"  - Peak hours: {', '.join(spike_hours[:3])}")
            if anomaly_types:
                lines.append(f"  - Anomaly types: {', '.join(anomaly_types)}")

            new_analysis = (analysis + "\n" + "\n".join(lines)).strip()

            updated = state.copy()
            tr = dict(updated.get("tool_results") or {})
            tr.update({"phase6_triggers": {"count": len(triggers)}})
            updated.update({
                "current_step": "cross_service_correlation_complete",
                "analysis": new_analysis,
                "cross_service_triggers": triggers,
                "followup_seed_services": followup_seeds,
                "global_correlation_signals": global_context,
                "tool_results": tr,
            })
            return updated
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error(f"CrossServiceCorrelationNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "cross_service_correlation_error",
                "error": f"Cross-service correlation failed: {exc}",
            })
            return updated

    def _extract_service(self, entry: Dict[str, Any]) -> Optional[str]:
        """Best-effort extraction of a service identifier from a log entry."""

        if not entry:
            return None
        # Direct hints first
        for key in ("service", "service_name", "component", "logger"):
            val = entry.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()

        resource = entry.get("resource") or {}
        labels = resource.get("labels") or {}
        for key in (
            "service_name",
            "service",
            "resource_name",
            "container_name",
            "job_name",
            "function_name",
        ):
            val = labels.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()

        json_payload = entry.get("jsonPayload") or {}
        for key in ("service", "serviceName", "component", "sourceService"):
            val = json_payload.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()

        labels = entry.get("labels") or {}
        for key in ("k8s-pod/app", "k8s-pod/component", "app"):
            val = labels.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()

        return None

    def _infer_priority(self, score: float, signals: List[str]) -> str:
        if any(sig.startswith("correlation:flow_path") for sig in signals) or score >= 1.8:
            return "high"
        if any(sig.startswith("anomaly:") for sig in signals) or score >= 1.2:
            return "medium"
        return "low"

    def _suggest_action(self, signals: List[str]) -> str:
        if any(sig.startswith("correlation:flow_path") for sig in signals):
            return "trace_dependency_chain"
        if any(sig.startswith("correlation:error_neighbor") for sig in signals):
            return "compare_neighbor_logs"
        if any(sig.startswith("metric:") for sig in signals):
            return "review_performance_baselines"
        if any(sig.startswith("anomaly:") for sig in signals):
            return "deep_dive_anomalies"
        return "expand_log_scope"
