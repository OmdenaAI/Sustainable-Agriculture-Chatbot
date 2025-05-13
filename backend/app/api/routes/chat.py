from fastapi import APIRouter, Depends, HTTPException, status, Body, Request, Query, Path
from typing import List, Dict, Any, Optional
import logging
import uuid
import time
from datetime import datetime
import os

from app.models.schemas import User, ChatRequest, ChatResponse, ChatSessionResponse, ChatMessageResponse
from app.services.ai_service import AIService
from app.services.rag import RAGService
from app.db.chat_history import ChatHistoryRepository
from app.core.exceptions import DatabaseError, AIServiceError, ResourceNotFoundError
from app.core.security import get_current_user

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
ai_service = AIService()
rag_service = RAGService()
chat_history_repo = ChatHistoryRepository()

@router.post("", response_model=ChatResponse)
async def chat(
    request: Request,
    chat_request: ChatRequest = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    Process a chat message and return a response
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    start_time = time.time()
    
    try:
        logger.info(f"Chat request received: {chat_request.message[:50]}...", extra={"request_id": request_id})
        
        # Get or create a session
        session_id = chat_request.session_id
        
        try:
            # Initialize the repository if needed
            await chat_history_repo.initialize()
            
            if not session_id:
                # Create a new session
                session = await chat_history_repo.create_session(current_user.id)
                if not session:
                    raise DatabaseError("Failed to create chat session")
                session_id = session["id"]
                logger.info(f"Created new session: {session_id}", extra={"request_id": request_id})
            
            # Save user message to history
            user_message = await chat_history_repo.add_message(
                session_id=session_id,
                role="user",
                content=chat_request.message
            )
            
            if not user_message:
                logger.warning(f"Failed to save user message to history", extra={"request_id": request_id})
        except Exception as db_error:
            # If database operations fail, log but continue with the chat
            logger.error(f"Database error: {str(db_error)}", extra={"request_id": request_id})
            session_id = session_id or str(uuid.uuid4())
        
        # Generate a simple response
        try:
            # Try to use RAG and AI service
            relevant_docs = await rag_service.retrieve(chat_request.message)
            
            # Get chat history if not provided
            history = chat_request.history
            if not history and session_id:
                try:
                    # Get messages from the database
                    messages = await chat_history_repo.get_session_messages(session_id)
                    history = [{"role": msg["role"], "content": msg["content"]} for msg in messages]
                except Exception as e:
                    logger.warning(f"Could not retrieve chat history: {str(e)}", extra={"request_id": request_id})
                    history = []
            
            # Generate response using AI service
            response = await ai_service.generate_response(
                message=chat_request.message,
                context=relevant_docs,
                history=history,
                user_id=current_user.id
            )
            
        except Exception as ai_error:
            # If AI service fails, use a fallback response
            logger.error(f"AI service error: {str(ai_error)}", extra={"request_id": request_id})
            response = f"I'm having trouble generating a response right now. You asked about: {chat_request.message}"
        
        try:
            # Try to save the assistant response
            await chat_history_repo.add_message(
                session_id=session_id,
                role="assistant",
                content=response
            )
            
            # Update session title if this is the first message
            messages_count = len(await chat_history_repo.get_session_messages(session_id))
            if messages_count <= 2:  # Just the user message and assistant response
                # Generate a title based on the first message
                title = chat_request.message
                if len(title) > 50:
                    title = title[:50] + "..."
                await chat_history_repo.update_session(session_id, {"title": title})
        except Exception as save_error:
            # If saving the response fails, just log the error
            logger.error(f"Failed to save assistant response: {str(save_error)}", extra={"request_id": request_id})
        
        total_time = time.time() - start_time
        logger.info(f"Processed chat request in {total_time:.3f}s", extra={"request_id": request_id})
        
        return ChatResponse(
            response=response,
            session_id=session_id
        )
    
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}", extra={"request_id": request_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing request: {str(e)}"
        )

@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_chat_sessions(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    include_archived: bool = Query(False),
    current_user: User = Depends(get_current_user)
):
    """
    Get all chat sessions for the current user
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    try:
        logger.info(f"Getting chat sessions for user: {current_user.id}", extra={
            "request_id": request_id,
            "user_id": current_user.id,
            "limit": limit,
            "include_archived": include_archived
        })
        
        sessions = await chat_history_repo.get_user_sessions(
            user_id=current_user.id,
            limit=limit,
            include_archived=include_archived
        )
        
        logger.info(f"Retrieved {len(sessions)} sessions", extra={
            "request_id": request_id,
            "user_id": current_user.id,
            "session_count": len(sessions)
        })
        
        return [
            ChatSessionResponse(
                id=session["id"],
                title=session["title"],
                created_at=session["created_at"],
                updated_at=session["updated_at"],
                is_archived=session["is_archived"]
            )
            for session in sessions
        ]
    except DatabaseError as e:
        logger.error(f"Database error getting chat sessions: {str(e)}", extra={
            "request_id": request_id,
            "user_id": current_user.id
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error getting chat sessions: {str(e)}", extra={
            "request_id": request_id,
            "user_id": current_user.id
        }, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving chat sessions"
        )

@router.get("/sessions/{session_id}", response_model=List[ChatMessageResponse])
async def get_session_messages(
    request: Request,
    session_id: str = Path(...),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user)
):
    """
    Get all messages for a chat session
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    try:
        logger.info(f"Getting messages for session: {session_id}", extra={
            "request_id": request_id,
            "user_id": current_user.id,
            "session_id": session_id,
            "limit": limit
        })
        
        # Verify the session belongs to the user
        session = await chat_history_repo.get_session(session_id)
        if not session:
            logger.warning(f"Session not found: {session_id}", extra={
                "request_id": request_id,
                "user_id": current_user.id
            })
            raise ResourceNotFoundError("Chat session not found")
            
        if session["user_id"] != current_user.id:
            logger.warning(f"Unauthorized access to session: {session_id}", extra={
                "request_id": request_id,
                "user_id": current_user.id,
                "session_owner": session["user_id"]
            })
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this chat session"
            )
        
        messages = await chat_history_repo.get_session_messages(
            session_id=session_id,
            limit=limit
        )
        
        logger.info(f"Retrieved {len(messages)} messages", extra={
            "request_id": request_id,
            "user_id": current_user.id,
            "session_id": session_id,
            "message_count": len(messages)
        })
        
        return [
            ChatMessageResponse(
                id=message["id"],
                role=message["role"],
                content=message["content"],
                created_at=message["created_at"],
                metadata=message.get("metadata", {})
            )
            for message in messages
        ]
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DatabaseError as e:
        logger.error(f"Database error getting session messages: {str(e)}", extra={
            "request_id": request_id,
            "user_id": current_user.id,
            "session_id": session_id
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error getting session messages: {str(e)}", extra={
            "request_id": request_id,
            "user_id": current_user.id,
            "session_id": session_id
        }, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving chat messages"
        )

@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    request: Request,
    title: str = Body("New Chat"),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new chat session
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    try:
        logger.info(f"Creating new chat session for user: {current_user.id}", extra={
            "request_id": request_id,
            "user_id": current_user.id,
            "title": title
        })
        
        session = await chat_history_repo.create_session(
            user_id=current_user.id,
            title=title
        )
        
        if not session:
            raise DatabaseError("Failed to create chat session")
        
        logger.info(f"Created new session: {session['id']}", extra={
            "request_id": request_id,
            "user_id": current_user.id,
            "session_id": session["id"]
        })
        
        return ChatSessionResponse(
            id=session["id"],
            title=session["title"],
            created_at=session["created_at"],
            updated_at=session["updated_at"],
            is_archived=session["is_archived"]
        )
    except DatabaseError as e:
        logger.error(f"Database error creating chat session: {str(e)}", extra={
            "request_id": request_id,
            "user_id": current_user.id
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error creating chat session: {str(e)}", extra={
            "request_id": request_id,
            "user_id": current_user.id
        }, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating chat session"
        )

@router.patch("/sessions/{session_id}", response_model=ChatSessionResponse)
async def update_chat_session(
    request: Request,
    session_id: str = Path(...),
    title: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user)
):
    """
    Update a chat session
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    try:
        logger.info(f"Updating chat session: {session_id}", extra={
            "request_id": request_id,
            "user_id": current_user.id,
            "session_id": session_id,
            "title": title
        })
        
        # Verify the session belongs to the user
        session = await chat_history_repo.get_session(session_id)
        if not session:
            logger.warning(f"Session not found: {session_id}", extra={
                "request_id": request_id,
                "user_id": current_user.id
            })
            raise ResourceNotFoundError("Chat session not found")
            
        if session["user_id"] != current_user.id:
            logger.warning(f"Unauthorized access to session: {session_id}", extra={
                "request_id": request_id,
                "user_id": current_user.id,
                "session_owner": session["user_id"]
            })
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this chat session"
            )
        
        updated_session = await chat_history_repo.update_session(
            session_id=session_id,
            data={"title": title}
        )
        
        if not updated_session:
            raise DatabaseError("Failed to update chat session")
        
        logger.info(f"Updated session: {session_id}", extra={
            "request_id": request_id,
            "user_id": current_user.id,
            "session_id": session_id
        })
        
        return ChatSessionResponse(
            id=updated_session["id"],
            title=updated_session["title"],
            created_at=updated_session["created_at"],
            updated_at=updated_session["updated_at"],
            is_archived=updated_session["is_archived"]
        )
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DatabaseError as e:
        logger.error(f"Database error updating chat session: {str(e)}", extra={
            "request_id": request_id,
            "user_id": current_user.id,
            "session_id": session_id
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error updating chat session: {str(e)}", extra={
            "request_id": request_id,
            "user_id": current_user.id,
            "session_id": session_id
        }, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while updating chat session"
        )

@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(
    request: Request,
    session_id: str = Path(...),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a chat session
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    try:
        logger.info(f"Deleting chat session: {session_id}", extra={
            "request_id": request_id,
            "user_id": current_user.id,
            "session_id": session_id
        })
        
        # Verify the session belongs to the user
        session = await chat_history_repo.get_session(session_id)
        if not session:
            logger.warning(f"Session not found: {session_id}", extra={
                "request_id": request_id,
                "user_id": current_user.id
            })
            raise ResourceNotFoundError("Chat session not found")
            
        if session["user_id"] != current_user.id:
            logger.warning(f"Unauthorized access to session: {session_id}", extra={
                "request_id": request_id,
                "user_id": current_user.id,
                "session_owner": session["user_id"]
            })
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this chat session"
            )
        
        success = await chat_history_repo.delete_session(session_id)
        
        if not success:
            raise DatabaseError("Failed to delete chat session")
        
        logger.info(f"Deleted session: {session_id}", extra={
            "request_id": request_id,
            "user_id": current_user.id,
            "session_id": session_id
        })
        
        return None
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DatabaseError as e:
        logger.error(f"Database error deleting chat session: {str(e)}", extra={
            "request_id": request_id,
            "user_id": current_user.id,
            "session_id": session_id
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error deleting chat session: {str(e)}", extra={
            "request_id": request_id,
            "user_id": current_user.id,
            "session_id": session_id
        }, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while deleting chat session"
        )

@router.patch("/sessions/{session_id}/archive", response_model=ChatSessionResponse)
async def archive_chat_session(
    request: Request,
    session_id: str = Path(...),
    current_user: User = Depends(get_current_user)
):
    """
    Archive a chat session
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    try:
        logger.info(f"Archiving chat session: {session_id}", extra={
            "request_id": request_id,
            "user_id": current_user.id,
            "session_id": session_id
        })
        
        # Verify the session belongs to the user
        session = await chat_history_repo.get_session(session_id)
        if not session:
            logger.warning(f"Session not found: {session_id}", extra={
                "request_id": request_id,
                "user_id": current_user.id
            })
            raise ResourceNotFoundError("Chat session not found")
            
        if session["user_id"] != current_user.id:
            logger.warning(f"Unauthorized access to session: {session_id}", extra={
                "request_id": request_id,
                "user_id": current_user.id,
                "session_owner": session["user_id"]
            })
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to archive this chat session"
            )
        
        updated_session = await chat_history_repo.update_session(
            session_id=session_id,
            data={"is_archived": True}
        )
        
        if not updated_session:
            raise DatabaseError("Failed to archive chat session")
        
        logger.info(f"Archived session: {session_id}", extra={
            "request_id": request_id,
            "user_id": current_user.id,
            "session_id": session_id
        })
        
        return ChatSessionResponse(
            id=updated_session["id"],
            title=updated_session["title"],
            created_at=updated_session["created_at"],
            updated_at=updated_session["updated_at"],
            is_archived=updated_session["is_archived"]
        )
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DatabaseError as e:
        logger.error(f"Database error archiving chat session: {str(e)}", extra={
            "request_id": request_id,
            "user_id": current_user.id,
            "session_id": session_id
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error archiving chat session: {str(e)}", extra={
            "request_id": request_id,
            "user_id": current_user.id,
            "session_id": session_id
        }, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while archiving chat session"
        )