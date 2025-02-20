from fastapi import APIRouter, HTTPException
from typing import Literal, List, Dict, Optional
from pydantic import BaseModel

router = APIRouter()

class ClientDetailsResponse(BaseModel):
    id: str
    name: str
    entity_type: Literal["ltd", "llp", "partnership", "sole-trader", "charity", "trust", "other"]
    crn: str 
    utr: str | None = None
    vat_number: str | None = None
    registered_address: str
    accounting_period: str 
    tax_period: str 



@router.get("/client_accounts")
async def get_client_accounts(user_id: str):
    return {"message": "Hello, World!"}