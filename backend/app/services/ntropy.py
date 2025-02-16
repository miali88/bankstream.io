from typing import List

from app.schemas.transactions import TransactionsTable
from app.schemas.ntropy import EnrichedTransactionRequest

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
