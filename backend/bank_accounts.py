from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pydantic import BaseModel
from app.services.supabase import get_supabase
from app.core.auth import get_current_user

router = APIRouter()

class GetBankAccountsResponse(BaseModel):
    id: str
    iban: str
    bban: str
    owner_name: str
    institution_id: str

@router.get("/")
async def get_bank_accounts(
    user_id: str
) -> List[GetBankAccountsResponse]:
    supabase = await get_supabase()
    result = await supabase.table('gocardless_accounts').select('*').eq('user_id', user_id).execute()
    
    transformed_accounts = [
        GetBankAccountsResponse(
            id=account['results']['id'],
            iban=account['results'].get('iban', ''),
            bban=account['results'].get('bban', ''),
            owner_name=account['results'].get('owner_name', ''),
            institution_id=account['results'].get('institution_id', '')
        )
        for account in result.data
    ]
    print(transformed_accounts)
    return transformed_accounts


if __name__ == "__main__":
    import asyncio
    asyncio.run(get_bank_accounts("user_2tEnUq7rivacYtZnsAXPlC5gi9B"))