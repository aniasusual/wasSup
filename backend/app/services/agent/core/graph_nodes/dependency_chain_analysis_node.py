"""
Dependency Chain Analysis (Phase 6 - X1)

Examines upstream and downstream dependencies for services flagged by
automated follow-up investigations. Relies on the topology map (WW) to
reconstruct multi-hop relationships and surfaces high-impact chains.
"""

import logging
from collections import deque
from typing import Any, Deque, Dict, List, Optional, Set, Tuple

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


class DependencyChainAnalysisNode:
    """Performs dependency chain analysis for Phase 6 node X1."""

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.DependencyChainAnalysisNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            project_id = state.get("project_id") or ""
            if not project_id:
                raise ValueError("Missing project_id")

            topo = await project_architecture_service.get_topology_map(project_id)
            dependencies: List[Dict[str, Any]] = topo.get("dependencies") or []

            down_map: Dict[str, List[str]] = {}
            up_map: Dict[str, List[str]] = {}
            for dep in dependencies:
                src = dep.get("from_service_id") or dep.get("source") or dep.get("from")
                dst = dep.get("to_service_id") or dep.get("destination") or dep.get("to")
                if not src or not dst:
                    continue
                down_map.setdefault(src, []).append(dst)
                up_map.setdefault(dst, []).append(src)

            seeds = list(dict.fromkeys(
                state.get("followup_service_seeds")
                or state.get("followup_seed_services")
                or [t.get("service") for t in state.get("cross_service_triggers") or []]
            ))
            seeds = [s for s in seeds if isinstance(s, str) and s]

            followups = list(state.get("auto_followup_investigations") or [])
            priority_map = {
                f.get("service"): f.get("priority")
                for f in followups
                if f.get("service")
            }

            chain_insights: List[Dict[str, Any]] = []
            coverage_services: Set[str] = set()

            for seed in seeds[:8]:  # limit breadth for practicality
                upstream = self._walk_graph(seed, up_map)
                downstream = self._walk_graph(seed, down_map)
                coverage_services.update(upstream)
                coverage_services.update(downstream)

                impact = self._compute_impact(seed, upstream, downstream, priority_map)
                critical_paths = self._extract_paths(seed, down_map, up_map)

                chain_insights.append({
                    "service": seed,
                    "upstream": upstream,
                    "downstream": downstream,
                    "critical_paths": critical_paths,
                    "impact_score": impact,
                })

            analysis = state.get("analysis") or ""
            lines: List[str] = ["", "SECTION: Dependency Chain Analysis"]
            if chain_insights:
                lines.append(f"  - Services analyzed: {len(chain_insights)}")
                lines.append(
                    f"  - Linked services covered: {len(coverage_services)}"
                )
            else:
                lines.append("  - Outcome: dependency chains not identified")

            new_analysis = (analysis + "\n" + "\n".join(lines)).strip()

            updated = state.copy()
            tr = dict(updated.get("tool_results") or {})
            tr.update({"phase6_dependency_chain": {"count": len(chain_insights)}})
            updated.update({
                "current_step": "dependency_chain_analysis_complete",
                "analysis": new_analysis,
                "dependency_chain_insights": chain_insights,
                "followup_dependency_services": list(dict.fromkeys(seeds + list(coverage_services))),
                "tool_results": tr,
            })
            return updated
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error(f"DependencyChainAnalysisNode error: {exc}", exc_info=True)
            updated = state.copy()
            updated.update({
                "current_step": "dependency_chain_analysis_error",
                "error": f"Dependency chain analysis failed: {exc}",
            })
            return updated

    def _walk_graph(self, start: str, graph: Dict[str, List[str]], depth_limit: int = 3) -> List[str]:
        """Breadth-first traversal collecting nodes up to depth_limit."""

        visited: Set[str] = set()
        order: List[str] = []
        queue: Deque[Tuple[str, int]] = deque()
        queue.append((start, 0))

        while queue:
            current, depth = queue.popleft()
            if depth >= depth_limit:
                continue
            for neighbor in graph.get(current, []):
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                order.append(neighbor)
                queue.append((neighbor, depth + 1))

        return order

    def _compute_impact(
        self,
        seed: str,
        upstream: List[str],
        downstream: List[str],
        priority_map: Dict[str, str],
    ) -> float:
        score = 0.2 * len(upstream) + 0.25 * len(downstream)
        priority = priority_map.get(seed)
        if priority == "high":
            score += 0.5
        elif priority == "medium":
            score += 0.3
        return round(min(1.0, score), 2)

    def _extract_paths(
        self,
        seed: str,
        down_map: Dict[str, List[str]],
        up_map: Dict[str, List[str]],
    ) -> Dict[str, List[List[str]]]:
        """Return representative upstream/downstream paths (max 2 each)."""

        downstream_paths: List[List[str]] = []
        upstream_paths: List[List[str]] = []

        for first in down_map.get(seed, [])[:2]:
            tail = down_map.get(first, [])[:2]
            downstream_paths.append([seed, first] + tail)

        for first in up_map.get(seed, [])[:2]:
            tail = up_map.get(first, [])[:2]
            upstream_paths.append(tail + [first, seed])

        return {
            "downstream": downstream_paths,
            "upstream": upstream_paths,
        }
