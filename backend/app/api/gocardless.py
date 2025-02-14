from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.security import HTTPAuthorizationCredentials
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import asyncio
from typing import Dict
import logging

from app.services import gocardless
from app.core.auth import get_current_user

load_dotenv()

router = APIRouter()

# Store active SSE connections
active_sse_connections: Dict[str, asyncio.Queue] = {}

class BankListResponse(BaseModel):
    id: str
    name: str
    transaction_total_days: str
    logo: str

class BuildLinkResponse(BaseModel):
    link: str

""" step 1, user selects country and selects their bank from the list of banks """
@router.get("/bank_list")
async def get_list_of_banks(country: str, user_id: str = Depends(get_current_user)):
    print(f"\n /list-of-banks called by user {user_id}")
    return await gocardless.fetch_list_of_banks(country)


""" step 2, we build a link to the chosen bank, and return the link for user to approve our access """
@router.get("/build_link")
async def build_bank_link(institution_id: str, user_id: str = Depends(get_current_user),
                          medium: str = "online"):
    print(f"\n /build_link called by user {user_id}")
    try:
        link = await gocardless.build_link(institution_id, user_id, medium)
        return {"link": link}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sse")
async def sse_endpoint(request: Request, token: str = Query(...)):
    try:
        # Verify the token
        print(f"\n SSE connection attempt with token prefix: {token[:20]}...")
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token.replace("Bearer ", ""))
        user_id = await get_current_user(credentials)
        print(f"SSE connection authenticated for user: {user_id}")
        
        # Create a queue for this user
        queue = asyncio.Queue()
        active_sse_connections[user_id] = queue
        print(f"Created SSE queue for user: {user_id}")

        async def event_generator():
            try:
                print(f"Starting event generator for user: {user_id}")
                while True:
                    if await request.is_disconnected():
                        print(f"SSE connection disconnected for user: {user_id}")
                        break

                    try:
                        # Wait for messages with a timeout
                        message = await asyncio.wait_for(queue.get(), timeout=30)
                        print(f"Sending SSE message to user {user_id}: {message}")
                        yield message
                    except asyncio.TimeoutError:
                        # Send keepalive comment
                        print(f"Sending keepalive to user: {user_id[:10]}...")
                        yield ": keepalive\n\n"
            except Exception as e:
                print(f"SSE Error for user {user_id}: {str(e)}")
            finally:
                print(f"Cleaning up SSE connection for user: {user_id}")
                active_sse_connections.pop(user_id, None)

        return EventSourceResponse(event_generator())
    except Exception as e:
        print(f"SSE connection failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Unauthorized")

""" step 3, redirect user to our site, fetch transactions for new accounts added """
@router.get("/callback")
async def callback(ref: str, user_id: str = Depends(get_current_user)):
    print(f"\n /callback called by user {user_id}")
    result = await gocardless.get_transactions(ref, user_id)
    
    # Send SSE notification if user has an active connection
    if user_id in active_sse_connections:
        try:
            print(f"Sending account_linked notification to user: {user_id}")
            queue = active_sse_connections[user_id]
            await queue.put({
                "event": "message",
                "data": {
                    "type": "account_linked",
                    "message": "Bank account successfully linked!"
                }
            })
            print(f"Successfully sent account_linked notification to user: {user_id}")
        except Exception as e:
            print(f"Error sending SSE notification: {str(e)}")
    else:
        print(f"No active SSE connection found for user: {user_id}")
    
    return result

    
