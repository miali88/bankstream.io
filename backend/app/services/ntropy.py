from typing import List

from ntropy_sdk import SDK
from app.services.supabase import get_supabase

from app.schemas.transactions import TransactionsTable
from app.schemas.ntropy import EnrichedTransactionRequest
from app.schemas.ntropy import BatchCreateResponse

def transform_transactions_for_ntropy(transactions: List[TransactionsTable]) -> List[EnrichedTransactionRequest]:
    """
    Transform transactions from TransactionsTable format to Ntropy-compatible format
    
    Args:
        transactions (List[TransactionsTable]): List of transaction objects
        
    Returns:
        List[EnrichedTransactionRequest]: Transformed transactions ready for Ntropy
    """
    transformed_transactions = []
    
    for tx in transactions:
        # Construct description from available fields
        description = " ".join(filter(None, [
            tx.creditor_name,
            tx.debtor_name,
            tx.remittance_info,
            tx.code,
            tx.chart_of_account
        ]))
        
        # Convert amount from integer (cents) to float (dollars)
        amount_float = float(tx.amount) / 100 if tx.amount is not None else 0.0
        
        # Determine entry_type based on amount
        entry_type = "outgoing" if amount_float >= 0 else "incoming"
        
        transformed_tx = EnrichedTransactionRequest(
            id=tx.internal_transaction_id or tx.transaction_id or tx.id,
            description=description.strip(),
            date=tx.created_at.date().isoformat(),
            amount=abs(amount_float),  # Ntropy expects positive amounts
            entry_type=entry_type,
            currency=tx.currency or "GBP",  # Default to EUR if not specified
            account_holder_id=tx.user_id,
            location={}  # Empty dict as per EnrichedTransactionRequest schema
        )
        transformed_transactions.append(transformed_tx)
    
    return transformed_transactions

class NtropyService:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Ntropy API key not configured")
        self.sdk = SDK(api_key)
        self._supabase = None

    async def get_supabase(self):
        if not self._supabase:
            self._supabase = await get_supabase()
        return self._supabase

    async def get_user_transactions(self, user_id: str) -> List[TransactionsTable]:
        """
        Fetch all transactions for a given user
        
        Args:
            user_id (str): The ID of the user
            
        Returns:
            List[TransactionsTable]: List of transactions for the user
        """
        supabase = await self.get_supabase()
        result = await supabase.table('transactions').select('*').eq('user_id', user_id).execute()
        
        if not result.data:
            return []
        
        return [TransactionsTable(**tx) for tx in result.data]

    async def enrich_transactions(self, user_id: str) -> BatchCreateResponse:
        """
        Enrich all transactions for a given user using Ntropy API
        
        Args:
            user_id (str): The ID of the user
            
        Returns:
            BatchCreateResponse: The batch creation response containing the batch ID
        """
        transactions = await self.get_user_transactions(user_id)
        
        if not transactions:
            raise ValueError("No transactions found for the user")
        
        ntropy_transactions = transform_transactions_for_ntropy(transactions)
        return self.sdk.batches.create(
            operation="POST /v3/transactions",
            data=ntropy_transactions
        )

    async def store_ntropy_transaction(self, batch_id: str, transaction_data: dict) -> dict:
        """
        Store Ntropy transaction data in Supabase
        
        Args:
            batch_id (str): The Ntropy batch ID
            transaction_data (dict): The enriched transaction data from Ntropy
            
        Returns:
            dict: The inserted record
        """
        try:
            data = {
                'id': transaction_data.get('id'),
                'batch_id': batch_id,
                'enriched_data': transaction_data,
                'status': 'completed'
            }
            
            supabase = await self.get_supabase()
            result = await supabase.table('ntropy_transactions').insert(data).execute()
            return result.data[0]
        except Exception as e:
            raise ValueError(f"Failed to store Ntropy transaction: {str(e)}")

    async def get_batch_status(self, batch_id: str) -> dict:
        """
        Get the current status of a batch
        
        Args:
            batch_id (str): The batch ID to check
            
        Returns:
            dict: Status response containing status and progress information
        """
        batch = self.sdk.batches.get(id=batch_id)
        
        if batch.is_completed():
            # Still get and store the results, but don't return them
            results = self.sdk.batches.results(id=batch_id)
            
            # Store each enriched transaction in Supabase
            for transaction in results.model_dump().get('data', []):
                await self.store_ntropy_transaction(batch_id, transaction)
            
            return {
                "status": "complete",
                "progress": 100,
                "total": batch.total
            }
        elif batch.is_error():
            return {
                "status": "error",
                "progress": 0,
                "error": "Batch processing failed"
            }
        else:
            return {
                "status": "processing",
                "progress": batch.progress,
                "total": batch.total
            }
