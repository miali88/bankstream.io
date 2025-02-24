from nylas import Client
import os
from dotenv import load_dotenv
import logging
from typing import Optional

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Required environment variables
REQUIRED_ENV_VARS = [
    "NYLAS_CLIENT_ID",
    "NYLAS_API_KEY",
    "NYLAS_API_URI"
]

# Check for missing environment variables
missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

class NylasClientManager:
    _instance: Optional[Client] = None
    
    @classmethod
    def get_client(cls) -> Client:
        """Get or create Nylas client instance"""
        if cls._instance is None:
            try:
                cls._instance = Client(
                    api_key=os.getenv("NYLAS_API_KEY"),
                    api_uri=os.getenv("NYLAS_API_URI")
                )
                logger.info("Nylas client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Nylas client: {str(e)}")
                raise
        
        return cls._instance

def get_nylas_client() -> Client:
    """FastAPI dependency for Nylas client"""
    return NylasClientManager.get_client() 