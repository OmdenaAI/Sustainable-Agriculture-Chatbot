from fastapi import APIRouter, Depends, HTTPException, status, Body, Response, Request, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from typing import Optional
from datetime import datetime, timedelta
import logging
import inspect

from supabase import create_client
from app.db.supabase import get_supabase_client, get_supabase_admin_client
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

# Debug logging to check if keys are loaded
logger.debug(f"SUPABASE_URL: {settings.SUPABASE_URL}")
logger.debug(f"SUPABASE_KEY length: {len(settings.SUPABASE_KEY) if settings.SUPABASE_KEY else 0}")
logger.debug(f"SUPABASE_SERVICE_ROLE_KEY length: {len(settings.SUPABASE_SERVICE_ROLE_KEY) if settings.SUPABASE_SERVICE_ROLE_KEY else 0}")

@router.post("/signup", response_model=UserResponse)
async def signup(user_data: UserCreate = Body(...)):
    """
    Create a new user account using Supabase Auth
    """
    supabase = get_supabase_client()
    supabase_admin = get_supabase_admin_client()
    
    try:
        # Create user with Supabase Auth
        auth_response = supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password,
            "options": {
                "data": {
                    "name": user_data.name
                }
            }
        })
        
        # Check if user was created successfully
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
        
        # Auto-confirm the email using admin client
        try:
            supabase_admin.auth.admin.update_user_by_id(
    auth_response.user.id,
    {"email_confirmed_at": datetime.now().isoformat()}
)
        except Exception as e:
            logger.warning(f"Could not auto-confirm email: {str(e)}")
        
        # Create a profile for the user
        profile_data = {
            "user_id": auth_response.user.id,
            "avatar_url": None,
            "bio": None
        }
        
        profile_response = supabase_admin.table("profile").insert(profile_data).execute()
        
        if not profile_response.data:
            # Log the error but don't fail the request
            logger.error("Failed to create user profile")
        
        return UserResponse(
            id=auth_response.user.id,
            name=user_data.name,
            email=auth_response.user.email,
            message="User created successfully"
        )
    
    except Exception as e:
        error_msg = str(e)
        
        # Check if the error is because the user already exists
        if "User already registered" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        logger.error(f"Error during signup: {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during signup: {error_msg}"
        )
@router.post("/confirm-email/{email}")
async def confirm_email(email: str):
    """
    Manually confirm a user's email (for testing purposes only)
    """
    supabase_admin = get_supabase_admin_client()
    
    try:
        # Get user by email
        user_response = supabase_admin.auth.admin.list_users()
        
        # Check if the response is a list (which it appears to be)
        if isinstance(user_response, list):
            users = [u for u in user_response if u.email == email]
        else:
            # Handle the case where it might have a different structure
            logger.info(f"Response type: {type(user_response)}")
            if hasattr(user_response, 'users'):
                users = [u for u in user_response.users if u.email == email]
            else:
                logger.error(f"Unexpected response format: {user_response}")
                return {"message": "Could not list users", "response": str(user_response)}
        
        if not users:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update user to confirm email
        user_id = users[0].id
        logger.info(f"Found user with ID: {user_id}")
        
        # Try different parameter names for email confirmation
        try:
            update_response = supabase_admin.auth.admin.update_user_by_id(
                user_id,
                {"email_confirmed_at": datetime.now().isoformat()}
            )
            logger.info(f"Update response: {update_response}")
        except Exception as e1:
            logger.error(f"First update attempt failed: {str(e1)}")
            try:
                # Try alternative parameter name
                update_response = supabase_admin.auth.admin.update_user_by_id(
                    user_id,
                    {"confirmed_at": datetime.now().isoformat()}
                )
                logger.info(f"Update response (second attempt): {update_response}")
            except Exception as e2:
                logger.error(f"Second update attempt failed: {str(e2)}")
                return {
                    "error": f"Could not update user: {str(e1)} / {str(e2)}",
                    "user_id": user_id
                }
        
        return {
            "message": f"Email {email} confirmation attempted",
            "user_id": user_id
        }
    except Exception as e:
        logger.error(f"Error confirming email: {str(e)}")
        return {
            "error": str(e),
            "message": "Error confirming email, see logs for details"
        }
           

@router.post("/login", response_model=Token)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    Authenticate a user and return a JWT token
    """
    supabase = get_supabase_client()
    
    try:
        # Use Supabase Auth for login instead of querying a custom table
        auth_response = supabase.auth.sign_in_with_password({
            "email": form_data.username,
            "password": form_data.password
        })
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=60 * 24)  # 24 hours
        access_token = create_access_token(
            data={"sub": auth_response.user.id},
            expires_delta=access_token_expires
        )
        
        # Set cookie
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            max_age=60 * 60 * 24,  # 24 hours
            samesite="lax",
            secure=False
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer"
        )
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
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

@router.get("/test")
async def test_endpoint():
    """
    Test endpoint that doesn't require authentication
    """
    return {
        "message": "API is working",
        "timestamp": datetime.now().isoformat(),
        "status": "success"
    }

@router.get("/test-supabase-detailed")
async def test_supabase_detailed():
    """
    Test Supabase connection with detailed debugging
    """
    try:
        # Inspect the create_client function
        signature = inspect.signature(create_client)
        logger.debug(f"create_client signature: {signature}")
        
        # Get the source code if possible
        try:
            source = inspect.getsource(create_client)
            logger.debug(f"create_client source: {source}")
        except Exception as e:
            logger.debug(f"Could not get source: {str(e)}")
        
        # Try creating client with explicit parameters
        try:
            # Only pass the required parameters explicitly
            client = create_client(
                supabase_url=settings.SUPABASE_URL,
                supabase_key=settings.SUPABASE_KEY
            )
            return {"message": "Supabase client created successfully with explicit parameters"}
        except Exception as e:
            logger.error(f"Error with explicit parameters: {str(e)}")
            
        # Try with **kwargs to avoid any unexpected parameters
        try:
            # Create a clean kwargs dict with only the required parameters
            kwargs = {
                "supabase_url": settings.SUPABASE_URL,
                "supabase_key": settings.SUPABASE_KEY
            }
            client = create_client(**kwargs)
            return {"message": "Supabase client created successfully with kwargs"}
        except Exception as e:
            logger.error(f"Error with kwargs: {str(e)}")
        
        return {"error": "All attempts to create Supabase client failed"}
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {"error": str(e)}
    
@router.get("/check-env")
async def check_environment():
    """
    Check environment variables and configuration
    """
    import os
    import sys
    
    # Get relevant environment variables
    env_vars = {k: v for k, v in os.environ.items() if 'SUPABASE' in k.upper() or 'PROXY' in k.upper()}
    
    # Get Python path
    python_path = sys.path
    
    return {
        "environment_variables": env_vars,
        "python_path": python_path,
        "python_version": sys.version
    }   

@router.get("/test-supabase-operations")
async def test_supabase_operations():
    """Test Supabase operations"""
    try:
        # Get the Supabase client
        supabase_client = get_supabase_client()
        
        # Try a simple query
        response = supabase_client.table("profile").select("*").limit(5).execute()
        
        return {
            "status": "success",
            "message": "Supabase operations test successful",
            "data": {
                "profiles_count": len(response.data) if hasattr(response, "data") else 0,
                "profiles_sample": response.data[:2] if hasattr(response, "data") else None
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Supabase operations test failed: {str(e)}",
            "error_type": type(e).__name__
        } 
    
@router.get("/test-supabase-url")
async def test_supabase_url():
    """Test Supabase URL configuration"""
    return {
        "supabase_url": settings.SUPABASE_URL,
        "is_url_valid": settings.SUPABASE_URL.startswith("https://") and "." in settings.SUPABASE_URL
    }
