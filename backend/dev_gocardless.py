import requests
from dotenv import load_dotenv
import os
load_dotenv()

GOCARDLESS_CLIENT_ID = os.getenv('GOCARDLESS_CLIENT_ID')
GOCARDLESS_CLIENT_SECRET = os.getenv('GOCARDLESS_CLIENT_SECRET')
if not GOCARDLESS_CLIENT_ID or not GOCARDLESS_CLIENT_SECRET:
    raise ValueError('GOCARDLESS_CLIENT_ID and GOCARDLESS_CLIENT_SECRET must be set')
else:
    print('GOCARDLESS_CLIENT_ID and GOCARDLESS_CLIENT_SECRET are set')


''' STEP 1 - ACCESS TOKEN '''
# GoCardless OAuth endpoint for obtaining access tokens
AUTH_URL = 'https://bankaccountdata.gocardless.com/api/v2/token/new/'


def get_access_token():
    # Data to be sent in the POST request
    data = {
        "secret_id": GOCARDLESS_CLIENT_ID,
        "secret_key": GOCARDLESS_CLIENT_SECRET
    }

    # Making the POST request to obtain the access token
    response = requests.post(AUTH_URL, json=data)
    response.raise_for_status()  # Raise exception for non-200 responses

    # Parsing the JSON response
    access_token = response.json()
    return access_token

access_token = get_access_token()['access']

''' END USER SELECTING A BANK '''
"https://github.com/nordigen/nordigen-bank-ui"

url = "https://bankaccountdata.gocardless.com/api/v2/institutions/"
params = {
    "country": "PT"
}
headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {access_token}"  # Replace ACCESS_TOKEN with your actual access token
}

list_of_banks = requests.get(url, headers=headers, params=params)

if list_of_banks.status_code == 200:
    list_of_banks = list_of_banks.json()
    print("Response:")
    print(list_of_banks)
else:
    print("Error:", list_of_banks.text)
    list_of_banks.raise_for_status()  # Raise exception for non-200 responses


def extract_schema(json_list):
    """
    Extract schema from a list of dictionaries, showing all possible keys and their data types
    
    Args:
        json_list (list): List of dictionaries
    
    Returns:
        dict: Schema showing keys and their possible data types
    """
    schema = {}
    
    # Handle single dictionary case
    if isinstance(json_list, dict):
        json_list = [json_list]
    
    for item in json_list:
        for key, value in item.items():
            # Get the type of the value
            value_type = type(value).__name__
            
            # If key exists, add new type if different
            if key in schema:
                if value_type not in schema[key]:
                    schema[key].append(value_type)
            else:
                schema[key] = [value_type]
    
    return schema

# Example usage with your list_of_banks data:
schema = extract_schema(list_of_banks)
for key, types in schema.items():
    print(f"{key}: {types}")
# bank_list_schema:
"""
id: ['str']
name: ['str']
bic: ['str']
transaction_total_days: ['str']
countries: ['list']
logo: ['str']
max_access_valid_for_days: ['str']
"""

''' STEP 3 - CREATE END USER AGREEMENT '''
# API endpoint
url = "https://bankaccountdata.gocardless.com/api/v2/agreements/enduser/"

# Headers
headers = {
    "Authorization": f"Bearer {access_token}"
}

INSTITUTION_ID = "NATWEST_NWBKGB2L"
# Data
data = {
    "institution_id": INSTITUTION_ID,
    "max_historical_days": "730",
    "access_valid_for_days": "30",
    "access_scope": ["balances", "details", "transactions"]
}

# Make POST request
try:
    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()  # Raise exception for non-200 responses
    result = response.json()
    print(result)
except requests.exceptions.RequestException as e:
    print(f"Error making POST request: {e}")


''' STEP 4 - BUILD A LINK '''
import random
def generate_random_id():
    return ''.join(random.choices('0123456789', k=21))
random_id = generate_random_id()

url = "https://bankaccountdata.gocardless.com/api/v2/requisitions/"
headers = {
    "accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": f"Bearer {access_token}"  # Replace ACCESS_TOKEN with your actual access token
}
data = {
    "redirect": "https://michaelalilondon.bubbleapps.io/version-test",
    "institution_id": result['institution_id'],
    "reference": random_id,
    "agreement": result['id'],
    "user_language": "EN"
}
response = requests.post(url, headers=headers, json=data)
response.json()

''' STEP 5 - LIST ACCOUNTS '''

url = f"https://bankaccountdata.gocardless.com/api/v2/requisitions/"

response = requests.get(url, headers=headers)
response.json()


requsitions = {
    "barclays": "881a82f5-9c82-4476-a88f-34921f0f5c9c",
    "natwest": "e1849ee0-6146-4cb8-8f16-a80c1eba6bca",
}

""" new account ids are issued with each new requisition """
natwest_accounts = [
    '81451d40-c0fb-4524-9ef0-7b36f7b2cc50']

barclays_accounts = [
    'd318a85e-58c1-4249-87a2-058bb817c070',
    'f9ee4378-ecc9-45c6-aedc-d982a7329072']

### accounts endpoint takes account id. 
url = f"https://bankaccountdata.gocardless.com/api/v2/accounts/{natwest_accounts[0]}/transactions/"

headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {access_token}"  # Replace ACCESS_TOKEN with your actual access token
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    print("Response:")
    print(response.json())
else:
    print("Error:", response.text)
