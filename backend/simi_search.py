from typing import List, Dict, Any
import asyncio

from app.services.vectorise_data import get_embedding, JinaTask
from app.services.supabase import get_supabase

async def init_supabase():
    return await get_supabase()

async def search_chart_of_accounts(
    query_text: str,
    match_threshold: float = 0.2,  # Lowered from 0.5 to allow more semantic matches
    match_count: int = 10,
    user_id: str = None
) -> List[Dict[Any, Any]]:
    """
    Search for chart of accounts entries similar to the provided query text.
    Uses a combination of semantic similarity and text matching to find relevant results.
    
    Args:
        query_text: The transaction description or query text
        match_threshold: Minimum similarity score (0-1). Lower values (0.2-0.3) work better for semantic search
        match_count: Maximum number of results to return
        user_id: Optional user ID to filter results
    
    Returns:
        List of matching chart of accounts entries with similarity scores
    """
    supabase = await init_supabase()
    
    # Generate embedding for the query text
    embedding, token_count = await get_embedding(query_text, JinaTask.RETRIEVAL_QUERY)
    
    try:
        # Call the RPC function
        response = await supabase.rpc(
            'search_chart_of_accounts',
            {
                'query_text': query_text,
                'query_embedding': embedding,
                'match_threshold': match_threshold,
                'match_count': match_count,
                'search_user_id': user_id
            }
        ).execute()
        
        # Return the results
        return response.data
    except Exception as e:
        raise Exception(f"Error calling search_chart_of_accounts: {str(e)}")

async def main():
    # Test queries
    queries = [
        "chairs for the office from Staples",
        "computer equipment and hardware",
        "salary payment to developers",
        "office supplies and stationery",
        "software licenses monthly subscription"
    ]

    print("\nTesting similarity search with different queries...")
    print("=" * 80)

    for query in queries:
        results = await search_chart_of_accounts(
            query_text=query,
            match_threshold=0.2,  # Lower threshold for better semantic matching
            match_count=5
        )
        
        print(f"\nQuery: '{query}'")
        print("-" * 40)
        
        if not results:
            print("No matching accounts found.")
            continue
            
        print(f"Found {len(results)} matching accounts:")
        for i, match in enumerate(results, 1):
            print(f"\n{i}. {match['name']} (Code: {match['code']})")
            print(f"   Type: {match['account_type']}")
            print(f"   Description: {match['description']}")
            if match.get('similarity'):
                print(f"   Similarity: {match['similarity']:.4f}")
        print("-" * 40)

if __name__ == "__main__":
    asyncio.run(main())



# import voyageai

# voyageai.api_key = os.getenv("VOYAGE_API_KEY")

# voyageai.Embedding.create(
#     input="Hello, world!",
# )

# voyageai.Client.embed()