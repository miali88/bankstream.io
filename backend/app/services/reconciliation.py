""" LLM inference for reconciliation"""

from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
import time
from typing import Dict, Tuple, List
import logging
import json


from pydantic import BaseModel
import pandas as pd


from backend.app.services.etl.supabase import get_supabase

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

class TransactionToLLM(BaseModel):
    id: str
    entity_name : str
    amount : float
    remittance_info : str
    ntropy_enrich : bool
    ntropy_entity : str
    ntropy_category : str

class CoAToLLM(BaseModel):
    code: str
    name: str
    account_type: str
    description: str
    account_class: str

class TransactionClassifier:
    def __init__(self):
        logger.info("Initializing TransactionClassifier")
        self.system_prompt = """
            <coa_categorization_prompt>
            <instructions>
                <step>Identify the entity name from the transaction and infer what type of business it is.</step>
                <step>Determine the purpose of the transaction based on the entity and description.</step>
                <step>Assign a Chart of Accounts category based on UK GAAP standards.</step>
            </instructions>
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
            </coa_categorization_prompt>
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
          <context>
            <task>Analyze business transactions to assign appropriate Chart of Accounts code. Do so under UK GAAP</task>
            <business_info>
                <company_name>{{company_name}}</company_name>
                <description>{{company_description}}</description>
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
            </business_info>
            </context>

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
    
    # stop_counter = 0
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

        # stop_counter += 1
        # if stop_counter > 4:
        #     break
    logger.info("Finished processing all transaction groups")
    logger.debug(f"Final DataFrame shape: {df.shape}")
    return df

async def fetch_and_prepare_transactions(user_id: str) -> pd.DataFrame:
    """
    Fetch transactions from Supabase and prepare DataFrame for a specific user
    
    Args:
        user_id (str): The ID of the user whose transactions to fetch
    
    Returns:
        pd.DataFrame: Prepared DataFrame with merged transaction data
    """
    logger.info(f"Starting to fetch transactions from Supabase for user {user_id}")
    
    try:
        # Get Supabase client
        supabase = await get_supabase()
        logger.info("Successfully connected to Supabase")
        
        # Query both tables asynchronously with user_id filter
        logger.info("Querying Supabase tables...")
        ntropy_response = await supabase.table('ntropy_transactions').select('*').execute()
        gocardless_response = await supabase.table('gocardless_transactions')\
            .select('*')\
            .eq('user_id', user_id)\
            .or_('coa_set_by.is.null, coa_set_by.neq.AI')\
            .execute()
        
        logger.info(f"Retrieved {len(ntropy_response.data)} ntropy transactions")
        logger.info(f"Retrieved {len(gocardless_response.data)} gocardless transactions")

        # Handle empty gocardless transactions case
        if not gocardless_response.data:
            logger.info("No gocardless transactions to process")
            return pd.DataFrame()  # Return empty DataFrame
        
        # Convert to DataFrames
        ntropy_df = pd.DataFrame(ntropy_response.data)
        gocardless_df = pd.DataFrame(gocardless_response.data)

        # Create base result DataFrame from gocardless data
        result_df = pd.DataFrame({
            'id': gocardless_df['id'],
            'entity_name': gocardless_df.apply(
                lambda row: row['creditor_name'] if pd.notnull(row['creditor_name'])
                else row['debtor_name'],
                axis=1
            ),
            'amount': gocardless_df['amount']/100,
            'remittance_info': gocardless_df['remittance_info'],
            'ntropy_enrich': False,  # Default to False
            'ntropy_entity': None,
            'ntropy_category': None
        })

        # Only attempt merge if ntropy data exists
        if not ntropy_df.empty:
            try:
                # Ensure ntropy_id column exists
                if 'ntropy_id' not in ntropy_df.columns:
                    logger.warning("ntropy_id column missing in ntropy transactions")
                    return result_df

                # Merge with ntropy data where available
                ntropy_enriched = pd.merge(
                    result_df,
                    ntropy_df,
                    how='left',
                    left_on='id',
                    right_on='ntropy_id'
                )

                # Update enrichment fields where ntropy data exists
                mask = ntropy_enriched['enriched_data'].notna()
                result_df.loc[mask, 'ntropy_enrich'] = True
                result_df.loc[mask, 'ntropy_entity'] = ntropy_enriched.loc[mask, 'enriched_data'].apply(
                    lambda x: x['entities']['counterparty']['name'] if x and 'entities' in x else None
                )
                result_df.loc[mask, 'ntropy_category'] = ntropy_enriched.loc[mask, 'enriched_data'].apply(
                    lambda x: x['categories']['general'] if x and 'categories' in x else None
                )

            except Exception as e:
                logger.error(f"Error merging with ntropy data: {e}")
                # Continue with base gocardless data
                pass

        logger.info(f"Final prepared DataFrame contains {len(result_df)} rows")
        logger.debug(f"DataFrame columns: {result_df.columns.tolist()}")
        
        return result_df
        
    except Exception as e:
        logger.error("Error in fetch_and_prepare_transactions", exc_info=True)
        raise

async def fetch_chart_of_accounts(supabase) -> list:
    """
    Fetch chart of accounts from Supabase
    
    Returns:
        list: List of active accounts with relevant fields
    """
    logger.info("Fetching chart of accounts from Supabase")
    try:
        response = await supabase.table('chart_of_accounts').select('*').eq('status', 'ACTIVE').execute()
        accounts = response.data
        
        # Extract only the required fields and format for LLM
        parsed_accounts = [
            {
                'code': account['code'],
                'name': account['name'],
                'type': account['account_type'],
                'description': account.get('description', ''),
                'class': account.get('account_class', ''),
            }
            for account in accounts
        ]
        
        # Create a mapping of code to accountId for later use
        code_to_id_map = {
            account['code']: account['account_id'] 
            for account in accounts
        }
        
        logger.info(f"Loaded {len(parsed_accounts)} active accounts from Supabase")
        return parsed_accounts, code_to_id_map
        
    except Exception as e:
        logger.error("Error fetching chart of accounts", exc_info=True)
        raise

def map_coa_codes_to_ids(df: pd.DataFrame, code_to_id_map: dict) -> pd.DataFrame:
    """
    Map the COA codes to their corresponding account IDs
    
    Args:
        df (pd.DataFrame): DataFrame with coa_agent column containing codes
        code_to_id_map (dict): Mapping of codes to account IDs
    
    Returns:
        pd.DataFrame: DataFrame with new account_id column
    """
    df = df.copy()
    df['account_id'] = df['coa_agent'].map(code_to_id_map)
    return df

""" entry point """
async def reconcile_transactions(user_id: str) -> pd.DataFrame:
    """
    Main function to reconcile transactions for a specific user and save results to database
    """
    logger.info(f"Starting reconciliation process for user {user_id}")
    
    try:
        # Get Supabase client
        supabase = await get_supabase()
        
        # Fetch and prepare transactions first
        logger.info("Fetching and preparing transactions")
        result_df = await fetch_and_prepare_transactions(user_id)
        
        # Early return if no transactions to process
        if result_df.empty:
            logger.info("No transactions to reconcile")
            return result_df
            
        # Fetch chart of accounts only if we have transactions
        parsed_accounts, code_to_id_map = await fetch_chart_of_accounts(supabase)
        
        logger.info(f"Retrieved {len(result_df)} transactions to process")
        
        # Process transactions (LLM only sees codes, not UUIDs)
        logger.info("Starting transaction processing")
        df_reconciled = process_transactions(result_df, parsed_accounts)
        
        # Map the COA codes to account IDs
        logger.info("Mapping COA codes to account IDs")
        df_reconciled = map_coa_codes_to_ids(df_reconciled, code_to_id_map)
        
        # Save reconciliation results to database
        logger.info("Saving reconciliation results to database")
        updates = []
        for _, row in df_reconciled.iterrows():
            # Ensure all values are valid before updating
            if pd.isna(row['account_id']) or pd.isna(row['coa_reason']) or pd.isna(row['coa_confidence']):
                # logger.warning(f"Skipping update for transaction {row['id']} due to missing values")
                updates.append(False)
                continue

            update_data = {
                'chart_of_accounts': str(row['account_id']),  # Ensure UUID is string
                'coa_reason': str(row['coa_reason']),        # Ensure string
                'coa_confidence': float(row['coa_confidence']), # Ensure float
                'coa_set_by': 'AI'
            }
            
            try:
                # Log the update data for debugging
                logger.debug(f"Updating transaction {row['id']} with data: {update_data}")
                
                response = await supabase.table('gocardless_transactions')\
                    .update(update_data)\
                    .eq('id', row['id'])\
                    .execute()
                
                # Check if update was successful
                if response.data:
                    updates.append(True)
                else:
                    logger.error(f"No data returned for transaction {row['id']}")
                    updates.append(False)
                    
            except Exception as e:
                logger.error(f"Error updating transaction {row['id']}: {str(e)}")
                logger.error(f"Update data was: {update_data}")
                updates.append(False)

        logger.info(f"Successfully updated {sum(updates)} out of {len(updates)} transactions")
        
        return df_reconciled
        
    except Exception as e:
        logger.error("Error in reconcile_transactions function", exc_info=True)
        raise


# Remove the main function and replace with new entry point
if __name__ == "__main__":
    import asyncio
    
    # Example usage
    async def example():
        user_id = "user_2szfxuKAsHFmNfGtZtfnu3Pjdi7"  # Replace with actual user ID
        df_reconciled = await reconcile_transactions(user_id)
        print(df_reconciled)
    
    asyncio.run(example())