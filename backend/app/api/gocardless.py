from fastapi import APIRouter, Depends, HTTPException
from dotenv import load_dotenv
from app.services import gocardless

load_dotenv()

router = APIRouter()

@router.get("/bank_list")
async def get_list_of_banks():
    print("\n /list-of-banks called")
    return await gocardless.fetch_list_of_banks()

@router.get("/build_link")
async def get_account_details(institution_id: str):
    print("\n /build_link called")
    return await gocardless.build_link(institution_id)