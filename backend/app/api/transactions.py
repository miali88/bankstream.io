from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Optional
import logging
from fastapi.responses import StreamingResponse
from io import StringIO
import csv

from app.services.supabase import get_supabase
from app.core.auth import get_current_user
from app.schemas.transactions import GetTransactions
from app.services.transactions import TransactionService

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

logger = logging.getLogger(__name__)

class TransactionUpdate(BaseModel):
    id: str
    category: Optional[str] = None
    chart_of_accounts: Optional[str] = None

class TransactionBatchUpdate(BaseModel):
    transactions: List[TransactionUpdate]
    page: Optional[int] = None
    page_size: Optional[int] = None

class ReconciliationRequest(BaseModel):
    transaction_ids: List[str]

@router.post("/")
async def create_transaction(
    transaction_data: dict,
    user_id: str = Depends(get_current_user)
):
    logger.info("Creating a new transaction")
    try:
        supabase = await get_supabase()
        transaction_data["user_id"] = user_id
        result = await supabase.table("transactions").insert(transaction_data).execute()
        logger.info("Transaction created successfully")
        return result.data
    except Exception as e:
        logger.error(f"Error creating transaction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=GetTransactions)
async def get_transactions(
    user_id: str = Depends(get_current_user),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100)
):
    logger.info(f"Fetching transactions for user {user_id}")
    try:
        transaction_service = TransactionService()
        result = await transaction_service.get_user_transactions(
            user_id=user_id,
            page=page,
            page_size=page_size
        )
        logger.info(f"Fetched {len(result.transactions)} transactions")
        return result
    except Exception as e:
        logger.error(f"Error fetching transactions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{transaction_id}")
async def update_transaction(
    transaction_id: str,
    transaction_data: dict,
    user_id: str = Depends(get_current_user)
):
    logger.info(f"Updating transaction {transaction_id}")
    try:
        supabase = await get_supabase()
        result = await supabase.table("transactions")\
            .update(transaction_data)\
            .eq("id", transaction_id)\
            .eq("user_id", user_id)\
            .execute()
        logger.info(f"Transaction {transaction_id} updated successfully")
        return result.data
    except Exception as e:
        logger.error(f"Error updating transaction {transaction_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: str,
    user_id: str = Depends(get_current_user)
):
    logger.info(f"Deleting transaction {transaction_id}")
    try:
        supabase = await get_supabase()
        result = await supabase.table("transactions")\
            .delete()\
            .eq("id", transaction_id)\
            .eq("user_id", user_id)\
            .execute()
        logger.info(f"Transaction {transaction_id} deleted successfully")
        return {"message": "Transaction deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting transaction {transaction_id}: {str(e)}")
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
            print(f"  Chart of Account: {transaction.chart_of_accounts}")
            print(f"  Raw transaction data: {transaction.dict()}")
        print("\n=== End Request Details ===\n")

        supabase = await get_supabase()
        transaction_ids = [t.id for t in update_data.transactions]
        logger.debug(f"Transaction IDs to update: {transaction_ids}")
        
        verification = await supabase.table("gocardless_transactions")\
            .select("id")\
            .in_("id", transaction_ids)\
            .eq("user_id", user_id)\
            .execute()
        
        if len(verification.data) != len(transaction_ids):
            logger.warning("Transaction count mismatch during verification")
            raise HTTPException(
                status_code=403,
                detail="Some transactions do not belong to the user"
            )
        
        results = []
        for transaction in update_data.transactions:
            update_dict = transaction.dict(exclude_unset=True, exclude={'id'})
            logger.debug(f"Updating transaction {transaction.id} with data: {update_dict}")
            
            try:
                result = await supabase.table("gocardless_transactions")\
                    .update(update_dict)\
                    .eq("id", transaction.id)\
                    .eq("user_id", user_id)\
                    .execute()
                results.extend(result.data)
                logger.info(f"Transaction {transaction.id} updated successfully")
            except Exception as transaction_error:
                logger.error(f"Error updating transaction {transaction.id}: {str(transaction_error)}")
                raise
            
        logger.info(f"Batch update completed for {len(results)} transactions")
        return results
    except Exception as e:
        logger.error(f"Batch update failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fetch_csv")
async def export_transactions_csv(
    user_id: str = Depends(get_current_user)
):
    logger.info(f"Exporting transactions to CSV for user {user_id}")
    try:
        supabase = await get_supabase()
        result = await supabase.table("gocardless_transactions").select("*").eq("user_id", user_id).execute()
        
        if not result.data:
            logger.warning(f"No transactions found for user {user_id}")
            raise HTTPException(status_code=404, detail="No transactions found")

        output = StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "id",
                "user_id",
                "creditor_name",
                "debtor_name",
                "amount",
                "currency",
                "remittance_info",
                "code",
                "created_at",
                "institution_id",
                "iban",
                "bban",
                "transaction_id",
                "internal_transaction_id",
                "logo",
                "category",
                "chart_of_accounts",
                "agreement_id",
                "ntropy_enrich",
                "coa_reason",
                "coa_confidence",
                "coa_set_by"
            ]
        )
        
        writer.writeheader()
        
        for transaction in result.data:
            writer.writerow({
                "id": transaction.get("id"),
                "user_id": transaction.get("user_id"),
                "creditor_name": transaction.get("creditor_name"),
                "debtor_name": transaction.get("debtor_name"),
                "amount": transaction.get("amount"),
                "currency": transaction.get("currency"),
                "remittance_info": transaction.get("remittance_info"),
                "code": transaction.get("code"),
                "created_at": transaction.get("created_at"),
                "institution_id": transaction.get("institution_id"),
                "iban": transaction.get("iban"),
                "bban": transaction.get("bban"),
                "transaction_id": transaction.get("transaction_id"),
                "internal_transaction_id": transaction.get("internal_transaction_id"),
                "logo": transaction.get("logo"),
                "category": transaction.get("category"),
                "chart_of_accounts": transaction.get("chart_of_accounts"),
                "agreement_id": transaction.get("agreement_id"),
                "ntropy_enrich": transaction.get("ntropy_enrich"),
                "coa_reason": transaction.get("coa_reason"),
                "coa_confidence": transaction.get("coa_confidence"),
                "coa_set_by": transaction.get("coa_set_by")
            })
            logger.debug(f"Transaction {transaction.get('id')} written to CSV")

        output.seek(0)
        
        logger.info("CSV export completed successfully")
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=transactions.csv"
            }
        )
    except HTTPException as http_exc:
        logger.error(f"HTTP error during CSV export: {str(http_exc)}")
        raise
    except Exception as e:
        logger.error(f"Error exporting transactions to CSV: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fetch_csv")
async def export_transactions_csv(
    user_id: str = Depends(get_current_user)
):
    logger.info(f"Exporting transactions to CSV for user {user_id}")
    try:
        transaction_service = TransactionService()
        csv_data = await transaction_service.export_transactions_to_csv(user_id)
        
        return StreamingResponse(
            iter([csv_data]),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=transactions.csv"
            }
        )
    except Exception as e:
        logger.error(f"Error exporting transactions to CSV: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
