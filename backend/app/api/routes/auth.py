from fastapi import APIRouter, Depends, HTTPException, status, Body, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from typing import Optional
from datetime import timedelta

from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
    get_current_user,
    oauth2_scheme
)
from app.db.supabase import get_supabase_client
from app.models.schemas import User, UserCreate, Token, UserResponse

router = APIRouter()

@router.post("/signup", response_model=UserResponse)
async def signup(user_data: UserCreate = Body(...)):
    """
    Create a new user account
    """
    supabase = get_supabase_client()
    
    # Check if user already exists
    user_exists = supabase.table("users").select("*").eq("email", user_data.email).execute()
    if user_exists.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash the password
    hashed_password = get_password_hash(user_data.password)
    
    # Create new user
    new_user = {
        "name": user_data.name,
        "email": user_data.email,
        "password": hashed_password
    }
    
    result = supabase.table("users").insert(new_user).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
    
    created_user = result.data[0]
    
    return UserResponse(
        id=created_user["id"],
        name=created_user["name"],
        email=created_user["email"],
        message="User created successfully"
    )

@router.post("/login", response_model=Token)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    Authenticate a user and return a JWT token
    """
    supabase = get_supabase_client()
    
    # Find user by email
    user_result = supabase.table("users").select("*").eq("email", form_data.username).execute()
    
    if not user_result.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = user_result.data[0]
    
    # Verify password
    if not verify_password(form_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=60 * 24)  # 24 hours
    access_token = create_access_token(
        data={"sub": user["id"]},
        expires_delta=access_token_expires
    )
    
    # Set cookie
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=60 * 60 * 24,  # 24 hours
        samesite="lax",
        secure=True  # Set to False in development
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer"
    )

@router.post("/logout")
async def logout(
    response: Response,
    current_user: User = Depends(get_current_user)
):
    """
    Logout a user by clearing the cookie
    """
    response.delete_cookie(key="access_token")
    return {"message": "Successfully logged out"}

@router.get("/check", response_model=UserResponse)
async def check_auth(current_user: User = Depends(get_current_user)):
    """
    Check if the user is authenticated
    """
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        message="Authenticated"
    )
