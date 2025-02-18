from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class TransactionsTable(BaseModel):
    id: str = Field(..., max_length=100)
    user_id: Optional[str] = None
    creditor_name: Optional[str] = None
    debtor_name: Optional[str] = None
    amount: Optional[int] = None
    currency: Optional[str] = None
    remittance_info: Optional[str] = None
    code: Optional[str] = None
    created_at: datetime
    institution_id: Optional[str] = None
    iban: Optional[str] = None
    bban: Optional[str] = None
    transaction_id: Optional[str] = None
    internal_transaction_id: Optional[str] = None
    logo: Optional[str] = None
    category: Optional[str] = None
    chart_of_accounts: Optional[str] = None
    agreement_id: Optional[str] = None
    ntropy_enrich: Optional[bool] = None
    coa_reason: Optional[str] = None
    coa_confidence: Optional[str] = None
    coa_set_by: Optional[str] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class GetTransactions(BaseModel):
    transactions: List[TransactionsTable]
    total_count: int
    page: int
    page_size: int
    total_pages: int

class TransactionCreate(TransactionsTable):
    pass
