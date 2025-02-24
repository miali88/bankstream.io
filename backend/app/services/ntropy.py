import os
import logging
from typing import List
from datetime import datetime
import json

from ntropy_sdk import SDK
from app.core.supabase_client import get_supabase

from app.schemas.transactions import TransactionsTable
from app.schemas.ntropy import EnrichedTransactionRequest
from app.schemas.ntropy import BatchCreateResponse

# Configure logging
logger = logging.getLogger(__name__)

def transform_transactions_for_ntropy(
        transactions: List[TransactionsTable]) -> List[EnrichedTransactionRequest]:
    """
    Transform transactions from TransactionsTable format to Ntropy-compatible format
    
    Args:
        transactions (List[TransactionsTable]): List of transaction objects
        
    Returns:
        List[EnrichedTransactionRequest]: Transformed transactions ready for Ntropy
    """
    logger.info(f"Starting transformation of {len(transactions)} transactions for Ntropy")
    transformed_transactions = []
    
    for tx in transactions:
        logger.debug(f"Transforming transaction {tx.id}")
        # Get the party name (either creditor or debtor, but not both)
        entity_name = tx.creditor_name if tx.creditor_name else tx.debtor_name

        # Construct description from available fields
        description = " ".join(filter(None, [
            entity_name,
            tx.remittance_info,
        ]))
        
        # Convert amount from integer (cents) to float (dollars)
        amount_float = float(tx.amount) / 100 if tx.amount is not None else 0.0
        
        # Determine entry_type based on amount
        entry_type = "incoming" if amount_float >= 0 else "outgoing"
        logger.debug(f"Transaction {tx.id}: amount={amount_float}, entry_type={entry_type}")
        
        # Create location object with required country field
        location = {
            "country": "GB"  # Default to GB (United Kingdom) if not specified
        }
        
        transformed_tx = EnrichedTransactionRequest(
            id=tx.id,
            description=description.strip(),
            date=tx.created_at.date().isoformat(),
            amount=abs(amount_float),  # Ntropy expects positive amounts
            entry_type=entry_type,
            currency=tx.currency or "GB",  # Default to GBP if not specified
            account_holder_id=tx.user_id,
            location=location
        )
        transformed_transactions.append(transformed_tx)
        logger.debug(f"Successfully transformed transaction {tx.id}")
    
    logger.info(f"Completed transformation of {len(transformed_transactions)} transactions")
    return transformed_transactions

def serialize_datetime(obj):
    """Helper function to serialize datetime objects to ISO format strings"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

class NtropyService:
    def __init__(self):
        logger.info("Initializing NtropyService")
        api_key = os.getenv("NTROPY_API_KEY")
        if not api_key:
            logger.error("NTROPY_API_KEY environment variable not configured")
            raise ValueError("NTROPY_API_KEY environment variable not configured")
        self.sdk = SDK(api_key)
        self._supabase = None
        logger.info("NtropyService initialized successfully")

    async def get_supabase(self):
        if not self._supabase:
            logger.debug("Initializing Supabase connection")
            self._supabase = await get_supabase()
        return self._supabase

    async def get_user_transactions(self, user_id: str) -> List[TransactionsTable]:
        """
        Fetch all transactions for a given user that haven't been enriched by Ntropy yet
        
        Args:
            user_id (str): The ID of the user
            
        Returns:
            List[TransactionsTable]: List of non-enriched transactions for the user
        """
        logger.info(f"Fetching non-enriched transactions for user {user_id}")
        supabase = await self.get_supabase()
        query = (supabase.table('gocardless_transactions')
                .select('*')
                .eq('user_id', user_id)
                .or_('ntropy_enrich.is.null,ntropy_enrich.eq.false'))

        result = await query.execute()
        
        if not result.data:
            logger.info(f"No non-enriched transactions found for user {user_id}")
            return []
        
        transactions = [TransactionsTable(**tx) for tx in result.data]
        logger.info(f"Found {len(transactions)} non-enriched transactions for user {user_id}")
        return transactions

    async def create_account_holder(self, user_id: str) -> str:
        """
        Create a new Ntropy account holder for a user
        
        Args:
            user_id (str): The ID of the user
            
        Returns:
            str: The created Ntropy account holder ID
        """
        logger.info(f"Creating new Ntropy account holder for user {user_id}")
        try:
            # Create account holder in Ntropy
            account_holder = self.sdk.account_holders.create(
                id=user_id,
                type="business",  # Default to business type
                name=f"Account {user_id}",  # Basic name based on ID
            )
            
            # Store the account holder in our database
            supabase = await self.get_supabase()
            await supabase.table('ntropy_account_holders').insert({
                'id': account_holder.id,
                'type': account_holder.type,
                'name': account_holder.name,
                'created_at': account_holder.created_at.isoformat()
            }).execute()
            
            logger.info(f"Successfully created Ntropy account holder: {account_holder.id}")
            return account_holder.id
            
        except Exception as e:
            logger.error(f"Failed to create Ntropy account holder: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to create Ntropy account holder: {str(e)}")

    async def get_account_holder_id(self, user_id: str) -> str:
        """
        Get the Ntropy account holder ID for a given user, creating one if it doesn't exist
        
        Args:
            user_id (str): The ID of the user
            
        Returns:
            str: The Ntropy account holder ID
        """
        logger.info(f"Getting Ntropy account holder ID for user {user_id}")
        supabase = await self.get_supabase()
        result = await supabase.table('ntropy_account_holders').select('id').eq('id', user_id).execute()
        
        if not result.data:
            logger.info(f"No existing Ntropy account holder found for user {user_id}, creating new one")
            return await self.create_account_holder(user_id)
            
        return result.data[0]['id']

    async def store_ntropy_transaction(self, batch_id: str, transaction_data: dict) -> dict:
        """
        Store Ntropy transaction data in Supabase and update the enrichment flag
        
        Args:
            batch_id (str): The Ntropy batch ID
            transaction_data (dict): The enriched transaction data from Ntropy
            
        Returns:
            dict: The inserted record
        """
        logger.info(f"Storing enriched transaction data for batch {batch_id}")
        try:
            supabase = await self.get_supabase()
            
            # Add validation for transaction data
            if not transaction_data or 'id' not in transaction_data:
                logger.error("Invalid transaction data received")
                raise ValueError("Invalid transaction data structure")
            
            # Serialize the transaction data with datetime handling
            try:
                serialized_data = json.loads(
                    json.dumps(transaction_data, default=serialize_datetime)
                )
            except Exception as serialize_error:
                logger.error(f"Error serializing transaction data: {str(serialize_error)}")
                raise ValueError(f"Failed to serialize transaction data: {str(serialize_error)}")
            
            ntropy_tx_id = transaction_data.get('id')
            
            # Store enriched data in ntropy_transactions table
            ntropy_data = {
                'ntropy_id': ntropy_tx_id,
                'batch_id': batch_id,
                'enriched_data': serialized_data,
                'status': 'completed'
            }
            
            # Add transaction to both tables in a try-except block
            try:
                logger.debug(f"Inserting enriched data into ntropy_transactions table for transaction {ntropy_tx_id}")
                ntropy_result = await supabase.table('ntropy_transactions').insert(ntropy_data).execute()
                
                logger.debug(f"Updating ntropy_enrich flag for transaction {ntropy_tx_id}")
                await supabase.table('gocardless_transactions').update({
                    'ntropy_enrich': True
                }).eq('id', ntropy_tx_id).execute()
                
                return ntropy_result.data[0]
            except Exception as db_error:
                logger.error(f"Database error while storing transaction: {str(db_error)}")
                raise ValueError(f"Failed to store transaction in database: {str(db_error)}")
            
        except Exception as e:
            logger.error(f"Failed to store Ntropy transaction: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to store Ntropy transaction: {str(e)}")

    async def get_batch_status(self, batch_id: str) -> dict:
        """
        Get the current status of a batch
        
        Args:
            batch_id (str): The batch ID to check
            
        Returns:
            dict: Status response containing status and progress information
        """
        logger.info(f"Checking status for batch {batch_id}")
        batch = self.sdk.batches.get(id=batch_id)
        
        if batch.is_completed():
            logger.info(f"Batch {batch_id} is complete, retrieving results")
            batch_result = self.sdk.batches.results(id=batch_id)
            # Log the raw batch result for debugging
            logger.debug(f"Raw batch result from Ntropy: {batch_result}")
            
            # Access the enriched transactions from the results field
            transactions = batch_result.results
            logger.info(f"Processing {len(transactions)} enriched transactions from batch {batch_id}")
            
            for transaction in transactions:
                # Convert to dict if it's not already
                tx_data = transaction.model_dump() if hasattr(transaction, 'model_dump') else transaction
                await self.store_ntropy_transaction(batch_id, tx_data)
            
            return {
                "status": "complete",
                "progress": 100,
                "total": batch.total
            }
        elif batch.is_error():
            logger.error(f"Batch {batch_id} processing failed")
            return {
                "status": "error",
                "progress": 0,
                "error": "Batch processing failed"
            }
        else:
            logger.info(f"Batch {batch_id} is still processing, progress: {batch.progress}/{batch.total}")
            return {
                "status": "processing",
                "progress": batch.progress,
                "total": batch.total
            }

    """ entry point """
    async def enrich_transactions(self, user_id: str) -> BatchCreateResponse:
        """
        Enrich all transactions for a given user using Ntropy API
        
        Args:
            user_id (str): The ID of the user
            
        Returns:
            BatchCreateResponse: The batch creation response containing the batch ID
        """
        logger.info(f"Starting transaction enrichment for user {user_id}")
        
        try:
            # Get the Ntropy account holder ID
            account_holder_id = await self.get_account_holder_id(user_id)
            logger.info(f"Found Ntropy account holder ID: {account_holder_id}")
            
            transactions = await self.get_user_transactions(user_id)
            
            if not transactions:
                logger.warning(f"No transactions found for user {user_id}")
                return None
            
            logger.info(f"Transforming {len(transactions)} transactions for Ntropy enrichment")
            ntropy_transactions = transform_transactions_for_ntropy(transactions)
            ntropy_transactions_dict = [tx.model_dump() for tx in ntropy_transactions]
            
            # Add error handling for batch creation
            try:
                logger.info(f"Sending batch of {len(ntropy_transactions_dict)} transactions to Ntropy")
                response = self.sdk.batches.create(
                    operation="POST /v3/transactions",
                    data=ntropy_transactions_dict
                )
                logger.info(f"Successfully created Ntropy batch with ID: {response.id}")
                return response
            except Exception as batch_error:
                logger.error(f"Error creating Ntropy batch: {str(batch_error)}", exc_info=True)
                raise ValueError(f"Failed to create Ntropy batch: {str(batch_error)}")
            
        except Exception as e:
            logger.error(f"Error in transaction enrichment: {str(e)}", exc_info=True)
            raise ValueError(f"Transaction enrichment failed: {str(e)}")
