"""
Architecture Loader Node - Phase 1, Step A1 of the investigation workflow.

This node loads and processes project architecture context to enhance
log analysis capabilities with architectural understanding.
"""

import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    # Try relative imports first (for normal usage)
    from ....models.agent import AgentState, NodeResult, WorkflowConfig
    from ....models.project_architecture import ProjectArchitecture
    from ....services.project_architecture_service import project_architecture_service
    from .llm_service import LLMService
except ImportError:
    # Fall back to absolute imports (for LangGraph Studio)
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
    from app.models.agent import AgentState, NodeResult, WorkflowConfig
    from app.models.project_architecture import ProjectArchitecture
    from app.services.project_architecture_service import project_architecture_service
    from app.services.agent.core.llm_service import LLMService

logger = logging.getLogger(__name__)


class ArchitectureLoaderNode:
    """
    Architecture Loader Node - Loads and processes project architecture context.
    
    This node handles:
    - Loading project architecture from database
    - Parsing architecture description using NLP
    - Extracting service information and dependencies
    - Building architecture context for log analysis
    - Identifying relevant services for the query
    """
    
    def __init__(self, config: WorkflowConfig):
        """
        Initialize the Architecture Loader node.
        
        Args:
            config: Workflow configuration
        """
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.ArchitectureLoaderNode")
        
        # Initialize LLM service for architecture parsing
        self.llm_service = LLMService()
        
        self.logger.info("ArchitectureLoaderNode initialized")
    
    async def execute(self, state: AgentState) -> AgentState:
        """
        Execute the Architecture Loader node.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state with architecture context
        """
        start_time = datetime.utcnow()
        
        try:
            
            self.logger.info(f"Loading architecture context for project: {state.get('project_id', 'Unknown')}")
            
            # Load project architecture from database
            architecture = await self._load_project_architecture(state["project_id"])
            
            if not architecture:
                return self._handle_no_architecture(state)
            
            
            # Parse architecture using LLM
            parsed_architecture = await self._parse_architecture_nlp(architecture.architecture_prompt)

            # Phase 4: Build and persist Project Topology Map (WW)
            topo_summary = {}
            try:
                services_topo, deps_topo, topo_summary = await self._build_topology_map(state.get("project_id"), parsed_architecture)
            except Exception as topo_err:
                self.logger.warning(f"Topology build skipped: {topo_err}")
                services_topo, deps_topo = [], []

            # Phase 4: Build and persist Service Registry (XX)
            svc_reg_summary = {}
            try:
                registry, svc_reg_summary = await self._build_service_registry(state.get("project_id"), parsed_architecture)
            except Exception as reg_err:
                self.logger.warning(f"Service registry build skipped: {reg_err}")

            # Phase 4: Build and persist Data Flow Patterns (YY)
            df_summary = {}
            try:
                flows, df_summary = await self._build_data_flows(state.get("project_id"), parsed_architecture, services_topo)
            except Exception as flow_err:
                self.logger.warning(f"Data flow build skipped: {flow_err}")

            # Phase 4: Build and persist Infrastructure Layout (ZZ)
            infra_summary = {}
            try:
                infra, infra_summary = await self._build_infrastructure_layout(state.get("project_id"), parsed_architecture, services_topo)
            except Exception as infra_err:
                self.logger.warning(f"Infrastructure layout build skipped: {infra_err}")

            # Phase 4: Build and persist Performance Baselines (AAA)
            perf_summary = {}
            try:
                baselines, perf_summary = await self._build_performance_baselines(state.get("project_id"), parsed_architecture, services_topo)
            except Exception as perf_err:
                self.logger.warning(f"Performance baselines build skipped: {perf_err}")

            # Phase 4: Build and persist Failure Patterns (BBB)
            failure_summary = {}
            try:
                failures, failure_summary = await self._build_failure_patterns(state.get("project_id"), parsed_architecture, services_topo)
            except Exception as fail_err:
                self.logger.warning(f"Failure patterns build skipped: {fail_err}")
            
            # Extract relevant services for the current query
            relevant_services = self._extract_relevant_services(
                parsed_architecture, 
                state.get("extracted_entities", {}),
                state.get("services", [])
            )
            
            # Build architecture context
            architecture_context = self._build_architecture_context(
                architecture, 
                parsed_architecture, 
                relevant_services
            )
            
            # Update state with architecture context
            complexity_level = self._assess_architecture_complexity(parsed_architecture)
            
            updated_state = state.copy()
            updated_state.update({
                "current_step": "architecture_loaded",
                "architecture_context": architecture_context,
                "relevant_services": relevant_services,
                "architecture_insights": {
                    "has_architecture": True,
                    "service_count": len(parsed_architecture.get("services", [])),
                    "dependency_count": len(parsed_architecture.get("dependencies", [])),
                    "complexity_level": complexity_level,
                    "last_updated": architecture.updated_at.isoformat()
                },
                "tool_results": {
                    **(state.get("tool_results") or {}),
                    "architecture_loader": {
                        "loaded_architecture": True,
                        "parsed_services": parsed_architecture.get("services", []),
                        "relevant_services": relevant_services,
                        "parsing_method": "llm",
                        "topology": topo_summary,
                        "service_registry": svc_reg_summary,
                        "data_flows": df_summary,
                        "infrastructure": infra_summary,
                        "performance": perf_summary,
                        "failures": failure_summary
                    }
                }
            })
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            self.logger.info(f"Architecture context loaded in {execution_time:.3f}s")
            
            return updated_state
            
        except Exception as e:
            self.logger.error(f"Error in ArchitectureLoaderNode: {str(e)}", exc_info=True)
            return self._handle_architecture_error(state, str(e))

    async def _build_topology_map(self, project_id: str, parsed_architecture: Dict[str, Any]):
        """
        Build WW: Project Topology Map from parsed architecture and save it.
        Canonicalizes resource types strictly via LLM (no local aliasing).
        """
        try:
            from ....services.project_architecture_service import project_architecture_service
            services_raw = parsed_architecture.get("services", []) or []
            deps_raw = parsed_architecture.get("dependencies", []) or []

            # Extract identifiers for canonicalization
            identifiers: List[str] = []
            svc_candidates: List[Dict[str, Any]] = []
            for svc in services_raw:
                if isinstance(svc, dict):
                    ident = svc.get("type") or svc.get("name") or ""
                    name = svc.get("service_name") or svc.get("name") or None
                else:
                    ident = str(svc)
                    name = None
                ident = str(ident).strip()
                if not ident:
                    continue
                identifiers.append(ident)
                svc_candidates.append({"identifier": ident, "name": name})

            # Canonicalize via LLM strictly
            try:
                from . import filter_components as fc
            except Exception:
                from app.services.agent.core import filter_components as fc

            canonical_map: Dict[str, str] = {}
            for cand in svc_candidates:
                ident = cand["identifier"]
                try:
                    canon_list = await fc.canonicalize_resource_types_via_llm([ident])
                    if canon_list:
                        canonical_map[ident] = canon_list[0]
                except Exception as ce:
                    self.logger.warning(f"Canonicalize failed for '{ident}': {ce}")
                    continue

            # Build normalized services list with stable ids
            def _slug(s: str) -> str:
                import re
                s = (s or "").lower()
                return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

            services_topo: List[Dict[str, Any]] = []
            id_set = set()
            for idx, cand in enumerate(svc_candidates):
                ident = cand["identifier"]
                canon = canonical_map.get(ident)
                if not canon:
                    continue
                name = cand.get("name") or ident
                sid = f"svc-{_slug(canon)}-{_slug(name)}"
                if sid in id_set:
                    sid = f"svc-{_slug(canon)}-{idx}"
                id_set.add(sid)
                services_topo.append({
                    "id": sid,
                    "type": canon,
                    "name": name,
                })

            # Build dependencies by matching names/identifiers to ids
            name_to_id = { (s.get("name") or "").lower(): s["id"] for s in services_topo if s.get("name") }
            ident_to_id = {}
            for cand in svc_candidates:
                ident = cand["identifier"]
                canon = canonical_map.get(ident)
                if not canon:
                    continue
                key = ident.lower()
                ident_to_id[key] = f"svc-{_slug(canon)}-{_slug(cand.get('name') or ident)}"

            def _resolve_token(tok: str) -> Optional[str]:
                t = (tok or "").strip().lower()
                if not t:
                    return None
                return name_to_id.get(t) or ident_to_id.get(t)

            deps_topo: List[Dict[str, Any]] = []
            for dep in deps_raw:
                if isinstance(dep, dict):
                    f = _resolve_token(dep.get("from") or dep.get("source") or "")
                    to = _resolve_token(dep.get("to") or dep.get("target") or "")
                    rel = dep.get("relation")
                else:
                    f = to = None
                    rel = None
                if f and to:
                    deps_topo.append({"from_service_id": f, "to_service_id": to, "relation": rel})

            # Persist
            await project_architecture_service.update_topology_map(project_id, services_topo, deps_topo)

            topo_summary = {"services": len(services_topo), "dependencies": len(deps_topo)}
            return services_topo, deps_topo, topo_summary
        except Exception as e:
            self.logger.error(f"_build_topology_map error: {e}")
            raise

    async def _build_service_registry(self, project_id: str, parsed_architecture: Dict[str, Any]):
        """
        Build XX: Service Registry from parsed architecture and save it.
        Canonicalizes resource types strictly via LLM (no local aliasing).
        Registry items include resource_type, optional labels/configs if present.
        """
        try:
            from ....services.project_architecture_service import project_architecture_service
            services_raw = parsed_architecture.get("services", []) or []

            # Derive candidates and canonicalize
            svc_candidates: List[Dict[str, Any]] = []
            for svc in services_raw:
                if isinstance(svc, dict):
                    svc_candidates.append(svc)
                elif isinstance(svc, str):
                    svc_candidates.append({"type": svc})

            try:
                from . import filter_components as fc
            except Exception:
                from app.services.agent.core import filter_components as fc

            # Canonicalize individually, strict
            canonical_map: Dict[str, str] = {}
            for svc in svc_candidates:
                ident = str((svc.get("type") or svc.get("name") or "").strip())
                if not ident:
                    continue
                canon_list = await fc.canonicalize_resource_types_via_llm([ident])
                if canon_list:
                    canonical_map[ident] = canon_list[0]

            # Same slug/id scheme as topology for consistency
            def _slug(s: str) -> str:
                import re
                s = (s or "").lower()
                return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

            registry: List[Dict[str, Any]] = []
            for idx, svc in enumerate(svc_candidates):
                ident = str((svc.get("type") or svc.get("name") or "").strip())
                canon = canonical_map.get(ident)
                if not canon:
                    continue
                name = svc.get("service_name") or svc.get("name") or ident
                sid = f"svc-{_slug(canon)}-{_slug(name)}"
                entry: Dict[str, Any] = {
                    "service_id": sid,
                    "resource_type": canon,
                }
                # Optional metadata passthrough (strict: only use provided fields)
                if isinstance(svc.get("labels"), dict):
                    entry["resource_labels"] = svc.get("labels")
                if svc.get("region"):
                    entry["region"] = svc.get("region")
                if svc.get("env"):
                    entry["env"] = svc.get("env")
                if isinstance(svc.get("config"), dict):
                    entry["config"] = svc.get("config")

                registry.append(entry)

            await project_architecture_service.update_service_registry(project_id, registry)
            summary = {"count": len(registry)}
            return registry, summary
        except Exception as e:
            self.logger.error(f"_build_service_registry error: {e}")
            raise

    async def _build_data_flows(self, project_id: str, parsed_architecture: Dict[str, Any], services_topo: List[Dict[str, Any]]):
        """
        Build YY: Data Flow Patterns from parsed architecture and save them.
        Strict mapping: include only flows whose hops map to known topology service ids.
        Flow item example:
          { path_id, hops: [service_id], protocol?, typical_latency?, typical_error_rate? }
        """
        try:
            from ....services.project_architecture_service import project_architecture_service
            flows_raw = parsed_architecture.get("data_flows") or parsed_architecture.get("flows") or []

            # Build name -> id map from topology
            name_to_id = { (s.get("name") or "").lower(): s["id"] for s in (services_topo or []) if s.get("name") }

            def _resolve_name(n: str) -> Optional[str]:
                t = (n or "").strip().lower()
                return name_to_id.get(t)

            flows_norm: List[Dict[str, Any]] = []
            for idx, f in enumerate(flows_raw):
                # Accept dicts with hops or simple arrays of names
                hops_names: List[str] = []
                protocol = None
                tlat = None
                terr = None
                if isinstance(f, dict):
                    hops_names = f.get("hops") or f.get("services") or []
                    protocol = f.get("protocol")
                    tlat = f.get("typical_latency")
                    terr = f.get("typical_error_rate")
                elif isinstance(f, list):
                    hops_names = f
                else:
                    continue

                # Resolve to ids; strict: if any hop missing, skip the flow
                hop_ids: List[str] = []
                ok = True
                for name in hops_names:
                    sid = _resolve_name(str(name))
                    if not sid:
                        ok = False
                        break
                    hop_ids.append(sid)
                if not ok or len(hop_ids) < 2:
                    continue

                flows_norm.append({
                    "path_id": f"path-{idx}",
                    "hops": hop_ids,
                    **({"protocol": protocol} if protocol else {}),
                    **({"typical_latency": tlat} if tlat else {}),
                    **({"typical_error_rate": terr} if terr else {}),
                })

            await project_architecture_service.update_data_flow_patterns(project_id, flows_norm)
            summary = {"count": len(flows_norm)}
            return flows_norm, summary
        except Exception as e:
            self.logger.error(f"_build_data_flows error: {e}")
            raise

    async def _build_infrastructure_layout(self, project_id: str, parsed_architecture: Dict[str, Any], services_topo: List[Dict[str, Any]]):
        """
        Build ZZ: Infrastructure Layout from parsed architecture and save it.
        Normalizes a list of infra components (clusters, networks, databases)
        and, when possible, links them to known service_ids via service names.
        Strict mapping: do not infer unknown links.
        """
        try:
            from ....services.project_architecture_service import project_architecture_service
            infra_raw = parsed_architecture.get("infrastructure") or {}

            items: List[Dict[str, Any]] = []

            # Name -> service_id mapping from topology
            name_to_id = { (s.get("name") or "").lower(): s["id"] for s in (services_topo or []) if s.get("name") }

            def _link_services(names: Any) -> List[str]:
                if not names:
                    return []
                out: List[str] = []
                for n in names if isinstance(names, list) else [names]:
                    sid = name_to_id.get(str(n).strip().lower())
                    if sid:
                        out.append(sid)
                return out

            # Common buckets: clusters, networks, databases, storage, queues
            for kind in ["clusters", "networks", "databases", "storage", "queues", "gateways"]:
                bucket = infra_raw.get(kind) or []
                for idx, obj in enumerate(bucket):
                    if isinstance(obj, dict):
                        name = obj.get("name") or obj.get("id") or f"{kind}-{idx}"
                        entry: Dict[str, Any] = {"kind": kind[:-1] if kind.endswith('s') else kind, "name": name}
                        if obj.get("region"):
                            entry["region"] = obj.get("region")
                        if isinstance(obj.get("labels"), dict):
                            entry["labels"] = obj.get("labels")
                        # optional service links
                        links = _link_services(obj.get("services"))
                        if links:
                            entry["services"] = links
                        items.append(entry)
                    elif isinstance(obj, str):
                        items.append({"kind": kind[:-1] if kind.endswith('s') else kind, "name": obj})

            await project_architecture_service.update_infrastructure_layout(project_id, items)
            summary = {"count": len(items)}
            return items, summary
        except Exception as e:
            self.logger.error(f"_build_infrastructure_layout error: {e}")
            raise

    async def _build_performance_baselines(self, project_id: str, parsed_architecture: Dict[str, Any], services_topo: List[Dict[str, Any]]):
        """
        Build AAA: Performance Baselines from parsed architecture and save them.
        Each baseline item references a known service_id and includes typical
        response times and error rates when available.
        Item example:
          { service_id, p50_latency_ms?, p95_latency_ms?, error_rate_pct?, notes? }
        Strict mapping: only include items whose service name maps to a topology service.
        """
        try:
            from ....services.project_architecture_service import project_architecture_service
            perf_raw = parsed_architecture.get("performance") or parsed_architecture.get("baselines") or []

            # Build name -> service_id map from topology
            name_to_id = { (s.get("name") or "").lower(): s["id"] for s in (services_topo or []) if s.get("name") }

            def _resolve_name(n: str) -> Optional[str]:
                t = (n or "").strip().lower()
                return name_to_id.get(t)

            baselines: List[Dict[str, Any]] = []
            for obj in perf_raw:
                if not isinstance(obj, dict):
                    continue
                sname = obj.get("service") or obj.get("name")
                sid = _resolve_name(sname)
                if not sid:
                    continue
                entry: Dict[str, Any] = {"service_id": sid}
                # Normalize common baseline metrics if present
                if obj.get("p50_latency_ms") is not None:
                    entry["p50_latency_ms"] = obj.get("p50_latency_ms")
                if obj.get("p95_latency_ms") is not None:
                    entry["p95_latency_ms"] = obj.get("p95_latency_ms")
                if obj.get("error_rate_pct") is not None:
                    entry["error_rate_pct"] = obj.get("error_rate_pct")
                if obj.get("notes"):
                    entry["notes"] = obj.get("notes")
                baselines.append(entry)

            await project_architecture_service.update_performance_baselines(project_id, baselines)
            summary = {"count": len(baselines)}
            return baselines, summary
        except Exception as e:
            self.logger.error(f"_build_performance_baselines error: {e}")
            raise

    async def _build_failure_patterns(self, project_id: str, parsed_architecture: Dict[str, Any], services_topo: List[Dict[str, Any]]):
        """
        Build BBB: Failure Patterns from parsed architecture and save them.
        Pattern item example:
          { pattern_id, name?, description?, services?: [service_id], triggers?: [str], signals?: [str] }
        Strict mapping: service links only when service names map to known topology service ids.
        """
        try:
            from ....services.project_architecture_service import project_architecture_service
            patterns_raw = parsed_architecture.get("failure_patterns") or parsed_architecture.get("patterns") or []

            name_to_id = { (s.get("name") or "").lower(): s["id"] for s in (services_topo or []) if s.get("name") }

            def _resolve_services(names: Any) -> List[str]:
                out: List[str] = []
                if not names:
                    return out
                arr = names if isinstance(names, list) else [names]
                for n in arr:
                    sid = name_to_id.get(str(n).strip().lower())
                    if sid:
                        out.append(sid)
                return out

            patterns: List[Dict[str, Any]] = []
            for idx, obj in enumerate(patterns_raw):
                if not isinstance(obj, dict):
                    continue
                entry: Dict[str, Any] = {"pattern_id": f"pattern-{idx}"}
                if obj.get("name"):
                    entry["name"] = obj.get("name")
                if obj.get("description"):
                    entry["description"] = obj.get("description")
                svcs = _resolve_services(obj.get("services") or obj.get("affected_services"))
                if svcs:
                    entry["services"] = svcs
                if obj.get("triggers"):
                    entry["triggers"] = obj.get("triggers")
                if obj.get("signals"):
                    entry["signals"] = obj.get("signals")
                patterns.append(entry)

            await project_architecture_service.update_failure_patterns(project_id, patterns)
            summary = {"count": len(patterns)}
            return patterns, summary
        except Exception as e:
            self.logger.error(f"_build_failure_patterns error: {e}")
            raise
    
    async def _load_project_architecture(self, project_id: str) -> Optional[ProjectArchitecture]:
        """
        Load project architecture from database.
        
        Args:
            project_id: GCP project ID
            
        Returns:
            ProjectArchitecture object or None if not found
        """
        try:
            architecture = await project_architecture_service.get_architecture_by_project(project_id)
            # print(f"Architecture: {architecture}")
            if architecture:
                self.logger.info(f"Loaded architecture for project {project_id}")
            else:
                self.logger.warning(f"No architecture found for project {project_id}")
            return architecture
        except Exception as e:
            self.logger.error(f"Error loading architecture for project {project_id}: {str(e)}")
            raise
    
    async def _parse_architecture_nlp(self, architecture_prompt: str) -> Dict[str, Any]:
        """
        Parse architecture description using LLM.
        
        Args:
            architecture_prompt: Raw architecture description
            
        Returns:
            Parsed architecture information
        """
        # Use LLM service for intelligent architecture parsing
        parsed = await self.llm_service.parse_architecture(architecture_prompt)
        self.logger.info("Successfully parsed architecture using LLM")
        return parsed
    
    
    def _extract_relevant_services(
        self, 
        parsed_architecture: Dict[str, Any], 
        extracted_entities: Dict[str, Any], 
        user_services: List[str]
    ) -> List[str]:
        """
        Extract services relevant to the current query.
        
        Args:
            parsed_architecture: Parsed architecture information
            extracted_entities: Entities extracted from user query
            user_services: Services specified by user
            
        Returns:
            List of relevant service types
        """
        relevant_services = set()
        
        # Add user-specified services
        if user_services:
            relevant_services.update(user_services)
        
        # Add services from extracted entities
        query_services = extracted_entities.get("services", {})
        for service_filter in query_services.keys():
            # Extract service type from filter (e.g., "resource.type=cloud_run" -> "cloud_run")
            if "resource.type=" in service_filter:
                service_type = service_filter.split("resource.type=")[1]
                relevant_services.add(service_type)
        
        # Add services from architecture that match query intent
        architecture_services = []
        for s in parsed_architecture.get("services", []):
            # Handle LLM parsing format
            if isinstance(s, dict):
                service_type = s.get("type") or s.get("name", "")
                if service_type:
                    architecture_services.append(service_type)
            elif isinstance(s, str):
                architecture_services.append(s)
        
        # If no specific services mentioned, include all architecture services
        if not relevant_services and architecture_services:
            relevant_services.update(architecture_services)
        
        # If specific services mentioned, find related services from architecture
        if relevant_services and architecture_services:
            # Add services that are dependencies or related
            for service in list(relevant_services):
                # Find related services in architecture
                for arch_service in parsed_architecture.get("services", []):
                    service_type = ""
                    if isinstance(arch_service, dict):
                        service_type = arch_service.get("type") or arch_service.get("name", "")
                    elif isinstance(arch_service, str):
                        service_type = arch_service
                    
                    if service in service_type.lower():
                        relevant_services.add(service_type)
                        
                        # Add dependencies
                        for dep in parsed_architecture.get("dependencies", []):
                            if service in dep.lower():
                                # Try to match dependency to known service types
                                for service_info in parsed_architecture.get("services", []):
                                    dep_service_type = service_info.get("type", "")
                                    if dep_service_type and dep_service_type in dep.lower():
                                        relevant_services.add(dep_service_type)
        
        return list(relevant_services)
    
    def _build_architecture_context(
        self, 
        architecture: ProjectArchitecture, 
        parsed_architecture: Dict[str, Any], 
        relevant_services: List[str]
    ) -> Dict[str, Any]:
        """
        Build comprehensive architecture context for log analysis.
        
        Args:
            architecture: Database architecture object
            parsed_architecture: Parsed architecture information
            relevant_services: Services relevant to current query
            
        Returns:
            Architecture context dictionary
        """
        return {
            "project_id": architecture.project_id,
            "architecture_id": str(architecture.id),
            "raw_description": architecture.architecture_prompt,
            "parsed_services": parsed_architecture.get("services", []),
            "relevant_services": relevant_services,
            "dependencies": parsed_architecture.get("dependencies", []),
            "data_flows": parsed_architecture.get("data_flows", []),
            "technologies": parsed_architecture.get("technologies", []),
            "infrastructure": parsed_architecture.get("infrastructure", {}),
            "patterns": parsed_architecture.get("patterns", []),
            "created_by": architecture.created_by,
            "last_updated": architecture.updated_at.isoformat(),
            "is_active": architecture.is_active,
            "context_summary": self._generate_context_summary(parsed_architecture, relevant_services)
        }
    
    def _generate_context_summary(self, parsed_architecture: Dict[str, Any], relevant_services: List[str]) -> str:
        """
        Generate a summary of the architecture context.
        
        Args:
            parsed_architecture: Parsed architecture information
            relevant_services: Services relevant to current query
            
        Returns:
            Context summary string
        """
        services = parsed_architecture.get("services", [])
        dependencies = parsed_architecture.get("dependencies", [])
        technologies = parsed_architecture.get("technologies", [])
        
        summary_parts = []
        
        if services:
            service_names = [s.get("name", s.get("type", "Unknown")) for s in services]
            summary_parts.append(f"Services: {', '.join(service_names)}")
        
        if relevant_services:
            summary_parts.append(f"Query-relevant services: {', '.join(relevant_services)}")
        
        if technologies:
            summary_parts.append(f"Technologies: {', '.join(technologies)}")
        
        if dependencies:
            summary_parts.append(f"Dependencies: {len(dependencies)} identified")
        
        return " | ".join(summary_parts) if summary_parts else "Basic architecture context loaded"
    
    def _assess_architecture_complexity(self, parsed_architecture: Dict[str, Any]) -> str:
        """
        Assess the complexity level of the architecture.
        
        Args:
            parsed_architecture: Parsed architecture information
            
        Returns:
            Complexity level: "simple", "moderate", or "complex"
        """
        service_count = len(parsed_architecture.get("services", []))
        dependency_count = len(parsed_architecture.get("dependencies", []))
        data_flow_count = len(parsed_architecture.get("data_flows", []))
        
        total_complexity = service_count + dependency_count + data_flow_count
        
        if total_complexity <= 3:
            return "simple"
        elif total_complexity <= 8:
            return "moderate"
        else:
            return "complex"
    
    def _handle_no_architecture(self, state: AgentState) -> AgentState:
        """
        Handle case when no architecture is found.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with no-architecture context
        """
        
        updated_state = state.copy()
        updated_state.update({
            "current_step": "architecture_not_found",
            "architecture_context": {
                "has_architecture": False,
                "message": "No project architecture defined",
                "suggestion": "Consider defining your project architecture for better log analysis"
            },
            "relevant_services": state.get("services", []),
            "architecture_insights": {
                "has_architecture": False,
                "service_count": 0,
                "dependency_count": 0,
                "complexity_level": "unknown",
                "last_updated": None
            },
            "tool_results": {
                **state.get("tool_results", {}),
                "architecture_loader": {
                    "loaded_architecture": False,
                    "message": "No architecture found",
                    "no_architecture": True
                }
            }
        })
        
        
        self.logger.warning("No project architecture found - proceeding with basic context")
        return updated_state
    
    def _handle_architecture_error(self, state: AgentState, error_message: str) -> AgentState:
        """
        Handle architecture loading errors.
        
        Args:
            state: Current agent state
            error_message: Error message
            
        Returns:
            Updated state with error information
        """
        
        updated_state = state.copy()
        updated_state.update({
            "current_step": "architecture_load_error",
            "error": f"Architecture loading failed: {error_message}",
            "architecture_context": {
                "has_architecture": False,
                "error": error_message,
                "error_mode": True
            },
            "relevant_services": state.get("services", []),
            "architecture_insights": {
                "has_architecture": False,
                "error": True,
                "error_message": error_message
            },
            "tool_results": {
                **(state.get("tool_results") or {}),
                "architecture_loader": {
                    "loaded_architecture": False,
                    "error": error_message,
                    "no_architecture": True
                }
            }
        })
        
        
        self.logger.error(f"Architecture loading error: {error_message}")
        return updated_state
