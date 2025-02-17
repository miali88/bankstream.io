# from xero_python.api_client import Configuration, ApiClient
# from xero_python.api_client.api_exception import ApiException
# from xero_python.api_client.api_token_auth import (
#     TokenType,  
#     Token,
# )

import json
import logging
from pydantic import BaseModel

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

