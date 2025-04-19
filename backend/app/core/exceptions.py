class BaseAppException(Exception):
    """Base exception for application-specific exceptions"""
    def __init__(self, message: str = "An error occurred"):
        self.message = message
        super().__init__(self.message)

class DatabaseError(BaseAppException):
    """Exception raised for database-related errors"""
    def __init__(self, message: str = "Database error"):
        super().__init__(message)

class AIServiceError(BaseAppException):
    """Exception raised for AI service-related errors"""
    def __init__(self, message: str = "AI service error"):
        super().__init__(message)

class ResourceNotFoundError(BaseAppException):
    """Exception raised when a requested resource is not found"""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message)

class AuthenticationError(BaseAppException):
    """Exception raised for authentication-related errors"""
    def __init__(self, message: str = "Authentication error"):
        super().__init__(message)

class ValidationError(BaseAppException):
    """Exception raised for validation errors"""
    def __init__(self, message: str = "Validation error"):
        super().__init__(message)

class RateLimitError(BaseAppException):
    """Exception raised when rate limits are exceeded"""
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message)
