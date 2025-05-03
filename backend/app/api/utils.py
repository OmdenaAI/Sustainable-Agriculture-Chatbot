from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uuid

security = HTTPBearer(auto_error=False)

# Simple in-memory user store
users = {
    "test@example.com": {
        "id": "test-user-id",
        "email": "test@example.com",
        "password": "password123"
    }
}

# Simple token store
tokens = {
    "test-token": "test@example.com"  # token -> email
}

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    A simplified version of get_current_user that always returns a test user
    """
    # For testing, always return a test user
    return users["test@example.com"]
    
    # If you want to implement actual token checking later:
    # if credentials is None:
    #     return users["test@example.com"]
    # 
    # token = credentials.credentials
    # if token not in tokens:
    #     return users["test@example.com"]
    # 
    # email = tokens[token]
    # if email not in users:
    #     return users["test@example.com"]
    # 
    # return users[email]