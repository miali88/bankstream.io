from fastapi import APIRouter, Depends, HTTPException, Query
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Optional
import logging

from app.services.supabase import get_supabase
from app.core.auth import get_current_user

load_dotenv()

router = APIRouter()

class TransactionUpdate(BaseModel):
    id: str
    category: Optional[str] = None
    chart_of_account: Optional[str] = None

class TransactionBatchUpdate(BaseModel):
    transactions: List[TransactionUpdate]
    page: Optional[int] = None
    page_size: Optional[int] = None

@router.post("/")
async def create_transaction(
    transaction_data: dict,
    user_data: dict = Depends(get_current_user)
):
    try:
        supabase = await get_supabase()
        transaction_data["user_id"] = user_data.get("id")
        result = await supabase.table("transactions").insert(transaction_data).execute()
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
        supabase = await get_supabase()
        offset = (page - 1) * page_size

        print("Executing query for user_id:", user_id)
        print(f"Pagination: page={page}, page_size={page_size}, offset={offset}")
        
        # Single query to get all data
        result = await supabase.table("gocardless_transactions")\
            .select("*", count="exact")\
            .eq("user_id", user_id)\
            .range(offset, offset + page_size - 1)\
            .order("created_at", desc=True)\
            .execute()
        
        total_count = result.count
        
        # Debug the response
        if result.data:
            print("First transaction ID:", result.data[0]['id'])
            print("Number of transactions returned:", len(result.data))
            print("Sample transaction:", result.data[0])
        else:
            print("No transactions found")
        
        return {
            "transactions": result.data,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": -(-total_count // page_size)
        }
    except Exception as e:
        print(f"Error in get_transactions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{transaction_id}")
async def update_transaction(
    transaction_id: str,
    transaction_data: dict,
    user_data: dict = Depends(get_current_user)
):
    try:
        supabase = await get_supabase()
        result = await supabase.table("transactions")\
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
        supabase = await get_supabase()
        result = await supabase.table("transactions")\
            .delete()\
            .eq("id", transaction_id)\
            .eq("user_id", user_data.get("id"))\
            .execute()
        return {"message": "Transaction deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/batch")
async def patch_transactions_batch(
    update_data: TransactionBatchUpdate,
    user_id: str = Depends(get_current_user)
):
    try:
        print("\n=== Batch Update Request Details ===")
        print(f"User ID: {user_id}")
        print(f"Number of transactions to update: {len(update_data.transactions)}")
        print(f"Page: {update_data.page}")
        print(f"Page Size: {update_data.page_size}")
        print("\nTransaction Updates:")
        for idx, transaction in enumerate(update_data.transactions, 1):
            print(f"\nTransaction {idx}:")
            print(f"  ID: {transaction.id}")
            print(f"  Category: {transaction.category}")
            print(f"  Chart of Account: {transaction.chart_of_account}")
            print(f"  Raw transaction data: {transaction.dict()}")
        print("\n=== End Request Details ===\n")

        supabase = await get_supabase()
        logging.info(f"Starting batch update for user {user_id} with {len(update_data.transactions)} transactions")
        # Verify all transactions belong to the user
        transaction_ids = [t.id for t in update_data.transactions]
        logging.debug(f"Transaction IDs to update: {transaction_ids}")
        
        verification = await supabase.table("gocardless_transactions")\
            .select("id")\
            .in_("id", transaction_ids)\
            .eq("user_id", user_id)\
            .execute()
        
        logging.info(f"Verification found {len(verification.data)} transactions belonging to user")
        
        if len(verification.data) != len(transaction_ids):
            logging.warning(f"Transaction count mismatch. Expected: {len(transaction_ids)}, Found: {len(verification.data)}")
            raise HTTPException(
                status_code=403,
                detail="Some transactions do not belong to the user"
            )
        
        # Perform batch update
        results = []
        for transaction in update_data.transactions:
            print("transaction id", transaction.id)
            # Convert to dict and exclude None values
            update_dict = transaction.dict(exclude_unset=True, exclude={'id'})
            print("update_dict", update_dict)
            logging.debug(f"Updating transaction {transaction.id} with data: {update_dict}")
            
            try:
                result = await supabase.table("gocardless_transactions")\
                    .update(update_dict)\
                    .eq("id", transaction.id)\
                    .eq("user_id", user_id)\
                    .execute()
                results.extend(result.data)
                logging.debug(f"Successfully updated transaction {transaction.id}")
            except Exception as transaction_error:
                logging.error(f"Error updating transaction {transaction.id}: {str(transaction_error)}")
                raise
            
        logging.info(f"Successfully completed batch update of {len(results)} transactions")
        return results
    except Exception as e:
        logging.error(f"Batch update failed with error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) 