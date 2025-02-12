from fastapi import APIRouter, Depends, HTTPException
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from .auth import verify_token

load_dotenv()

router = APIRouter()

# Initialize Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

@router.post("/")
async def create_transaction(
    transaction_data: dict,
    user_data: dict = Depends(verify_token)
):
    try:
        transaction_data["user_id"] = user_data.get("id")
        result = supabase.table("transactions").insert(transaction_data).execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@router.get("/")
async def get_transactions():
    try:
        result = supabase.table("transactions")\
            .select("*")\
            .eq("user_id", user_data.get("id"))\
            .execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{transaction_id}")
async def get_transaction(
    transaction_id: str,
    user_data: dict = Depends(verify_token)
):
    try:
        result = supabase.table("transactions")\
            .select("*")\
            .eq("id", transaction_id)\
            .eq("user_id", user_data.get("id"))\
            .single()\
            .execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{transaction_id}")
async def update_transaction(
    transaction_id: str,
    transaction_data: dict,
    user_data: dict = Depends(verify_token)
):
    try:
        result = supabase.table("transactions")\
            .update(transaction_data)\
            .eq("id", transaction_id)\
            .eq("user_id", user_data.get("id"))\
            .execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: str,
    user_data: dict = Depends(verify_token)
):
    try:
        result = supabase.table("transactions")\
            .delete()\
            .eq("id", transaction_id)\
            .eq("user_id", user_data.get("id"))\
            .execute()
        return {"message": "Transaction deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 