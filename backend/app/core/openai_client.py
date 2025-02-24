from openai import AsyncOpenAI
import os
from dotenv import load_dotenv
import logging
from typing import Optional

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Check for OpenAI API key
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("Missing OPENAI_API_KEY environment variable")

class OpenAIClientManager:
    _instance: Optional[AsyncOpenAI] = None
    
    @classmethod
    def get_client(cls) -> AsyncOpenAI:
        """Get or create OpenAI client instance"""
        if cls._instance is None:
            try:
                cls._instance = AsyncOpenAI(
                    api_key=os.getenv("OPENAI_API_KEY")
                )
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {str(e)}")
                raise
        
        return cls._instance

def get_openai_client() -> AsyncOpenAI:
    """FastAPI dependency for OpenAI client"""
    return OpenAIClientManager.get_client() 