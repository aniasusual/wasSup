"""
Resource Utilization Correlation (Phase 6 - X3)

Correlates resource usage patterns from the current log sample with
performance baselines and investigation signals. Highlights services and
resource types that exhibit heightened load or degradation.
"""

import logging
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

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


class ResourceUtilizationCorrelationNode:
    """Analyzes resource utilization correlations for Phase 6 node X3."""

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.ResourceUtilizationCorrelationNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            project_id = state.get("project_id") or ""
            relevant_logs: List[Dict[str, Any]] = list(state.get("relevant_logs") or [])
            total_logs = len(relevant_logs)

            seeds = set(
                state.get("followup_dependency_services")
                or state.get("followup_service_seeds")
                or []
            )

            perf_metrics = state.get("performance_metrics") or {}
            anomalies = list(state.get("anomalies") or [])

            baselines = await project_architecture_service.get_performance_baselines(project_id) if project_id else []
            baseline_map = {
                b.get("service_id"): b for b in baselines or [] if b.get("service_id")
            }

            counter: Counter[Tuple[Optional[str], str]] = Counter()
            for entry in relevant_logs:
                service = self._extract_service(entry)
                resource_type = self._extract_resource_type(entry)
                counter[(service, resource_type)] += 1

            correlations: List[Dict[str, Any]] = []
            if total_logs:
                for (service, resource_type), count in counter.items():
                    if seeds and service and service not in seeds:
                        continue
                    log_share = (count / total_logs) * 100.0
                    indicators = self._derive_indicators(
                        service,
                        resource_type,
                        log_share,
                        perf_metrics,
                        baseline_map.get(service) if service else None,
                        anomalies,
                    )
                    if not indicators and log_share < 20.0:
                        continue
                    confidence = min(0.9, 0.35 + 0.1 * len(indicators) + (log_share / 100.0) * 0.5)
                    correlations.append({
                        "service": service,
                        "resource_type": resource_type,
                        "log_share_pct": round(log_share, 2),
                        "count": count,
                        "indicators": indicators or ["elevated_log_volume"],
                        "confidence": round(confidence, 2),
                    })

            correlations.sort(key=lambda item: (-item["confidence"], -item["log_share_pct"]))

            analysis = state.get("analysis") or ""
            lines: List[str] = ["", "SECTION: Resource Utilization Correlation"]
            if correlations:
                lines.append(f"  - Correlated resources: {len(correlations)}")
                top = ", ".join(
                    [f"{c['service'] or 'shared'}:{c['resource_type']}" for c in correlations[:3]]
                )
                lines.append(f"  - Top correlations: {top}")
            else:
                lines.append("  - Outcome: significant resource correlations not detected")

            new_analysis = (analysis + "\n" + "\n".join(lines)).strip()

            updated = state.copy()
            tr = dict(updated.get("tool_results") or {})
            tr.update({"phase6_resource_correlations": {"count": len(correlations)}})
            updated.update({
                "current_step": "resource_utilization_correlation_complete",
                "analysis": new_analysis,
                "resource_correlation_insights": correlations,
                "tool_results": tr,
            })
            return updated
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error(f"ResourceUtilizationCorrelationNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "resource_utilization_correlation_error",
                "error": f"Resource utilization correlation failed: {exc}",
            })
            return updated

    def _extract_service(self, entry: Dict[str, Any]) -> Optional[str]:
        for key in ("service", "service_name", "component"):
            val = entry.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
        resource = entry.get("resource") or {}
        labels = resource.get("labels") or {}
        for key in ("service_name", "service", "job_name", "container_name"):
            val = labels.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
        json_payload = entry.get("jsonPayload") or {}
        for key in ("service", "serviceName"):
            val = json_payload.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
        return None

    def _extract_resource_type(self, entry: Dict[str, Any]) -> str:
        resource = entry.get("resource") or {}
        rtype = resource.get("type")
        if isinstance(rtype, str) and rtype.strip():
            return rtype.strip()
        return "unknown"

    def _derive_indicators(
        self,
        service: Optional[str],
        resource_type: str,
        log_share: float,
        perf_metrics: Dict[str, Any],
        baseline: Optional[Dict[str, Any]],
        anomalies: List[Dict[str, Any]],
    ) -> List[str]:
        indicators: List[str] = []

        error_rate = perf_metrics.get("error_rate_pct")
        if baseline and isinstance(error_rate, (int, float)):
            baseline_error = baseline.get("error_rate_pct")
            if isinstance(baseline_error, (int, float)) and error_rate > baseline_error * 1.3 + 1.0:
                indicators.append("error_rate_above_baseline")

        latency = perf_metrics.get("p95_ms")
        if baseline and isinstance(latency, (int, float)):
            baseline_latency = baseline.get("p95_latency_ms")
            if isinstance(baseline_latency, (int, float)) and latency > baseline_latency * 1.5 + 150:
                indicators.append("latency_spike_vs_baseline")

        if log_share >= 35.0:
            indicators.append("dominant_log_volume")
        elif log_share >= 20.0:
            indicators.append("elevated_log_volume")

        for anomaly in anomalies:
            atype = anomaly.get("type")
            if atype in {"latency", "error_rate"}:
                indicators.append(f"linked_anomaly:{atype}")
                break

        return indicators
