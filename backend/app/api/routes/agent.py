from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException

from ..helpers.authHelper import get_current_user
from ...services.agent import LogAnalysisAgent


router = APIRouter(tags=["agent"])


@router.post("/agent/query")
async def agent_query(
    payload: Dict[str, Any] = Body(...),
    current_user: str = Depends(get_current_user),
):
    question: str = payload.get("question", "").strip()
    project_id: str = payload.get("projectId", "").strip()
    session_id: Optional[str] = payload.get("sessionId")
    services: Optional[List[str]] = payload.get("services")
    time_range: Optional[Dict[str, str]] = payload.get("timeRange")
    collection: Optional[str] = payload.get("collection")
    tab_context: Optional[Dict[str, Any]] = payload.get("tabContext")
    
    if not question or not project_id:
        raise HTTPException(status_code=400, detail="question and projectId are required")

    agent = LogAnalysisAgent()
    result = await agent.analyze(
        question=question,
        project_id=project_id,
        session_id=session_id,
        user_id=current_user,
        services=services,
        time_range=time_range,
        collection=collection,
        tab_context=tab_context,
    )

    return result


@router.get("/agent/sessions")
async def get_user_sessions(
    current_user: str = Depends(get_current_user),
):
    """Get all active conversation sessions for the current user."""
    agent = LogAnalysisAgent()
    sessions = await agent.get_user_sessions(current_user)
    return {"sessions": sessions}


@router.get("/agent/sessions/{session_id}/history")
async def get_conversation_history(
    session_id: str,
    limit: int = 20,
    current_user: str = Depends(get_current_user),
):
    """Get conversation history for a specific session."""
    agent = LogAnalysisAgent()
    history = await agent.get_conversation_history(session_id, limit)
    return {"sessionId": session_id, "history": history}


@router.delete("/agent/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: str = Depends(get_current_user),
):
    """Delete a conversation session."""
    from ...services.conversation_manager import conversation_manager
    
    session = conversation_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.user_id != current_user:
        raise HTTPException(status_code=403, detail="Not authorized to delete this session")
    
    conversation_manager._remove_session(session_id)
    return {"message": "Session deleted successfully"}
