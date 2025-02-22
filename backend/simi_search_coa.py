from typing import List, Dict, Any
import asyncio
import json

from app.services.etl.vectorise_data import get_embedding, get_voyage_embedding
from app.services.etl.supabase import get_supabase


""" our sql similarity search function """
async def search_chart_of_accounts(
    embedding_column: str,
    query_text: str,
    user_id: str,
    match_count: int = 10,
    similarity_threshold: float = 0.3,  # Lowered from 0.5 to allow more semantic matches
) -> List[Dict[Any, Any]]:
    """
    Search for chart of accounts entries similar to the provided query text.
    Uses a combination of semantic similarity and text matching to find relevant results.
    
    Args:
        embedding_column: Which embedding column to use ('embedding', 'jina_embedding', 'voyage_embeddings')
        query_text: The transaction description or query text
        user_id: User ID to filter results
        match_count: Maximum number of results to return
        similarity_threshold: Minimum similarity score (0-1). Lower values (0.2-0.3) work better for semantic search
    
    Returns:
        List of matching chart of accounts entries with similarity scores
    """
    
    # Generate embedding for the query text
    if embedding_column == 'voyage_embeddings':
        embedding = await get_voyage_embedding(query_text, "query")
    else:
        embedding = await get_embedding(query_text)  # Default embedding for other types
    
    try:
        supabase = await get_supabase()
        # Get results from RPC
        response = await supabase.rpc(
            'search_account_embeddings',
            {
                'query_embedding': embedding,
                'user_id': user_id, 
                'embedding_column': embedding_column,
                'similarity_threshold': similarity_threshold,
                'match_count': match_count
            }
        ).execute()
        

        return response.data
    except Exception as e:
        raise Exception(f"Error calling search_account_embeddings: {str(e)}")

async def search_transactions_categories() -> None:
    """
    Fetch transactions with details and use LLM to match against chart of accounts.
    Includes transaction amount, entity name, and remittance info in the decision process.
    """
    try:
        supabase = await get_supabase()
        print("\n🔄 Fetching transactions with details...")
        
        # Expanded transaction fields
        response = await supabase.table('gocardless_transactions') \
            .select('''
                id, 
                llm_category,
                amount,
                entity_name,
                remittance_info,
                description
            ''') \
            .limit(5) \
            .execute()
        
        transactions = response.data
        
        if not transactions:
            print("❌ No transactions found")
            return
            
        print("\n📊 Analyzing Transactions")
        print("=" * 80)
        
        for tx in transactions:
            if not tx.get('llm_category'):
                continue
                
            try:
                # Parse LLM category
                llm_data = json.loads(tx['llm_category']) if isinstance(tx['llm_category'], str) else tx['llm_category']
                category = llm_data.get('category')
                if not category:
                    continue
                
                print(f"\n🔍 Transaction Analysis")
                print("=" * 60)
                print(f"📝 Transaction ID: {tx['id']}")
                print(f"💰 Amount: {tx['amount']}")
                print(f"🏢 Entity: {tx['entity_name']}")
                print(f"📄 Remittance Info: {tx['remittance_info']}")
                print(f"🏷️  Category: {category}")
                print("-" * 60)
                
                # Get similar accounts
                results = await search_chart_of_accounts(
                    embedding_column='voyage_embeddings',
                    query_text=category,
                    user_id='ALL',
                    similarity_threshold=0.3,
                    match_count=5
                )
                
                if not results:
                    print("❌ No matching accounts found.")
                    continue
                
                print(f"✨ Found {len(results)} potential account matches:")
                
                # Prepare context for LLM decision
                accounts_context = []
                for i, match in enumerate(results, 1):
                    similarity_percentage = match['similarity'] * 100
                    account_info = {
                        'name': match['account_name'],
                        'code': match['account_code'],
                        'type': match['account_type'],
                        'similarity': similarity_percentage
                    }
                    accounts_context.append(account_info)
                    
                    print(f"\n{i}. {match['account_name']}")
                    print(f"   Code: {match['account_code']} | Type: {match['account_type']}")
                    print(f"   Match Score: {similarity_percentage:.1f}%")
                
                # TODO: Call LLM to make final account selection
                # We'll need to implement this function
                selected_account = await select_best_account_match(
                    transaction={
                        'amount': tx['amount'],
                        'entity': tx['entity_name'],
                        'remittance': tx['remittance_info'],
                        'description': tx['description'],
                        'category': category
                    },
                    potential_accounts=accounts_context
                )
                
                print("\n✅ LLM Account Selection:")
                print(f"Selected: {selected_account['name']} ({selected_account['code']})")
                print(f"Reason: {selected_account['reason']}")
                
            except json.JSONDecodeError:
                print(f"⚠️  Invalid JSON in llm_category for transaction {tx['id']}")
                continue
            except Exception as e:
                print(f"❌ Error processing transaction {tx['id']}: {str(e)}")
                continue
            
            print("=" * 60)
            
    except Exception as e:
        print(f"❌ Error fetching transactions: {str(e)}")

async def select_best_account_match(transaction: dict, potential_accounts: List[dict]) -> dict:
    """
    Use LLM to select the best matching account based on transaction details and potential matches.
    
    Args:
        transaction: Dict containing transaction details
        potential_accounts: List of potential matching accounts with similarity scores
    
    Returns:
        Dict containing selected account and reasoning
    """
    # TODO: Implement LLM call to make selection
    # For now, return the highest similarity match
    best_match = max(potential_accounts, key=lambda x: x['similarity'])
    return {
        'name': best_match['name'],
        'code': best_match['code'],
        'reason': 'Selected based on highest similarity score (LLM selection pending implementation)'
    }

async def main():
    await search_transactions_categories()

if __name__ == "__main__":
    asyncio.run(main())


