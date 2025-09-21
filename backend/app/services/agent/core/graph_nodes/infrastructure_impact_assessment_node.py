"""
Infrastructure Impact Assessment (Phase 6 - X2)

Evaluates infrastructure layout information (ZZ/AAA/BBB) to determine
where correlated services co-reside. Highlights shared clusters, regions,
or critical components that may amplify impact.
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


class InfrastructureImpactAssessmentNode:
    """Analyzes infrastructure implications of the current investigation."""

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.InfrastructureImpactAssessmentNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            project_id = state.get("project_id") or ""
            if not project_id:
                raise ValueError("Missing project_id")

            services_in_scope: List[str] = list(
                dict.fromkeys(
                    state.get("followup_dependency_services")
                    or state.get("followup_service_seeds")
                    or []
                )
            )

            infra_layout = await project_architecture_service.get_infrastructure_layout(project_id)
            performance_baselines = await project_architecture_service.get_performance_baselines(project_id)
            failure_patterns = await project_architecture_service.get_failure_patterns(project_id)

            baseline_map = {
                b.get("service_id"): b for b in performance_baselines or [] if b.get("service_id")
            }
            failure_map = {
                f.get("service_id"): f for f in failure_patterns or [] if f.get("service_id")
            }

            impacted_details: List[Dict[str, Any]] = []
            shared_components: Dict[str, Set[str]] = {
                "clusters": set(),
                "regions": set(),
                "environments": set(),
                "networks": set(),
                "datastores": set(),
            }

            component_counter: Counter[str] = Counter()

            for svc in services_in_scope[:10]:
                svc_entries = [e for e in (infra_layout or []) if self._matches_service(e, svc)]
                if not svc_entries:
                    continue

                clusters = sorted({self._value(e, "cluster") for e in svc_entries if self._value(e, "cluster")})
                regions = sorted({self._value(e, "region") or self._value(e, "location") for e in svc_entries if self._value(e, "region") or self._value(e, "location")})
                envs = sorted({self._value(e, "environment") for e in svc_entries if self._value(e, "environment")})
                nets = sorted({self._value(e, "network") for e in svc_entries if self._value(e, "network")})
                stores = sorted({self._value(e, "database") or self._value(e, "storage") for e in svc_entries if self._value(e, "database") or self._value(e, "storage")})
                resource_types = sorted({self._value(e, "resource_type") or self._value(e, "component") for e in svc_entries if self._value(e, "resource_type") or self._value(e, "component")})

                for col, values in (
                    ("clusters", clusters),
                    ("regions", regions),
                    ("environments", envs),
                    ("networks", nets),
                    ("datastores", stores),
                ):
                    for val in values:
                        if val:
                            shared_components[col].add(val)

                for val in resource_types:
                    if val:
                        component_counter[val] += 1

                baseline = baseline_map.get(svc) or {}
                failure = failure_map.get(svc) or {}

                impacted_details.append({
                    "service": svc,
                    "clusters": clusters,
                    "regions": regions,
                    "environments": envs,
                    "networks": nets,
                    "datastores": stores,
                    "resource_types": resource_types,
                    "baseline": {
                        "p95_latency_ms": baseline.get("p95_latency_ms"),
                        "error_rate_pct": baseline.get("error_rate_pct"),
                    },
                    "historical_failure": failure.get("pattern") or failure.get("description"),
                })

            shared_summary = {
                "clusters": sorted(shared_components["clusters"]),
                "regions": sorted(shared_components["regions"]),
                "environments": sorted(shared_components["environments"]),
                "networks": sorted(shared_components["networks"]),
                "datastores": sorted(shared_components["datastores"]),
                "common_resource_types": [k for k, v in component_counter.most_common() if v > 1],
            }

            analysis = state.get("analysis") or ""
            lines: List[str] = ["", "SECTION: Infrastructure Impact Assessment"]
            if impacted_details:
                lines.append(f"  - Impacted services with infra context: {len(impacted_details)}")
                if shared_summary["clusters"]:
                    lines.append(f"  - Shared clusters: {', '.join(shared_summary['clusters'][:3])}")
                if shared_summary["regions"]:
                    lines.append(f"  - Regions involved: {', '.join(shared_summary['regions'][:3])}")
            else:
                lines.append("  - Outcome: no infrastructure metadata available for focused services")

            new_analysis = (analysis + "\n" + "\n".join(lines)).strip()

            impact_payload = {
                "services": impacted_details,
                "shared": shared_summary,
                "summary": lines[1:] if len(lines) > 1 else [],
            }

            updated = state.copy()
            tr = dict(updated.get("tool_results") or {})
            tr.update({"phase6_infrastructure": {"services": len(impacted_details)}})
            updated.update({
                "current_step": "infrastructure_impact_assessed",
                "analysis": new_analysis,
                "infrastructure_impact": impact_payload,
                "tool_results": tr,
            })
            return updated
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error(f"InfrastructureImpactAssessmentNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "infrastructure_impact_error",
                "error": f"Infrastructure impact assessment failed: {exc}",
            })
            return updated

    def _matches_service(self, entry: Dict[str, Any], service: str) -> bool:
        if not entry or not service:
            return False
        for key in ("service_id", "service", "name", "component"):
            val = entry.get(key)
            if isinstance(val, str) and val.strip().lower() == service.lower():
                return True
        labels = entry.get("labels") or {}
        for key, val in labels.items():
            if isinstance(val, str) and val.strip().lower() == service.lower():
                return True
        return False

    def _value(self, entry: Dict[str, Any], key: str) -> Optional[str]:
        if not entry:
            return None
        val = entry.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
        labels = entry.get("labels") or {}
        val = labels.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
        return None
