from typing import List, Optional, Literal
import os
from datetime import datetime

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from ntropy_sdk import SDK

from app.models.transactions import TransactionsTable
from app.services.ntropy import transform_transactions_for_ntropy

router = APIRouter()

# Environment variables
NTROPY_API_KEY = os.getenv("NTROPY_API_KEY")


class EnrichedTransactionResponse(BaseModel):
    created_at: datetime
    id: str
    entities: dict
    categories: dict
    location: dict

class EnrichedTransactionRequest(BaseModel):
    id: str
    description: str
    date: str
    amount: float
    entry_type: str
    currency: str
    account_holder_id: str | None = None
    location: dict | None = None

class BatchCreateData(BaseModel):
    operation: Literal["POST /v3/transactions"]
    data: list[EnrichedTransactionRequest]

class BatchCreateResponse(BaseModel):
    id: str
    operation: str
    status: str
    created_at: datetime
    updated_at: datetime
    progress: int
    total: int
    request_id: str

@router.post("/enrich", request_model=List[TransactionsTable])
async def enrich_transactions(transactions: List[TransactionsTable]):
    """
    Endpoint to enrich a list of transactions using Ntropy API
    
    Args:
        transactions (List[TransactionsTable]): List of transaction objects to be enriched
        
    """
    if not NTROPY_API_KEY:
        raise HTTPException(status_code=500, detail="Ntropy API key not configured")

    ntropy_sdk = SDK(NTROPY_API_KEY)

    ntropy_transactions: list = transform_transactions_for_ntropy(transactions)

    r = ntropy_sdk.batches.create(
        operation="POST /v3/transactions",
        data=ntropy_transactions
    )

    return {"result": "posted to ntropy, await batch completion"}