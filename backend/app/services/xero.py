# from xero_python.api_client import Configuration, ApiClient
# from xero_python.api_client.api_exception import ApiException
# from xero_python.api_client.api_token_auth import (
#     TokenType,  
#     Token,
# )

import json
import logging
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from app.services.vectorise_data import kb_item_to_chunks
from app.services.supabase import get_supabase

logger = logging.getLogger(__name__)

class XeroCoA(BaseModel):
    account_id: str
    code: str
    name: str
    status: str
    account_type: str
    tax_type: str
    description: str
    account_class: str
    system_account: str
    enable_payments_to_account: bool
    show_in_expense_claims: bool
    bank_account_type: str
    reporting_code: str
    has_attachments: bool
    updated_date_utc: str
    add_to_watchlist: bool

class CoAVectoriseContent(BaseModel):
    Name : str 
    Type : str
    Description : str
    Class : str
    
class CoATableDB(XeroCoA):
    id : str
    user_id : str

class XeroService:
    def __init__(self):
        pass

    def get_xero_api_client(self):
        return self.api_client
    

async def vectorise_coa(user_id: str):
    """ get from xero api later """
    logger.info(f"Starting vectorise_coa process for user_id: {user_id}")
    
    # coa_data = await get_coa_data(user_id)
    supabase = await get_supabase()
    logger.debug("Supabase client initialized")

    try:
        with open("CoA.json", "r") as f:
            coa_data = json.load(f)
        logger.info("Successfully loaded CoA.json file")
    except Exception as e:
        logger.error(f"Failed to load CoA.json: {str(e)}")
        raise

    accounts = coa_data.get("Accounts", [])
    logger.info(f"Processing {len(accounts)} accounts from CoA data")
    
    for idx, account in enumerate(accounts, 1):
        account_id = account.get("AccountID")
        logger.info(f"Processing account {idx}/{len(accounts)} - AccountID: {account_id}")
        
        try:
            # Prepare the data for Supabase
            account_data = {
                "account_id": account.get("AccountID"),
                "code": account.get("Code", ""),
                "name": account.get("Name", ""),
                "status": account.get("Status", ""),
                "account_type": account.get("Type", ""),
                "tax_type": account.get("TaxType", ""),
                "description": account.get("Description", ""),
                "account_class": account.get("Class", ""),
                "system_account": account.get("SystemAccount", ""),
                "enable_payments_to_account": account.get("EnablePaymentsToAccount", False),
                "show_in_expense_claims": account.get("ShowInExpenseClaims", False),
                "bank_account_type": account.get("BankAccountType", ""),
                "reporting_code": account.get("ReportingCode", ""),
                "has_attachments": account.get("HasAttachments", False),
                "updated_date_utc": account.get("UpdatedDateUTC", ""),
                "add_to_watchlist": account.get("AddToWatchlist", False),
                "user_id": user_id
            }
            
            logger.debug(f"Saving account {account_id} to Supabase chart_of_accounts table")
            # Save to Supabase
            data = await supabase.table("chart_of_accounts").insert(account_data).execute()

            # Now create the model with all fields including the generated id
            supabase_id = data.data[0]['id']
            account_data['id'] = supabase_id
            logger.info(f"Successfully saved account {account_id} to Supabase with ID: {supabase_id}")

            # Create structured content for vectorization
            content = CoAVectoriseContent(
                Name=account.get("Name", ""),
                Type=account.get("Type", ""),
                Description=account.get("Description", ""),
                Class=account.get("Class", "")
            )
            
            # Convert to dict for serialization
            content_dict = content.model_dump()
            # Combine all content fields with their names into a single string
            content_str = " ".join(f"# {key}: {value}" for key, value in content_dict.items() if value)
            
            print("content_str:", content_str)
            logger.debug(f"Vectorizing content for account {account_id}")
            await kb_item_to_chunks(
                data_id=supabase_id,  # Using Supabase-generated ID
                data_content=content_str, 
                user_id=user_id, 
                title="Xero CoA",
                is_tabular=False
            )
            logger.info(f"Successfully vectorized content for account {account_id}")

        except Exception as e:
            logger.error(f"Error processing account {account_id}: {str(e)}")
            raise

    logger.info(f"Successfully completed vectorise_coa process for user_id: {user_id}")
    return True

async def store_xero_credentials(user_id: str, token_data: Dict[Any, Any]) -> None:
    """Store Xero credentials in Supabase."""
    try:
        supabase = await get_supabase()
        
        # Calculate expires_at timestamp
        expires_in = token_data.get('expires_in', 1800)  # Default to 30 minutes if not provided
        expires_at = datetime.now(timezone.utc).timestamp() + expires_in
        
        # Extract tenant information
        tenant_id = token_data.get('tenant_id')
        if not tenant_id:
            raise ValueError("No tenant_id found in token data")
            
        # Prepare credentials for storage - only include fields that exist in the database
        credentials = {
            'user_id': user_id,
            'tenant_id': tenant_id,
            'access_token': token_data['access_token'],
            'refresh_token': token_data.get('refresh_token'),  # This is required per schema
            'token_type': token_data['token_type'],
            'expires_at': datetime.fromtimestamp(expires_at, tz=timezone.utc).isoformat()
        }
        
        # Validate required fields
        if not credentials['refresh_token']:
            raise ValueError("refresh_token is required but not present in token data")
        
        # Upsert the credentials
        result = await supabase.table('xero_credentials').upsert(
            credentials,
            on_conflict='user_id,tenant_id'
        ).execute()
        
        if hasattr(result, 'error') and result.error is not None:
            raise Exception(f"Failed to store credentials: {result.error}")
                
        logger.info(f"Successfully stored Xero credentials for user {user_id} and tenant {tenant_id}")
        
    except Exception as e:
        logger.error(f"Error storing Xero credentials: {str(e)}")
        raise

async def get_xero_credentials(user_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve Xero credentials from Supabase."""
    try:
        supabase = await get_supabase()
        
        result = supabase.table('xero_credentials').select('*').eq(
            'user_id', user_id
        ).eq(
            'tenant_id', tenant_id
        ).execute()
        
        if hasattr(result, 'error') and result.error is not None:
            raise Exception(f"Failed to retrieve credentials: {result.error}")
            
        data = result.data
        if not data:
            return None
            
        credentials = data[0]
        
        # Check if token is expired
        expires_at = datetime.fromisoformat(credentials['expires_at'])
        if expires_at <= datetime.now(timezone.utc):
            logger.info(f"Token expired for user {user_id}, tenant {tenant_id}")
            # TODO: Implement token refresh logic here
            return None
            
        return credentials
        
    except Exception as e:
        logger.error(f"Error retrieving Xero credentials: {str(e)}")
        raise

async def delete_xero_credentials(user_id: str, tenant_id: Optional[str] = None) -> None:
    """Delete Xero credentials from Supabase."""
    try:
        supabase = await get_supabase()
        
        query = supabase.table('xero_credentials').delete().eq('user_id', user_id)
        if tenant_id:
            query = query.eq('tenant_id', tenant_id)
            
        result = query.execute()
        
        if hasattr(result, 'error') and result.error is not None:
            raise Exception(f"Failed to delete credentials: {result.error}")
            
        logger.info(f"Successfully deleted Xero credentials for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error deleting Xero credentials: {str(e)}")
        raise

