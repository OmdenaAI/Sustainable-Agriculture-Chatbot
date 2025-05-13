import logging
import os
from fastapi import Depends, HTTPException, status, Cookie, Header, Request, Security
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional

from app.core.config import settings

from app.models.schemas import TokenData, User

# Setup logging
logger = logging.getLogger(__name__)

# Define security scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)
http_bearer = HTTPBearer(auto_error=False)

# Check if authentication is bypassed
BYPASS_AUTH = os.getenv("BYPASS_AUTH", "false").lower() == "true"
if BYPASS_AUTH:
    logger.warning("Authentication bypass is enabled. This should not be used in production!")

# Mock user for development
TEST_USER = User(
    id="53042bb0-b1ff-4455-993a-253f9cf8c99d",
    name="Test User",
    email="test@example.com"
)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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

async def get_current_user(request: Request = None, token: str = Depends(oauth2_scheme), credentials: HTTPAuthorizationCredentials = Security(http_bearer)):
    """
    Get the current user from the JWT token
    """
    # If authentication is bypassed, return a test user
    if BYPASS_AUTH:
        logger.debug("Authentication bypass enabled - returning test user")
        return TEST_USER
    
    # Get token from various sources
    if request and not token and not credentials:
        token = get_token_from_request(request)
    elif credentials and not token:
        token = credentials.credentials
    
    if not token:
        logger.error("No authentication token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Decode the JWT token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            logger.error("Invalid token payload (missing sub)")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token_data = TokenData(user_id=user_id)
    except JWTError as e:
        logger.error(f"JWT verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # For testing, just return the test user
    # In a real app, you would query the database for the user
    return TEST_USER

def get_token_from_request(request: Request) -> str:
    """
    Extract token from request (various methods)
    """
    # Try to get from Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.replace("Bearer ", "")
    
    # Try to get from cookie
    token = request.cookies.get("access_token")
    if token:
        return token
    
    return None

def get_password_hash(password: str) -> str:
    """
    Mock password hashing - in a real app, use a proper hashing function
    """
    return f"hashed_{password}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Mock password verification - in a real app, use a proper verification function
    """
    return hashed_password == f"hashed_{plain_password}"

   
    
    
   