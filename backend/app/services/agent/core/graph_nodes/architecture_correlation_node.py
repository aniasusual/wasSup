"""
Architecture-Based Correlation Engine (Phase 6 - V4)

Correlates signals across services using:
  - Temporal spikes (V1)
  - Error clusters (V2)
  - Performance metrics (V3)
  - Anomalies (V5)
and the Architecture Context Repository (WW/YY/ZZ/AAA/BBB).

Produces a list of correlation findings to guide follow-up investigations.
"""

import logging
from typing import Dict, Any, List, Optional, Set

try:
    from .....models.agent import AgentState, WorkflowConfig
    from ....project_architecture_service import project_architecture_service
except ImportError:
    import sys, os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
    from app.models.agent import AgentState, WorkflowConfig
    from app.services.project_architecture_service import project_architecture_service


logger = logging.getLogger(__name__)


class ArchitectureCorrelationNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.ArchitectureCorrelationNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            project_id = state.get("project_id") or ""
            if not project_id:
                raise ValueError("Missing project_id")

            # Gather prior analysis signals
            temporal = state.get("temporal_trends") or {}
            clusters = state.get("error_clusters") or []
            perf = state.get("performance_metrics") or {}
            anomalies = state.get("anomalies") or []

            # Repository data
            topo = await project_architecture_service.get_topology_map(project_id)
            deps = topo.get("dependencies") or []
            flows = await project_architecture_service.get_data_flow_patterns(project_id)

            # Build quick helper maps
            down: Dict[str, List[str]] = {}
            up: Dict[str, List[str]] = {}
            for d in deps:
                a = d.get("from_service_id")
                b = d.get("to_service_id")
                if not a or not b:
                    continue
                down.setdefault(a, []).append(b)
                up.setdefault(b, []).append(a)

            def neighbors(sid: str) -> List[str]:
                return list(set((down.get(sid, []) + up.get(sid, []))))

            findings: List[Dict[str, Any]] = []

            # 1) Temporal spikes imply correlation windows
            spikes = (temporal.get("spikes") or []) if isinstance(temporal, dict) else []
            if spikes:
                findings.append({
                    "type": "temporal_spike_window",
                    "services": [],
                    "time_windows": [{"hour": s.get("hour"), "count": s.get("count")} for s in spikes],
                    "strength": 0.5 + min(0.5, len(spikes) * 0.1),
                })

            # 2) Error clusters hint at affected services via neighbors of anchors/plan
            seed_services: Set[str] = set()
            plan = state.get("filter_plan") or []
            if isinstance(plan, list) and plan:
                for sid in (plan[0].get("services") or []):
                    if isinstance(sid, str):
                        seed_services.add(sid)
            decomp = state.get("query_decomposition") or {}
            for sid in (decomp.get("anchors") or []):
                if isinstance(sid, str):
                    seed_services.add(sid)
            for sid in (decomp.get("flow_hint") or []):
                if isinstance(sid, str):
                    seed_services.add(sid)

            if clusters and seed_services:
                corr_svcs: Set[str] = set()
                for s in seed_services:
                    for nb in neighbors(s):
                        corr_svcs.add(nb)
                if corr_svcs:
                    findings.append({
                        "type": "error_neighbor_correlation",
                        "services": list(corr_svcs),
                        "signals": [c.get("name") for c in clusters[:3] if c.get("name")],
                        "strength": 0.6,
                    })

            # 3) Performance anomalies increase correlation weight
            if anomalies:
                kinds = {a.get("type") for a in anomalies}
                if "latency" in kinds or "error_rate" in kinds:
                    findings.append({
                        "type": "performance_anomaly_correlation",
                        "services": list(seed_services),
                        "metrics": {"p95_ms": perf.get("p95_ms"), "error_rate_pct": perf.get("error_rate_pct")},
                        "strength": 0.7,
                    })

            # 4) Flow-based correlation: if a flow contains multiple seeds, mark it
            for f in flows or []:
                hops = f.get("hops") or []
                if len([h for h in hops if h in seed_services]) >= 2:
                    findings.append({
                        "type": "flow_path_correlation",
                        "services": hops,
                        "path_id": f.get("path_id"),
                        "strength": 0.65,
                    })

            # Compose a compact analysis section
            lines: List[str] = ["", "SECTION: Architecture Correlation"]
            if findings:
                lines.append(f"  - Findings generated: {len(findings)}")
                for idx, finding in enumerate(findings[:5], start=1):
                    svc_ct = len(finding.get("services") or [])
                    lines.append(
                        f"  - Finding {idx}: type={finding.get('type')} services={svc_ct} strength={finding.get('strength')}"
                    )
            else:
                lines.append("  - Outcome: no strong cross-service correlations identified")

            analysis = state.get("analysis") or ""
            new_analysis = (analysis + "\n" + "\n".join(lines)).strip()

            updated = state.copy()
            tr = updated.get("tool_results") or {}
            tr.update({"v4_correlation": {"finding_count": len(findings)}})
            updated.update({
                "current_step": "architecture_correlation_complete",
                "analysis": new_analysis,
                "correlation_findings": findings,
                "tool_results": tr,
            })
            return updated
        except Exception as e:
            self.logger.error(f"ArchitectureCorrelationNode error: {e}")
            updated = state.copy()
            updated.update({
                "current_step": "architecture_correlation_error",
                "error": f"Correlation engine failed: {e}",
            })
            return updated
