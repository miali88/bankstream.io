from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Union
from decimal import Decimal

class TransactionsTable(BaseModel):
    id: str = Field(..., max_length=100)
    booking_date: datetime
    user_id: str
    creditor_name: Optional[str] = None
    debtor_name: Optional[str] = None
    amount: Decimal
    currency: str
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
    coa_confidence: Optional[float] = None
    coa_set_by: Optional[str] = None


    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: str(v)
        }

class GetTransactions(BaseModel):
    transactions: List[TransactionsTable]
    total_count: int
    page: int
    page_size: int
    total_pages: int

class TransactionCreate(TransactionsTable):
    pass

# TODO: store data as timeseries 
class Insights(BaseModel):
    spending_by_category: List[Dict[str, Union[str, float]]]  # [{ "category": "SaaS", "amount": 2000.0 }]
    spending_by_entity: List[Dict[str, Union[str, float]]]  # [{ "entity": "AWS", "amount": 2000.0 }]
    # burn_rate: float  # Net burn rate per month
    # revenue: float  # Monthly revenue
    # net_cashflow: float  # revenue - expenses
    # runway: float  # Months left before running out of cash
    # top_vendors: List[Dict[str, float]]  # [{ "vendor": "AWS", "amount": 5000.0 }]
    # largest_transactions: List[Dict[str, float]]  # [{ "description": "Office Rent", "amount": 4000.0 }]
    # average_transaction_size: float  # Average transaction amount
    # transactions_count: int  # Number of transactions processed in the period

