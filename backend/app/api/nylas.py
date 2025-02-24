from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request, Header
from fastapi.responses import JSONResponse, RedirectResponse
from typing import Dict, Optional
import logging, os, hmac, hashlib
from datetime import datetime

from nylas.models.auth import URLForAuthenticationConfig, CodeExchangeRequest

from app.core.supabase_client import get_supabase
from app.core.nylas_client import get_nylas_client
from app.core.openai_client import get_openai_client
from app.core.auth import get_current_user
from app.services.nylas import store_nylas_credentials, get_nylas_credentials, EmailAssistant

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter()

# Load Nylas configuration
nylas_config = {
    "client_id": os.getenv("NYLAS_CLIENT_ID"),
    "callback_uri": os.getenv("NYLAS_CALLBACK_URI"),
    "api_key": os.getenv("NYLAS_API_KEY"),
    "api_uri": os.getenv("NYLAS_API_URI"),
    "webhook_secret": os.getenv("NYLAS_WEBHOOK_SECRET"),
}

def verify_webhook_signature(
    raw_data: bytes,
    signature: Optional[str],
    secret: str
) -> bool:
    """Verify the webhook signature using HMAC"""
    if not signature:
        logger.error("No signature provided in webhook request")
        return False
        
    computed_signature = hmac.new(
        secret.encode('utf-8'),
        raw_data,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(computed_signature, signature)

@router.post("/webhook")
async def nylas_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    nylas_client=Depends(get_nylas_client),
    supabase=Depends(get_supabase),
    openai_client=Depends(get_openai_client),
    x_nylas_signature: Optional[str] = Header(None)
):
    """Handle Nylas webhooks for email processing"""
    try:
        # Get raw request body for signature verification
        raw_body = await request.body()
        
        # Handle webhook challenge if present
        if request.query_params.get("challenge"):
            logger.info("Received Nylas webhook challenge")
            return {"challenge": request.query_params["challenge"]}
            
        # Verify webhook signature
        if not verify_webhook_signature(
            raw_body,
            x_nylas_signature,
            nylas_config["webhook_secret"]
        ):
            logger.error("Invalid webhook signature")
            raise HTTPException(status_code=401, detail="Invalid signature")
            
        # Parse webhook data
        webhook_data = await request.json()
        logger.info(f"Received webhook type: {webhook_data.get('type', 'unknown')}")
        
        # Process webhook in background
        assistant = EmailAssistant(nylas_client, supabase, openai_client)
        background_tasks.add_task(
            assistant.process_incoming_email,
            webhook_data
        )
        
        logger.info("Successfully queued webhook for processing")
        return {"status": "processing"}
        
    except Exception as e:
        logger.error(f"Error in webhook handler: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@router.get("/auth")
async def nylas_auth(
    request: Request,
    nylas_client=Depends(get_nylas_client),
    # user_id: str = Depends(get_current_user)
):
    """
    Initiates the Nylas OAuth2 flow by redirecting to Nylas login
    """
    try:
        # Store the user_id in session for the callback
        # request.session["clerk_user_id"] = user_id
        
        auth_url = nylas_client.auth.url_for_oauth2({
            "client_id": nylas_config["client_id"],
            "redirect_uri": nylas_config["callback_uri"],
        })
        return RedirectResponse(url=auth_url)
    except Exception as e:
        logger.error(f"Error initiating OAuth flow: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/oauth/exchange")
async def oauth_exchange(
    request: Request,
    code: str,
    nylas_client=Depends(get_nylas_client),
    supabase=Depends(get_supabase)
):
    """
    Handles the OAuth2 callback from Nylas
    """
    logger.info(f"Received code: {code}")
    logger.info(f"Using callback URI: {nylas_config['callback_uri']}")

    # Get the user_id from session
    user_id = request.session.get("clerk_user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="No user ID found in session")

    if not code:
        raise HTTPException(status_code=400, detail="No authorization code returned from Nylas")

    try:
        exchange_request = CodeExchangeRequest({
            "redirect_uri": nylas_config["callback_uri"],
            "code": code,
            "client_id": nylas_config["client_id"]
        })
        
        exchange = nylas_client.auth.exchange_code_for_token(exchange_request)
        grant_id = exchange.grant_id

        # Store the credentials in Supabase
        await store_nylas_credentials(supabase, user_id, grant_id)

        # Redirect to frontend with success message
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        return RedirectResponse(
            url=f"{frontend_url}/dashboard?nylas_connected=true",
            status_code=302
        )
    except Exception as e:
        logger.error(f"Exchange error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to exchange authorization code for token: {str(e)}")

async def get_nylas_grant_id(
    user_id: str = Depends(get_current_user),
    supabase=Depends(get_supabase)
) -> str:
    grant_id = await get_nylas_credentials(supabase, user_id)
    if not grant_id:
        raise HTTPException(status_code=401, detail="Not authenticated with Nylas")
    return grant_id

@router.get("/recent-emails")
async def recent_emails(
    grant_id: str = Depends(get_nylas_grant_id), 
    nylas_client=Depends(get_nylas_client)
):
    """Retrieves recent emails using the stored grant_id"""
    try:
        messages = nylas_client.messages.list(grant_id, {"limit": 5}).data
        return JSONResponse(messages)
    except Exception as e:
        logger.error(f"Error fetching emails: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching emails: {str(e)}")

@router.get("/status")
async def connection_status(
    supabase=Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """Check if user has connected their email"""
    grant_id = await get_nylas_credentials(supabase, user_id)
    return {"connected": bool(grant_id)}