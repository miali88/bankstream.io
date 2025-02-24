import os 
import requests
from dotenv import load_dotenv
import random
import logging
import uuid  # Add UUID import
from datetime import datetime, timedelta

from app.core.supabase_client import get_supabase

load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

''' STEP 1 - ACCESS TOKEN '''
# GoCardless OAuth endpoint for obtaining access tokens
AUTH_URL = 'https://bankaccountdata.gocardless.com/api/v2/token/new/'
FRONTEND_URL = os.getenv('FRONTEND_URL')
BASE_API_URL = os.getenv('BASE_API_URL')

# In-memory cache for link data
link_data_cache = {}

async def get_access_token():
    logger.info("Starting access token retrieval")
    try:
        data = {
            "secret_id": os.getenv('GOCARDLESS_CLIENT_ID'),
            "secret_key": os.getenv('GOCARDLESS_CLIENT_SECRET')
        }
        response = requests.post(AUTH_URL, json=data)
        response.raise_for_status()
        access_token = response.json()
        logger.info("Access token retrieved successfully")
        return access_token
    except Exception as e:
        logger.error(f"Failed to retrieve access token: {str(e)}")
        raise

""" ADD BANK DATA CALL FLOW """
""" Step 1 """
async def fetch_list_of_banks(country: str = "GB"):
    logger.info(f"Fetching list of banks for country: {country}")
    try:
        access_token = await get_access_token()
        access_token = access_token['access']
        logger.debug("Making request to GoCardless institutions endpoint")
        url = "https://bankaccountdata.gocardless.com/api/v2/institutions/"
        params = {
            "country": country
        }
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {access_token}"
        }

        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            banks_data = response.json()
            logger.debug(f"Successfully retrieved {len(banks_data)} banks")
            return banks_data
        else:
            logger.error(f"Failed to fetch banks: {response.text}")
            response.raise_for_status()
    except Exception as e:
        logger.error(f"Error in fetch_list_of_banks: {str(e)}")
        raise

""" Step 2 """
async def build_link(institution_id: str, transaction_total_days: str,
                     user_id: str = None, medium: str = "online"
                     ) -> str:
    logger.info(f"Building link for institution_id: {institution_id}, user_id: {user_id}")
    try:
        access_token = await get_access_token()
        access_token = access_token['access']
        logger.debug("Successfully obtained access token for link building")

        ''' STEP 3 - CREATE END USER AGREEMENT '''
        # API endpoint
        url = "https://bankaccountdata.gocardless.com/api/v2/agreements/enduser/"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        data = {
            "institution_id": institution_id,  # Use the provided institution_id
            "max_historical_days": transaction_total_days,
            "access_valid_for_days": "30",
            "access_scope": ["balances", "details", "transactions"]
        }

        logger.debug("Creating end user agreement")
        agreement_response = requests.post(url, json=data, headers=headers)

        agreement_response.raise_for_status()
        agreement_result = agreement_response.json()
        logger.info(f"End user agreement created successfully with ID: {agreement_result['id']}")

        ''' STEP 4 - BUILD A LINK '''
        # Generate random reference ID
        random_id = ''.join(random.choices('0123456789', k=21))
        logger.debug(f"Generated reference ID: {random_id}")
        
        requisition_url = "https://bankaccountdata.gocardless.com/api/v2/requisitions/"
        requisition_data = {
            "redirect": f"{FRONTEND_URL}/gocardless/callback",
            "institution_id": institution_id,
            "reference": random_id,
            "agreement": agreement_result['id'],
            "user_language": "EN"
        }
        
        logger.debug("Creating requisition")
        requisition_response = requests.post(requisition_url, headers=headers, json=requisition_data)
        requisition_response.raise_for_status()
        requisition_result = requisition_response.json()
        logger.info(f"Link built successfully with requisition ID: {requisition_result['id']}")

        await store_requisition_data({
            'id': requisition_result['id'],
            'agreement': agreement_result['id'],
            'reference': random_id,
            'institution_id': institution_id,
            'created': requisition_result.get('created', None),
            'user_id': user_id
        })

        return requisition_result['link'], random_id 
    except Exception as e:
        logger.error(f"Failed to build link: {str(e)}")
        raise

async def store_requisition_data(requisition_data: dict):
    logger.info(f"Storing link data in Supabase for reference: {requisition_data.get('reference')}")
    supabase = await get_supabase()
    
    # First verify the user exists
    user_id = requisition_data.get('user_id')
    if user_id:
        user_result = await supabase.table('users').select('user_id').eq('user_id', user_id).execute()
        if not user_result.data:
            logger.error(f"User {user_id} not found in users table")
            raise ValueError(f"User {user_id} not found in users table. Please ensure user exists before creating agreement.")
    
    # Calculate expiration date (30 days from creation)
    created_date = datetime.fromisoformat(requisition_data['created'].replace('Z', '+00:00'))
    expiration_date = created_date + timedelta(days=30)
    
    data = {
        'id': requisition_data['id'],
        'agreement': requisition_data['agreement'],
        'reference': requisition_data['reference'],
        'institution_id': requisition_data['institution_id'],
        'created': requisition_data['created'],
        'expires_at': expiration_date.isoformat(),
        'user_id': requisition_data['user_id']
    }
    
    try:
        result = await supabase.table('gocardless_agreements').insert(data).execute()
        # Store in cache using reference as key
        link_data_cache[data['reference']] = data
        logger.info("Link data stored successfully in database and cache")
        return result
    except Exception as e:
        logger.error(f"Failed to store link data: {str(e)}")
        raise

""" Step 4 """
""" entry point for adding new bank link """
async def add_account(reference: str):
    logger.info(f"Starting account addition process for reference: {reference}")
    try:
        # Get necessary tokens and IDs
        access_token = await get_access_token()
        access_token = access_token['access']
        logger.debug("Successfully obtained access token")

        requisition_id = await get_requisition_id(reference)
        user_id = await get_user_id_from_reference(reference)

        # Fetch requisition details
        requisition_data = await get_requisition_data(requisition_id, access_token)
        
        # Get accounts and fetch their transactions
        accounts = requisition_data['accounts']
        logger.info(f"Found {len(accounts)} accounts for requisition")
        
        # Fetch and store account details for each account
        agreement_id = requisition_data.get('agreement')
        for account_id in accounts:
            account_details = await get_account_details(account_id, access_token)
            await store_account_details(account_details, user_id, agreement_id)
        
        transactions = await get_transactions(accounts, access_token)
        transformed_transactions = transform_transactions(transactions['transactions']['booked'])
        await store_transactions(transformed_transactions, user_id, agreement_id)
        
        logger.info("Successfully completed account addition and transaction retrieval")
        return transactions
    except Exception as e:
        logger.error(f"Error in add_account: {str(e)}")
        raise

async def get_account_details(account_id: str, access_token: str) -> dict:
    """Fetch details for a single account."""
    logger.info(f"Fetching details for account: {account_id}")
    try:
        url = f"https://bankaccountdata.gocardless.com/api/v2/accounts/{account_id}/"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        account_details = response.json()
        logger.info(f"Successfully retrieved details for account {account_id}")
        return account_details
    except Exception as e:
        logger.error(f"Error fetching account details: {str(e)}")
        raise

async def store_account_details(account_details: dict, user_id: str, agreement_id: str):
    """Store account details in the database. Updates if exists, inserts if new."""
    logger.info("Storing account details in Supabase")
    try:
        supabase = await get_supabase()
        
        # Get access token for logo fetch
        access_token = await get_access_token()
        access_token = access_token['access']
        
        # Get institution ID from account details
        institution_id = account_details.get('institution_id')
        
        # Fetch logo if we have an institution ID
        logo_url = None
        if institution_id:
            logo_url = await get_institution_logo(institution_id, access_token)
        
        account_data = {
            'id': account_details.get('id'),
            'user_id': user_id,
            'results': account_details,
            'agreement_id': agreement_id,
            'logo': logo_url  # Add the logo URL to the stored data
        }
        
        # Use upsert operation instead of insert
        result = await supabase.table('gocardless_accounts')\
            .upsert(account_data)\
            .execute()
            
        logger.info(f"Successfully stored/updated account details for account {account_details.get('id')}")
        return result
    except Exception as e:
        logger.error(f"Failed to store account details: {str(e)}")
        raise

async def get_institution_logo(institution_id: str, access_token: str) -> str:
    """Fetch the logo URL for a given institution."""
    logger.info(f"Fetching logo for institution: {institution_id}")
    try:
        url = f"https://bankaccountdata.gocardless.com/api/v2/institutions/{institution_id}"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        institution_data = response.json()
        logo_url = institution_data.get('logo')
        logger.info(f"Successfully retrieved logo for institution {institution_id}")
        return logo_url
    except Exception as e:
        logger.error(f"Error fetching institution logo: {str(e)}")
        return None

async def get_requisition_data(requisition_id: str, access_token: str) -> dict:
    """Fetch requisition details from GoCardless API."""
    logger.info(f"Fetching requisition data for requisition ID: {requisition_id}")
    try:
        url = f"https://bankaccountdata.gocardless.com/api/v2/requisitions/{requisition_id}"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        requisition_response = requests.get(url, headers=headers)
        requisition_response.raise_for_status()
        requisition_data = requisition_response.json()
        logger.info(f"Successfully retrieved requisition data with {len(requisition_data.get('accounts', []))} accounts")
        return requisition_data
    except Exception as e:
        logger.error(f"Error fetching requisition data: {str(e)}")
        raise
    
# TODO: need to ensure the bank date request is only from the last fetched date. 
# TODO: Need to add a last fetched date column to the gocardless_accounts table
async def get_transactions(accounts: str | list, access_token: str) -> dict:
    """Fetch transactions for one or multiple accounts.
    
    Args:
        accounts: Either a single account ID (str) or a list of account IDs
        access_token: The GoCardless access token
    
    Returns:
        dict: Aggregated transactions in the format {'transactions': {'booked': [...]}}
    """
    # Convert single account to list for consistent processing
    if isinstance(accounts, str):
        accounts = [accounts]
    
    logger.info(f"Starting transaction retrieval for {len(accounts)} account(s)")
    try:
        all_transactions = {
            'transactions': {
                'booked': []
            }
        }
        
        for i, account in enumerate(accounts, 1):
            logger.info(f"Fetching transactions for account {i} of {len(accounts)}")
            logger.info(f"Account: {account}")
            url = f"https://bankaccountdata.gocardless.com/api/v2/accounts/{account}/transactions/"

            headers = {
                "accept": "application/json",
                "Authorization": f"Bearer {access_token}"
            }
            accounts_transactions = requests.get(url, headers=headers)
            accounts_transactions.raise_for_status()
            accounts_transactions: dict = accounts_transactions.json()
            
            # Aggregate transactions from this account
            if 'transactions' in accounts_transactions and 'booked' in accounts_transactions['transactions']:
                all_transactions['transactions']['booked'].extend(accounts_transactions['transactions']['booked'])
            
        logger.info(f"Retrieved a total of {len(all_transactions['transactions']['booked'])} transactions")
        return all_transactions
    except Exception as e:
        logger.error(f"Error fetching transactions: {str(e)}")
        raise

def transform_transactions(transactions: list) -> list:
    logger.debug(f"Transforming {len(transactions)} transactions")
    try:
        transformed = []
        for transaction in transactions:
            # Log the transaction structure for debugging
            logger.debug(f"Transaction structure: {transaction}")
            
            # Handle different possible transaction amount structures
            amount = 0
            currency = 'GBP'  # default currency
            
            # Get both transaction IDs
            gc_transaction_id = transaction.get('transactionId')
            internal_transaction_id = transaction.get('internalTransactionId')
            
            if 'transactionAmount' in transaction:
                amount_data = transaction['transactionAmount']
                currency = amount_data.get('currency', 'GBP')
                amount_str = amount_data.get('amount', '0')
            else:
                # Handle alternative structure where amount might be directly in transaction
                amount_str = transaction.get('amount', '0')
                currency = transaction.get('currency', 'GBP')
            
            # Convert amount to integer (cents)
            try:
                amount = int(float(amount_str) * 100)
            except (ValueError, TypeError):
                logger.warning(f"Could not convert amount '{amount_str}' to integer")
                amount = 0
            
            # Create transformed transaction with concatenated UUIDs as primary key and both transaction IDs
            transformed_transaction = {
                'id': f"{str(uuid.uuid4())}-{str(uuid.uuid4())}",  # Generate concatenated UUIDs as primary key
                'transaction_id': gc_transaction_id,  # GoCardless transaction ID
                'internal_transaction_id': internal_transaction_id,  # Internal transaction ID
                'currency': currency,
                'amount': amount,
                'creditorName': transaction.get('creditorName'),
                'debtorName': transaction.get('debtorName'),
                'remittanceInformationUnstructured': transaction.get('remittanceInformationUnstructured'),
                'proprietaryBankTransactionCode': transaction.get('proprietaryBankTransactionCode')
            }
            
            transformed.append(transformed_transaction)
        
        logger.debug("Transaction transformation completed successfully")
        return transformed
    except Exception as e:
        logger.error(f"Error transforming transactions: {str(e)}")
        raise

async def store_transactions(transactions: dict, user_id: str, agreement_id: str):
    logger.info(f"Storing {len(transactions)} transactions in Supabase")
    
    # Don't proceed if there are no transactions to store
    if not transactions:
        logger.info("No transactions to store, skipping database insert")
        return None
        
    supabase = await get_supabase()
    
    # Map the transaction fields to match database schema
    formatted_transactions = []
    for transaction in transactions:
        entity_name = transaction.get("creditorName") if transaction.get("amount") < 0 else transaction.get("debtorName")
        formatted_transaction = {
            'id': transaction['id'],  # UUID primary key
            'booking_date': transaction.get('bookingDate'),
            'transaction_id': transaction.get('transaction_id'),
            'internal_transaction_id': transaction.get('internal_transaction_id'),
            'user_id': user_id,
            'entity_name': entity_name,
            'amount': transaction.get('amount'),
            'currency': transaction.get('currency'),
            'remittance_info': transaction.get('remittanceInformationUnstructured'),
            'code': transaction.get('proprietaryBankTransactionCode'),
            'iban': transaction.get('iban'),
            'institution_id': transaction.get('institution_id'),
            'agreement_id': agreement_id
        }
        formatted_transactions.append(formatted_transaction)

    try:
        result = await supabase.table('gocardless_transactions').insert(formatted_transactions).execute()
        logger.info(f"Successfully stored {len(formatted_transactions)} transactions")
        return result
    except Exception as e:
        logger.error(f"Failed to store transactions: {str(e)}")
        raise

async def get_user_id_from_reference(reference: str) -> str:
    logger.info(f"Fetching user ID for reference: {reference}")
    
    if reference in link_data_cache and link_data_cache[reference].get('user_id'):
        logger.debug("Found user ID in cache")
        return link_data_cache[reference]['user_id']
    
    logger.debug("User ID not in cache, querying database")
    supabase = await get_supabase()
    result = await supabase.table('gocardless_agreements').select('user_id').eq('reference', reference).execute()
    
    if result.data and len(result.data) > 0 and result.data[0]['user_id']:
        user_id = result.data[0]['user_id']
        logger.debug(f"Found user ID in database: {user_id}")
        return user_id
    
    logger.error(f"No user ID found for reference: {reference}")
    raise ValueError(f"No user ID found for reference: {reference}")

async def get_requisition_id(reference: str) -> str:
    logger.info(f"Looking up requisition ID for reference: {reference}")
    
    if reference in link_data_cache:
        logger.debug("Found requisition ID in cache")
        return link_data_cache[reference]['id']
    
    logger.debug("Requisition ID not in cache, querying database")
    supabase = await get_supabase()
    result = await supabase.table('gocardless_agreements').select('id').eq('reference', reference).execute()
    
    if result.data and len(result.data) > 0:
        requisition_id = result.data[0]['id']
        # Store in cache for future use
        link_data_cache[reference] = result.data[0]
        logger.debug("Found requisition ID in database")
        return requisition_id
    
    logger.error(f"No requisition found for reference: {reference}")
    raise ValueError(f"No requisition found for reference: {reference}")


