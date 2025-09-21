"""
Dependency-Based Investigation Strategy Node (Phase 4 - J)

Produces a staged investigation plan using the project topology (WW) and
the anchors/flow_hint from E (query decomposition). The basic strategy is a
downstream expansion from anchors across dependency edges.

Outputs `investigation_plan`: a list of stages with service_ids.
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


class DependencyStrategyNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.DependencyStrategyNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            project_id = state.get("project_id") or ""
            if not project_id:
                raise ValueError("Missing project_id")

            decomp = state.get("query_decomposition") or {}
            anchors: List[str] = list(decomp.get("anchors") or [])
            flow_hint: List[str] = list(decomp.get("flow_hint") or [])
            if not anchors and not flow_hint:
                raise ValueError("No anchors or flow hint provided in decomposition")

            topo = await project_architecture_service.get_topology_map(project_id)
            deps = topo.get("dependencies") or []
            if not deps:
                raise ValueError("No dependencies available in topology map")

            # Build adjacency for downstream traversal
            adj: Dict[str, List[str]] = {}
            for d in deps:
                fr = d.get("from_service_id")
                to = d.get("to_service_id")
                if not fr or not to:
                    continue
                adj.setdefault(fr, []).append(to)

            # Seed initial frontier from anchors or flow_hint first hop
            frontier: List[str] = anchors[:] if anchors else (flow_hint[:1] if flow_hint else [])
            seen: Set[str] = set(frontier)
            plan: List[Dict[str, Any]] = []

            if frontier:
                plan.append({
                    "stage": 0,
                    "services": frontier[:],
                    "rationale": "Anchors from query decomposition"
                })

            # If flow_hint is present, add it as a guided stage
            if flow_hint:
                guided = [s for s in flow_hint if s not in seen]
                if guided:
                    plan.append({
                        "stage": len(plan),
                        "services": guided,
                        "rationale": "Guided by flow_hint"
                    })
                    seen.update(guided)
                    frontier = guided

            # Expand downstream up to a small cap
            max_stages = 3
            while len(plan) < max_stages + 1 and frontier:
                nxt: List[str] = []
                for s in frontier:
                    for nb in adj.get(s, []):
                        if nb not in seen:
                            seen.add(nb)
                            nxt.append(nb)
                if not nxt:
                    break
                plan.append({
                    "stage": len(plan),
                    "services": nxt,
                    "rationale": "Downstream expansion from previous stage"
                })
                frontier = nxt

            updated = state.copy()
            tr = updated.get("tool_results") or {}
            total_svcs = len({sid for st in plan for sid in (st.get('services') or [])})
            tr.update({
                "dependency_strategy": {"stages": len(plan), "total_services": total_svcs}
            })
            updated.update({
                "current_step": "dependency_strategy_planned",
                "investigation_plan": plan,
                "tool_results": tr,
            })
            return updated
        except Exception as e:
            self.logger.error(f"DependencyStrategyNode error: {e}")
            updated = state.copy()
            updated.update({
                "current_step": "dependency_strategy_error",
                "error": f"Dependency strategy failed: {e}",
            })
            return updated

