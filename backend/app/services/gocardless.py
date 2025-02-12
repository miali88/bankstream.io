import os 
import requests
from dotenv import load_dotenv
import random

load_dotenv()

''' STEP 1 - ACCESS TOKEN '''
# GoCardless OAuth endpoint for obtaining access tokens
AUTH_URL = 'https://bankaccountdata.gocardless.com/api/v2/token/new/'

async def get_access_token():
    print("\nget_access_token called")
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
    print("\n\n\naccess_token", access_token)
    return access_token

''' FETCH LIST OF BANKS '''
async def fetch_list_of_banks(country: str = "GB"):
    print("\nfetch_list_of_banks called")
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
        # Print detailed structure of the response
        print("\n=== Banks Data Structure ===")
        for bank in banks_data:
            print("\nBank Fields:")
            for key, value in bank.items():
                print(f"{key}: {value}")
        return banks_data
    else:
        print("Error:", response.text)
        response.raise_for_status()


async def build_link(institution_id: str):
    print("\nbuild_link called")
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
        "max_historical_days": "90",
        "access_valid_for_days": "30",
        "access_scope": ["balances", "details", "transactions"]
    }

    try:
        agreement_response = requests.post(url, json=data, headers=headers)
        agreement_response.raise_for_status()
        agreement_result = agreement_response.json()

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
        
        link_response = requests.post(requisition_url, headers=headers, json=requisition_data)
        link_response.raise_for_status()
        link_result = link_response.json()

        return link_result['link']  # Return just the link URL

        ## TODO: 
        # Store the link dict in your database, create table for link data
        
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        raise

async def get_accounts():
    print("\nget_accounts called")
    access_token = await get_access_token()
    access_token = access_token['access']

    url = "https://bankaccountdata.gocardless.com/api/v2/accounts/"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print("Error:", response.text)
        response.raise_for_status()
        