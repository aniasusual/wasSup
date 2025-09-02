"""
Log Analysis Node

Handles AI-powered analysis of retrieved logs with intelligent batching and sampling.
"""

import asyncio
import json
import logging
import random
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List

from ..core.state import AgentState, InvestigationStep

logger = logging.getLogger(__name__)


class LogAnalysisNode:
    """Node for AI-powered log analysis."""
    
    def __init__(self, gemini_model):
        self.model = gemini_model
    
    async def execute(self, state: AgentState) -> AgentState:
        """Execute AI-powered log analysis."""
        logger.info("🧠 Smart Agent: Log analysis node")
        
        try:
            # Check if we have logs to analyze
            if not state.get("relevant_logs"):
                state["analysis"] = "No logs available for analysis."
                state["current_step"] = InvestigationStep.LOG_ANALYSIS
                logger.info("🧠 Smart Agent: No logs to analyze")
                return state
            
            logger.info(f"🧠 Smart Agent: Analyzing {len(state['relevant_logs'])} logs")
            
            # Build intelligent analysis prompt
            prompt = self._build_intelligent_analysis_prompt(state)
            
            # Get analysis from Gemini model
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.model.generate_content(prompt)
            )
            analysis = response.text or ""
            
            state["analysis"] = analysis
            state["current_step"] = InvestigationStep.LOG_ANALYSIS
            
            logger.info("🧠 Smart Agent: Analysis completed")
            
        except Exception as e:
            state["error"] = f"Error in log analysis: {str(e)}"
            logger.error(f"❌ Smart Agent: Log analysis error: {str(e)}")
            import traceback
            logger.error(f"❌ Smart Agent: Traceback: {traceback.format_exc()}")
        
        return state
    
    def _build_intelligent_analysis_prompt(self, state: AgentState) -> str:
        """Build an intelligent analysis prompt with intelligent batching for large datasets."""
        
        context = state["investigation_context"]
        
        # Get complete log objects from investigation context
        complete_logs = context.get("complete_logs") or context.get("retrieved_logs") or []
        
        # Intelligent batching for very large datasets
        total_logs = len(complete_logs)
        max_logs_for_analysis = 5000  # Reasonable limit for AI analysis
        
        if total_logs > max_logs_for_analysis:
            # For very large datasets, use intelligent sampling
            logger.info(f"🧠 Smart Agent: Large dataset detected ({total_logs} logs), using intelligent sampling")
            
            # Sample logs intelligently - prioritize recent and high-severity logs
            sampled_logs = self._intelligent_log_sampling(complete_logs, max_logs_for_analysis)
            
            logger.info(f"🧠 Smart Agent: Sampled {len(sampled_logs)} logs from {total_logs} total logs")
            analysis_logs = sampled_logs
        else:
            # Use all logs for smaller datasets
            analysis_logs = complete_logs
        
        # Use complete log objects for context - preserve all log data
        context_lines = []
        
        for log in analysis_logs:
            if not log or not isinstance(log, dict):
                continue
            
            # Include the complete log object as JSON for full context
            try:
                # Pretty print the complete log object
                log_json = json.dumps(log, indent=2, default=str)
                context_lines.append(f"LOG ENTRY:\n{log_json}\n")
            except Exception as e:
                # Fallback to string representation if JSON serialization fails
                context_lines.append(f"LOG ENTRY:\n{str(log)}\n")
        
        context_text = "\n".join(context_lines)
        
        # Build conversation history
        conversation_history = ""
        if state["session_id"]:
            from ...conversation_manager import conversation_manager
            session = conversation_manager.get_session(state["session_id"])
            if session and session.messages:
                conversation_history = "\n".join([
                    f"{msg.role.upper()}: {msg.content}" for msg in session.messages[-5:]
                ])
        
        # Create intelligent prompt
        time_range_desc = "Not specified"
        if context.get("time_range") and isinstance(context["time_range"], dict):
            time_range_desc = context["time_range"].get("description", "Not specified")
        
        # Safe list handling for join operations
        services_list = context.get("services") or []
        severity_list = context.get("severity") or []
        
        # Handle cross-service analysis
        if services_list:
            services_str = ', '.join(services_list)
        else:
            services_str = "ALL SERVICES (cross-service analysis)"
        
        severity_str = ', '.join(severity_list) if severity_list else "All levels"
        
        # Add cross-service analysis guidance
        analysis_guidance = ""
        if not services_list:
            analysis_guidance = """
CROSS-SERVICE ANALYSIS MODE:
- You are analyzing logs across ALL services in the project
- Look for patterns that span multiple services
- Identify service-to-service communication issues
- Highlight which specific services are most affected
- Suggest service-specific investigation steps
- Compare error rates and patterns across different service types
"""
        
        # Add sampling information if intelligent sampling was used
        sampling_info = ""
        if total_logs > max_logs_for_analysis:
            sampling_info = f"""
INTELLIGENT SAMPLING APPLIED:
- Total logs available: {total_logs:,}
- Logs analyzed: {len(analysis_logs):,}
- Sampling method: Intelligent priority-based sampling
- Prioritized: ERROR logs (40%), WARNING logs (30%), representative service samples (20%), recent logs (10%)
- This ensures comprehensive coverage while maintaining analysis quality
"""
        
        prompt = f"""You are a senior SRE conducting an intelligent log investigation. Analyze the provided complete log objects and provide actionable insights.

INVESTIGATION CONTEXT:
- Project ID: {state["project_id"]}
- Services: {services_str}
- Time Range: {time_range_desc}
- Severity Focus: {severity_str}
- Search Query: {context.get("search_query", state["question"])}

CONVERSATION HISTORY:
{conversation_history or "This is the start of our investigation."}

RELEVANT LOGS ({len(analysis_logs)} complete log objects):
{context_text}

USER QUESTION: {state["question"]}

INSTRUCTIONS:
1. Analyze the complete log objects for patterns, errors, and insights based on the user's focus
2. Use all available fields in the log objects (timestamp, severity, resource, labels, jsonPayload, textPayload, httpRequest, traceId, etc.)
3. Provide specific evidence from the logs (cite insertId, traceId, or other identifiers when possible)
4. Consider the conversation context and build upon previous insights
5. Suggest next investigation steps that would be most valuable
6. Be conversational but professional - you're an SRE partner
7. Focus on actionable insights that help resolve the user's concern
8. Pay attention to structured data in jsonPayload and any custom fields that might be present
{analysis_guidance}
{sampling_info}

Please analyze these complete log objects and provide a comprehensive answer to: {state["question"]}"""
        
        return prompt
    
    def _intelligent_log_sampling(self, logs: List[Dict[str, Any]], target_count: int) -> List[Dict[str, Any]]:
        """
        Intelligently sample logs from a large dataset, prioritizing:
        1. High-severity logs (ERROR, WARNING)
        2. Recent logs (by timestamp)
        3. Logs with unique patterns/errors
        4. Representative sample across all services
        """
        if len(logs) <= target_count:
            return logs
        
        # Categorize logs by severity and service
        error_logs = []
        warning_logs = []
        info_logs = []
        other_logs = []
        
        service_logs = defaultdict(list)
        
        for log in logs:
            severity = log.get("severity", "DEFAULT").upper()
            service_type = (log.get("resource", {}).get("type", "unknown") if isinstance(log.get("resource"), dict) else "unknown")
            
            service_logs[service_type].append(log)
            
            if severity == "ERROR":
                error_logs.append(log)
            elif severity == "WARNING":
                warning_logs.append(log)
            elif severity == "INFO":
                info_logs.append(log)
            else:
                other_logs.append(log)
        
        sampled_logs = []
        
        # Priority 1: Include ALL error logs (up to 40% of target)
        error_quota = min(len(error_logs), int(target_count * 0.4))
        if error_logs:
            sampled_logs.extend(error_logs[:error_quota])
        
        # Priority 2: Include warning logs (up to 30% of target)
        warning_quota = min(len(warning_logs), int(target_count * 0.3))
        if warning_logs:
            sampled_logs.extend(warning_logs[:warning_quota])
        
        # Priority 3: Include representative sample from each service (up to 20% of target)
        service_quota = int(target_count * 0.2)
        service_sample_size = max(1, service_quota // len(service_logs)) if service_logs else 0
        
        for service_type, service_log_list in service_logs.items():
            if len(sampled_logs) >= target_count:
                break
            
            # Sort by timestamp (most recent first) and take sample
            try:
                sorted_logs = sorted(service_log_list, key=lambda x: x.get("timestamp", ""), reverse=True)
                sampled_logs.extend(sorted_logs[:service_sample_size])
            except:
                # Fallback to random sampling if timestamp sorting fails
                sampled_logs.extend(random.sample(service_log_list, min(service_sample_size, len(service_log_list))))
        
        # Priority 4: Fill remaining quota with recent info logs and others
        remaining_quota = target_count - len(sampled_logs)
        if remaining_quota > 0:
            # Combine remaining logs and sort by timestamp
            remaining_logs = []
            for log in info_logs + other_logs:
                if log not in sampled_logs:
                    remaining_logs.append(log)
            
            try:
                # Sort by timestamp (most recent first)
                remaining_logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
                sampled_logs.extend(remaining_logs[:remaining_quota])
            except:
                # Fallback to random sampling
                sampled_logs.extend(random.sample(remaining_logs, min(remaining_quota, len(remaining_logs))))
        
        # Ensure we don't exceed target count
        sampled_logs = sampled_logs[:target_count]
        
        # Add metadata about sampling
        sampling_info = {
            "total_logs": len(logs),
            "sampled_logs": len(sampled_logs),
            "sampling_method": "intelligent_priority",
            "error_logs_included": len([l for l in sampled_logs if l.get("severity", "").upper() == "ERROR"]),
            "warning_logs_included": len([l for l in sampled_logs if l.get("severity", "").upper() == "WARNING"]),
            "services_represented": len(set((l.get("resource", {}).get("type", "unknown") if isinstance(l.get("resource"), dict) else "unknown") for l in sampled_logs))
        }
        
        # Add sampling info to the first log entry for reference
        if sampled_logs:
            sampled_logs[0]["_sampling_info"] = sampling_info
        
        return sampled_logs
