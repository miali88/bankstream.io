from typing import List, Dict, Any
import asyncio
import json
import openai
from openai import AsyncOpenAI
import os
from datetime import datetime
from pydantic import BaseModel
from enum import Enum
from itertools import islice
from dataclasses import dataclass
from collections import defaultdict

from app.services.etl.vectorise_data import get_embedding, get_voyage_embedding
from backend.app.core.supabase_client import get_supabase

# Initialize OpenAI client
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class SelectedAccount(BaseModel):
    name: str
    code: str

class AccountSelectionResponse(BaseModel):
    selected_account: SelectedAccount
    confidence: ConfidenceLevel
    reasoning: str

@dataclass
class TransactionBatch:
    transaction_id: str
    prompt: str
    potential_accounts: List[dict]

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

async def save_account_match(transaction_id: str, account_match: dict) -> None:
    """Save the selected account match back to Supabase"""
    try:
        supabase = await get_supabase()
        
        print(f"\n💾 Saving account match for transaction {transaction_id}")
        
        update_data = {
            'chart_of_accounts': account_match['account_id'],
        }
        
        response = await supabase.table('gocardless_transactions') \
            .update(update_data) \
            .eq('id', transaction_id) \
            .execute()
            
        print("✅ Account match saved successfully")
        
    except Exception as e:
        print(f"❌ Error saving account match: {str(e)}")

async def prepare_transaction_batch(transactions: List[dict]) -> List[TransactionBatch]:
    """Prepare transactions for batch processing"""
    batches = []
    print("\n📦 Preparing transaction batch...")

    for tx in transactions:
        try:
            if not tx.get('llm_category'):
                continue

            # Parse LLM category
            llm_data = json.loads(tx['llm_category']) if isinstance(tx['llm_category'], str) else tx['llm_category']
            category = llm_data.get('category')
            if not category:
                continue

            entity_name = (
                tx.get('creditor_name', 'Unknown Entity') if tx['amount'] > 0 
                else tx.get('debtor_name', 'Unknown Entity')
            )
            remittance_info = tx.get('remittance_info', '')

            # Get similar accounts
            results = await search_chart_of_accounts(
                embedding_column='voyage_embeddings',
                query_text=category,
                user_id='ALL',
                similarity_threshold=0.3,
                match_count=5
            )

            if not results:
                continue

            # Prepare accounts context
            accounts_context = []
            for match in results:
                similarity_percentage = match['similarity'] * 100
                account_info = {
                    'name': match['account_name'],
                    'code': match['account_code'],
                    'account_id': match['account_id'],
                    'type': match['account_type'],
                    'similarity': similarity_percentage
                }
                accounts_context.append(account_info)

            # Format prompt
            prompt = format_llm_prompt({
                'amount': tx['amount'],
                'entity': entity_name,
                'remittance': remittance_info,
                'category': category
            }, accounts_context)

            batches.append(TransactionBatch(
                transaction_id=tx['id'],
                prompt=prompt,
                potential_accounts=accounts_context
            ))

        except Exception as e:
            print(f"❌ Error preparing transaction {tx['id']}: {str(e)}")
            continue

    return batches

def format_llm_prompt(transaction: dict, accounts: List[dict]) -> str:
    """Format prompt for LLM"""
    accounts_text = "\n".join([
        f"Account {i+1}:"
        f"\n- Name: {acc['name']}"
        f"\n- Code: {acc['code']}"
        f"\n- Type: {acc['type']}"
        f"\n- Similarity: {acc['similarity']:.1f}%"
        for i, acc in enumerate(accounts)
    ])

    return f"""
    <prompt>
        <role>You are an expert accountant. Analyze this transaction and select the most appropriate account from the options.</role>
        <transaction_details>
            <amount>{transaction['amount']}</amount>
            <entity>{transaction['entity']}</entity>
            <description>{transaction['remittance']}</description>
            <category>{transaction['category']}</category>
        </transaction_details>

        <available_accounts>
            {accounts_text}
        </available_accounts>

        <considerations>
            <factor>1. Account type appropriateness</factor>
            <factor>2. Transaction nature</factor>
            <factor>3. Amount scale</factor>
            <factor>4. Entity relationship</factor>
        </considerations>
    </prompt>
    """

async def process_batch(batch: List[TransactionBatch], batch_size: int = 5) -> List[Dict]:
    """Process a batch of transactions with rate limiting"""
    results = []
    
    # Process in smaller chunks to avoid rate limits
    for chunk in chunks(batch, batch_size):
        chunk_tasks = []
        for tx_batch in chunk:
            task = client.beta.chat.completions.parse(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert accountant assistant that helps classify transactions to the correct account codes."},
                    {"role": "user", "content": tx_batch.prompt}
                ],
                response_format=AccountSelectionResponse,
                temperature=0
            )
            chunk_tasks.append(task)

        # Process chunk concurrently
        chunk_responses = await asyncio.gather(*chunk_tasks, return_exceptions=True)
        
        # Process responses
        for tx_batch, response in zip(chunk, chunk_responses):
            try:
                if isinstance(response, Exception):
                    raise response

                result = response.choices[0].message.parsed
                
                # Find matching account
                selected = next(
                    acc for acc in tx_batch.potential_accounts 
                    if acc['code'] == result.selected_account.code
                )

                results.append({
                    'transaction_id': tx_batch.transaction_id,
                    'account_match': {
                        'name': selected['name'],
                        'account_id': selected['account_id'],
                        'code': selected['code'],
                        'confidence': result.confidence,
                        'reason': result.reasoning
                    }
                })

            except Exception as e:
                print(f"❌ Error processing transaction {tx_batch.transaction_id}: {str(e)}")
                # Fallback to highest similarity match
                best_match = max(tx_batch.potential_accounts, key=lambda x: x['similarity'])
                results.append({
                    'transaction_id': tx_batch.transaction_id,
                    'account_match': {
                        'name': best_match['name'],
                        'account_id': best_match['account_id'],
                        'code': best_match['code'],
                        'confidence': ConfidenceLevel.LOW,
                        'reason': f'Fallback to highest similarity match due to error: {str(e)}'
                    }
                })

        # Rate limiting pause between chunks
        await asyncio.sleep(1)

    return results

async def batch_save_matches(matches: List[Dict]) -> None:
    """Save multiple account matches in parallel"""
    save_tasks = [
        save_account_match(match['transaction_id'], match['account_match'])
        for match in matches
    ]
    await asyncio.gather(*save_tasks)

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

async def search_transactions_categories() -> None:
    """Main function with batch processing"""
    try:
        supabase = await get_supabase()
        print("\n🔄 Fetching transactions...")
        
        response = await supabase.table('gocardless_transactions') \
            .select('''
                id, 
                llm_category,
                amount,
                creditor_name,
                debtor_name,
                remittance_info,
                chart_of_accounts
            ''') \
            .execute()
        
        transactions = response.data
        if not transactions:
            print("❌ No transactions found")
            return

        # Prepare batches
        batches = await prepare_transaction_batch(transactions)
        print(f"\n📊 Prepared {len(batches)} transactions for processing")

        # Process batches
        results = await process_batch(batches)
        print(f"\n✅ Processed {len(results)} transactions")

        # Save results
        await batch_save_matches(results)
        print("\n💾 All matches saved to database")

    except Exception as e:
        print(f"❌ Error in batch processing: {str(e)}")

async def main():
    await search_transactions_categories()

if __name__ == "__main__":
    asyncio.run(main())


