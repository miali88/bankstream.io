import os

from fastapi import APIRouter, HTTPException, Depends

from app.schemas.ntropy import BatchCreateResponse, BatchStatusResponse
from app.services.ntropy import NtropyService
from app.core.auth import get_current_user
from app.services.reconciliation import reconcile_transactions
router = APIRouter()
ntropy_service = NtropyService(os.getenv("NTROPY_API_KEY"))

@router.post("/enrich", response_model=BatchCreateResponse)
async def enrich_transactions(
    user_id: str = Depends(get_current_user)
):
    """
    Endpoint to enrich all transactions for the authenticated user using Ntropy API
    
    Args:
        user_data (str): The authenticated user's ID
            
    Returns:
        BatchCreateResponse: The batch creation response containing the batch ID
    """
    try:
        return await ntropy_service.enrich_transactions(user_id)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/enrich/{batch_id}/status", response_model=BatchStatusResponse)
async def get_batch_status(batch_id: str, user_id: str = Depends(get_current_user)):
    """
    Get the current status of a batch enrichment process
    
    Args:
        batch_id (str): The batch ID to check
        
    Returns:
        BatchStatusResponse: Current status of the batch, including progress and results if complete
    """
    try:
        ntropy_status = await ntropy_service.get_batch_status(batch_id)
        
        # Only reconcile when the batch is complete
        if ntropy_status.status == "completed":
            await reconcile_transactions(user_id)
            
        return ntropy_status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
