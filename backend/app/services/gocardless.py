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

async def get_access_token():
    logger.info("Starting access token retrieval")
    # Data to be sent in the POST request
    data = {
        "secret_id": os.getenv('GOCARDLESS_CLIENT_ID'),
        "secret_key": os.getenv('GOCARDLESS_CLIENT_SECRET')
    }

    # Making the POST request to obtain the access token
    response = requests.post(AUTH_URL, json=data)
    response.raise_for_status()  # Raise exception for non-200 responses

    # Parsing the JSON response
    access_token = response.json()
    logger.debug("Access token retrieved successfully")
    return access_token

''' FETCH LIST OF BANKS '''
async def fetch_list_of_banks(country: str = "GB"):
    logger.info(f"Fetching list of banks for country: {country}")
    access_token = await get_access_token()
    access_token = access_token['access']
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


async def store_link_data(link_data: dict):
    logger.info("Storing link data in Supabase")
    supabase = await get_supabase()
    
    data = {
        'id': link_data['id'],
        'agreement': link_data['agreement'],
        'reference': link_data['reference'],
        'institution_id': link_data['institution_id'],
        'created': link_data['created'],
        'user_id': link_data['user_id']
    }
    
    try:
        result = await supabase.table('gocardless').insert(data).execute()
        logger.info("Link data stored successfully")
        return result
    except Exception as e:
        logger.error(f"Failed to store link data: {str(e)}")
        raise

async def build_link(institution_id: str, user_id: str = None) -> str:
    logger.info(f"Building link for institution_id: {institution_id}")
    access_token = await get_access_token()
    access_token = access_token['access']

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


    try:
        logger.debug("Creating end user agreement")
        agreement_response = requests.post(url, json=data, headers=headers)

        agreement_response.raise_for_status()
        agreement_result = agreement_response.json()
        logger.debug("End user agreement created successfully")

        ''' STEP 4 - BUILD A LINK '''
        # Generate random reference ID
        random_id = ''.join(random.choices('0123456789', k=21))
        
        requisition_url = "https://bankaccountdata.gocardless.com/api/v2/requisitions/"
        requisition_data = {
            "redirect": "http://localhost:3001/app",
            "institution_id": institution_id,
            "reference": random_id,
            "agreement": agreement_result['id'],
            "user_language": "EN"
        }
        
        logger.debug("Creating requisition")
        link_response = requests.post(requisition_url, headers=headers, json=requisition_data)
        link_response.raise_for_status()
        link_result = link_response.json()
        logger.debug("Requisition created successfully")

        await store_link_data({
            'id': link_result['id'],
            'agreement': agreement_result['id'],
            'reference': random_id,
            'institution_id': institution_id,
            'created': link_result.get('created', None),
            'user_id': user_id
        })

        return link_result['link']  # Return just the link URL
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to build link: {str(e)}")
        raise

async def get_accounts():
    logger.info("Retrieving accounts")
    access_token = await get_access_token()
    access_token = access_token['access']

    url = "https://bankaccountdata.gocardless.com/api/v2/accounts/"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        logger.debug("Successfully retrieved accounts")
        return response.json()
    else:
        logger.error(f"Failed to get accounts: {response.text}")
        response.raise_for_status()
        