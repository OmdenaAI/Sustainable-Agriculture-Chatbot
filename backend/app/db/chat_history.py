from typing import List, Dict, Any, Optional
import logging
import uuid
from datetime import datetime
import json

from app.core.exceptions import DatabaseError, ResourceNotFoundError

# Setup logging
logger = logging.getLogger(__name__)

# Global in-memory storage
_memory_db = {
    "chat_sessions": [],
    "chat_messages": []
}

class ChatHistoryRepository:
    """
    Repository for managing chat history in memory
    """
    def __init__(self):
        self.db = _memory_db
    
    async def initialize(self):
        """
        Initialize the repository
        """
        logger.info("Initializing in-memory chat history repository")
        # No initialization needed for in-memory storage
    
    async def create_session(self, user_id: str, title: str = "New Chat") -> Optional[Dict[str, Any]]:
        """
        Create a new chat session
        """
        # Create a new session
        session_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        session = {
            "id": session_id,
            "user_id": user_id,
            "title": title,
            "created_at": now,
            "updated_at": now,
            "is_archived": False
        }
        
        self.db["chat_sessions"].append(session)
        logger.info(f"Created chat session {session_id} for user {user_id}")
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a chat session by ID
        """
        for session in self.db["chat_sessions"]:
            if session["id"] == session_id:
                return session
        
        logger.warning(f"Chat session {session_id} not found")
        return None
    
    async def get_user_sessions(self, user_id: str, limit: int = 20, include_archived: bool = False) -> List[Dict[str, Any]]:
        """
        Get all chat sessions for a user
        """
        sessions = []
        
        for session in self.db["chat_sessions"]:
            if session["user_id"] == user_id:
                if include_archived or not session.get("is_archived", False):
                    sessions.append(session)
                    
                    if len(sessions) >= limit:
                        break
        
        # Sort by updated_at, newest first
        sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        
        return sessions
    
    async def update_session(self, session_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a chat session
        """
        for i, session in enumerate(self.db["chat_sessions"]):
            if session["id"] == session_id:
                # Add updated_at timestamp
                now = datetime.utcnow().isoformat()
                data["updated_at"] = now
                
                # Update the session
                self.db["chat_sessions"][i] = {**session, **data}
                
                logger.info(f"Updated chat session {session_id}")
                return self.db["chat_sessions"][i]
        
        logger.warning(f"Chat session {session_id} not found for update")
        return None
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a chat session
        """
        # First delete all messages for this session
        self.db["chat_messages"] = [msg for msg in self.db["chat_messages"] if msg["session_id"] != session_id]
        
        # Then delete the session
        initial_count = len(self.db["chat_sessions"])
        self.db["chat_sessions"] = [session for session in self.db["chat_sessions"] if session["id"] != session_id]
        
        deleted = len(self.db["chat_sessions"]) < initial_count
        
        if deleted:
            logger.info(f"Deleted chat session {session_id}")
        else:
            logger.warning(f"Chat session {session_id} not found for deletion")
        
        return deleted
    
    async def add_message(self, session_id: str, role: str, content: str, metadata: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Add a message to a chat session
        """
        # Check if session exists
        session_exists = False
        for session in self.db["chat_sessions"]:
            if session["id"] == session_id:
                session_exists = True
                break
        
        if not session_exists:
            logger.warning(f"Cannot add message to non-existent session {session_id}")
            return None
        
        # Create message data
        message_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        message = {
            "id": message_id,
            "session_id": session_id,
            "role": role,
            "content": content,
            "created_at": now,
            "metadata": metadata
        }
        
        # Add to messages
        self.db["chat_messages"].append(message)
        
        # Update session updated_at
        await self.update_session(session_id, {})
        
        logger.info(f"Added {role} message {message_id} to session {session_id}")
        return message
    
    async def get_session_messages(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all messages for a chat session
        """
        messages = [msg for msg in self.db["chat_messages"] if msg["session_id"] == session_id]
        
        # Sort by created_at, oldest first
        messages.sort(key=lambda x: x.get("created_at", ""))
        
        # Apply limit
        if limit and limit > 0:
            messages = messages[:limit]
        
        return messages
    
    async def delete_message(self, message_id: str) -> bool:
        """
        Delete a chat message
        """
        initial_count = len(self.db["chat_messages"])
        self.db["chat_messages"] = [msg for msg in self.db["chat_messages"] if msg["id"] != message_id]
        
        deleted = len(self.db["chat_messages"]) < initial_count
        
        if deleted:
            logger.info(f"Deleted chat message {message_id}")
        else:
            logger.warning(f"Chat message {message_id} not found for deletion")
        
        return deleted
