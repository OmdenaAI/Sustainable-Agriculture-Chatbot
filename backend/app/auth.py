from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from typing import Optional

router = APIRouter()

# In a real app, you'd use a database. For now, we'll use a simple dict
users = {}

class UserAuth(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    email: str
    token: Optional[str] = None
    message: str

@router.post("/login")
async def login(user_data: UserAuth):
    if user_data.email not in users:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if users[user_data.email] != user_data.password:  # In real app, use proper password hashing
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return AuthResponse(
        email=user_data.email,
        token="dummy_token",  # In real app, generate proper JWT token
        message="Login successful"
    )

@router.post("/signup")
async def signup(user_data: UserAuth):
    if user_data.email in users:
        raise HTTPException(status_code=400, detail="User already exists")
    
    users[user_data.email] = user_data.password  # In real app, hash the password
    
    return AuthResponse(
        email=user_data.email,
        message="Signup successful"
    )
