from typing import List, Dict, Any
import voyageai
from app.services.vectorise_data import get_voyage_embedding
from app.services.supabase import get_supabase

async def prepare_account_text(account: Dict[str, Any]) -> str:
    """Prepare account text for embedding by combining relevant fields"""
    text_parts = [
        account.get('name', ''),
        account.get('description', ''),
        account.get('account_type', ''),
        account.get('reporting_code', '')
    ]
    return ' '.join([part for part in text_parts if part])

async def prepare_transaction_text(transaction: Dict[str, Any]) -> str:
    """Prepare transaction text for embedding"""
    text_parts = [
        transaction.get('creditor_name', ''),
        transaction.get('remittance_info', '')
    ]
    return ' '.join([part for part in text_parts if part])

async def embed_accounts(accounts: List[Dict[str, Any]]) -> None:
    """Create and store embeddings for chart of accounts"""
    supabase = await get_supabase()
    
    for account in accounts:
        account_text = await prepare_account_text(account)
        embedding = await get_voyage_embedding(account_text, input_type="document")
        
        # Update the account with its embedding
        await supabase.table('chart_of_accounts').update({
            'embedding': embedding
        }).eq('id', account['id']).execute()

async def find_matching_account(
    transaction: Dict[str, Any],
    similarity_threshold: float = 0.7,
    max_matches: int = 5
) -> List[Dict[str, Any]]:
    """Find matching accounts for a transaction using vector similarity"""
    supabase = await get_supabase()
    
    # Prepare and embed transaction text
    transaction_text = await prepare_transaction_text(transaction)
    print(f"Transaction text: {transaction_text}")  # Debugging
    query_embedding = await get_voyage_embedding(transaction_text, input_type="query")
    
    # Debugging: Print embedding shape
    print(f"Query embedding length: {len(query_embedding)}")
    
    # Search for similar accounts
    result = await supabase.rpc(
        'search_account_embeddings',
        {
            'query_embedding': query_embedding,
            'similarity_threshold': similarity_threshold,
            'match_count': max_matches,
            'user_id': transaction['user_id']
        }
    ).execute()
    
    # Debugging: Print raw results
    print(f"Search results: {result.data}")
    
    return result.data

async def batch_process_transactions(
    transactions: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Process a batch of transactions and find matching accounts"""
    results = []
    
    for transaction in transactions:
        matches = await find_matching_account(transaction)
        results.append({
            'transaction': transaction,
            'matches': matches
        })
    
    return results

async def verify_embeddings(user_id: str) -> bool:
    """Verify that embeddings exist and are valid"""
    supabase = await get_supabase()
    result = await supabase.table('chart_of_accounts') \
        .select('id, embedding') \
        .eq('user_id', user_id) \
        .limit(1) \
        .execute()
    
    if not result.data:
        return False
        
    account = result.data[0]
    return 'embedding' in account and isinstance(account['embedding'], list) and len(account['embedding']) > 0 

async def test_matching():
    test_transaction = {
        'creditor_name': 'TFL TRAVEL CHARGE',
        'remittance_info': 'TFL TRAVEL CHARGE       TFL.GOV.UK/CP',
        'amount': -919,
        'user_id': 'user_123'
    }
    
    # Verify embeddings first
    if not await verify_embeddings(test_transaction['user_id']):
        print("No embeddings found. Please run embed_accounts first.")
        return
        
    # Test matching
    matches = await find_matching_account(test_transaction)
    if matches:
        print("Matching accounts found:")
        for match in matches:
            print(f"- {match['name']} (similarity: {match['similarity']})")
    else:
        print("No matches found. Consider lowering the similarity threshold.") 