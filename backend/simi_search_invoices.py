from typing import List, Dict, Any
import asyncio

from app.services.etl.vectorise_data import get_embedding, get_voyage_embedding
from app.services.etl.supabase import get_supabase

async def init_supabase():
    return await get_supabase()

""" 
status:
- currently very poor transaction to invoice matching
- need to consider search by invoice from to entity, and range matching on amounts (+- 10%) and dates (+- 1 month)
- perhaps instead of hard match, we present the retrieved invoices and allow the user to select the best match
to implement re-indexing as suggested here:
https://claude.ai/chat/9b6eff20-64f6-4c74-a884-56071ab380f8
 """
async def search_invoices(
    embedding_column: str,
    query_text: str,
    client_id: str = None,
    match_count: int = 10,
    similarity_threshold: float = 0.3,
) -> List[Dict[Any, Any]]:
    """
    Search for invoices similar to the provided query text.
    Uses a combination of semantic similarity and text matching to find relevant results.
    
    Args:
        embedding_column: Which embedding column to use ('embedding', 'jina_embedding', 'voyage_embeddings')
        query_text: The search query text
        client_id: Client ID to filter results
        match_count: Maximum number of results to return
        similarity_threshold: Minimum similarity score (0-1)
    
    Returns:
        List of matching invoices with similarity scores
    """
    supabase = await init_supabase()
    
    # Generate embedding for the query text
    if embedding_column == 'voyage_embeddings':
        embedding = await get_voyage_embedding(query_text, "query")
    else:
        embedding = await get_embedding(query_text)
    
    try:
        response = await supabase.rpc(
            'search_invoices',
            {
                'query_embedding': embedding,
                'query_text': query_text,
                'embedding_column': embedding_column,
                'search_client_id': client_id,
                'match_threshold': similarity_threshold,
                'match_count': match_count
            }
        ).execute()
        
        return response.data
    except Exception as e:
        raise Exception(f"Error calling search_invoices: {str(e)}")

async def main():
    # Test queries
    queries = ["""
        'creditor name: CURSOR, AI POWEREDIDE NEW YORK US'
        'amount: 4990'
        'currency: GBP'
        'description: 2876 07FEB25  CURSOR, AI POWEREDIDE  NEW YORK US   USD  60.00VRATE  1.2355N-S TRN FEE   1.34'
            """]

    print("\nTesting invoice similarity search...")
    print("=" * 80)

    for query in queries:
        results = await search_invoices(
            embedding_column='voyage_embeddings',
            query_text=query,
            similarity_threshold=0.3,
            match_count=10
        )
        
        print(f"\nQuery: '{query}'")
        print("-" * 40)
        
        if not results:
            print("No matching invoices found.")
            continue
            
        print(f"Found {len(results)} matching invoices:")
        for i, match in enumerate(results, 1):
            print(f"\n{i}. Invoice ID: {match['invoice_id']}")
            print(f"   Client ID: {match['client_id']}")
            print(f"   Status: {match['status']}")
            print(f"   Source File: {match['source_file']}")
            print(f"   Created At: {match['created_at']}")
            if match.get('similarity'):
                print(f"   Similarity: {match['similarity']:.4f}")
            # Print a truncated version of the results JSON
            print(f"   Results Preview: {str(match['results'])}...")
        print("-" * 40)

if __name__ == "__main__":
    asyncio.run(main())

