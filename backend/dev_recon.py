""" LLM inference for reconciliation"""

from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
import time
from typing import Dict, Tuple, List
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

# Initialize the ChatGroq model
groq_model = ChatGroq(model_name="Llama-3.3-70b-Specdec")
openai_model = ChatOpenAI(model="gpt-4o")


class TransactionClassifier:
    def __init__(self):
        logger.info("Initializing TransactionClassifier")
        self.system_prompt = """
        You are a helpful financial expert responsible for classifying transactions.
        You will be given multiple transactions and a list of chart of accounts to reconcile. 

        For each transaction, you must provide:
        1. A brief thought process and explanation of which chart of account is appropriate for this transaction
        2. The code for the most appropriate chart of account
        3. A confidence score between 0 and 1 (e.g., 0.95 for high confidence, 0.40 for low confidence)

        # IMPORTANT: Instructions for your response:
        You must respond with valid JSON in the following format only:
        {
          "classifications": [
            {
              "transaction_index": 0,
              "reasoning": "string",
              "account": "string",
              "confidence": float
            },
            {
              "transaction_index": 1,
              "reasoning": "string",
              "account": "string",
              "confidence": float
            },
            {
              "transaction_index": 2,
              "reasoning": "string",
              "account": "string",
              "confidence": float
            },
          ]
        }
        """
        self.last_request_time = 0
        self.rate_limit_delay = 2  # 2 seconds between requests (30 requests/minute)

    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.rate_limit_delay:
            delay = self.rate_limit_delay - time_since_last_request
            logger.debug(f"Rate limiting: waiting {delay:.2f} seconds")
            time.sleep(delay)
        self.last_request_time = time.time() 

    def classify_transactions_batch(self, transactions: List[Dict], chart_of_accounts: list) -> List[Tuple[str, str, float]]:
        """Classify a batch of transactions using the LLM"""
        logger.info(f"Starting classification of batch with {len(transactions)} transactions")
        logger.debug(f"Transactions to classify: {json.dumps(transactions, indent=2)}")
        logger.debug(f"Number of chart of accounts: {len(chart_of_accounts)}")
        
        self._rate_limit()

        # Format the transactions for the LLM
        transactions_prompt = f"""
        Please classify the following transactions:
        Transactions: {transactions}
        
        chart of accounts: {chart_of_accounts}
        """
        logger.debug(f"Generated prompt: {transactions_prompt}")

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=transactions_prompt)
        ]

        try:
            logger.info("Sending request to LLM")
            response = openai_model.invoke(messages)
            logger.debug(f"Raw LLM response: {response.content}")

            try:
                import re
                json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if json_match:
                    logger.debug("Found JSON structure in response")
                    result = json.loads(json_match.group())
                    classifications = result.get('classifications', [])
                    logger.info(f"Successfully parsed {len(classifications)} classifications")
                    logger.debug(f"Classifications: {json.dumps(classifications, indent=2)}")
                    
                    # Convert to list of tuples
                    return [
                        (c['account'], c['reasoning'], c['confidence'])
                        for c in sorted(classifications, key=lambda x: x['transaction_index'])
                    ]
                else:
                    logger.error("No JSON structure found in response")
                    return [(f"ERROR: No JSON found", "", 0.0)] * len(transactions)
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.debug(f"Problematic response content: {response.content}")
                return [(f"ERROR: {str(e)}", "", 0.0)] * len(transactions)

        except Exception as e:
            logger.error(f"Batch classification failed: {str(e)}", exc_info=True)
            return [(f"ERROR: {str(e)}", "", 0.0)] * len(transactions)

""" fetch transactions + ntropy enrich from supabase """
from pydantic import BaseModel
import pandas as pd

from app.services.supabase import get_supabase

class TransactionToLLM(BaseModel):
    entity_name : str
    amount : float
    remittance_info : str
    ntropy_enrich : bool
    ntropy_entity : str
    ntropy_category : str

def process_transactions(df: pd.DataFrame, chart_of_accounts: list) -> pd.DataFrame:
    """Process transactions grouped by remittance_info in batches of 3 groups"""
    logger.info(f"Starting to process {len(df)} transactions")
    logger.debug(f"Input DataFrame shape: {df.shape}")
    
    classifier = TransactionClassifier()

    # Create copy of DataFrame with new columns
    df = df.copy()
    df['coa_agent'] = None
    df['coa_reason'] = None
    df['coa_confidence'] = None

    # Group by remittance_info and get representative samples
    grouped = df.groupby('remittance_info')
    unique_groups = list(grouped.groups.keys())
    
    # Process groups in batches of 3
    batch_size = 3
    total_batches = (len(unique_groups) + batch_size - 1) // batch_size
    
    for i in range(0, len(unique_groups), batch_size):
        batch_end = min(i + batch_size, len(unique_groups))
        current_batch = (i // batch_size) + 1
        logger.info(f"Processing batch {current_batch}/{total_batches} (groups {i} to {batch_end-1})")
        
        # Get representative transactions from each group in this batch
        batch_transactions = []
        group_indices = []
        
        for remittance_info in unique_groups[i:batch_end]:
            group_df = grouped.get_group(remittance_info)
            # Take the first transaction as representative for the group
            representative = group_df.iloc[0]
            batch_transactions.append({
                **representative.to_dict(),
                'amount': representative['amount'],
                'group_size': len(group_df)
            })
            group_indices.append(remittance_info)
        
        # Get classifications for the batch
        classifications = classifier.classify_transactions_batch(batch_transactions, chart_of_accounts)
        
        # Apply classifications to all transactions in each group
        for remittance_info, (account, reasoning, confidence) in zip(group_indices, classifications):
            mask = df['remittance_info'] == remittance_info
            df.loc[mask, 'coa_agent'] = account
            df.loc[mask, 'coa_reason'] = reasoning
            df.loc[mask, 'coa_confidence'] = confidence
            
            group_size = len(df[mask])
            logger.info(f"Applied classification to group '{remittance_info}' ({group_size} transactions):")
            logger.info(f"Account: {account}")
            logger.info(f"Confidence: {confidence}")
            logger.info(f"Reason Preview: {' '.join(reasoning.split()[:10])}...")
            logger.info("-" * 50)

    logger.info("Finished processing all transaction groups")
    logger.debug(f"Final DataFrame shape: {df.shape}")
    return df

async def fetch_and_prepare_transactions() -> pd.DataFrame:
    """Fetch transactions from Supabase and prepare DataFrame"""
    logger.info("Starting to fetch transactions from Supabase")
    
    try:
        # Get Supabase client
        supabase = await get_supabase()
        logger.info("Successfully connected to Supabase")
        
        # Query both tables asynchronously
        logger.info("Querying Supabase tables...")
        ntropy_response = await supabase.table('ntropy_transactions').select('*').execute()
        gocardless_response = await supabase.table('gocardless_transactions').select('*').execute()
        
        logger.info(f"Retrieved {len(ntropy_response.data)} ntropy transactions")
        logger.info(f"Retrieved {len(gocardless_response.data)} gocardless transactions")
        
        # Convert to DataFrames
        ntropy_df = pd.DataFrame(ntropy_response.data)
        gocardless_df = pd.DataFrame(gocardless_response.data)
        
        # Merge DataFrames on the specified keys
        merged_df = pd.merge(
            gocardless_df,
            ntropy_df,
            how='left',
            left_on='id',
            right_on='ntropy_id'
        )
        
        # Create a new DataFrame with selected columns
        result_df = pd.DataFrame({
            'id': merged_df['id'],
            'entity_name': merged_df.apply(
                lambda row: row['creditor_name'] if pd.notnull(row['creditor_name'])
                else row['debtor_name'] if pd.notnull(row['debtor_name'])
                else row['enriched_data']['entities']['counterparty']['name'] if pd.notnull(row['enriched_data'])
                else None,
                axis=1
            ),
            'amount': merged_df['amount']/100,
            'remittance_info': merged_df['remittance_info'],
            'ntropy_enrich': merged_df['enriched_data'].notnull(),
            'ntropy_entity': merged_df['enriched_data'].apply(
                lambda x: x['entities']['counterparty']['name'] if pd.notnull(x) else None
            ),
            'ntropy_category': merged_df['enriched_data'].apply(
                lambda x: x['categories']['general'] if pd.notnull(x) else None
            )
        })
        
        logger.info(f"Final prepared DataFrame contains {len(result_df)} rows")
        logger.debug(f"DataFrame columns: {result_df.columns.tolist()}")
        
        return result_df
        
    except Exception as e:
        logger.error("Error in fetch_and_prepare_transactions", exc_info=True)
        raise

async def main():
    """Main async function to orchestrate the reconciliation process"""
    logger.info("Starting reconciliation process")
    
    try:
        # Load chart of accounts
        logger.info("Loading chart of accounts from coa.json")
        with open('coa.json', 'r') as file:
            data = json.load(file)
        
        # Extract only the required fields from each account
        parsed_accounts = [
            {
                'code': account.get('Code', ''),
                'name': account.get('Name', ''),
                'type': account.get('Type', ''),
                'description': account.get('Description', ''),
                'class': account.get('Class', ''),
            }
            for account in data['Accounts']
            if account.get('Status') == 'ACTIVE'
        ]
        logger.info(f"Loaded {len(parsed_accounts)} active accounts from CoA")
        
        # Fetch and prepare transactions
        logger.info("Fetching and preparing transactions")
        result_df = await fetch_and_prepare_transactions()
        logger.info(f"Retrieved {len(result_df)} transactions to process")
        
        # Process transactions
        logger.info("Starting transaction processing")
        df_reconciled = process_transactions(result_df, parsed_accounts)
        logger.info("Completed reconciliation process")
        
        return df_reconciled
        
    except Exception as e:
        logger.error("Error in main function", exc_info=True)
        raise

if __name__ == "__main__":
    import asyncio
    df_reconciled = asyncio.run(main())
    print(df_reconciled)