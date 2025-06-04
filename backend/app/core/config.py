import os
from pydantic_settings import BaseSettings

from typing import List

class Settings(BaseSettings):
    # API settings
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Agriculture Chatbot"
    VERSION: str = "1.0.0"
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "https://localhost:3000"]
    
    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-for-jwt")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Supabase settings
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", os.getenv("SUPABASE_ANON_KEY", ""))
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    
    # AI settings
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "no lo encontre")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    

    # Environment
    ENVIRONMENT: str = "development"  # "development", "staging", "production"
    
    # Cookie settings
    USE_HTTPS: bool = False  # Default to False for development
    
    @property
    def cookie_secure(self) -> bool:
        """Whether cookies should be secure (HTTPS only)"""
        return self.USE_HTTPS or self.ENVIRONMENT == "production"
    
    # Qdrant settings
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")
    QDRANT_COLLECTION: str = os.getenv("QDRANT_COLLECTION", "agriculture_docs")
    EMBEDDING_DIMENSION: int = 1536  # OpenAI ada-002 embedding dimension
    
    # Cookie settings
    SECURE_COOKIES: bool = os.getenv("SECURE_COOKIES", "false").lower() == "true"
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()