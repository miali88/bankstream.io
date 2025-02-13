from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
import logging
import os 
from typing import Optional, Dict
from fastapi import Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
import httpx
from dotenv import load_dotenv
import json

from svix.webhooks import Webhook, WebhookVerificationError
from app.services.clerk import post_user

router = APIRouter()

logger = logging.getLogger(__name__)

load_dotenv()

security = HTTPBearer()
CLERK_JWT_ISSUER = os.getenv("CLERK_JWT_ISSUER")
CLERK_PUBLIC_KEY = os.getenv("CLERK_PUBLIC_KEY")

if not CLERK_JWT_ISSUER:
    logger.error("CLERK_JWT_ISSUER environment variable is not set")

if not CLERK_PUBLIC_KEY:
    logger.error("CLERK_PUBLIC_KEY environment variable is not set")

# Cache for JWKS
_jwks_cache: Dict = {}

async def get_jwks():
    """Fetch the JWKS from Clerk"""
    global _jwks_cache
    
    try:
        # Return cached JWKS if available
        if _jwks_cache:
            return _jwks_cache
            
        jwks_url = f"{CLERK_JWT_ISSUER}/.well-known/jwks.json"
        logger.info(f"Fetching JWKS from: {jwks_url}")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(jwks_url)
            response.raise_for_status()
            
            _jwks_cache = response.json()
            logger.info(f"Successfully fetched JWKS with {len(_jwks_cache.get('keys', []))} keys")
            return _jwks_cache
            
    except Exception as e:
        logger.error(f"Error fetching JWKS: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching JWKS: {str(e)}")

@router.post('/webhook')
async def handle_clerk_event(request: Request, svix_id: str = Header(None), \
                             svix_timestamp: str = Header(None), svix_signature: str = Header(None)):
    print("\nclerk endpoint:")

    # Validate the webhook
    payload = await request.body()
    headers = {
        "svix-id": svix_id,
        "svix-timestamp": svix_timestamp,
        "svix-signature": svix_signature
    }
    secret = os.getenv("CLERK_SIGNING_SECRET")
    if not secret:
        raise HTTPException(status_code=500, detail="CLERK_SIGNING_SECRET not set")

    webhook = Webhook(secret)

    try:
        event = webhook.verify(payload, headers)
    except WebhookVerificationError:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    event_type = event.get('type')
    logger.info(f"Received event type: {event_type}")
    print("\nEVENT TYPE")
    print(event_type)

    if event_type == "user.created":
        print("user created")
        await post_user(event)
        
    elif event_type == "session.created":
        print("session created")
        # await post_session(payload)

    # Process the event as needed
    return {"status": "success"}

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """
    Validate the JWT token from Clerk and return the user ID
    """
    try:
        token = credentials.credentials
        logger.info("Received token for verification")
        
        # Decode header without verification to get the key ID
        try:
            header = jwt.get_unverified_header(token)
            logger.info(f"Token header decoded, kid: {header.get('kid')}")
        except Exception as e:
            logger.error(f"Error decoding token header: {str(e)}")
            raise HTTPException(status_code=401, detail="Invalid token header")
        
        # Get the key ID from the header
        kid = header.get('kid')
        if not kid:
            raise HTTPException(status_code=401, detail="No 'kid' in token header")
            
        # Get JWKS and find the matching key
        jwks = await get_jwks()
        key = None
        for jwk in jwks.get('keys', []):
            if jwk.get('kid') == kid:
                key = jwk
                break
                
        if not key:
            logger.error(f"No matching key found for kid: {kid}")
            raise HTTPException(status_code=401, detail="No matching key found")
            
        # Verify the token
        try:
            payload = jwt.decode(
                token,
                key,
                algorithms=['RS256'],
                audience='bankstream',
                issuer=CLERK_JWT_ISSUER
            )
        except jwt.ExpiredSignatureError:
            logger.error("Token has expired")
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.JWTError as e:
            logger.error(f"JWT validation error: {str(e)}")
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
            
        # Get the user ID from the token
        user_id = payload.get("sub")
        if not user_id:
            logger.error("No user ID found in token payload")
            raise HTTPException(status_code=401, detail="Invalid user ID in token")
            
        logger.info(f"Successfully validated token for user: {user_id}")
        return user_id
        
    except Exception as e:
        logger.error(f"Unexpected error during token validation: {str(e)}")
        raise HTTPException(status_code=401, detail=str(e))

