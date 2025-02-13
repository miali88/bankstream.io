import os 
import requests
from dotenv import load_dotenv
import random
import logging

from app.services.supabase import get_supabase

load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

''' STEP 1 - ACCESS TOKEN '''
# GoCardless OAuth endpoint for obtaining access tokens
AUTH_URL = 'https://bankaccountdata.gocardless.com/api/v2/token/new/'

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
async def build_link(institution_id: str, user_id: str = None) -> str:
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
            "max_historical_days": "730",
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
            "redirect": "http://localhost:3001/app",
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

        return requisition_result['link']  # Return just the link URL
    except Exception as e:
        logger.error(f"Failed to build link: {str(e)}")
        raise

async def store_requisition_data(requisition_data: dict):
    logger.info(f"Storing link data in Supabase for reference: {requisition_data.get('reference')}")
    supabase = await get_supabase()
    
    data = {
        'id': requisition_data['id'],
        'agreement': requisition_data['agreement'],
        'reference': requisition_data['reference'],
        'institution_id': requisition_data['institution_id'],
        'created': requisition_data['created'],
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
async def get_transactions(reference: str):
    logger.info(f"Starting transaction retrieval for reference: {reference}")
    try:
        access_token = await get_access_token()
        access_token = access_token['access']
        logger.debug("Successfully obtained access token for transactions")

        requisition_id = await get_requisition_id(reference)

        """ ONCE USER HAS BEEN REDIRECTED TO OUR SITE, WE CAN FETCH THEIR ACCOUNTS """
        url = f"https://bankaccountdata.gocardless.com/api/v2/requisitions/{requisition_id}"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        requisition_response = requests.get(url, headers=headers)
        requisition_response.raise_for_status()
        requisition_response = requisition_response.json()

        """ THEN LOOP THROUGH ACCOUNTS LIST AND GET TRANSACTIONS FOR EACH ACCOUNT """
        accounts = requisition_response['accounts']
        logger.info(f"Found {len(accounts)} accounts for requisition")

        for i, account in enumerate(accounts, 1):
            logger.debug(f"Fetching transactions for account {i} of {len(accounts)}")
            url = f"https://bankaccountdata.gocardless.com/api/v2/accounts/{account}/transactions/"
            accounts_transactions = requests.get(url, headers=headers)
            accounts_transactions.raise_for_status()
            accounts_transactions = accounts_transactions.json()
            transformed_transactions = transform_transactions(accounts_transactions['transactions']['booked'])
            await store_transactions(transformed_transactions)
            logger.debug(f"Successfully retrieved transactions for account {i}")
            
        logger.info("Completed transaction retrieval and storage")
    except Exception as e:
        logger.error(f"Error in get_transactions: {str(e)}")
        raise

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

def transform_transactions(transactions: list) -> list:
    logger.debug(f"Transforming {len(transactions)} transactions")
    try:
        for transaction in transactions:
            # Extract currency and amount from transactionAmount
            currency = transaction['transactionAmount']['currency']
            # Convert amount to integer (assuming amount is a string like "10.50")
            amount_str = transaction['transactionAmount']['amount']
            # Remove decimal point and convert to integer (e.g., "10.50" becomes 1050)
            amount = int(float(amount_str) * 100)
            
            # Add new fields
            transaction['currency'] = currency
            transaction['amount'] = amount
            
            # Remove original transactionAmount field
            del transaction['transactionAmount']
        
        logger.debug("Transaction transformation completed successfully")
        return transactions
    except Exception as e:
        logger.error(f"Error transforming transactions: {str(e)}")
        raise

async def store_transactions(transactions: dict):
    logger.info(f"Storing {len(transactions)} transactions in Supabase")
    supabase = await get_supabase()
    
    # Map the transaction fields to match database schema
    formatted_transactions = []
    for transaction in transactions:
        formatted_transaction = {
            'id': transaction.get('transactionId'),
            'user_id': "USER_ID_HERE",
            'creditor_name': transaction.get('creditorName'),
            'debtor_name': transaction.get('debtorName'),
            'amount': transaction.get('amount'),
            'currency': transaction.get('currency'),
            'remittance_info': transaction.get('remittanceInformationUnstructured'),
            'code': transaction.get('proprietaryBankTransactionCode'),
        }
        formatted_transactions.append(formatted_transaction)

    result = await supabase.table('gocardless_transactions').insert(formatted_transactions).execute()
    logger.info(f"Successfully stored {len(formatted_transactions)} transactions")
    return result