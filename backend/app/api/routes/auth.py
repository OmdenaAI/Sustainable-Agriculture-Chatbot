from fastapi import APIRouter, Depends, HTTPException, status, Body, Response, Request, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from typing import Optional
from datetime import datetime, timedelta
import logging
import os

from app.core.config import settings
from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
    get_current_user,
    oauth2_scheme
)
from app.models.schemas import User, UserCreate, Token, UserResponse

# Setup logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Mock users database
USERS_DB = {
    "test@example.com": {
        "id": "53042bb0-b1ff-4455-993a-253f9cf8c99d",
        "email": "test@example.com",
        "name": "Test User",
        "hashed_password": get_password_hash("password123")
    }
}

@router.post("/signup", response_model=UserResponse)
async def signup(user_data: UserCreate = Body(...)):
    """
    Create a new user
    """
    # Check if user already exists
    if user_data.email in USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create a new user
    user_id = os.urandom(16).hex()
    hashed_password = get_password_hash(user_data.password)
    
    # Save user in memory database
    USERS_DB[user_data.email] = {
        "id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "hashed_password": hashed_password
    }
    
    logger.info(f"Created new user: {user_data.email}")
    
    return {
        "id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "message": "User created successfully"
    }

@router.post("/login", response_model=Token)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    Authenticate a user and return a JWT token
    """
    if form_data.username not in USERS_DB:
        logger.error(f"User {form_data.username} not found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = USERS_DB[form_data.username]
    hashed_password = user["hashed_password"]
    
    if not verify_password(form_data.password, hashed_password):
        logger.error(f"Invalid password for user {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["id"]}, expires_delta=access_token_expires
    )
    
    # Set cookie
    cookie_secure = settings.SECURE_COOKIES
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=cookie_secure,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    
    logger.info(f"User {form_data.username} logged in successfully")
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=User)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """
    Get the current logged in user
    """
    return current_user

@router.post("/logout")
async def logout(response: Response):
    """
    Logout the current user
    """
    response.delete_cookie(key="access_token")
    return {"message": "Logged out successfully"}

@router.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    """
    Test protected route
    """
    return {"message": "You are authenticated!", "user": current_user}
