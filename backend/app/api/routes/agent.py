"""
Agent API routes for the LangGraph-based GCP Log Investigation System.

This module provides REST API endpoints for interacting with the
intelligent agent workflow.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Body, Request
from fastapi.responses import StreamingResponse

from ...services.agent.core import GCPLogInvestigationAgent
from ..helpers.authHelper import get_current_user, ensure_fresh_access_token

logger = logging.getLogger(__name__)

router = APIRouter(tags=["agent"])


def get_agent(request: Request) -> GCPLogInvestigationAgent:
    """Retrieve the managed agent instance from application state."""
    agent = getattr(request.app.state, "agent", None)
    if agent is None:
        logger.error("Agent instance requested before startup initialization")
        raise HTTPException(status_code=503, detail="Agent service unavailable")

    return agent


@router.post("/agent/query/stream")
async def process_agent_query_stream(
    query: Dict[str, Any] = Body(...),
    current_user: str = Depends(get_current_user),
    agent: GCPLogInvestigationAgent = Depends(get_agent),
):
    """
    Process a user query with real-time streaming responses.
    
    This endpoint provides streaming updates during the investigation process,
    allowing the frontend to show progress and intermediate results.
    
    Args:
        query: Query input containing question, project_id, and optional parameters
        current_user: Authenticated user identifier
        
    Returns:
        Server-Sent Events stream with investigation progress
    """
    async def generate_stream():
        """Generate streaming response data."""
        try:
            # Get a fresh Google access token
            try:
                fresh_access_token = await ensure_fresh_access_token(current_user)
            except Exception as e:
                yield f"data: {_create_sse_data('error', f'Auth error: {str(e)}')}\n\n"
                return

            # Add authentication information to query
            query_with_auth = query.copy()
            query_with_auth["access_token"] = fresh_access_token
            query_with_auth["user_id"] = current_user
            
            # Generate session ID if not provided
            session_id = query.get("session_id") or query.get("sessionId")  # Support both formats
            if not session_id:
                session_id = f"session_{current_user}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            # Get agent instance and process query with streaming
            # Process query with streaming
            async for chunk in agent.process_query_stream(query_with_auth, session_id):
                ctype = chunk.get("type")
                if ctype == "chunk":
                    # Stream text chunks
                    yield f"data: {_create_sse_data('chunk', chunk.get('content', ''), 'chunk')}\n\n"
                elif ctype == "node_event":
                    # Forward node events with full payload in 'data'
                    import json
                    payload = {
                        "type": "node_event",
                        "node": chunk.get("node"),
                        "title": chunk.get("title"),
                        "status": chunk.get("status"),
                        "data": chunk.get("data", {}),
                        "timestamp": chunk.get("timestamp"),
                    }
                    yield f"data: {json.dumps(payload)}\n\n"
                elif ctype == "status":
                    yield f"data: {_create_sse_data('status', chunk.get('message', ''), data=chunk.get('data'))}\n\n"
                elif ctype == "result":
                    # Send final result
                    yield f"data: {_create_sse_data('result', chunk.get('data', {}), 'result')}\n\n"
                elif ctype == "error":
                    # Send error
                    yield f"data: {_create_sse_data('error', chunk.get('message', 'Unknown error'), 'error')}\n\n"
            
            logger.info(f"Streaming query processed successfully for user {current_user}, session {session_id}")
            
        except Exception as e:
            logger.error(f"Error in streaming query: {str(e)}", exc_info=True)
            yield f"data: {_create_sse_data('error', str(e))}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.get("/agent/sessions")
async def get_user_sessions(current_user: str = Depends(get_current_user)):
    """
    Get all active sessions for the current user.
    
    Args:
        current_user: Authenticated user identifier
        
    Returns:
        List of user's active sessions
    """
    try:
        # TODO: Implement session retrieval from database
        # For now, return empty list
        sessions = []
        
        return {"sessions": sessions}
        
    except Exception as e:
        logger.error(f"Error retrieving user sessions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving sessions: {str(e)}")


@router.get("/agent/sessions/{session_id}/history")
async def get_session_history(
    session_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    Get conversation history for a specific session.
    
    Args:
        session_id: Session identifier
        current_user: Authenticated user identifier
        
    Returns:
        Session conversation history
    """
    try:
        # TODO: Implement session history retrieval from database
        # For now, return empty history
        history = []
        
        return {"history": history}
        
    except Exception as e:
        logger.error(f"Error retrieving session history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving session history: {str(e)}")


@router.delete("/agent/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    Delete a specific session and its history.
    
    Args:
        session_id: Session identifier
        current_user: Authenticated user identifier
        
    Returns:
        Success confirmation
    """
    try:
        # TODO: Implement session deletion from database
        # For now, just return success
        
        return {"message": "Session deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")


@router.get("/agent/health")
async def agent_health_check(
    agent: GCPLogInvestigationAgent = Depends(get_agent),
):
    """
    Health check endpoint for the agent system.
    
    Returns:
        Agent system health status
    """
    try:
        return {
            "status": "healthy",
            "agent_initialized": agent is not None,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Agent health check failed: {str(e)}", exc_info=True)
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


def _create_sse_data(event_type: str, message: str, step: Optional[str] = None, data: Optional[Dict[str, Any]] = None) -> str:
    """
    Create Server-Sent Events data format.
    
    Args:
        event_type: Type of event (status, result, error, chunk)
        message: Event message or content
        step: Optional step identifier
        data: Optional additional data
        
    Returns:
        JSON-formatted SSE data
    """
    import json
    
    sse_data = {
        "type": event_type,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if step:
        sse_data["step"] = step
    
    if data:
        sse_data["data"] = data
    
    return json.dumps(sse_data)
