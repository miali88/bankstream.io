from typing import List
import os
import asyncio

from fastapi import APIRouter, HTTPException, Depends
from ntropy_sdk import SDK

from app.schemas.ntropy import BatchCreateResponse, BatchStatusResponse
from app.services.ntropy import NtropyService
from app.core.auth import get_current_user

router = APIRouter()
ntropy_service = NtropyService(os.getenv("NTROPY_API_KEY"))

@router.post("/enrich", response_model=BatchCreateResponse)
async def enrich_transactions(user_data: dict = Depends(get_current_user)):
    """
    Endpoint to enrich all transactions for the authenticated user using Ntropy API
            
    Returns:
        BatchCreateResponse: The batch creation response containing the batch ID
    """
    try:
        return await ntropy_service.enrich_transactions(user_data.get("id"))
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/enrich/{batch_id}/status", response_model=BatchStatusResponse)
async def get_batch_status(batch_id: str):
    """
    Get the current status of a batch enrichment process
    
    Args:
        batch_id (str): The batch ID to check
        
    Returns:
        BatchStatusResponse: Current status of the batch, including progress and results if complete
    """
    try:
        return await ntropy_service.get_batch_status(batch_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
