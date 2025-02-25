from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request, Header
from fastapi.responses import JSONResponse, RedirectResponse
from typing import Dict, Optional, List
import logging, os, hmac, hashlib
from datetime import datetime

from nylas.models.auth import URLForAuthenticationConfig, CodeExchangeRequest
from nylas.models.webhooks import WebhookTriggers

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

@router.api_route("/webhook", methods=["GET", "POST"])
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
        # Log request details for debugging
        logger.info(f"Received webhook request: Method={request.method}, Headers={dict(request.headers)}")
        
        # Handle webhook challenge (GET request with challenge)
        if request.method == "GET" and request.query_params.get("challenge"):
            challenge = request.query_params.get("challenge")
            logger.info(f"Received Nylas webhook challenge: {challenge}")
            return {"challenge": challenge}
            
        # Handle regular GET request (browser or health check)
        if request.method == "GET":
            logger.info("Received GET request without challenge parameter (likely a browser or health check)")
            return {"status": "healthy", "message": "Webhook endpoint is active"}
            
        # Handle webhook notification (POST request)
        if request.method == "POST":
            # Get raw request body for signature verification
            raw_body = await request.body()
            logger.info(f"Received webhook body: {raw_body.decode('utf-8', errors='replace')}")
            
            # Log signature information
            logger.info(f"Webhook signature: {x_nylas_signature}")
            logger.info(f"Webhook secret configured: {'Yes' if nylas_config['webhook_secret'] else 'No'}")
            
            # TEMPORARILY DISABLED FOR TESTING
            # Verify webhook signature
            # if not verify_webhook_signature(
            #     raw_body,
            #     x_nylas_signature,
            #     nylas_config["webhook_secret"]
            # ):
            #     logger.error("Invalid webhook signature")
            #     raise HTTPException(status_code=401, detail="Invalid signature")
                
            # Parse webhook data
            webhook_data = await request.json()
            logger.info(f"Received webhook type: {webhook_data.get('type', 'unknown')}")
            logger.info(f"Webhook data: {webhook_data}")
            
            # Process webhook in background
            assistant = EmailAssistant(nylas_client, supabase, openai_client)
            background_tasks.add_task(
                assistant.process_incoming_email,
                webhook_data
            )
            
            logger.info("Successfully queued webhook for processing")
            return {"status": "processing", "webhook_type": webhook_data.get('type', 'unknown')}
        
        # If neither GET nor POST, return method not allowed
        logger.warning(f"Unsupported method: {request.method}")
        return JSONResponse(
            status_code=405,
            content={"detail": f"Method {request.method} Not Allowed"}
        )
        
    except Exception as e:
        logger.error(f"Error in webhook handler: {str(e)}")
        # Log the full traceback for debugging
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Return a proper error response instead of raising an exception
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal server error: {str(e)}"}
        )

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@router.get("/auth")
async def nylas_auth(
    request: Request,
    nylas_client=Depends(get_nylas_client),
    user_id: str = Depends(get_current_user)
):
    """
    Initiates the Nylas OAuth2 flow by redirecting to Nylas login
    """
    try:
        # Store the user_id in session for the callback
        request.session["clerk_user_id"] = user_id
        
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

@router.post("/create-webhook")
async def create_webhook(
    nylas_client=Depends(get_nylas_client),
    grant_id: str = Depends(get_nylas_grant_id),
    user_id: str = Depends(get_current_user),
    supabase=Depends(get_supabase)
):
    """Create a webhook to monitor new emails"""
    try:
        # Get webhook URL from environment or configuration
        webhook_url = os.getenv("NYLAS_WEBHOOK_URL")
        if not webhook_url:
            raise HTTPException(status_code=400, detail="Webhook URL not configured")
            
        # Get user email for notifications
        user_data = await supabase.table('users').select('email').eq('id', user_id).single().execute()
        notification_email = user_data.data.get('email') if user_data.data else None
        
        if not notification_email:
            logger.warning(f"No notification email found for user {user_id}")
            
        # Create the webhook
        webhook = nylas_client.webhooks.create(
            request_body={
                "trigger_types": [WebhookTriggers.MESSAGE_CREATED],
                "webhook_url": webhook_url,
                "description": f"Email monitor for user {user_id}",
                "notification_email_address": notification_email,
            }
        )
        
        # Store webhook ID in database for future reference
        await supabase.table('nylas_webhooks').upsert({
            'user_id': user_id,
            'webhook_id': webhook.id,
            'grant_id': grant_id,
            'created_at': datetime.utcnow().isoformat()
        }).execute()
        
        logger.info(f"Created webhook {webhook.id} for user {user_id}")
        return {"status": "success", "webhook_id": webhook.id}
        
    except Exception as e:
        logger.error(f"Error creating webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/webhooks")
async def list_webhooks(
    nylas_client=Depends(get_nylas_client),
    user_id: str = Depends(get_current_user),
    supabase=Depends(get_supabase)
):
    """List all webhooks for the current user"""
    try:
        # Get webhooks from database
        result = await supabase.table('nylas_webhooks').select('*').eq('user_id', user_id).execute()
        webhooks = result.data
        
        # Get detailed information from Nylas
        detailed_webhooks = []
        for webhook in webhooks:
            try:
                webhook_details = nylas_client.webhooks.find(webhook['webhook_id'])
                detailed_webhooks.append({
                    **webhook,
                    'details': webhook_details
                })
            except Exception as e:
                logger.error(f"Error fetching webhook details: {str(e)}")
                detailed_webhooks.append(webhook)
        
        return {"webhooks": detailed_webhooks}
        
    except Exception as e:
        logger.error(f"Error listing webhooks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    nylas_client=Depends(get_nylas_client),
    user_id: str = Depends(get_current_user),
    supabase=Depends(get_supabase)
):
    """Delete a webhook"""
    try:
        # Check if webhook belongs to user
        result = await supabase.table('nylas_webhooks').select('*').eq('webhook_id', webhook_id).eq('user_id', user_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Webhook not found")
            
        # Delete from Nylas
        nylas_client.webhooks.destroy(webhook_id)
        
        # Delete from database
        await supabase.table('nylas_webhooks').delete().eq('webhook_id', webhook_id).execute()
        
        logger.info(f"Deleted webhook {webhook_id}")
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error deleting webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))