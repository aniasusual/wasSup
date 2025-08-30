from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import StreamingResponse

from ..helpers.authHelper import get_current_user, get_user_tokens, is_token_expired
from ...services.langgraph_agent import LangGraphAgent


router = APIRouter(tags=["agent"])


@router.post("/agent/query")
async def agent_query(
    payload: Dict[str, Any] = Body(...),
    current_user: str = Depends(get_current_user),
):
    question: str = payload.get("question", "").strip()
    # Support both camelCase and snake_case for project_id
    project_id: str = payload.get("projectId") or payload.get("project_id", "").strip()
    session_id: Optional[str] = payload.get("sessionId") or payload.get("session_id")
    services: Optional[List[str]] = payload.get("services")
    # Support both camelCase and snake_case for time_range
    time_range: Optional[Dict[str, str]] = payload.get("timeRange") or payload.get("time_range")
    collection: Optional[str] = payload.get("collection")
    
    if not question or not project_id:
        raise HTTPException(status_code=400, detail="question and projectId are required")

    # Get user's access token for GCP API calls
    user_token_data = get_user_tokens(current_user)
    if not user_token_data:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    # Check if token is expired
    if is_token_expired(current_user):
        raise HTTPException(status_code=401, detail="Token expired, please re-authenticate")

    try:
        agent = LangGraphAgent()
        result = await agent.analyze(
            question=question,
            project_id=project_id,
            session_id=session_id,
            user_id=current_user,
            services=services,
            time_range=time_range,
            collection=collection,
            access_token=user_token_data["access_token"],
        )
        return result
    except Exception as e:
        print(f"❌ Agent query error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Agent analysis failed: {str(e)}")


@router.get("/agent/sessions")
async def get_user_sessions(
    current_user: str = Depends(get_current_user),
):
    """Get all active conversation sessions for the current user."""
    agent = LangGraphAgent()
    sessions = await agent.get_user_sessions(current_user)
    return {"sessions": sessions}


@router.get("/agent/sessions/{session_id}/history")
async def get_conversation_history(
    session_id: str,
    limit: int = 20,
    current_user: str = Depends(get_current_user),
):
    """Get conversation history for a specific session."""
    agent = LangGraphAgent()
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


@router.get("/agent/resources/{project_id}")
async def discover_project_resources(
    project_id: str,
    resource_types: Optional[List[str]] = None,
    current_user: str = Depends(get_current_user),
):
    """Discover available GCP resources in a project."""
    from ...services.gcp_resource_discovery import GCPResourceDiscovery
    
    discovery = GCPResourceDiscovery()
    result = await discovery.discover_resources(
        project_id=project_id,
        resource_types=resource_types
    )
    
    return result


@router.get("/agent/resources/{project_id}/summary")
async def get_resource_summary(
    project_id: str,
    current_user: str = Depends(get_current_user),
):
    """Get a summary of available resources in a project."""
    from ...services.gcp_resource_discovery import GCPResourceDiscovery
    
    discovery = GCPResourceDiscovery()
    result = await discovery.get_resource_summary(project_id)
    
    return result


@router.post("/agent/query/stream")
async def agent_query_streaming(
    payload: Dict[str, Any] = Body(...),
    current_user: str = Depends(get_current_user),
):
    """Streaming version of agent query that provides real-time updates."""
    question: str = payload.get("question", "").strip()
    # Support both camelCase and snake_case for project_id
    project_id: str = payload.get("projectId") or payload.get("project_id", "").strip()
    session_id: Optional[str] = payload.get("sessionId") or payload.get("session_id")
    services: Optional[List[str]] = payload.get("services")
    # Support both camelCase and snake_case for time_range
    time_range: Optional[Dict[str, str]] = payload.get("timeRange") or payload.get("time_range")
    collection: Optional[str] = payload.get("collection")
    
    if not question or not project_id:
        raise HTTPException(status_code=400, detail="question and projectId are required")

    # Get user's access token for GCP API calls
    user_token_data = get_user_tokens(current_user)
    if not user_token_data:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    # Check if token is expired
    if is_token_expired(current_user):
        raise HTTPException(status_code=401, detail="Token expired, please re-authenticate")

    try:
        agent = LangGraphAgent()
        
        async def generate_stream():
            try:
                async for update in agent.analyze_streaming(
                    question=question,
                    project_id=project_id,
                    session_id=session_id,
                    user_id=current_user,
                    services=services,
                    time_range=time_range,
                    collection=collection,
                    access_token=user_token_data["access_token"],
                ):
                    yield update
            except Exception as e:
                import json
                yield f"data: {json.dumps({'type': 'error', 'message': f'Streaming error: {str(e)}'})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent streaming failed: {str(e)}")
