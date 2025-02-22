import os
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends

from app.schemas.ntropy import BatchCreateResponse, BatchStatusResponse
from app.services.ntropy import NtropyService
from app.core.auth import get_current_user
from app.services.reconciliation import reconcile_transactions

# Set up logger
logger = logging.getLogger(__name__)

router = APIRouter()
ntropy_service = NtropyService()

def get_mock_batch_response() -> BatchCreateResponse:
    """Generate a mock batch response for testing"""
    current_time = datetime.now(timezone.utc)
    return BatchCreateResponse(
        id="test_batch_123",
        operation="enrich",
        status="pending",
        created_at=current_time,
        updated_at=current_time,
        progress=0,
        total=100,
        request_id="test_request_456"
    )

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
    logger.info(f"Starting transaction enrichment for user_id: {user_id}")
    try:
        mock_response = get_mock_batch_response()
        logger.info(f"Returning mock response for user_id: {user_id}. Batch ID: {mock_response.id}")
        return mock_response
            
        # response = await ntropy_service.enrich_transactions(user_id)
        # logger.info(f"Successfully created enrichment batch for user_id: {user_id}. Batch ID: {response.batch_id}")
        # return response
    except ValueError as e:
        logger.error(f"Error enriching transactions for user_id: {user_id}. Error: {str(e)}")
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
    logger.info(f"Checking batch status for batch_id: {batch_id}, user_id: {user_id}")
    try:
        # Start reconciliation
        logger.info(f"Batch {batch_id} completed. Starting transaction reconciliation for user_id: {user_id}")
        df_reconciled = await reconcile_transactions(user_id)
        
        if df_reconciled.empty:
            logger.info(f"No transactions to reconcile for user_id: {user_id}")
            return BatchStatusResponse(
                status="complete",
                progress=100,
                total=100,
                error=None,
                message="No transactions required reconciliation"
            )
            
        logger.info(f"Successfully reconciled {len(df_reconciled)} transactions for user_id: {user_id}")
        
        return BatchStatusResponse(
            status="complete",
            progress=100,
            total=100,
            error=None
        )
    except Exception as e:
        logger.error(f"Error checking batch status for batch_id: {batch_id}, user_id: {user_id}. Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process batch: {str(e)}"
        )

