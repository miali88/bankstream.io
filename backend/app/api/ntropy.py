from typing import List
import os
import asyncio
from sse_starlette.sse import EventSourceResponse

from fastapi import APIRouter, HTTPException, Request
from ntropy_sdk import SDK

from app.schemas.transactions import TransactionsTable
from app.schemas.ntropy import BatchCreateResponse, BatchResultsResponse
from app.services.ntropy import transform_transactions_for_ntropy

router = APIRouter()

# Environment variables
NTROPY_API_KEY = os.getenv("NTROPY_API_KEY")

@router.post("/enrich", response_model=BatchCreateResponse)
async def enrich_transactions(transactions: List[TransactionsTable]):
    """
    Endpoint to enrich a list of transactions using Ntropy API
    
    Args:
        transactions (List[TransactionsTable]): List of transaction objects to be enriched
        
    Returns:
        BatchCreateResponse: The batch creation response containing the batch ID
    """
    if not NTROPY_API_KEY:
        raise HTTPException(status_code=500, detail="Ntropy API key not configured")

    ntropy_sdk = SDK(NTROPY_API_KEY)

    ntropy_transactions: list = transform_transactions_for_ntropy(transactions)

    r: BatchCreateResponse = ntropy_sdk.batches.create(
        operation="POST /v3/transactions",
        data=ntropy_transactions
    )

    return r

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
    if not NTROPY_API_KEY:
        raise HTTPException(status_code=500, detail="Ntropy API key not configured")

    ntropy_sdk = SDK(NTROPY_API_KEY)

    async def event_generator():
        while True:
            if await request.is_disconnected():
                break

            try:
                # Get batch status
                batch = ntropy_sdk.batches.get(id=batch_id)
                
                # If batch is completed, get results and send final event
                if batch.is_completed():
                    results: BatchResultsResponse = ntropy_sdk.batches.results(id=batch_id)
                    yield {
                        "event": "complete",
                        "data": {"status": batch.status, "results": results.dict()}
                    }
                    break
                # If batch encountered an error, send error event and stop
                elif batch.is_error():
                    yield {
                        "event": "error",
                        "data": {"status": batch.status, "error": "Batch processing failed"}
                    }
                    break
                # Otherwise send progress update
                else:
                    yield {
                        "event": "progress",
                        "data": {
                            "status": batch.status,
                            "progress": batch.progress,
                            "total": batch.total
                        }
                    }
                
                await asyncio.sleep(5)  # Poll every 5 seconds
                
            except Exception as e:
                yield {
                    "event": "error",
                    "data": {"error": str(e)}
                }
                break

    return EventSourceResponse(event_generator())