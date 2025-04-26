from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routers
from api.endpoints import users, courses, conversations, auth
from db.utils.database import get_db
from vector_db.qdrant_client import initialize_collection

# Create FastAPI app
app = FastAPI(
    title="Educational AI Agent API",
    description="API for AI agent integration with Laravel-based CRM",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, set specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(courses.router, prefix="/courses", tags=["Courses"])
app.include_router(conversations.router, prefix="/conversations", tags=["Conversations"])

@app.on_event("startup")
def startup_db_client():
    """Initialize vector database on startup"""
    initialize_collection()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Educational AI Agent API"}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    debug = os.getenv("API_DEBUG", "True").lower() == "true"
    
    uvicorn.run("api.main:app", host=host, port=port, reload=debug)