from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional

from app.core.config import settings
from app.db.supabase import get_supabase_client
from app.models.schemas import TokenData, User

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
    if not access_token:
        return None
    
    # Remove "Bearer " prefix if present
    if access_token.startswith("Bearer "):
        access_token = access_token[7:]
    
    return access_token

async def get_current_user(
    token: str = Depends(get_token_from_cookie)
) -> User:
    """
    Get the current user from the token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        raise credentials_exception
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise credentials_exception
        
        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    supabase = get_supabase_client()
    user_result = supabase.table("users").select("*").eq("id", token_data.user_id).execute()
    
    if not user_result.data:
        raise credentials_exception
    
    user_data = user_result.data[0]
    
    return User(
        id=user_data["id"],
        email=user_data["email"],
        name=user_data["name"],
        created_at=user_data.get("created_at")
    )
