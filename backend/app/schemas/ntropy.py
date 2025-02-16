from pydantic import BaseModel
from datetime import datetime
from typing import Literal, Optional

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

class BatchCreateResponse(BaseModel):
    id: str
    operation: str
    status: str
    created_at: datetime
    updated_at: datetime
    progress: int
    total: int
    request_id: str

class BatchGetResponse(BatchCreateResponse):
    pass

class BatchResultsResponse(BaseModel):
    id: str
    total: int
    status: str
    results: list[EnrichedTransactionResponse]
    request_id: str

class BatchStatusResponse(BaseModel):
    status: Literal["complete", "error", "processing"]
    progress: int
    total: Optional[int] = None
    error: Optional[str] = None

