"""
store the agreement ID, which can be used to authenticate ongoing requests with that bank account

the callback URL will include the ref of the agreement, this 
"""

from typing import List
from pydantic import BaseModel, RootModel

class Bank(BaseModel):
    id: str
    name: str
    bic: str
    transaction_total_days: str
    countries: List[str]
    logo: str
    max_access_valid_for_days: str

BankListResponse = RootModel[List[Bank]]

class BuildLinkResponse(BaseModel):
    link: str
    ref: str

class GCLAccountsResponse(BaseModel):
    id: str
    created: str
    last_accessed: str
    iban: str
    bban: str
    status: str
    institution_id: str
    owner_name: str
