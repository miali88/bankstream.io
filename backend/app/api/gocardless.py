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

# Store active SSE connections by ref instead of user_id
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
        link, ref = await gocardless.build_link(institution_id, user_id, medium)
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

""" step 3, redirect user to our site, fetch transactions for new accounts added """
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

    
