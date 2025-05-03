from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

# User models
class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: str
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    message: Optional[str] = None

# Authentication models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[str] = None

# Profile models
class ProfileBase(BaseModel):
    name: Optional[str] = None

class ProfileUpdate(ProfileBase):
    pass

class ProfileResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# Chat models
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatHistoryItem(BaseModel):
    role: str
    content: str    

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = []
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str

# Chat history models
class ChatSessionResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    is_archived: bool

class ChatMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None

# Document models
class DocumentIngestionRequest(BaseModel):
    content: str
    title: str
    source: Optional[str] = None
    author: Optional[str] = None
    metadata: Dict[str, Any] = {}
    chunk_size: Optional[int] = None

class DocumentIngestionResponse(BaseModel):
    success: bool
    message: str
    document_id: str
    chunk_count: int

class DocumentResponse(BaseModel):
    id: str
    text: str
    title: str
    source: Optional[str] = None
    author: Optional[str] = None
    score: float
    metadata: Dict[str, Any] = {}    
