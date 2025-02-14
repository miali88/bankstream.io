from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import create_client, Client
import os
from dotenv import load_dotenv

from app.core.auth import get_current_user

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
    user_data: dict = Depends(get_current_user)
):
    try:
        transaction_data["user_id"] = user_data.get("id")
        result = supabase.table("transactions").insert(transaction_data).execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def get_transactions(
    user_id: str = Depends(get_current_user),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100)
):
    try:
        # Calculate offset
        offset = (page - 1) * page_size

        # Get total count
        count_result = supabase.table("gocardless_transactions")\
            .select("*", count="exact")\
            .eq("user_id", user_id)\
            .execute()
        total_count = count_result.count

        # Get paginated transactions
        result = supabase.table("gocardless_transactions")\
            .select("*")\
            .eq("user_id", user_id)\
            .range(offset, offset + page_size - 1)\
            .order("created_at", desc=True)\
            .execute()

        return {
            "transactions": result.data,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": -(-total_count // page_size)  # Ceiling division
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{transaction_id}")
async def get_transaction(
    transaction_id: str,
    user_data: dict = Depends(get_current_user)
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
    user_data: dict = Depends(get_current_user)
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
    user_data: dict = Depends(get_current_user)
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