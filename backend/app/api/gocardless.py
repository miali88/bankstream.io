from dotenv import load_dotenv
import asyncio
from typing import Dict, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel

from app.schemas.gocardless import BuildLinkResponse, Bank
from app.services import gocardless
from app.services import agreement_monitor
from app.core.auth import get_current_user

load_dotenv()

router = APIRouter()

# Store active SSE connections by ref instead of user_id
active_sse_connections: Dict[str, asyncio.Queue] = {}


""" step 1, user selects country and selects their bank from the list of banks """
@router.get("/bank_list", response_model=List[Bank])
async def get_list_of_banks(country: str, user_id: str = Depends(get_current_user)):
    print(f"\n /list-of-banks called by user {user_id}")
    return await gocardless.fetch_list_of_banks(country)


""" step 2, we build a link to the chosen bank, and return the link for user to approve our access """
@router.get("/build_link", response_model=BuildLinkResponse)
async def build_bank_link(institution_id: str, transaction_total_days: str,
                          user_id: str = Depends(get_current_user), medium: str = "online"):
    print(f"\n /build_link called by user {user_id}")
    try:
        link, ref = await gocardless.build_link(institution_id, transaction_total_days, user_id, medium)
        return {"link": link, "ref": ref}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sse")
async def sse_endpoint(request: Request, ref: str = Query(...)):
    try:
        print(f"SSE connection attempt for ref: {ref}")
        
        # Create a queue for this ref
        queue = asyncio.Queue()
        active_sse_connections[ref] = queue
        print(f"Created SSE queue for ref: {ref}")

        async def event_generator():
            try:
                print(f"Starting event generator for ref: {ref}")
                while True:
                    if await request.is_disconnected():
                        print(f"SSE connection disconnected for ref: {ref}")
                        break

                    try:
                        # Wait for messages with a timeout
                        message = await asyncio.wait_for(queue.get(), timeout=30)
                        print(f"Sending SSE message for ref {ref}: {message}")
                        yield message
                    except asyncio.TimeoutError:
                        # Send keepalive comment
                        print(f"Sending keepalive for ref: {ref}")
                        yield ": keepalive\n\n"
            except Exception as e:
                print(f"SSE Error for ref {ref}: {str(e)}")
            finally:
                print(f"Cleaning up SSE connection for ref: {ref}")
                active_sse_connections.pop(ref, None)

        return EventSourceResponse(event_generator())
    except Exception as e:
        print(f"SSE connection failed: {str(e)}")
        raise HTTPException(status_code=400, detail="Bad Request")


""" step 3, gocardless redirects user to our site, fetch transactions for new accounts added """
@router.get("/callback")
async def add_account_callback(ref: str):
    print(f"\n /callback called with ref: {ref}")
    try:
        result = await gocardless.add_account(ref)
        
        # Send SSE notification if we have an active connection for this ref
        if ref in active_sse_connections:
            try:
                print(f"Sending account_linked notification for ref: {ref}")
                queue = active_sse_connections[ref]
                await queue.put({
                    "event": "message",
                    "data": {
                        "type": "account_linked",
                        "message": "Bank account successfully linked!"
                    }
                })
                print(f"Successfully sent account_linked notification for ref: {ref}")
            except Exception as e:
                print(f"Error sending SSE notification: {str(e)}")
        else:
            print(f"No active SSE connection found for ref: {ref}")
        
        return result
    except Exception as e:
        print(f"Error in callback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class ExpiringAgreement(BaseModel):
    id: str
    institution_id: str
    expires_at: str
    days_until_expiry: int

@router.get("/check-expiring", response_model=List[ExpiringAgreement])
async def check_expiring_agreements(
    user_id: str = Depends(get_current_user),
    days_threshold: int = Query(default=7, ge=1, le=30)
):
    """
    Check for agreements that are expiring soon for the current user
    """
    try:
        # Get expiring agreements
        agreements = await agreement_monitor.get_expiring_agreements(days_threshold)
        
        # Filter for current user and calculate days until expiry
        now = datetime.utcnow()
        user_agreements = []
        
        for agreement in agreements:
            if agreement['user_id'] == user_id:
                expires_at = datetime.fromisoformat(agreement['expires_at'].replace('Z', '+00:00'))
                days_until = (expires_at - now).days
                
                user_agreements.append(ExpiringAgreement(
                    id=agreement['id'],
                    institution_id=agreement['institution_id'],
                    expires_at=agreement['expires_at'],
                    days_until_expiry=days_until
                ))
        
        return user_agreements
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    
