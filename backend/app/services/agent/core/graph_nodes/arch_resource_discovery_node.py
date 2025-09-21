"""
Architecture-Guided Resource Discovery (Phase 5 - U)

Discovers related services to investigate when the result set is empty,
using the Architecture Context Repository:

- Seeds from filter_plan (K) or query_decomposition (E)
- Adds upstream/downstream neighbors from WW (topology)
- Adds adjacent hops from YY (data flow patterns)
- (Optional) May include services sharing infra components from ZZ

Outputs `discovered_resources`: [{ service_id, reasons: [..] }]
Filtering is applied in U1; this node only discovers and records.
"""

import logging
from typing import Dict, Any, List, Set

try:
    from .....models.agent import AgentState, WorkflowConfig
    from ....project_architecture_service import project_architecture_service
except ImportError:
    import sys, os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
    from app.models.agent import AgentState, WorkflowConfig
    from app.services.project_architecture_service import project_architecture_service


logger = logging.getLogger(__name__)


class ArchResourceDiscoveryNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.ArchResourceDiscoveryNode")

    async def execute(self, state: AgentState) -> AgentState:
        try:
            project_id = state.get("project_id") or ""
            if not project_id:
                raise ValueError("Missing project_id")

            # 1) Seed set from filter_plan or query_decomposition
            seeds: List[str] = []
            plan = state.get("filter_plan") or []
            if isinstance(plan, list) and plan:
                for s in (plan[0].get("services") or []):
                    if isinstance(s, str) and s not in seeds:
                        seeds.append(s)
            decomp = state.get("query_decomposition") or {}
            for s in (decomp.get("anchors") or []):
                if isinstance(s, str) and s not in seeds:
                    seeds.append(s)
            for s in (decomp.get("flow_hint") or []):
                if isinstance(s, str) and s not in seeds:
                    seeds.append(s)

            if not seeds:
                # No basis to discover neighbors
                updated = state.copy()
                updated.update({
                    "current_step": "arch_resources_discovered",
                    "discovered_resources": [],
                })
                return updated

            # 2) Load topology (WW) and flows (YY)
            topo = await project_architecture_service.get_topology_map(project_id)
            deps = topo.get("dependencies") or []
            flows = await project_architecture_service.get_data_flow_patterns(project_id)

            # Build adjacency both directions from WW
            down: Dict[str, List[str]] = {}
            up: Dict[str, List[str]] = {}
            for d in deps:
                a = d.get("from_service_id")
                b = d.get("to_service_id")
                if not a or not b:
                    continue
                down.setdefault(a, []).append(b)
                up.setdefault(b, []).append(a)

            # Neighbor discovery
            discovered_map: Dict[str, Dict[str, Any]] = {}
            seed_set: Set[str] = set(seeds)

            def _add(sid: str, reason: str):
                if sid in seed_set:
                    return
                ent = discovered_map.setdefault(sid, {"service_id": sid, "reasons": []})
                if reason not in ent["reasons"]:
                    ent["reasons"].append(reason)

            # From WW: one-hop neighbors
            for s in seeds:
                for nb in down.get(s, []):
                    _add(nb, "downstream")
                for nb in up.get(s, []):
                    _add(nb, "upstream")

            # From YY: flow neighbors in any path containing seed
            for f in flows or []:
                hops = f.get("hops") or []
                for i, sid in enumerate(hops):
                    if sid in seed_set:
                        if i - 1 >= 0:
                            _add(hops[i-1], "flow_neighbor")
                        if i + 1 < len(hops):
                            _add(hops[i+1], "flow_neighbor")

            discovered = list(discovered_map.values())

            updated = state.copy()
            tr = updated.get("tool_results") or {}
            tr.update({
                "arch_discovery": {"seeds": len(seeds), "discovered": len(discovered)}
            })
            updated.update({
                "current_step": "arch_resources_discovered",
                "discovered_resources": discovered,
                "tool_results": tr,
            })
            return updated
        except Exception as e:
            updated = state.copy()
            updated.update({
                "current_step": "arch_resources_discovery_error",
                "error": f"Architecture discovery failed: {e}",
            })
            return updated
