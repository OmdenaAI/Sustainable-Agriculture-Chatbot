import logging
import os
from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Request
import uuid
from app.core.config import settings

from app.models.schemas import TokenData, User
from app.db.supabase import get_supabase_client, get_supabase_admin_client

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def verify_password(plain_password, hashed_password):
    """
    Verify a password against a hash
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """
    Hash a password
    """
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create a JWT access token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt

async def get_token_from_cookie(access_token: Optional[str] = Cookie(None)):
    """
    Extract token from cookie
    """
    logger.debug(f"Cookie access_token present: {access_token is not None}")
    
    if not access_token:
        logger.debug("No access_token cookie found")
        return None
    
    # Remove "Bearer " prefix if present
    if access_token.startswith("Bearer "):
        access_token = access_token[7:]
        logger.debug(f"Removed Bearer prefix, token length: {len(access_token)}")
    
    logger.debug(f"Returning token from cookie, first 10 chars: {access_token[:10] if access_token else 'None'}")
    return access_token


# Add this function
async def get_token(request: Request, access_token: Optional[str] = Cookie(None)):
    """
    Extract token from cookie or Authorization header
    """
    logger.debug("Attempting to get token from cookie or Authorization header")
    
    # Try to get from cookie first
    token = access_token
    logger.debug(f"Token from cookie: {'Present' if token else 'None'}")
    
    # If not in cookie, try Authorization header
    if not token:
        auth_header = request.headers.get("Authorization")
        logger.debug(f"Authorization header: {auth_header}")
        
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            logger.debug("Extracted token from Authorization header")
    
    # Remove "Bearer " prefix if present in cookie
    elif token and token.startswith("Bearer "):
        token = token[7:]
        logger.debug("Removed Bearer prefix from cookie token")
    
    logger.debug(f"Final token present: {token is not None}")
    return token

 
from app.db.supabase import get_supabase_client, get_supabase_admin_client

# async def get_current_user(
#     token: str = Depends(get_token)
# ) -> User:
#     """
#     Get the current user from the token
#     """
#     logger.debug(f"Token present in get_current_user: {token is not None}")
    
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
    
#     if not token:
#         logger.debug("No token provided, raising credentials exception")
#         raise credentials_exception
    
#     try:
#         logger.debug(f"Attempting to decode token, first 10 chars: {token[:10] if len(token) > 10 else token}")
#         payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
#         user_id: str = payload.get("sub")
        
#         if user_id is None:
#             logger.debug("No sub claim in token payload")
#             raise credentials_exception
        
#         logger.debug(f"Token contains user_id: {user_id}")
#         token_data = TokenData(user_id=user_id)
#     except JWTError as e:
#         logger.debug(f"JWT decode error: {str(e)}")
#         raise credentials_exception
#     except Exception as e:
#         logger.debug(f"Unexpected error decoding token: {str(e)}")
#         raise credentials_exception
    
#     # Get user from Supabase admin API
#     try:
#         logger.debug(f"Looking up user with ID: {token_data.user_id}")
#         supabase_admin = get_supabase_admin_client()
        
#         # Get all users and find the one with matching ID
#         user_response = supabase_admin.auth.admin.list_users()
        
#         # Find the user with the matching ID
#         matching_users = [u for u in user_response if u.id == token_data.user_id]
        
#         if not matching_users:
#             logger.debug(f"No user found with ID: {token_data.user_id}")
#             raise credentials_exception
        
#         user_data = matching_users[0]
#         logger.debug(f"Found user: {user_data.email}")
        
#         # Extract name from user metadata
#         name = user_data.user_metadata.get("name", "Unknown") if user_data.user_metadata else "Unknown"
        
#         return User(
#             id=user_data.id,
#             email=user_data.email,
#             name=name
#         )
#     except Exception as e:
#         logger.debug(f"Error retrieving user from Supabase admin API: {str(e)}")
#         raise credentials_exception      


# async def get_current_user(
#     token: str = Depends(get_token)
# ) -> User:
#     """
#     Get the current user from the token
#     """
#     # Bypass authentication in development
#     if os.environ.get("BYPASS_AUTH", "false").lower() == "true":
#         logger.debug("Authentication bypass enabled - returning test user")
#         return User(
#             id="53042bb0-b1ff-4455-993a-253f9cf8c99d",
#             email="test3@example.com",
#             name="Test User"
#         )

# Set the only allowed email here
ALLOWED_USER_EMAIL = "test3@example.com"

async def get_current_user(
    token: str = Depends(get_token)
) -> User:
    """
    Get the current user from the token and restrict to a specific email address.
    """
    # Bypass authentication in development
    if os.environ.get("BYPASS_AUTH", "false").lower() == "true":
        logger.debug("Authentication bypass enabled - returning test user")
        return User(
            id="53042bb0-b1ff-4455-993a-253f9cf8c99d",
            email=ALLOWED_USER_EMAIL,
            name="Test User"
        )

    
    logger.debug(f"Token present in get_current_user: {token is not None}")
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        logger.debug("No token provided, raising credentials exception")
        raise credentials_exception
    
    # Rest of your existing function remains unchanged
    try:
        logger.debug(f"Attempting to decode token, first 10 chars: {token[:10] if len(token) > 10 else token}")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            logger.debug("No sub claim in token payload")
            raise credentials_exception
        
        logger.debug(f"Token contains user_id: {user_id}")
        token_data = TokenData(user_id=user_id)
    except JWTError as e:
        logger.debug(f"JWT decode error: {str(e)}")
        raise credentials_exception
    except Exception as e:
        logger.debug(f"Unexpected error decoding token: {str(e)}")
        raise credentials_exception
    
    # Get user from Supabase admin API
    try:
        logger.debug(f"Looking up user with ID: {token_data.user_id}")
        supabase_admin = get_supabase_admin_client()
        
        # Get all users and find the one with matching ID
        user_response = supabase_admin.auth.admin.list_users()
        
        # Find the user with the matching ID
        matching_users = [u for u in user_response if u.id == token_data.user_id]
        
        if not matching_users:
            logger.debug(f"No user found with ID: {token_data.user_id}")
            raise credentials_exception
        
        user_data = matching_users[0]
        logger.debug(f"Found user: {user_data.email}")

         # Restrict access to only the allowed email
        if user_data.email.lower() != ALLOWED_USER_EMAIL.lower():
            logger.debug(f"User {user_data.email} is not allowed to access the system")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not allowed to access this service"
            )
        
        # Extract name from user metadata
        name = user_data.user_metadata.get("name", "Unknown") if user_data.user_metadata else "Unknown"
        
        return User(
            id=user_data.id,
            email=user_data.email,
            name=name
        )
    except Exception as e:
        logger.debug(f"Error retrieving user from Supabase admin API: {str(e)}")
        raise credentials_exception