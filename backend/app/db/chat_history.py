from typing import List, Dict, Any, Optional
import logging
import uuid
from datetime import datetime
import json

from app.db.supabase import get_supabase_client
from app.core.config import settings
from app.core.exceptions import DatabaseError, ResourceNotFoundError

# Setup logging
logger = logging.getLogger(__name__)

class ChatHistoryRepository:
    """
    Repository for managing chat history in Supabase
    """
    def __init__(self):
        self.client = None
    
    async def initialize(self):
        """
        Initialize the Supabase client
        """
        self.client = get_supabase_client()
        if not self.client:
            logger.warning("Supabase client not initialized")
    
    async def create_session(self, user_id: str, title: str = "New Chat") -> Optional[Dict[str, Any]]:
        """
        Create a new chat session
        """
        if not self.client:
            await self.initialize()
            if not self.client:
                logger 
            await self.initialize()
            if not self.client:
                logger.error("Failed to initialize Supabase client")
                raise DatabaseError("Database connection failed")
        
        try:
            # Create a new session
            session_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()
            
            response = self.client.table("chat_sessions").insert({
                "id": session_id,
                "user_id": user_id,
                "title": title,
                "created_at": now,
                "updated_at": now,
                "is_archived": False
            }).execute()
            
            if not response.data or len(response.data) == 0:
                logger.error(f"Failed to create chat session for user {user_id}")
                raise DatabaseError("Failed to create chat session")
            
            logger.info(f"Created chat session {session_id} for user {user_id}")
            return response.data[0]
        except Exception as e:
            logger.error(f"Error creating chat session: {str(e)}")
            raise DatabaseError(f"Failed to create chat session: {str(e)}")
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a chat session by ID
        """
        if not self.client:
            await self.initialize()
            if not self.client:
                logger.error("Failed to initialize Supabase client")
                raise DatabaseError("Database connection failed")
        
        try:
            response = self.client.table("chat_sessions").select("*").eq("id", session_id).execute()
            
            if not response.data or len(response.data) == 0:
                logger.warning(f"Chat session {session_id} not found")
                return None
            
            return response.data[0]
        except Exception as e:
            logger.error(f"Error getting chat session {session_id}: {str(e)}")
            raise DatabaseError(f"Failed to get chat session: {str(e)}")
    
    async def get_user_sessions(self, user_id: str, limit: int = 20, include_archived: bool = False) -> List[Dict[str, Any]]:
        """
        Get all chat sessions for a user
        """
        if not self.client:
            await self.initialize()
            if not self.client:
                logger.error("Failed to initialize Supabase client")
                raise DatabaseError("Database connection failed")
        
        try:
            query = self.client.table("chat_sessions").select("*").eq("user_id", user_id)
            
            if not include_archived:
                query = query.eq("is_archived", False)
            
            response = query.order("updated_at", desc=True).limit(limit).execute()
            
            if not response.data:
                return []
            
            return response.data
        except Exception as e:
            logger.error(f"Error getting user chat sessions for user {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to get user chat sessions: {str(e)}")
    
    async def update_session(self, session_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a chat session
        """
        if not self.client:
            await self.initialize()
            if not self.client:
                logger.error("Failed to initialize Supabase client")
                raise DatabaseError("Database connection failed")
        
        try:
            # Add updated_at timestamp
            update_data = {
                **data,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            response = self.client.table("chat_sessions").update(update_data).eq("id", session_id).execute()
            
            if not response.data or len(response.data) == 0:
                logger.warning(f"Chat session {session_id} not found or not updated")
                return None
            
            return response.data[0]
        except Exception as e:
            logger.error(f"Error updating chat session {session_id}: {str(e)}")
            raise DatabaseError(f"Failed to update chat session: {str(e)}")
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a chat session
        """
        if not self.client:
            await self.initialize()
            if not self.client:
                logger.error("Failed to initialize Supabase client")
                raise DatabaseError("Database connection failed")
        
        try:
            # First delete all messages in the session
            self.client.table("chat_messages").delete().eq("session_id", session_id).execute()
            
            # Then delete the session
            response = self.client.table("chat_sessions").delete().eq("id", session_id).execute()
            
            success = response.data is not None
            if success:
                logger.info(f"Deleted chat session {session_id}")
            else:
                logger.warning(f"Failed to delete chat session {session_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error deleting chat session {session_id}: {str(e)}")
            raise DatabaseError(f"Failed to delete chat session: {str(e)}")
    
    async def add_message(self, session_id: str, role: str, content: str, metadata: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Add a message to a chat session
        """
        if not self.client:
            await self.initialize()
            if not self.client:
                logger.error("Failed to initialize Supabase client")
                raise DatabaseError("Database connection failed")
        
        try:
            # Create message data
            message_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()
            
            message_data = {
                "id": message_id,
                "session_id": session_id,
                "role": role,
                "content": content,
                "created_at": now
            }
            
            if metadata:
                # Convert metadata to JSON string if it's not already
                if isinstance(metadata, dict):
                    message_data["metadata"] = json.dumps(metadata)
                else:
                    message_data["metadata"] = metadata
            
            # Insert message
            response = self.client.table("chat_messages").insert(message_data).execute()
            
            if not response.data or len(response.data) == 0:
                logger.error(f"Failed to add message to session {session_id}")
                raise DatabaseError("Failed to add chat message")
            
            # Update session updated_at timestamp
            await self.update_session(session_id, {})
            
            logger.info(f"Added {role} message {message_id} to session {session_id}")
            return response.data[0]
        except Exception as e:
            logger.error(f"Error adding chat message to session {session_id}: {str(e)}")
            raise DatabaseError(f"Failed to add chat message: {str(e)}")
    
    async def get_session_messages(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all messages for a chat session
        """
        if not self.client:
            await self.initialize()
            if not self.client:
                logger.error("Failed to initialize Supabase client")
                raise DatabaseError("Database connection failed")
        
        try:
            response = self.client.table("chat_messages") \
                .select("*") \
                .eq("session_id", session_id) \
                .order("created_at", desc=False) \
                .limit(limit) \
                .execute()
            
            if not response.data:
                return []
            
            # Parse metadata JSON if present
            messages = []
            for msg in response.data:
                if "metadata" in msg and msg["metadata"]:
                    try:
                        if isinstance(msg["metadata"], str):
                            msg["metadata"] = json.loads(msg["metadata"])
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse metadata JSON for message {msg['id']}")
                
                messages.append(msg)
            
            return messages
        except Exception as e:
            logger.error(f"Error getting session messages for session {session_id}: {str(e)}")
            raise DatabaseError(f"Failed to get session messages: {str(e)}")
    
    async def delete_message(self, message_id: str) -> bool:
        """
        Delete a chat message
        """
        if not self.client:
            await self.initialize()
            if not self.client:
                logger.error("Failed to initialize Supabase client")
                raise DatabaseError("Database connection failed")
        
        try:
            response = self.client.table("chat_messages").delete().eq("id", message_id).execute()
            
            success = response.data is not None
            if success:
                logger.info(f"Deleted chat message {message_id}")
            else:
                logger.warning(f"Failed to delete chat message {message_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error deleting chat message {message_id}: {str(e)}")
            raise DatabaseError(f"Failed to delete chat message: {str(e)}")
