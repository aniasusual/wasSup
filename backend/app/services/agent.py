from __future__ import annotations

from typing import Any, Dict, List, Optional
import os
import asyncio
from datetime import datetime

import google.generativeai as genai

from .vector_store import QdrantVectorStore
from .conversation_manager import conversation_manager, Message


GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")


class LogAnalysisAgent:
    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
        self.vector = QdrantVectorStore()

    async def analyze(
        self,
        question: str,
        project_id: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        services: Optional[List[str]] = None,
        time_range: Optional[Dict[str, str]] = None,
        collection: Optional[str] = None,
        tab_context: Optional[Dict[str, Any]] = None,
        limit: int = 25,
    ) -> Dict[str, Any]:
        """
        Retrieve semantically relevant logs from Qdrant and ask Gemini to analyze.
        Now maintains conversation context across sessions.
        """
        # Handle session management
        if not session_id and user_id:
            # Create new session
            session_id = conversation_manager.create_session(
                user_id=user_id,
                project_id=project_id,
                initial_context={
                    "project_id": project_id,
                    "services": services or [],
                    "time_range": time_range,
                    "collection": collection or f"logs_{project_id}",
                    "filters": {"projectId": project_id},
                    "conversation_summary": "",
                    "key_insights": [],
                    "investigation_path": []
                }
            )
        
        session = conversation_manager.get_session(session_id) if session_id else None
        
        # Analyze tab context and determine investigation approach
        investigation_plan = self._analyze_tab_context_and_plan_investigation(
            question, tab_context, services, time_range
        )
        
        # Update context if new filters provided
        if session and (services or time_range):
            context_updates = {}
            if services:
                context_updates["services"] = services
            if time_range:
                context_updates["time_range"] = time_range
            conversation_manager.update_context(session_id, context_updates)
            session = conversation_manager.get_session(session_id)

        # Get current context
        current_context = session.context if session else {
            "project_id": project_id,
            "services": services or [],
            "time_range": time_range,
            "collection": collection or f"logs_{project_id}",
            "filters": {"projectId": project_id},
            "conversation_summary": "",
            "key_insights": [],
            "investigation_path": []
        }

        # Build filters from context
        filters: Dict[str, Any] = {"projectId": project_id}
        if current_context.get("services"):
            filters["resource.type"] = current_context["services"]

        # 1) Retrieve relevant logs
        retrieved = self.vector.search(
            collection=current_context["collection"],
            query=question,
            limit=limit,
            filters=filters,
        )

        # Build short context for the model
        def format_log(log: Dict[str, Any]) -> str:
            ts = log.get("timestamp") or log.get("time")
            sev = log.get("severity")
            msg = log.get("message") or log.get("textPayload")
            svc = (log.get("resource") or {}).get("type") if isinstance(log.get("resource"), dict) else None
            insert_id = log.get("id") or log.get("insertId")
            return f"[{ts}] [{sev}] [{svc}] ({insert_id}) {str(msg)[:500]}"

        context_lines = [format_log(l) for l in retrieved[:limit]]
        context_text = "\n".join(context_lines)

        # 2) Build conversation-aware prompt
        conversation_history = ""
        if session and session.messages:
            # Get all conversation history for full context
            conversation_history = "\n".join([
                f"{msg.role.upper()}: {msg.content}" for msg in session.messages
            ])

        # Build context summary
        context_summary = self._build_context_summary(current_context, session)
        
        # Create enhanced prompt with conversation context and investigation plan
        prompt = self._build_conversation_prompt(
            question=question,
            context_text=context_text,
            conversation_history=conversation_history,
            context_summary=context_summary,
            retrieved_logs=retrieved[:limit],
            investigation_plan=investigation_plan
        )

        # 3) Ask Gemini for analysis
        analysis: str = ""
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            model = genai.GenerativeModel(GEMINI_MODEL)
            resp = await asyncio.get_event_loop().run_in_executor(None, lambda: model.generate_content(prompt))
            analysis = resp.text or ""
        else:
            analysis = "Gemini is not configured (GEMINI_API_KEY missing). Showing retrieved logs only."

        # Prepare relevant logs list for UI
        relevant_logs = []
        for log in retrieved[:limit]:
            relevant_logs.append(
                {
                    "id": str(log.get("id") or log.get("insertId")),
                    "insertId": log.get("insertId"),
                    "timestamp": log.get("timestamp"),
                    "severity": log.get("severity"),
                    "messageSnippet": (log.get("message") or log.get("textPayload") or "")[:250],
                    "serviceId": (log.get("resource") or {}).get("type") if isinstance(log.get("resource"), dict) else None,
                    "traceId": log.get("traceId") or log.get("trace"),
                    "score": log.get("_score", 0.0),
                    "raw": log,
                }
            )

        # 4) Update conversation context
        if session_id:
            # Add user message to conversation
            conversation_manager.add_message(
                session_id=session_id,
                role="user",
                content=question,
                metadata={
                    "project_id": project_id,
                    "services": services,
                    "time_range": time_range,
                    "logs_retrieved": len(retrieved)
                }
            )
            
            # Add assistant response to conversation
            conversation_manager.add_message(
                session_id=session_id,
                role="assistant",
                content=analysis,
                metadata={
                    "logs_analyzed": len(retrieved),
                    "filters_applied": filters,
                    "relevantLogs": relevant_logs  # Store relevant logs in metadata
                }
            )
            
            # Update context with new insights
            self._update_conversation_context(session_id, analysis, retrieved)

        # Generate contextual follow-ups based on conversation history
        followups = self._generate_contextual_followups(session, analysis, retrieved)

        return {
            "analysis": analysis,
            "relevantLogs": relevant_logs,
            "followUps": followups,
            "sessionId": session_id,
            "contextSummary": context_summary,
            "investigationPlan": investigation_plan,
            "actions": [
                {"label": "Open top log in context", "actionId": "open_in_context", "params": {"insertId": relevant_logs[0]["insertId"] if relevant_logs else None}},
            ],
        }

    def _build_context_summary(self, context: Dict[str, Any], session: Optional[Any] = None) -> str:
        """Build a summary of the current investigation context."""
        summary_parts = []
        
        if context.get("services"):
            summary_parts.append(f"Focusing on services: {', '.join(context['services'])}")
        
        if context.get("time_range"):
            summary_parts.append(f"Time range: {context['time_range']}")
        
        if context.get("key_insights"):
            summary_parts.append(f"Previous insights: {len(context['key_insights'])} identified")
        
        if context.get("investigation_path"):
            summary_parts.append(f"Investigation steps: {len(context['investigation_path'])} taken")
        
        if session and session.messages:
            summary_parts.append(f"Conversation length: {len(session.messages)} messages")
        
        return "; ".join(summary_parts) if summary_parts else "Starting fresh investigation"

    def _build_conversation_prompt(
        self,
        question: str,
        context_text: str,
        conversation_history: str,
        context_summary: str,
        retrieved_logs: List[Dict[str, Any]],
        investigation_plan: Dict[str, Any]
    ) -> str:
        """Build a conversation-aware prompt for the AI."""
        
        # Analyze the current logs for patterns
        severity_counts = {}
        service_counts = {}
        error_patterns = []
        
        for log in retrieved_logs:
            sev = log.get("severity", "UNKNOWN")
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
            
            svc = (log.get("resource") or {}).get("type") if isinstance(log.get("resource"), dict) else None
            if svc:
                service_counts[svc] = service_counts.get(svc, 0) + 1
            
            if sev in ["ERROR", "CRITICAL"]:
                msg = log.get("message") or log.get("textPayload", "")
                if "error" in msg.lower() or "exception" in msg.lower():
                    error_patterns.append(f"[{sev}] {msg[:100]}...")

        # Build the enhanced prompt
        prompt = f"""You are a senior SRE conducting an ongoing investigation. You have access to the full conversation history and context.

INVESTIGATION PLAN:
{self._format_investigation_plan(investigation_plan)}

CURRENT CONTEXT:
{context_summary}

CONVERSATION HISTORY:
{conversation_history if conversation_history else "This is the start of our investigation."}

CURRENT LOG ANALYSIS:
- Retrieved {len(retrieved_logs)} relevant logs
- Severity distribution: {dict(severity_counts)}
- Service distribution: {dict(service_counts)}
- Error patterns found: {len(error_patterns)} significant errors

RELEVANT LOGS:
{context_text}

USER QUESTION: {question}

INSTRUCTIONS:
1. Consider the conversation history and build upon previous insights
2. If this is a follow-up question, reference previous findings
3. Provide actionable analysis with specific evidence (cite insertId)
4. Suggest next investigation steps based on the conversation flow
5. If you notice patterns across the conversation, highlight them
6. Be conversational but professional - you're an SRE partner, not just a tool
7. If the investigation plan suggests asking for clarification, do so clearly
8. If analyzing existing tabs, reference the tab context and filters

Respond in a conversational manner, building on the context and providing clear next steps."""

        return prompt

    def _update_conversation_context(self, session_id: str, analysis: str, retrieved_logs: List[Dict[str, Any]]):
        """Update the conversation context with new insights."""
        # Extract key insights from the analysis
        insights = []
        if "error" in analysis.lower():
            insights.append("Error patterns identified")
        if "trace" in analysis.lower():
            insights.append("Tracing information available")
        if "deployment" in analysis.lower():
            insights.append("Deployment-related issues detected")
        
        # Update context
        context_updates = {
            "last_analysis": analysis[:200] + "..." if len(analysis) > 200 else analysis,
            "total_logs_analyzed": len(retrieved_logs),
            "investigation_path": [f"Analyzed {len(retrieved_logs)} logs for: {analysis[:100]}..."]
        }
        
        if insights:
            context_updates["key_insights"] = insights
        
        conversation_manager.update_context(session_id, context_updates)

    def _generate_contextual_followups(self, session: Optional[Any], analysis: str, retrieved_logs: List[Dict[str, Any]]) -> List[str]:
        """Generate contextual follow-up questions based on conversation history."""
        followups = []
        
        # Base follow-ups
        followups.extend([
            "Zoom into errors with the highest severity",
            "Show logs from the same traceId for the top 3 relevant entries",
            "Check if this correlates with a recent deployment"
        ])
        
        # Context-aware follow-ups
        if session and session.messages:
            followups.append("Continue the investigation from where we left off")
            followups.append("Show me the timeline of events we've discussed")
        
        # Analysis-based follow-ups
        if "error" in analysis.lower():
            followups.append("Show me the error patterns we just identified")
        
        if "trace" in analysis.lower():
            followups.append("Follow the trace through all related services")
        
        if "deployment" in analysis.lower():
            followups.append("Compare logs before and after the deployment")
        
        return followups[:5]  # Limit to 5 follow-ups

    async def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversation history for a session."""
        messages = conversation_manager.get_conversation_history(session_id, limit)
        return [msg.to_dict() for msg in messages]

    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all active sessions for a user."""
        return conversation_manager.get_user_sessions(user_id)

    def _analyze_tab_context_and_plan_investigation(
        self,
        question: str,
        tab_context: Optional[Dict[str, Any]],
        services: Optional[List[str]],
        time_range: Optional[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Analyze open tabs and plan the investigation approach."""
        
        if not tab_context or not tab_context.get("openTabs"):
            return {
                "approach": "new_investigation",
                "reason": "No open tabs to analyze",
                "suggested_services": services or [],
                "suggested_filters": time_range or {}
            }
        
        open_tabs = tab_context["openTabs"]
        active_tab_id = tab_context.get("activeTabId")
        global_filters = tab_context.get("globalFilters", {})
        
        # Analyze what services are currently being investigated
        current_services = list(set([tab.get("serviceId") for tab in open_tabs if tab.get("serviceId")]))
        current_filters = global_filters
        
        # Determine if user wants to analyze existing tabs or new services
        question_lower = question.lower()
        
        # Check if user wants to analyze existing tabs
        wants_existing = any(word in question_lower for word in [
            "these", "current", "open", "existing", "same", "already", "tab", "tabs"
        ])
        
        # Check if user wants to analyze new services
        wants_new = any(word in question_lower for word in [
            "other", "different", "new", "additional", "another", "different service"
        ])
        
        # Check if user wants to analyze specific services
        specific_service_mentioned = False
        mentioned_services = []
        for service in current_services:
            if service.lower() in question_lower:
                specific_service_mentioned = True
                mentioned_services.append(service)
        
        if wants_existing or specific_service_mentioned:
            # User wants to analyze existing tabs
            return {
                "approach": "analyze_existing_tabs",
                "reason": "User wants to analyze logs from open tabs",
                "services_to_analyze": mentioned_services if specific_service_mentioned else current_services,
                "filters_to_use": current_filters,
                "tab_ids": [tab["id"] for tab in open_tabs if tab.get("serviceId") in (mentioned_services if specific_service_mentioned else current_services)],
                "suggested_question": f"Would you like me to analyze the logs from your open tabs ({', '.join(current_services)}) or would you prefer to analyze logs from different services?"
            }
        elif wants_new:
            # User wants to analyze new services
            return {
                "approach": "analyze_new_services",
                "reason": "User wants to analyze different services",
                "current_services": current_services,
                "suggested_question": f"I see you have tabs open for {', '.join(current_services)}. Which services would you like me to analyze instead?",
                "suggested_filters": time_range or {}
            }
        else:
            # Ambiguous - ask user for clarification
            return {
                "approach": "ask_clarification",
                "reason": "User's intent is unclear",
                "current_services": current_services,
                "suggested_question": f"I can see you have tabs open for {', '.join(current_services)}. Would you like me to:\n1. Analyze logs from these existing tabs, or\n2. Analyze logs from different services?\n\nPlease let me know your preference.",
                "suggested_filters": time_range or {}
            }




    def _format_investigation_plan(self, investigation_plan: Dict[str, Any]) -> str:
        """Format the investigation plan for the AI prompt."""
        if not investigation_plan:
            return "No specific investigation plan available."
        
        approach = investigation_plan.get("approach", "unknown")
        reason = investigation_plan.get("reason", "No reason provided")
        
        if approach == "analyze_existing_tabs":
            services = investigation_plan.get("services_to_analyze", [])
            tab_ids = investigation_plan.get("tab_ids", [])
            return f"""APPROACH: Analyze existing open tabs
REASON: {reason}
SERVICES: {", ".join(services) if services else "None specified"}
TAB IDs: {", ".join(tab_ids) if tab_ids else "None"}
ACTION: Use existing tab data and filters for analysis"""
        
        elif approach == "analyze_new_services":
            current_services = investigation_plan.get("current_services", [])
            return f"""APPROACH: Analyze new/different services
REASON: {reason}
CURRENT SERVICES: {", ".join(current_services) if current_services else "None"}
ACTION: Ask user which services to analyze and apply appropriate filters"""
        
        elif approach == "ask_clarification":
            current_services = investigation_plan.get("current_services", [])
            suggested_question = investigation_plan.get("suggested_question", "")
            return f"""APPROACH: Ask user for clarification
REASON: {reason}
CURRENT SERVICES: {", ".join(current_services) if current_services else "None"}
SUGGESTED QUESTION: {suggested_question}
ACTION: Ask user to clarify their investigation preference"""
        
        else:
            return f"""APPROACH: {approach}
REASON: {reason}
ACTION: Proceed with standard analysis"""




