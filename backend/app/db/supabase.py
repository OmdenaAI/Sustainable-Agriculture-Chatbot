from supabase import create_client, Client
from typing import Dict, Any, Optional
import logging


from app.core.config import settings

# Setup logging
logger = logging.getLogger(__name__)

# Singleton pattern for Supabase client
_supabase_client = None
_supabase_admin_client = None

# Monkey patch the SyncClient class to handle the proxy parameter
try:
    from supabase._sync.client import SyncClient
    
    # Store the original __init__ method
    original_init = SyncClient.__init__
    
    # Create a new __init__ method that filters out the 'proxy' parameter
    def patched_init(self, *args, **kwargs):
        # Remove 'proxy' from kwargs if it exists
        if 'proxy' in kwargs:
            logger.info("Removing 'proxy' parameter from SyncClient.__init__")
            del kwargs['proxy']
        
        # Call the original __init__ method
        original_init(self, *args, **kwargs)
    
    # Replace the original __init__ method with our patched version
    SyncClient.__init__ = patched_init
    logger.info("Successfully monkey-patched SyncClient.__init__ to handle 'proxy' parameter")
except Exception as e:
    logger.error(f"Failed to monkey-patch SyncClient.__init__: {str(e)}")

# Singleton pattern for Supabase client
_supabase_client = None

def get_supabase_client():
    global _supabase_client
    
    if _supabase_client is None:
        try:
            logger.info(f"Initializing Supabase client with URL: {settings.SUPABASE_URL}")
            
            # Create client with only the required parameters
            _supabase_client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY
            )
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Supabase client: {str(e)}")
    
    return _supabase_client

# In app/db/supabase.py
def get_supabase_admin_client():
    """Get Supabase admin client with service role key"""
    global _supabase_admin_client
    
    if _supabase_admin_client is None:
        try:
            logger.info("Initializing Supabase admin client")
            _supabase_admin_client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_ROLE_KEY
            )
            logger.info("Supabase admin client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Supabase admin client: {str(e)}")
    
    return _supabase_admin_client

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
            response = self.client.table("profile").select("*").eq("id", user_id).execute()
            
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
            
            response = self.client.table("profile").update(profile_data).eq("id", user_id).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            
            return None
        except Exception as e:
            logger.error(f"Error updating user profile: {str(e)}")
            return None