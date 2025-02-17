from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.main import api_router
from starlette.middleware.sessions import SessionMiddleware
import logging
import os

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title="BankStream API",
    description="API for banking and payment operations",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup session middleware with a secure secret key
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY", "your-secret-key-change-in-production"),
    session_cookie="xero_session",
    max_age=86400  # 24 hours
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to BankStream IO"}

@app.on_event("startup")
async def startup_event():
    logger.debug("Starting up FastAPI server...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.debug("Shutting down FastAPI server...")
