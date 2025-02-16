"""
store the agreement ID, which can be used to authenticate ongoing requests with that bank account

the callback URL will include the ref of the agreement, this 
"""

from pydantic import BaseModel

class BankListResponse(BaseModel):
    id: str
    name: str
    transaction_total_days: str
    logo: str

class BuildLinkResponse(BaseModel):
    link: str