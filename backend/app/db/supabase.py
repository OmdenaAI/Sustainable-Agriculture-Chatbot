from supabase import create_client, Client
from typing import Dict, Any, Optional, List
import logging
import os
import inspect
import uuid
from datetime import datetime
import json
import copy


from app.core.config import settings

# Setup logging
logger = logging.getLogger(__name__)

# Debug environment variables
logger.info(f"SUPABASE_URL from settings: {settings.SUPABASE_URL}")
logger.info(f"SUPABASE_KEY from settings: {settings.SUPABASE_KEY}")
logger.info(f"SUPABASE_ANON_KEY from env: {os.getenv('SUPABASE_ANON_KEY')}")
logger.info(f"Direct env variables: SUPABASE_URL={os.getenv('SUPABASE_URL')}, SUPABASE_KEY={os.getenv('SUPABASE_KEY')}")

# In-memory database for mock storage
_memory_db = {
    "chat_sessions": [],
    "chat_messages": []
}

# Direct replacement for supabase.create_client 
def custom_create_client(supabase_url, supabase_key):
    """Create a Supabase client without using the proxy parameter"""
    try:
        # Import the necessary components directly
        from supabase.client import Client as SupabaseClient
        
        # Create the client directly without using the factory function
        # The factory function might be adding the proxy parameter
        client = SupabaseClient(supabase_url, supabase_key)
        return client
    except Exception as e:
        logger.error(f"Error in custom_create_client: {str(e)}")
        # Fall back to mock
        return MockSupabaseClient()

class MockResponse:
    """Mock response from Supabase API"""
    def __init__(self, data=None):
        self.data = data or []

class MockTableQuery:
    """Mock table query builder with functional in-memory implementation"""
    
    def __init__(self, client, table_name):
        self.client = client
        self.table_name = table_name
        self.conditions = []
        self.order_by = None
        self.order_desc = False
        self.limit_val = None
        self.fields = "*"
        self.operation = "select"
        self.update_data = None
        self.insert_data = None
    
    def select(self, fields="*"):
        """Select fields"""
        self.operation = "select"
        self.fields = fields
        return self
    
    def insert(self, data):
        """Insert data"""
        self.operation = "insert"
        self.insert_data = data
        return self
    
    def update(self, data):
        """Update data"""
        self.operation = "update"
        self.update_data = data
        return self
    
    def delete(self):
        """Delete data"""
        self.operation = "delete"
        return self
    
    def eq(self, column, value):
        """Equality condition"""
        self.conditions.append(("eq", column, value))
        return self
    
    def order(self, column, desc=False):
        """Order by column"""
        self.order_by = column
        self.order_desc = desc
        return self
    
    def limit(self, limit_val):
        """Limit results"""
        self.limit_val = limit_val
        return self
    
    def execute(self):
        """Execute the query"""
        try:
            if self.table_name not in self.client.memory_tables:
                logger.warning(f"Table {self.table_name} not found in mock database")
                return MockResponse([])
            
            table_data = self.client.memory_tables[self.table_name]
            
            if self.operation == "insert":
                # Handle insert operation
                if isinstance(self.insert_data, list):
                    # Multiple rows
                    result = []
                    for item in self.insert_data:
                        # Add created_at and id if not present
                        if "id" not in item:
                            item["id"] = str(uuid.uuid4())
                        if "created_at" not in item:
                            item["created_at"] = datetime.utcnow().isoformat()
                        
                        table_data.append(copy.deepcopy(item))
                        result.append(item)
                    return MockResponse(result)
                else:
                    # Single row
                    # Add id if not present
                    if "id" not in self.insert_data:
                        self.insert_data["id"] = str(uuid.uuid4())
                    if "created_at" not in self.insert_data:
                        self.insert_data["created_at"] = datetime.utcnow().isoformat()
                    
                    # Deep copy to avoid reference issues
                    item_copy = copy.deepcopy(self.insert_data)
                    table_data.append(item_copy)
                    return MockResponse([item_copy])
            
            elif self.operation == "select":
                # Apply conditions
                filtered_data = table_data
                for cond_type, column, value in self.conditions:
                    if cond_type == "eq":
                        filtered_data = [item for item in filtered_data if item.get(column) == value]
                
                # Apply ordering
                if self.order_by:
                    filtered_data.sort(
                        key=lambda x: x.get(self.order_by, ""),
                        reverse=self.order_desc
                    )
                
                # Apply limit
                if self.limit_val and self.limit_val > 0:
                    filtered_data = filtered_data[:self.limit_val]
                
                # Return a copy of the data to prevent modifications
                return MockResponse([copy.deepcopy(item) for item in filtered_data])
            
            elif self.operation == "update":
                # Apply conditions and update matching rows
                result = []
                for i, item in enumerate(table_data):
                    # Check if this item matches all conditions
                    matches = True
                    for cond_type, column, value in self.conditions:
                        if cond_type == "eq" and item.get(column) != value:
                            matches = False
                            break
                    
                    if matches:
                        # Update the item
                        updated_item = {**item, **self.update_data}
                        # Add updated_at timestamp if not already provided
                        if "updated_at" not in self.update_data:
                            updated_item["updated_at"] = datetime.utcnow().isoformat()
                        
                        # Replace the item in the table
                        table_data[i] = updated_item
                        result.append(copy.deepcopy(updated_item))
                
                return MockResponse(result)
            
            elif self.operation == "delete":
                # Apply conditions and delete matching rows
                result = []
                indices_to_delete = []
                
                for i, item in enumerate(table_data):
                    # Check if this item matches all conditions
                    matches = True
                    for cond_type, column, value in self.conditions:
                        if cond_type == "eq" and item.get(column) != value:
                            matches = False
                            break
                    
                    if matches:
                        result.append(copy.deepcopy(item))
                        indices_to_delete.append(i)
                
                # Delete items in reverse order to avoid index shifting
                for index in sorted(indices_to_delete, reverse=True):
                    del table_data[index]
                
                return MockResponse(result)
            
            # Default empty response
            return MockResponse([])
        
        except Exception as e:
            logger.error(f"Error executing mock query: {str(e)}")
            return MockResponse([])

# Implement a mock Supabase client for fallback
class MockSupabaseClient:
    """A mock Supabase client that provides an in-memory implementation"""
    
    def __init__(self):
        self.memory_tables = _memory_db
        
        # Initialize tables if they don't exist
        if "chat_sessions" not in self.memory_tables:
            self.memory_tables["chat_sessions"] = []
        
        if "chat_messages" not in self.memory_tables:
            self.memory_tables["chat_messages"] = []
        
        logger.info(f"Initialized mock Supabase client with tables: {list(self.memory_tables.keys())}")
    
    def table(self, table_name):
        """Get a table reference"""
        return MockTableQuery(self, table_name)
    
    def from_(self, table_name):
        """Alternative method to get a table reference"""
        return self.table(table_name)
    
    def rpc(self, function_name):
        """Mock RPC call"""
        return MockTableQuery(self, "_rpc")

# Singleton pattern for Supabase client
_supabase_client = None
_supabase_admin_client = None

def get_supabase_client():
    """Get a regular Supabase client, or fall back to mock client"""
    global _supabase_client
    
    if _supabase_client is None:
        try:
            # Check if environment variables are set
            supabase_url = settings.SUPABASE_URL
            supabase_key = settings.SUPABASE_KEY
            
            # If not in settings, try to get directly from environment
            if not supabase_url:
                supabase_url = os.getenv('SUPABASE_URL', '')
            if not supabase_key:
                supabase_key = os.getenv('SUPABASE_KEY', os.getenv('SUPABASE_ANON_KEY', ''))
            
            logger.info(f"Initializing Supabase client with URL: {supabase_url}")
            logger.info(f"SUPABASE_KEY length: {len(supabase_key) if supabase_key else 0}")
            
            if not supabase_url:
                logger.error("SUPABASE_URL is not set")
                return MockSupabaseClient()
            
            if not supabase_key:
                logger.error("SUPABASE_KEY is not set")
                return MockSupabaseClient()
            
            # Use our custom client creation function
            logger.info("Trying custom Supabase client creation")
            _supabase_client = custom_create_client(supabase_url, supabase_key)
            
            # Check if we got a mock or real client
            if isinstance(_supabase_client, MockSupabaseClient):
                logger.info("Using mock Supabase client")
            else:
                logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Supabase client: {str(e)}")
            _supabase_client = MockSupabaseClient()
    
    return _supabase_client

def get_supabase_admin_client():
    """Get Supabase admin client with service role key, or fall back to mock client"""
    global _supabase_admin_client
    
    if _supabase_admin_client is None:
        try:
            # Get a regular client for now - we don't have a service role key
            _supabase_admin_client = get_supabase_client()
            logger.info("Using regular Supabase client for admin functions")
        except Exception as e:
            logger.error(f"Error initializing Supabase admin client: {str(e)}")
            _supabase_admin_client = MockSupabaseClient()
    
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