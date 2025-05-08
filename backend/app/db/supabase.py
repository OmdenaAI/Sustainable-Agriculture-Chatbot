from supabase import create_client, Client
from typing import Dict, Any, Optional
import logging
from app.core.config import settings

# Setup logging
logger = logging.getLogger(__name__)

# Singleton pattern for Supabase client
_supabase_client = None

def get_supabase_client() -> Optional[Client]:
    """
    Returns a singleton instance of the Supabase client
    """
    global _supabase_client
    
    if _supabase_client is None:
        try:
            if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
                logger.warning("Supabase URL or key not set")
                return None
                
            _supabase_client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_ANON_KEY
            )
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Supabase client: {str(e)}")
            return None
    
    return _supabase_client

def get_supabase_admin_client() -> Optional[Client]:
    """
    Returns a Supabase client with admin privileges (service role)
    """
    try:
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
            logger.warning("Supabase URL or service role key not set")
            return None
            
        admin_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY
        )
        logger.info("Supabase admin client initialized successfully")
        return admin_client
    except Exception as e:
        logger.error(f"Error initializing Supabase admin client: {str(e)}")
        return None


class SupabaseRepository:
    """
    Repository for interacting with Supabase
    """
    def __init__(self, admin: bool = False):
        if admin:
            self.client = get_supabase_admin_client()
        else:
            self.client = get_supabase_client()
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a user profile by ID
        """
        if not self.client:
            logger.warning("Supabase client not initialized")
            return None
            
        try:
            response = self.client.table("profiles").select("*").eq("id", user_id).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            
            return None
        except Exception as e:
            logger.error(f"Error getting user profile: {str(e)}")
            return None
    
    def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a user profile
        """
        if not self.client:
            logger.warning("Supabase client not initialized")
            return None
            
        try:
            # Add updated_at timestamp
            from datetime import datetime
            profile_data["updated_at"] = datetime.utcnow().isoformat()
            
            response = self.client.table("profiles").update(profile_data).eq("id", user_id).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            
            return None
        except Exception as e:
            logger.error(f"Error updating user profile: {str(e)}")
            return None