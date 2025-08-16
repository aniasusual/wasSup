from __future__ import annotations

from typing import Any, Dict, List, Optional
import uuid
from datetime import datetime, timedelta
import json
import os
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class Message:
    """Represents a single message in a conversation."""
    id: str
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata or {}
        }


@dataclass
class ConversationSession:
    """Represents a conversation session with context and history."""
    session_id: str
    user_id: str
    project_id: str
    created_at: datetime
    last_updated: datetime
    messages: List[Message]
    context: Dict[str, Any]  # Stores project context, filters, etc.
    summary: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "project_id": self.project_id,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "messages": [msg.to_dict() for msg in self.messages],
            "context": self.context,
            "summary": self.summary
        }


class ConversationManager:
    """Manages conversation sessions and maintains context."""
    
    def __init__(self):
        # In-memory storage for sessions (in production, use Redis or database)
        self.sessions: Dict[str, ConversationSession] = {}
        self.user_sessions: Dict[str, List[str]] = defaultdict(list)
        self.session_ttl = timedelta(hours=24)  # Sessions expire after 24 hours
    
    def create_session(
        self, 
        user_id: str, 
        project_id: str, 
        initial_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new conversation session."""
        session_id = str(uuid.uuid4())
        
        session = ConversationSession(
            session_id=session_id,
            user_id=user_id,
            project_id=project_id,
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow(),
            messages=[],
            context=initial_context or {
                "project_id": project_id,
                "services": [],
                "time_range": None,
                "collection": f"logs_{project_id}",
                "filters": {"projectId": project_id},
                "conversation_summary": "",
                "key_insights": [],
                "investigation_path": []
            }
        )
        
        self.sessions[session_id] = session
        self.user_sessions[user_id].append(session_id)
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Get a conversation session by ID."""
        session = self.sessions.get(session_id)
        if session and datetime.utcnow() - session.last_updated < self.session_ttl:
            return session
        elif session:
            # Session expired, remove it
            self._remove_session(session_id)
        return None
    
    def add_message(
        self, 
        session_id: str, 
        role: str, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Message]:
        """Add a message to a conversation session."""
        session = self.get_session(session_id)
        if not session:
            return None
        
        message = Message(
            id=str(uuid.uuid4()),
            role=role,
            content=content,
            timestamp=datetime.utcnow(),
            metadata=metadata
        )
        
        session.messages.append(message)
        session.last_updated = datetime.utcnow()
        
        return message
    
    def update_context(self, session_id: str, context_updates: Dict[str, Any]) -> bool:
        """Update the context of a conversation session."""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.context.update(context_updates)
        session.last_updated = datetime.utcnow()
        return True
    
    def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Message]:
        """Get recent conversation history."""
        session = self.get_session(session_id)
        if not session:
            return []
        
        return session.messages[-limit:] if limit > 0 else session.messages
    
    def get_context_summary(self, session_id: str) -> str:
        """Get a summary of the conversation context."""
        session = self.get_session(session_id)
        if not session:
            return ""
        
        context = session.context
        summary_parts = []
        
        if context.get("services"):
            summary_parts.append(f"Focusing on services: {', '.join(context['services'])}")
        
        if context.get("time_range"):
            summary_parts.append(f"Time range: {context['time_range']}")
        
        if context.get("key_insights"):
            summary_parts.append(f"Key insights: {len(context['key_insights'])} identified")
        
        if context.get("investigation_path"):
            summary_parts.append(f"Investigation path: {len(context['investigation_path'])} steps taken")
        
        return "; ".join(summary_parts) if summary_parts else "No specific context set"
    
    def _remove_session(self, session_id: str):
        """Remove a session from memory."""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            if session_id in self.user_sessions.get(session.user_id, []):
                self.user_sessions[session.user_id].remove(session_id)
            del self.sessions[session_id]
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions."""
        current_time = datetime.utcnow()
        expired_sessions = [
            session_id for session_id, session in self.sessions.items()
            if current_time - session.last_updated >= self.session_ttl
        ]
        
        for session_id in expired_sessions:
            self._remove_session(session_id)
    
    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all active sessions for a user."""
        session_ids = self.user_sessions.get(user_id, [])
        sessions = []
        
        for session_id in session_ids:
            session = self.get_session(session_id)
            if session:
                sessions.append({
                    "session_id": session_id,
                    "project_id": session.project_id,
                    "created_at": session.created_at.isoformat(),
                    "last_updated": session.last_updated.isoformat(),
                    "message_count": len(session.messages),
                    "context_summary": self.get_context_summary(session_id)
                })
        
        return sessions


# Global conversation manager instance
conversation_manager = ConversationManager()
