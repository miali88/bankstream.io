import asyncio
import os
import logging
from supabase import create_client
from openai import AsyncOpenAI
from typing import List, Dict
from collections import defaultdict
from brave_search import brave_search
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize clients
async_openai_client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

BATCH_SIZE = 10

def init_supabase():
    """Initialize Supabase client with error checking"""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        raise ValueError("Missing Supabase credentials in environment variables")
    
    logger.info(f"Initializing Supabase client with URL: {url[:20]}...")
    return create_client(url, key)

try:
    supabase = init_supabase()
    logger.info("Successfully initialized Supabase client")
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {str(e)}")
    raise

"""
AFTER RUNNING THIS, then run CoA assignment. 
sun simi search for transactions of similar categories 
"""

async def get_entity_context(entity_name: str) -> str:
    """Get additional context about an entity using Brave Search."""
    logger.info(f"Fetching context for entity: {entity_name}")
    try:
        # Add delay to respect rate limits
        await asyncio.sleep(1)
        search_results = await brave_search(entity_name, count=3)
        if search_results:
            logger.info(f"Successfully retrieved context for {entity_name}")
            return search_results
        else:
            logger.warning(f"Empty search results for {entity_name}")
            return ""
    except Exception as e:
        logger.error(f"Brave Search error for {entity_name}: {str(e)}")
        if "RATE_LIMITED" in str(e):
            logger.error("Hit Brave Search rate limit - waiting before retry")
            await asyncio.sleep(2)  # Wait longer on rate limit
            try:
                search_results = await brave_search(entity_name, count=3)
                return search_results
            except Exception as retry_e:
                logger.error(f"Retry failed: {str(retry_e)}")
        return ""

async def get_uk_gaap_category(transactions: List[Dict], entity_context: str) -> List[Dict]:
    """Get UK GAAP categories for a batch of transactions from the same entity."""
    logger.info(f"Processing {len(transactions)} transactions for categorization")
    
    # Define the JSON schema for structured output
    json_schema = {
        "type": "object",
        "properties": {
            "transactions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "transaction_id": {"type": "string"},
                        "category": {
                            "type": "object",
                            "properties": {
                                "uk_gaap_category": {"type": "string"},
                                "confidence_score": {"type": "number"},
                                "reasoning": {"type": "string"}
                            },
                            "required": ["uk_gaap_category", "confidence_score", "reasoning"]
                        }
                    },
                    "required": ["transaction_id", "category"]
                }
            }
        },
        "required": ["transactions"]
    }

    transactions_text = "\n".join([
        f"Transaction ID {tx['id']}:\n"
        f"- Amount: {tx['amount']}\n"
        f"- Remittance Info: {tx['remittance_info']}\n"
        f"- Entity: {tx['entity']}"
        for tx in transactions
    ])
    
    company_name = "Flowon AI"
    company_description = "Flowon AI is a agentic platform to create telephone and chatbots for your website."
    business_context = f"""
            <business_context>
            <company_name>{company_name}</company_name>
            <description>{company_description}</description>
            <personnel>
                <directors>
                <director>Michael Ali</director>
                <director>Jacob Nathanial</director>
                </directors>
                <shareholders>
                <shareholder>Billy Eilson</shareholder>
                <shareholder>Nick Freeson</shareholder>
                </shareholders>
                <employees>
                <employee>Riley Harold</employee>
                <employee>Nicki Hailey</employee>
                <employee>Susain Boyland</employee>
                </employees>
            </personnel>
            </business_context>
            """

    try:
        logger.info("Sending request to OpenAI API")
        response = await async_openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a UK based accountant. Analyze each transaction, note the client context, counterparty context, and transaction details. Then enrich the transaction by categorising them."},
                {"role": "user", "content": f"""
                    Please analyze these transactions and categorize them according to UK GAAP standards.
                    In each response, make no mention of other transactions, just the one you are categorising, as your response will be used directly in a database update.
                 
                    Client company context:
                    {business_context}

                    Transaction counterparty context:
                    {entity_context}
                    
                    Transactions:
                    {transactions_text}
                    """}
            ],
            functions=[
                {
                    "name": "categorize_transactions",
                    "description": "Categorize transactions according to UK GAAP standards",
                    "parameters": json_schema
                }
            ],
            function_call={"name": "categorize_transactions"},
            temperature=0.1
        )
        
        # Parse the structured response
        result_json = json.loads(response.choices[0].message.function_call.arguments)
        logger.debug(f"Parsed response: {result_json}")
        
        # Log detailed categorization results
        logger.info("\n=== Transaction Categorization Details ===")
        for tx in result_json["transactions"]:
            logger.info(f"""
Transaction ID: {tx['transaction_id']}
Category: {tx['category']['uk_gaap_category']}
Confidence: {tx['category']['confidence_score']}
Reasoning: {tx['category']['reasoning']}
----------------------------------------""")
        
        # Convert to required output format - combining all fields into a single JSON
        results = [
            {
                "id": tx["transaction_id"],
                "llm_category": {
                    "category": tx["category"]["uk_gaap_category"],
                    "reasoning": tx["category"]["reasoning"],
                    "confidence": tx["category"]["confidence_score"]
                }
            }
            for tx in result_json["transactions"]
        ]
        
        logger.info(f"Successfully categorized {len(results)} transactions")
        return results
        
    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        return []

async def process_entity_transactions(entity: str, transactions: List[Dict]):
    """Process all transactions for a single entity in batches."""
    logger.info(f"\n=== Processing transactions for entity: {entity} ===")
    logger.info(f"Total transactions: {len(transactions)}")
    
    entity_context = await get_entity_context(entity)
    if not entity_context:
        logger.warning(f"No context found for entity {entity}, proceeding with empty context")
    else:
        logger.info(f"Entity context: {entity_context[:200]}...")  # Show first 200 chars of context
    
    for i in range(0, len(transactions), BATCH_SIZE):
        batch = transactions[i:i + BATCH_SIZE]
        logger.info(f"\nProcessing batch {i//BATCH_SIZE + 1} for {entity} ({len(batch)} transactions)")
        
        updates = await get_uk_gaap_category(batch, entity_context)
        
        if updates:
            logger.info(f"Found {len(updates)} valid categories to update")
            await update_transactions(updates)
        else:
            logger.warning(f"No valid categories found for batch")
            print("updates", updates)
        
        await asyncio.sleep(1)

async def process_transactions():
    """Main processing function that groups transactions by entity."""
    logger.info("Starting transaction processing")
    
    try:
        # Fetch unprocessed transactions
        logger.info("Fetching unprocessed transactions from database")
        response = supabase.table("gocardless_transactions")\
            .select("*")\
            .is_("llm_category", "null") \
            .execute()
        
        if not response.data:
            logger.info("No unprocessed transactions found")
            return
            
        logger.info(f"Found {len(response.data)} unprocessed transactions")
        
        # Group transactions by entity (including null entities)
        entity_transactions = defaultdict(list)
        processed_entities = set()
        
        for tx in response.data:
            # Get entity name, use "UNKNOWN_ENTITY" for null cases
            entity = tx.get('creditor_name') or tx.get('debtor_name') or "UNKNOWN_ENTITY"
            
            tx_data = {
                'id': tx['id'],
                'amount': tx['amount'],
                'remittance_info': tx['remittance_info'],
                'entity': entity
            }
            entity_transactions[entity].append(tx_data)

        logger.info(f"Grouped {len(response.data)} transactions into {len(entity_transactions)} entities")
        logger.info(f"Number of transactions with unknown entity: {len(entity_transactions.get('UNKNOWN_ENTITY', []))}")
        
        # Process each entity's transactions
        for entity, txs in entity_transactions.items():
            try:
                logger.info(f"\n=== Processing entity: {entity} ===")
                logger.info(f"Processing {len(txs)} transactions for this entity")
                
                # Skip internet search for unknown entities
                if entity == "UNKNOWN_ENTITY":
                    logger.info("Processing transactions with no entity information")
                    entity_context = "No entity information available for this transaction."
                    
                    # Process transactions directly in batches
                    for i in range(0, len(txs), BATCH_SIZE):
                        batch = txs[i:i + BATCH_SIZE]
                        updates = await get_uk_gaap_category(batch, entity_context)
                        if updates:
                            await update_transactions(updates)
                else:
                    await process_entity_transactions(entity, txs)
                
                processed_entities.add(entity)
                
            except Exception as e:
                logger.error(f"Failed to process entity {entity}: {str(e)}")
                continue
            
            await asyncio.sleep(2)  # Rate limiting between entities
        
        # Summary logging
        logger.info("\n=== Processing Summary ===")
        logger.info(f"Total entities processed: {len(processed_entities)}/{len(entity_transactions)}")
        if len(processed_entities) < len(entity_transactions):
            failed_entities = set(entity_transactions.keys()) - processed_entities
            logger.warning(f"Failed to process entities: {failed_entities}")

    except Exception as e:
        logger.error(f"Error in main process: {str(e)}")
        raise

async def update_transactions(transaction_updates: List[Dict]):
    """Update transaction categories in the database with JSON data."""
    for update in transaction_updates:
        try:
            logger.info(f"""
            Attempting to update transaction in Supabase:
            - ID: {update['id']}
            - Category Data: {json.dumps(update['llm_category'], indent=2)}""")  # JSON.dumps just for logging
                        
            # First verify the transaction exists
            response = supabase.table("gocardless_transactions")\
                .select("id")\
                .eq("id", update['id'])\
                .execute()
            
            if not response.data:
                logger.error(f"Transaction {update['id']} not found in database")
                continue
                
            # Perform the update - passing the JSON object directly
            update_response = supabase.table("gocardless_transactions")\
                .update({"llm_category": update['llm_category']})\
                .eq("id", update['id'])\
                .execute()
            
            if not update_response.data:
                logger.error(f"Update failed for transaction {update['id']}: No data returned")
                logger.error(f"Update response: {update_response}")
                continue
                
            logger.info(f"Successfully updated transaction {update['id']}")
            logger.debug(f"Update response: {update_response.data}")
            
        except Exception as e:
            logger.error(f"Error updating transaction {update['id']}: {str(e)}")
            logger.error(f"Full error details: {repr(e)}")

if __name__ == "__main__":
    logger.info("Starting script execution")
    try:
        asyncio.run(process_transactions())
        logger.info("Script completed successfully")
    except Exception as e:
        logger.error(f"Script failed: {str(e)}")