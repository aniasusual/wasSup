"""
Architecture-Aware Query Decomposition Node (Phase 4 - E)

Analyzes the user's complex query in the context of the project's
architecture repository to produce a structured decomposition:

- anchors: primary services to investigate (service_ids)
- flow_hint: optional ordered hops across services (service_ids)
- goals: investigation goals/symptoms
- constraints: time/severity/keywords/status derived from query

Strict behavior: requires topology (WW) to resolve service names to
service_ids. If topology is unavailable or anchors cannot be resolved,
the node returns an error in state.
"""

import logging
from typing import Dict, Any, List, Optional

try:
    from .....models.agent import AgentState, WorkflowConfig
    from ....project_architecture_service import project_architecture_service
    from ..llm_service import LLMService
except ImportError:
    import sys, os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
    from app.models.agent import AgentState, WorkflowConfig
    from app.services.project_architecture_service import project_architecture_service
    from app.services.agent.core.llm_service import LLMService

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


class DecompositionSchema(BaseModel):
    anchors: List[str] = Field(default_factory=list, description="Primary services (names/identifiers)")
    flow_hint: List[str] = Field(default_factory=list, description="Ordered service names representing the user flow")
    goals: List[str] = Field(default_factory=list, description="Investigation goals or symptoms")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="time/severity/status/keywords constraints")


class ArchitectureAwareQueryDecompositionNode:
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.ArchitectureAwareQueryDecompositionNode")
        self.llm = LLMService()

    async def execute(self, state: AgentState) -> AgentState:
        try:
            project_id = state.get("project_id") or ""
            if not project_id:
                raise ValueError("Missing project_id")

            question = state.get("question") or state.get("processed_question") or ""
            if not question:
                raise ValueError("Missing question for decomposition")

            # Load topology map (WW)
            topo = await project_architecture_service.get_topology_map(project_id)
            services = topo.get("services") or []
            if not services:
                raise ValueError("Topology map unavailable for project")

            # Name -> id map
            name_to_id = { (s.get("name") or "").strip().lower(): s.get("id") for s in services if s.get("name") }

            # Build LLM prompt to extract anchors/goals/constraints
            parser = JsonOutputParser(pydantic_object=DecompositionSchema)
            prompt = ChatPromptTemplate.from_messages([
                ("system", """
You are an expert assistant decomposing complex log investigation queries in the context of a microservices architecture.
Return ONLY a JSON object with keys: anchors[], flow_hint[], goals[], constraints{}.
- anchors: service names mentioned or implied (short names, not types)
- flow_hint: ordered service names if a user/business flow is implied
- goals: symptoms or investigation goals (e.g., timeouts, auth failures)
- constraints: time/severity/keywords/status derived from the query
No extra keys or commentary.
"""),
                ("human", """
Project services (names):
{service_names}

Query:
{question}

{format_instructions}
"""),
            ])

            chain = prompt | self.llm.llm | parser
            service_names = "\n".join([f"- {s.get('name')}" for s in services if s.get("name")])
            result: DecompositionSchema = await chain.ainvoke({
                "service_names": service_names,
                "question": question,
                "format_instructions": parser.get_format_instructions(),
            })

            # Resolve anchors/flow_hint to service_ids strictly
            def _to_ids(names: List[str]) -> List[str]:
                out: List[str] = []
                for n in names or []:
                    sid = name_to_id.get(str(n).strip().lower())
                    if sid:
                        out.append(sid)
                return out

            anchor_ids = _to_ids(result.anchors)
            flow_ids = _to_ids(result.flow_hint)
            if not anchor_ids and flow_ids:
                # If only flow was provided, consider first hop an anchor
                anchor_ids = [flow_ids[0]]

            if not anchor_ids:
                raise ValueError("Could not resolve anchors from query and topology")

            decomposition = {
                "anchors": anchor_ids,
                "flow_hint": flow_ids,
                "goals": result.goals,
                "constraints": result.constraints,
            }

            updated = state.copy()
            tr = updated.get("tool_results") or {}
            tr.update({
                "query_decomposition": {
                    "anchors": len(anchor_ids),
                    "flow_hint": len(flow_ids),
                    "goals": len(result.goals),
                }
            })
            updated.update({
                "current_step": "query_decomposition_complete",
                "query_decomposition": decomposition,
                "tool_results": tr,
                "query_type": state.get("query_type") or "complex",
            })
            return updated
        except Exception as e:
            self.logger.error(f"ArchitectureAwareQueryDecompositionNode error: {e}")
            updated = state.copy()
            updated.update({
                "current_step": "query_decomposition_error",
                "error": f"Query decomposition failed: {e}",
            })
            return updated

