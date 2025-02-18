from typing import List, Dict, Any
import asyncio

from app.services.vectorise_data import get_embedding, get_voyage_embedding
from app.services.supabase import get_supabase

async def init_supabase():
    return await get_supabase()

async def search_chart_of_accounts(
    embedding_column: str,
    query_text: str,
    user_id: str,
    match_count: int = 10,
    similarity_threshold: float = 0.2,  # Lowered from 0.5 to allow more semantic matches
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
    supabase = await init_supabase()
    
    # Generate embedding for the query text
    if embedding_column == 'voyage_embeddings':
        embedding = await get_voyage_embedding(query_text, "query")
    else:
        embedding = await get_embedding(query_text)  # Default embedding for other types
    
    try:
        # Call the RPC function with correctly named parameters
        response = await supabase.rpc(
            'search_account_embeddings',
            {
                'query_embedding': embedding,  # Changed from query_text to query_embedding
                'user_id': user_id,
                'embedding_column': embedding_column,
                'similarity_threshold': similarity_threshold,
                'match_count': match_count
            }
        ).execute()
        
        # Return the results
        return response.data
    except Exception as e:
        raise Exception(f"Error calling search_account_embeddings: {str(e)}")

async def main():
    # Test queries
    queries = [
            """    'creditor_name': 'TFL TRAVEL CHARGE',
            'remittance_info': 'TFL TRAVEL CHARGE       TFL.GOV.UK/CP',
            'amount': -919,
            'user_id': 'user_123'""",
        

    ]

    print("\nTesting similarity search with different queries...")
    print("=" * 80)

    for query in queries:
        results = await search_chart_of_accounts(
            embedding_column='voyage_embeddings',  # Specify which embedding to use
            query_text=query,
            user_id='test-user',  # Add a test user ID
            similarity_threshold=0.2,  # Lower threshold for better semantic matching
            match_count=5
        )
        
        print(f"\nQuery: '{query}'")
        print("-" * 40)
        
        if not results:
            print("No matching accounts found.")
            continue
            
        print(f"Found {len(results)} matching accounts:")
        for i, match in enumerate(results, 1):
            print(f"\n{i}. {match['account_name']} (Code: {match['account_code']})")
            print(f"   Type: {match['account_type']}")
            print(f"   Description: {match['account_description']}")
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





# {
#   "id": "58568b90-2338-468b-a4ee-e7117a76c73a89875122-7084-4d1f-81b4-21378bffc75e",
#   "error": null,
#   "entities": {
#     "counterparty": {
#       "id": "4ba14a63-bcfa-311f-9fcc-c09b5c6c04f7",
#       "logo": "https://logos.ntropy.com/mcdonalds.com",
#       "mccs": [],
#       "name": "McDonald's Corporation",
#       "type": "organization",
#       "website": "mcdonalds.com"
#     },
#     "intermediaries": []
#   },
#   "categories": {
#     "general": "employee spend - restaurant",
#     "accounting": null
#   },
#   "created_at": "2025-02-17T21:22:21.728037+00:00"
# }
# {
#   "id": "7bc9c59f-b344-47d8-b63f-df4578a26a2525e0a527-e37a-4412-a70b-a6c99a81d299",
#   "error": null,
#   "entities": {
#     "counterparty": {
#       "id": "1c027e23-3fe1-3cb7-9e07-c9a0d18c1e81",
#       "logo": "https://logos.ntropy.com/tfl.gov.uk",
#       "mccs": [],
#       "name": "Transport for London",
#       "type": "organization",
#       "website": "tfl.gov.uk"
#     },
#     "intermediaries": [
#       {
#         "id": "1c027e23-3fe1-3cb7-9e07-c9a0d18c1e81",
#         "logo": "https://logos.ntropy.com/tfl.gov.uk",
#         "mccs": [],
#         "name": "Transport for London",
#         "website": "tfl.gov.uk"
#       }
#     ],
#   "categories": {
#     "general": "employee spend - public transportation",
#     "accounting": null
#   },
#   "created_at": "2025-02-17T20:55:21.219047+00:00"
# }

# {
#   "id": "15f58c8a-32d2-427c-90d3-2b889714c75cef5598b5-f738-4cb0-bafa-f4a6ff92829f",
#   "error": null,
#   "entities": {
#     "counterparty": {
#       "id": "c9485c47-6e77-30b4-88da-bbac9aa4ebf2",
#       "logo": "https://logos.ntropy.com/amazon.com",
#       "mccs": [],
#       "name": "Amazon UK",
#       "type": "organization",
#       "website": "amazon.com"
#     },
#     "intermediaries": []
#   },
#   "categories": {
#     "general": "employee spend - office supplies",
#     "accounting": null
#   },
#   "created_at": "2025-02-17T21:22:21.728020+00:00"
# }