from typing import Dict
from app.services.supabase import get_supabase

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
        supabase = await self.get_supabase()
        offset = (page - 1) * page_size

        # Get transactions with count
        result = await (supabase.table('gocardless_transactions')
            .select('*, ntropy_transactions(enriched_data)', count='exact')
            .eq('user_id', user_id)
            .eq('ntropy_enrich', True)
            .order('created_at', desc=True)
            .range(offset, offset + page_size - 1)
            .execute())
        
        total_count = result.count
        transactions = []

        # Process the results to extract only entities and categories
        for tx in result.data:
            ntropy_data = tx.pop('ntropy_transactions', [])
            if ntropy_data and len(ntropy_data) > 0:
                enriched_data = ntropy_data[0].get('enriched_data', {})
                tx['entities'] = enriched_data.get('entities')
                tx['categories'] = enriched_data.get('categories')
            else:
                tx['entities'] = None
                tx['categories'] = None
            transactions.append(tx)

        return {
            "transactions": transactions,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": -(-total_count // page_size)
        } 
    