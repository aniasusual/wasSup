"""
Context Retrieval Node

Handles log retrieval from GCP with comprehensive pagination and fallback strategies.
"""

import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional

from ..core.state import AgentState, InvestigationStep

logger = logging.getLogger(__name__)


class ContextRetrievalNode:
    """Node for retrieving context and logs from GCP."""
    
    def __init__(self, gcp_logging_client, gcp_resource_discovery):
        self.gcp_logging_client = gcp_logging_client
        self.gcp_resource_discovery = gcp_resource_discovery
    
    async def execute(self, state: AgentState) -> AgentState:
        """Execute context retrieval with fallback strategies."""
        logger.info("🧠 Smart Agent: Context retrieval node")
        
        try:
            context = state["investigation_context"]
            
            # Get available resources if we have an access token
            if state["access_token"]:
                available_resources = await self.gcp_resource_discovery.get_resource_summary(
                    state["project_id"], 
                    state["access_token"]
                )
                state["investigation_context"]["available_resources"] = available_resources
            
            # Build GCP Logging filter from parsed context
            filter_str = self._build_gcp_logging_filter(context, state["project_id"])
            
            # Fetch logs using GCP Logging REST API with comprehensive pagination
            retrieved_logs = await self.gcp_logging_client.fetch_logs(
                project_id=state["project_id"],
                filter_str=filter_str,
                access_token=state["access_token"],
                limit=state["limit"],
                fetch_all=True  # Always fetch all logs for comprehensive analysis
            )
            
            # If no logs found, try fallback strategies
            if not retrieved_logs:
                logger.info("🧠 Smart Agent: No logs found with primary filter, trying fallback strategies...")
                retrieved_logs = await self._try_fallback_strategies(context, state)
            
            # Store both formatted logs for UI and complete logs for agent analysis
            state["relevant_logs"] = self._format_logs_for_ui(retrieved_logs)
            state["investigation_context"]["retrieved_logs"] = retrieved_logs
            state["investigation_context"]["complete_logs"] = retrieved_logs
            state["investigation_context"]["filter_applied"] = filter_str
            state["current_step"] = InvestigationStep.CONTEXT_RETRIEVAL
            
            logger.info(f"🧠 Smart Agent: Retrieved {len(retrieved_logs)} logs using GCP Logging API")
            
        except Exception as e:
            state["error"] = f"Error retrieving context: {str(e)}"
            logger.error(f"❌ Smart Agent: Context retrieval error: {str(e)}")
        
        return state
    
    async def execute_streaming(self, state: AgentState, yield_updates: bool = False) -> AsyncGenerator[str, None]:
        """Execute context retrieval with streaming updates."""
        if yield_updates:
            yield f"data: {json.dumps({'type': 'status', 'message': 'Starting context retrieval...', 'step': 'context_retrieval_start'})}\n\n"
        
        logger.info("🧠 Smart Agent: Context retrieval node")
        
        try:
            context = state["investigation_context"]
            
            # Get available resources if we have an access token
            if state["access_token"]:
                if yield_updates:
                    yield f"data: {json.dumps({'type': 'status', 'message': 'Discovering available GCP resources...', 'step': 'resource_discovery'})}\n\n"
                
                available_resources = await self.gcp_resource_discovery.get_resource_summary(
                    state["project_id"], 
                    state["access_token"]
                )
                state["investigation_context"]["available_resources"] = available_resources
                
                if yield_updates:
                    resource_count = len(available_resources.get("summary", {}))
                    yield f"data: {json.dumps({'type': 'status', 'message': f'Discovered {resource_count} resource types', 'step': 'resource_discovery_complete'})}\n\n"
            
            # Build GCP Logging filter from parsed context
            if yield_updates:
                yield f"data: {json.dumps({'type': 'status', 'message': 'Building GCP log filter...', 'step': 'filter_building'})}\n\n"
            
            filter_str = self._build_gcp_logging_filter(context, state["project_id"])
            
            if yield_updates:
                yield f"data: {json.dumps({'type': 'status', 'message': f'Filter: {filter_str[:100]}...', 'step': 'filter_built'})}\n\n"
            
            # Fetch logs using GCP Logging REST API with comprehensive pagination and streaming updates
            if yield_updates:
                yield f"data: {json.dumps({'type': 'status', 'message': 'Starting comprehensive log fetch from GCP...', 'step': 'log_fetching'})}\n\n"
            
            # Use the comprehensive fetch function (always fetches all logs)
            retrieved_logs = await self.gcp_logging_client.fetch_logs(
                project_id=state["project_id"],
                filter_str=filter_str,
                access_token=state["access_token"],
                limit=state["limit"],
                fetch_all=True  # Always fetch all logs for comprehensive analysis
            )
            
            if yield_updates:
                logs_count = len(retrieved_logs)
                yield f"data: {json.dumps({'type': 'status', 'message': f'Comprehensive fetch complete: {logs_count} total logs retrieved', 'step': 'log_fetching_complete'})}\n\n"
            
            # If no logs found, try fallback strategies
            if not retrieved_logs:
                if yield_updates:
                    yield f"data: {json.dumps({'type': 'status', 'message': 'No logs found, trying fallback strategies...', 'step': 'fallback_start'})}\n\n"
                
                retrieved_logs = await self._try_fallback_strategies_streaming(context, state, yield_updates)
                
                if yield_updates:
                    fallback_logs_count = len(retrieved_logs)
                    yield f"data: {json.dumps({'type': 'status', 'message': f'Fallback complete: {fallback_logs_count} logs found', 'step': 'fallback_complete'})}\n\n"
            
            # Store both formatted logs for UI and complete logs for agent analysis
            state["relevant_logs"] = self._format_logs_for_ui(retrieved_logs)
            state["investigation_context"]["retrieved_logs"] = retrieved_logs
            state["investigation_context"]["complete_logs"] = retrieved_logs
            state["investigation_context"]["filter_applied"] = filter_str
            state["current_step"] = InvestigationStep.CONTEXT_RETRIEVAL
            
            logger.info(f"🧠 Smart Agent: Retrieved {len(retrieved_logs)} logs using GCP Logging API")
            
            if yield_updates:
                final_logs_count = len(retrieved_logs)
                yield f"data: {json.dumps({'type': 'status', 'message': f'Context retrieval complete: {final_logs_count} logs ready for analysis', 'step': 'context_retrieval_complete'})}\n\n"
            
        except Exception as e:
            state["error"] = f"Error retrieving context: {str(e)}"
            logger.error(f"❌ Smart Agent: Context retrieval error: {str(e)}")
            
            if yield_updates:
                yield f"data: {json.dumps({'type': 'error', 'message': f'Context retrieval error: {str(e)}', 'step': 'context_retrieval_error'})}\n\n"
        
        # Return the state by yielding it as the final update
        if yield_updates:
            yield f"data: {json.dumps({'type': 'state_update', 'state': state})}\n\n"
    
    async def _try_fallback_strategies(self, context: Dict[str, Any], state: AgentState) -> List[Dict[str, Any]]:
        """Try fallback strategies if primary filter returns no results."""
        retrieved_logs = []
        
        # Fallback 1: Remove severity filter
        if context.get("severity"):
            fallback_context = context.copy()
            fallback_context.pop("severity", None)
            fallback_filter = self._build_gcp_logging_filter(fallback_context, state["project_id"])
            logger.info(f"🧠 Smart Agent: Trying fallback filter (no severity): {fallback_filter}")
            
            retrieved_logs = await self.gcp_logging_client.fetch_logs(
                project_id=state["project_id"],
                filter_str=fallback_filter,
                access_token=state["access_token"],
                limit=state["limit"],
                fetch_all=True
            )
        
        # Fallback 2: Remove text search filter
        if not retrieved_logs and context.get("search_query"):
            fallback_context = context.copy()
            fallback_context.pop("search_query", None)
            fallback_filter = self._build_gcp_logging_filter(fallback_context, state["project_id"])
            logger.info(f"🧠 Smart Agent: Trying fallback filter (no text search): {fallback_filter}")
            
            retrieved_logs = await self.gcp_logging_client.fetch_logs(
                project_id=state["project_id"],
                filter_str=fallback_filter,
                access_token=state["access_token"],
                limit=state["limit"],
                fetch_all=True
            )
        
        # Fallback 3: Use only resource type
        if not retrieved_logs and context.get("services"):
            fallback_context = {"services": context["services"]}
            fallback_filter = self._build_gcp_logging_filter(fallback_context, state["project_id"])
            logger.info(f"🧠 Smart Agent: Trying fallback filter (services only): {fallback_filter}")
            
            retrieved_logs = await self.gcp_logging_client.fetch_logs(
                project_id=state["project_id"],
                filter_str=fallback_filter,
                access_token=state["access_token"],
                limit=state["limit"],
                fetch_all=True
            )
        
        # Fallback 4: Use default filter (last 7 days)
        if not retrieved_logs:
            fallback_filter = self._build_gcp_logging_filter({}, state["project_id"])
            logger.info(f"🧠 Smart Agent: Trying fallback filter (default): {fallback_filter}")
            
            retrieved_logs = await self.gcp_logging_client.fetch_logs(
                project_id=state["project_id"],
                filter_str=fallback_filter,
                access_token=state["access_token"],
                limit=state["limit"],
                fetch_all=True
            )
        
        return retrieved_logs
    
    async def _try_fallback_strategies_streaming(
        self, 
        context: Dict[str, Any], 
        state: AgentState, 
        yield_updates: bool
    ) -> List[Dict[str, Any]]:
        """Try fallback strategies with streaming updates."""
        retrieved_logs = []
        
        # Fallback 1: Remove severity filter
        if context.get("severity"):
            
            fallback_context = context.copy()
            fallback_context.pop("severity", None)
            fallback_filter = self._build_gcp_logging_filter(fallback_context, state["project_id"])
            logger.info(f"🧠 Smart Agent: Trying fallback filter (no severity): {fallback_filter}")
            
            retrieved_logs = await self.gcp_logging_client.fetch_logs(
                project_id=state["project_id"],
                filter_str=fallback_filter,
                access_token=state["access_token"],
                limit=state["limit"],
                fetch_all=True
            )
        
        # Fallback 2: Remove text search filter
        if not retrieved_logs and context.get("search_query"):
            
            fallback_context = context.copy()
            fallback_context.pop("search_query", None)
            fallback_filter = self._build_gcp_logging_filter(fallback_context, state["project_id"])
            logger.info(f"🧠 Smart Agent: Trying fallback filter (no text search): {fallback_filter}")
            
            retrieved_logs = await self.gcp_logging_client.fetch_logs(
                project_id=state["project_id"],
                filter_str=fallback_filter,
                access_token=state["access_token"],
                limit=state["limit"],
                fetch_all=True
            )
        
        # Fallback 3: Use only resource type
        if not retrieved_logs and context.get("services"):
            
            fallback_context = {"services": context["services"]}
            fallback_filter = self._build_gcp_logging_filter(fallback_context, state["project_id"])
            logger.info(f"🧠 Smart Agent: Trying fallback filter (services only): {fallback_filter}")
            
            retrieved_logs = await self.gcp_logging_client.fetch_logs(
                project_id=state["project_id"],
                filter_str=fallback_filter,
                access_token=state["access_token"],
                limit=state["limit"],
                fetch_all=True
            )
        
        # Fallback 4: Use default filter (last 7 days)
        if not retrieved_logs:
            
            fallback_filter = self._build_gcp_logging_filter({}, state["project_id"])
            logger.info(f"🧠 Smart Agent: Trying fallback filter (default): {fallback_filter}")
            
            retrieved_logs = await self.gcp_logging_client.fetch_logs(
                project_id=state["project_id"],
                filter_str=fallback_filter,
                access_token=state["access_token"],
                limit=state["limit"],
                fetch_all=True
            )
        
        return retrieved_logs
    
    def _build_gcp_logging_filter(self, context: Dict[str, Any], project_id: str) -> str:
        """
        Build GCP Logging filter string from parsed context.
        Supports comprehensive filtering including services, severity, time ranges, and text search.
        """
        filter_parts = []
        
        # Add resource type filter if services are specified
        if context.get("services"):
            service_filters = []
            for service in context["services"]:
                # Handle both exact matches and wildcard patterns
                if "*" in service:
                    # Convert wildcard to GCP regex pattern
                    regex_pattern = service.replace("*", ".*")
                    service_filters.append(f'resource.type=~"{regex_pattern}"')
                else:
                    service_filters.append(f'resource.type="{service}"')
            
            if len(service_filters) == 1:
                filter_parts.append(service_filters[0])
            else:
                filter_parts.append(f"({' OR '.join(service_filters)})")
            
            logger.info(f"🧠 Smart Agent: Added service filters: {service_filters}")
        else:
            # No specific services mentioned - this is a cross-service analysis
            logger.info(f"🧠 Smart Agent: No service filters specified - analyzing across ALL services")
        
        # Add severity filter if specified
        if context.get("severity"):
            severity_filters = []
            for severity in context["severity"]:
                severity_filters.append(f'severity="{severity}"')
            
            if len(severity_filters) == 1:
                filter_parts.append(severity_filters[0])
            else:
                filter_parts.append(f"({' OR '.join(severity_filters)})")
            
            logger.info(f"🧠 Smart Agent: Added severity filters: {severity_filters}")
        
        # Add time range filter if specified
        if context.get("time_range"):
            time_range = context["time_range"]
            start_time = time_range.get("start_time")
            end_time = time_range.get("end_time")
            
            if start_time and end_time:
                # Convert ISO format to RFC 3339 format for GCP Logging API
                start_timestamp = self._format_timestamp_for_gcp(start_time)
                end_timestamp = self._format_timestamp_for_gcp(end_time)
                
                if start_timestamp and end_timestamp:
                    filter_parts.append(f'timestamp>="{start_timestamp}" AND timestamp<="{end_timestamp}"')
                    logger.info(f"🧠 Smart Agent: Added time range filter: {start_timestamp} to {end_timestamp}")
        
        # Add text search filter if search query is available
        if context.get("search_query"):
            search_query = context["search_query"]
            # Escape quotes and wrap in textPayload search
            escaped_query = search_query.replace('"', '\\"')
            
            # Support both textPayload and jsonPayload searches
            text_search_filters = [
                f'textPayload:"{escaped_query}"',
                f'jsonPayload.message:"{escaped_query}"'
            ]
            filter_parts.append(f"({' OR '.join(text_search_filters)})")
            logger.info(f"🧠 Smart Agent: Added text search filter: {escaped_query}")
        
        # Combine all filters with AND
        if filter_parts:
            final_filter = " AND ".join(filter_parts)
            logger.info(f"🧠 Smart Agent: Built GCP filter: {final_filter}")
            return final_filter
        else:
            # Default filter for recent logs if no specific filters
            from datetime import datetime, timedelta
            now = datetime.utcnow()
            week_ago = now - timedelta(days=7)
            default_filter = f'timestamp>="{week_ago.isoformat()}Z"'
            logger.info(f"🧠 Smart Agent: Using default filter: {default_filter}")
            return default_filter
    
    def _format_timestamp_for_gcp(self, ts: str) -> str:
        """Format timestamp for GCP Logging API."""
        if not ts:
            return ts
        
        # Handle various timestamp formats
        if isinstance(ts, str):
            # Remove microseconds if present and add .000Z
            if '.' in ts and 'Z' not in ts:
                # Keep only 3 digits of microseconds
                parts = ts.split('.')
                if len(parts) == 2:
                    base_time = parts[0]
                    microseconds = parts[1][:3]  # Truncate to 3 digits
                    ts = f"{base_time}.{microseconds}Z"
            elif not ts.endswith('Z') and '+' not in ts:
                ts += 'Z'
        
        return ts
    
    def _format_logs_for_ui(self, logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format logs for UI display while preserving complete log structure."""
        formatted_logs = []
        for log in logs:
            if not log or not isinstance(log, dict):
                continue
            
            # Create a copy of the complete log object
            complete_log = log.copy()
            
            # Add UI-friendly fields for display while preserving all original data
            formatted_log = {
                # UI-friendly fields for display
                "id": str(log.get("id") or log.get("insertId") or "unknown"),
                "insertId": log.get("insertId"),
                "timestamp": log.get("timestamp"),
                "severity": log.get("severity"),
                "messageSnippet": (log.get("message") or log.get("textPayload") or "")[:250],
                "serviceId": (log.get("resource") or {}).get("type") if isinstance(log.get("resource"), dict) else None,
                "traceId": log.get("traceId") or log.get("trace"),
                "score": log.get("_score", 0.0),
                
                # Complete log object with all original fields preserved
                "completeLog": complete_log,
                
                # Legacy field for backward compatibility
                "raw": complete_log,
            }
            
            formatted_logs.append(formatted_log)
        return formatted_logs
