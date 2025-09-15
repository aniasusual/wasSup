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
        
        # Service type patterns for GCP services
        self.gcp_service_patterns = {
            'cloud_run': r'\b(?:cloud.?run|cloudrun|run|serverless|container)\b',
            'cloud_sql': r'\b(?:cloud.?sql|cloudsql|sql|database|db|mysql|postgres)\b',
            'gce_instance': r'\b(?:gce|compute.?engine|compute.?instance|vm|instance|virtual.?machine)\b',
            'gke_cluster': r'\b(?:gke|kubernetes|k8s|cluster|pod|container.?orchestration)\b',
            'app_engine': r'\b(?:app.?engine|gae|appengine)\b',
            'cloud_functions': r'\b(?:cloud.?functions|functions|gcf|serverless.?function)\b',
            'load_balancer': r'\b(?:load.?balancer|lb|ingress|traffic.?manager)\b',
            'cloud_storage': r'\b(?:cloud.?storage|storage|gcs|bucket|object.?storage)\b',
            'pubsub': r'\b(?:pub.?sub|pubsub|message.?queue|event.?stream)\b',
            'bigquery': r'\b(?:bigquery|big.?query|data.?warehouse|analytics)\b',
            'firestore': r'\b(?:firestore|firebase|document.?database|nosql)\b',
            'cloud_logging': r'\b(?:cloud.?logging|logging|logs|monitoring)\b',
            'cloud_monitoring': r'\b(?:cloud.?monitoring|monitoring|metrics|observability)\b'
        }
        
        self.logger.info("ArchitectureLoaderNode initialized with LLM service")
    
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
            
            
            # Parse architecture using LLM (with regex fallback)
            parsed_architecture = await self._parse_architecture_nlp(architecture.architecture_prompt)
            
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
                        "parsing_method": "llm_with_regex_fallback"
                    }
                }
            })
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            self.logger.info(f"Architecture context loaded in {execution_time:.3f}s")
            
            return updated_state
            
        except Exception as e:
            self.logger.error(f"Error in ArchitectureLoaderNode: {str(e)}", exc_info=True)
            return self._handle_architecture_error(state, str(e))
    
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
        Parse architecture description using NLP (LLM) with regex fallback.
        
        Args:
            architecture_prompt: Raw architecture description
            
        Returns:
            Parsed architecture information
        """
        try:
            # Use LLM service for intelligent architecture parsing
            parsed = await self.llm_service.parse_architecture(architecture_prompt)
            return parsed
        except Exception as e:
            self.logger.error(f"Error in NLP architecture parsing: {str(e)}")
            raise RuntimeError(f"Failed to parse architecture: {str(e)}")
    
    def _parse_architecture_regex(self, architecture_prompt: str) -> Dict[str, Any]:
        """
        Parse architecture description using regex patterns.
        
        Args:
            architecture_prompt: Raw architecture description
            
        Returns:
            Parsed architecture information
        """
        prompt_lower = architecture_prompt.lower()
        
        parsed = {
            "services": [],
            "dependencies": [],
            "data_flows": [],
            "infrastructure": {},
            "technologies": [],
            "patterns": []
        }
        
        # Extract GCP services
        for service_type, pattern in self.gcp_service_patterns.items():
            if re.search(pattern, prompt_lower):
                parsed["services"].append({
                    "type": service_type,
                    "name": service_type.replace("_", " ").title(),
                    "detected_by": "regex_pattern"
                })
        
        # Extract common technology patterns
        tech_patterns = {
            'docker': r'\b(?:docker|container)\b',
            'kubernetes': r'\b(?:kubernetes|k8s|kube)\b',
            'microservices': r'\b(?:microservice|micro.?service)\b',
            'api_gateway': r'\b(?:api.?gateway|gateway)\b',
            'message_queue': r'\b(?:message.?queue|queue|messaging)\b',
            'cache': r'\b(?:cache|caching|redis|memcached)\b',
            'cdn': r'\b(?:cdn|content.?delivery)\b'
        }
        
        for tech, pattern in tech_patterns.items():
            if re.search(pattern, prompt_lower):
                parsed["technologies"].append(tech)
        
        # Extract dependency patterns
        dependency_patterns = [
            r'(?:depends on|depends upon|uses|connects to|communicates with)\s+([a-zA-Z0-9\s\-_]+)',
            r'(?:calls|invokes|triggers)\s+([a-zA-Z0-9\s\-_]+)',
            r'(?:sends data to|receives data from)\s+([a-zA-Z0-9\s\-_]+)'
        ]
        
        for pattern in dependency_patterns:
            matches = re.findall(pattern, prompt_lower)
            parsed["dependencies"].extend([match.strip() for match in matches])
        
        # Extract data flow patterns
        flow_patterns = [
            r'(?:data flows? from|traffic flows? from)\s+([a-zA-Z0-9\s\-_]+)\s+(?:to|into)\s+([a-zA-Z0-9\s\-_]+)',
            r'([a-zA-Z0-9\s\-_]+)\s+(?:sends|transmits|forwards)\s+(?:to|data to)\s+([a-zA-Z0-9\s\-_]+)'
        ]
        
        for pattern in flow_patterns:
            matches = re.findall(pattern, prompt_lower)
            for match in matches:
                if len(match) == 2:
                    parsed["data_flows"].append({
                        "source": match[0].strip(),
                        "target": match[1].strip()
                    })
        
        self.logger.debug(f"Regex-parsed architecture: {parsed}")
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
            # Handle both LLM and fallback parsing formats
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
                    
                    if service in service_type:
                        # Add dependencies
                        for dep in parsed_architecture.get("dependencies", []):
                            if service in dep.lower():
                                # Extract service type from dependency
                                for dep_service_type in self.gcp_service_patterns.keys():
                                    if dep_service_type in dep.lower():
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
