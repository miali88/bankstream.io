from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

from app.services import gocardless
from app.core.auth import get_current_user

load_dotenv()

router = APIRouter()

class BankListResponse(BaseModel):
    id: str
    name: str
    transaction_total_days: str
    logo: str

class BuildLinkResponse(BaseModel):
    link: str

""" step 1, user selects country and selects their bank from the list of banks """
@router.get("/bank_list")
async def get_list_of_banks(country: str, user_id: str = Depends(get_current_user)):
    print(f"\n /list-of-banks called by user {user_id}")
    return await gocardless.fetch_list_of_banks(country)


""" step 2, we build a link to the chosen bank, and return the link for user to approve our access """
@router.get("/build_link")
async def build_bank_link(institution_id: str, user_id: str = Depends(get_current_user)):
    print(f"\n /build_link called by user {user_id}")
    try:
        link = await gocardless.build_link(institution_id)
        return {"link": link}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

""" step 3, redirect user to our site, fetch transactions for new accounts added """
@router.get("/transactions")
async def transactions(reference: str, user_id: str = Depends(get_current_user)):
    print(f"\n /transactions called by user {user_id}")
    return await gocardless.get_transactions(reference)


