from typing import Dict
import logging
import csv
from io import StringIO

from app.services.etl.supabase import get_supabase
from app.schemas.transactions import Insights
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

        # Get transactions with count and proper join on ntropy_id
        logger.debug("Executing Supabase query to fetch transactions")
        result = await (supabase.table('gocardless_transactions')
            .select('*, ntropy_transactions!inner(enriched_data)', count='exact')
            .eq('user_id', user_id)
            .order('created_at', desc=True)
            .range(offset, offset + page_size - 1)
            .execute())

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
                # Transform category from dict to string using the 'general' category
                categories = enriched_data.get('categories', {})
                tx['categories'] = categories  # Keep the full category data
                tx['category'] = categories.get('general') if isinstance(categories, dict) else None
            else:
                logger.debug(f"No enriched data found for transaction {tx.get('id')}")
                tx['entities'] = None
                tx['categories'] = None
                tx['category'] = None
            transactions.append(tx)

        logger.info(f"Returning {len(transactions)} processed transactions")
        return {
            "transactions": transactions,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": -(-total_count // page_size)  # Ceiling division
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
    
    
    async def get_insights(self, user_id: str) -> Insights:
        """
        Get insights for a user by calculating spending by category and entity
        
        Args:
            user_id (str): The ID of the user
            
        Returns:
            Insights: Object containing spending breakdowns by category and entity
        """
        logger.info(f"Calculating insights for user {user_id}")
        
        try:
            # Get transactions with enriched data
            supabase = await self.get_supabase()
            result = await supabase.table("gocardless_transactions")\
                .select("*, ntropy_transactions!inner(enriched_data)")\
                .eq("user_id", user_id)\
                .execute()

            transactions = result.data
            logger.info(f"Found {len(transactions)} transactions to analyze")

            # Initialize dictionaries to store category and entity totals
            category_totals = {}
            entity_totals = {}

            # Process each transaction
            for tx in transactions:
                amount = float(tx.get('amount', 0))
                amount = amount / 100  # Convert to dollars
                
                # Process category spending
                categories = tx.get('llm_category', {})
                category = categories.get('category') if isinstance(categories, dict) else categories
                
                if category:
                    logger.debug(f"Adding amount {amount} to category {category}")
                    category_totals[category] = category_totals.get(category, 0) + amount

                # Process entity spending
                entity_name = tx.get('ntropy_entity')
                if entity_name:
                    logger.debug(f"Adding amount {amount} to entity {entity_name}")
                    entity_totals[entity_name] = entity_totals.get(entity_name, 0) + amount

            # Convert dictionaries to lists of dictionaries as per the model
            spending_by_category = [
                {"category": str(cat), "amount": round(float(amount), 2)}  # Ensure types match schema
                for cat, amount in category_totals.items()
                if cat is not None  # Skip None categories
            ]
            
            spending_by_entity = [
                {"entity": str(ent), "amount": round(float(amount), 2)}  # Ensure types match schema
                for ent, amount in entity_totals.items()
                if ent is not None  # Skip None entities
            ]

            # Sort both lists by amount in descending order
            spending_by_category.sort(key=lambda x: x["amount"], reverse=True)
            spending_by_entity.sort(key=lambda x: x["amount"], reverse=True)

            logger.info(f"Successfully calculated insights: {len(spending_by_category)} categories, {len(spending_by_entity)} entities")
            
            return Insights(
                spending_by_category=spending_by_category,
                spending_by_entity=spending_by_entity
            )

        except Exception as e:
            logger.error(f"Error calculating insights: {str(e)}", exc_info=True)
            raise