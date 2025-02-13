from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
import logging
import os 
from dotenv import load_dotenv
import json

from svix.webhooks import Webhook, WebhookVerificationError
from app.services.clerk import post_user

router = APIRouter()

logger = logging.getLogger(__name__)

load_dotenv()

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
