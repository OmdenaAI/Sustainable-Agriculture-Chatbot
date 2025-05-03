# backend/app/api/docs.py
from fastapi.openapi.utils import get_openapi
from fastapi import FastAPI

def custom_openapi(app: FastAPI):
    """
    Customize OpenAPI documentation
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Agriculture Chatbot API",
        version="1.0.0",
        description="API for agriculture chatbot with RAG capabilities",
        routes=app.routes,
    )
    
    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        },
        "cookieAuth": {
            "type": "apiKey",
            "in": "cookie",
            "name": "access_token"
        }
    }
    
    # Add ErrorResponse schema
    if "schemas" not in openapi_schema["components"]:
        openapi_schema["components"]["schemas"] = {}
        
    openapi_schema["components"]["schemas"]["ErrorResponse"] = {
        "type": "object",
        "properties": {
            "detail": {
                "oneOf": [
                    {
                        "type": "string"
                    },
                    {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "loc": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    }
                                },
                                "msg": {
                                    "type": "string"
                                },
                                "type": {
                                    "type": "string"
                                }
                            }
                        }
                    }
                ]
            },
            "type": {
                "type": "string"
            },
            "status_code": {
                "type": "integer"
            },
            "request_id": {
                "type": "string"
            },
            "timestamp": {
                "type": "string",
                "format": "date-time"
            }
        },
        "required": ["detail", "type"]
    }
    
    # Apply security to all operations
    for path in openapi_schema["paths"].values():
        for operation in path.values():
            # Skip security for login, signup, and health check
            if any(tag in operation.get("tags", []) for tag in ["health"]):
                continue
                
            if operation.get("operationId") in ["login", "signup"]:
                continue
                
            operation["security"] = [
                {"bearerAuth": []},
                {"cookieAuth": []}
            ]
    
    # Add custom responses
    for path in openapi_schema["paths"].values():
        for operation in path.values():
            if "responses" not in operation:
                operation["responses"] = {}
            
            # Add standard error responses
            operation["responses"]["400"] = {
                "description": "Bad Request",
                "content": {
                    "application/json": {
                        "schema": {
                            "$ref": "#/components/schemas/ErrorResponse"
                        }
                    }
                }
            }
            
            operation["responses"]["401"] = {
                "description": "Unauthorized",
                "content": {
                    "application/json": {
                        "schema": {
                            "$ref": "#/components/schemas/ErrorResponse"
                        }
                    }
                }
            }
            
            operation["responses"]["500"] = {
                "description": "Internal Server Error",
                "content": {
                    "application/json": {
                        "schema": {
                            "$ref": "#/components/schemas/ErrorResponse"
                        }
                    }
                }
            }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema