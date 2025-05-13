from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
import uuid
import uvicorn
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables from .env file
dotenv_path = os.path.join(os.path.dirname(__file__), ".env.development")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    print(f"Loaded environment variables from {dotenv_path}")
else:
    print(f"No .env file found at {dotenv_path}")

# Enable authentication bypass for development
os.environ["BYPASS_AUTH"] = "true"

# Store mock data in memory
MEMORY_DB = {
    "chat_sessions": [],
    "chat_messages": [],
    "users": [
        {
            "id": "53042bb0-b1ff-4455-993a-253f9cf8c99d",
            "name": "Test User",
            "email": "test@example.com"
        }
    ]
}

# Import routes and services
from app.api.docs import custom_openapi
from app.api.routes import auth, chat, documents
from app.core.config import settings
from app.services.rag import RAGService
from app.db.chat_history import ChatHistoryRepository

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("agriculture-chatbot")

# Initialize services
rag_service = RAGService()
chat_history_repo = ChatHistoryRepository()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize services on startup
    logger.info("Starting Agriculture Chatbot API")
    try:
        # Check if initialize methods exist before calling them
        if hasattr(rag_service, 'initialize'):
            await rag_service.initialize()
        
        await chat_history_repo.initialize()
        logger.info("Services initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing services: {str(e)}")
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down Agriculture Chatbot API")


# Create FastAPI app
app = FastAPI(
    title="Agriculture Chatbot API",
    description="API for agriculture chatbot with in-memory authentication and RAG capabilities",
    version="1.0.0",
    lifespan=lifespan,
)

# OPTIONS preflight handler - must be registered before any middleware
@app.options("/{full_path:path}")
async def options_route(full_path: str):
    logger.info(f"OPTIONS request for path: {full_path}")
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "http://localhost:3000",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "86400",  # 24 hours
        },
    )

# CORS middleware - applying explicitly with maximum permission
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_origin_regex="http://localhost:.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400,  # 24 hours
)

# Custom middleware to ensure CORS headers are always present
@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    # For preflight requests, respond immediately
    if request.method == "OPTIONS":
        logger.info(f"Intercepted OPTIONS request in middleware for path: {request.url.path}")
        return JSONResponse(
            content={},
            headers={
                "Access-Control-Allow-Origin": "http://localhost:3000",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Max-Age": "86400",  # 24 hours
            },
        )
    
    # For all other requests, add CORS headers to the response
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    
    return response

# Request ID middleware - after CORS middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Add request ID to request state
    request.state.request_id = request_id
    logger.info(f"Request started: {request.method} {request.url.path}", extra={"request_id": request_id})
    
    try:
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        process_time = time.time() - start_time
        logger.info(
            f"Request completed: {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s",
            extra={"request_id": request_id, "status_code": response.status_code, "process_time": process_time}
        )
        
        return response
    except Exception as e:
        logger.error(
            f"Request failed: {request.method} {request.url.path} - Error: {str(e)}",
            extra={"request_id": request_id},
            exc_info=True
        )
        
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "request_id": request_id}
        )

# Apply the custom OpenAPI schema AFTER creating the app
app.openapi = lambda: custom_openapi(app)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={"request_id": request_id, "path": request.url.path},
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred",
            "request_id": request_id
        },
        headers={
            "Access-Control-Allow-Origin": "http://localhost:3000",
            "Access-Control-Allow-Credentials": "true",
        }
    )

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check(request: Request):
    request_id = request.state.request_id
    logger.info(f"Health check", extra={"request_id": request_id})
    
    return {
        "status": "ok",
        "version": settings.VERSION,
        "request_id": request_id
    }

# Test endpoint to verify CORS
@app.get("/ping")
async def ping():
    return {"ping": "pong"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",  # Changed from app.main:app to main:app since we're running from the backend directory
        host="0.0.0.0",
        port=8000
    )
