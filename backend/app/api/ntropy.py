from typing import List
import os
import asyncio

from sse_starlette.sse import EventSourceResponse
from fastapi import APIRouter, HTTPException, Request
from ntropy_sdk import SDK

from app.schemas.transactions import TransactionsTable
from app.schemas.ntropy import BatchCreateResponse
from app.services.ntropy import NtropyService

router = APIRouter()
ntropy_service = NtropyService(os.getenv("NTROPY_API_KEY"))

@router.post("/enrich", response_model=BatchCreateResponse)
async def enrich_transactions(transactions: List[TransactionsTable]):
    """
    Endpoint to enrich a list of transactions using Ntropy API
    
    Args:
        transactions (List[TransactionsTable]): List of transaction objects to be enriched
        
    Returns:
        BatchCreateResponse: The batch creation response containing the batch ID
    """
    try:
        return await ntropy_service.enrich_transactions(transactions)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/enrich/{batch_id}/status")
async def get_batch_status(request: Request, batch_id: str):
    """
    SSE endpoint to stream batch processing status
    
    Args:
        request (Request): The FastAPI request object
        batch_id (str): The batch ID to monitor
        
    Returns:
        EventSourceResponse: SSE response with batch status updates
    """
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break

            try:
                status = await ntropy_service.get_batch_status(batch_id)
                yield status
                
                if status["event"] in ["complete", "error"]:
                    break
                    
                await asyncio.sleep(5)  # Poll every 5 seconds
                
            except Exception as e:
                yield {
                    "event": "error",
                    "data": {"error": str(e)}
                }
                break

    return EventSourceResponse(event_generator())