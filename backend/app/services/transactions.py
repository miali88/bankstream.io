from typing import Dict
import logging
from app.services.supabase import get_supabase
import csv
from io import StringIO

logger = logging.getLogger(__name__)

class TransactionService:
    def __init__(self):
        self._supabase = None

    async def get_supabase(self):
        if not self._supabase:
            self._supabase = await get_supabase()
        return self._supabase

    async def get_user_transactions(
        self,
        user_id: str,
        page: int,
        page_size: int
    ) -> Dict:
        """
        Get paginated transactions for a user with enriched data when available
        
        Args:
            user_id (str): The ID of the user
            page (int): Page number (1-based)
            page_size (int): Number of items per page
            
        Returns:
            Dict containing:
                - transactions: List of transaction objects with enriched entities and categories
                - total_count: Total number of transactions
                - page: Current page number
                - page_size: Number of items per page
                - total_pages: Total number of pages
        """
        logger.info(f"Fetching transactions for user_id={user_id}, page={page}, page_size={page_size}")
        
        supabase = await self.get_supabase()
        offset = (page - 1) * page_size
        logger.debug(f"Calculated offset={offset} for pagination")

        # Get transactions with count
        logger.debug("Executing Supabase query to fetch transactions")
        result = await (supabase.table('gocardless_transactions')
            .select('*, ntropy_transactions(enriched_data)', count='exact')
            .eq('user_id', user_id)
            .is_('ntropy_enrich', 'true')
            .order('created_at', desc=True)
            .range(offset, offset + page_size - 1)
            .execute())
        print("bombaclart result", result)

        total_count = result.count
        logger.info(f"Found {total_count} total transactions for user")
        transactions = []

        # Process the results to extract only entities and categories
        logger.debug("Processing transaction results to extract enriched data")
        for tx in result.data:
            ntropy_data = tx.get('ntropy_transactions')
            if ntropy_data and isinstance(ntropy_data, list) and len(ntropy_data) > 0:
                logger.debug(f"Found enriched data for transaction {tx.get('id')}")
                enriched_data = ntropy_data[0].get('enriched_data', {})
                tx['entities'] = enriched_data.get('entities', {})
                tx['categories'] = enriched_data.get('categories', {})
            else:
                logger.debug(f"No enriched data found for transaction {tx.get('id')}")
                tx['entities'] = None
                tx['categories'] = None
            transactions.append(tx)

        logger.info(f"Returning {len(transactions)} processed transactions")
        return {
            "transactions": transactions,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": -(-total_count // page_size)
        }

    async def export_transactions_to_csv(self, user_id: str) -> str:
        """
        Export all transactions for a user to CSV format
        
        Args:
            user_id (str): The ID of the user
            
        Returns:
            str: CSV formatted string containing all transactions
        """
        logger.info(f"Starting CSV export for user {user_id}")
        
        supabase = await self.get_supabase()
        result = await supabase.table("gocardless_transactions").select("*").eq("user_id", user_id).execute()
        
        if not result.data:
            logger.warning(f"No transactions found for user {user_id}")
            raise ValueError("No transactions found")

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
        return output.getvalue() 
    