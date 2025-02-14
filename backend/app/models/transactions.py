from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TransactionBase(BaseModel):
    id: str
    user_id: Optional[str] = None
    creditor_name: Optional[str] = None
    debtor_name: Optional[str] = None
    amount: Optional[int] = None
    currency: Optional[str] = None
    remittance_info: Optional[str] = None
    code: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class TransactionCreate(TransactionBase):
    pass

class Transaction(TransactionBase):
    pass