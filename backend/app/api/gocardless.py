from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from app.services import gocardless

load_dotenv()

router = APIRouter()

class BankListResponse(BaseModel):
    id: str
    name: str
    bic: str
    transaction_total_days: str
    countries: list
    logo: str
    max_access_valid_for_days: str

class BuildLinkResponse(BaseModel):
    link: str

@router.get("/bank_list")
async def get_list_of_banks():
    print("\n /list-of-banks called")
    return await gocardless.fetch_list_of_banks()

@router.post("/build_link")
async def build_bank_link(institution_id: str):
    print("\n /build_link called")
    try:
        link = await gocardless.build_link(institution_id)
        return {"link": link}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))