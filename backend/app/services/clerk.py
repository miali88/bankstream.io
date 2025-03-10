from datetime import datetime
import requests, os, logging
from dotenv import load_dotenv
from fastapi import HTTPException

from app.core.supabase_client import get_supabase

load_dotenv()

# Set your Stripe secret key
# stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

logger = logging.getLogger(__name__)

async def post_user(payload):
    logger.info("Starting post_user function with new user payload")
    user_data = payload.get('data', {})
    logger.debug(f"Extracted user_data from payload: {user_data}")
    
    # Extract all required fields
    email_addresses = user_data.get('email_addresses', [])
    primary_email_address_id = user_data.get('primary_email_address_id')
    clerk_user_id = user_data.get('id')  # Get Clerk user ID
    
    logger.info(f"Processing user with Clerk ID: {clerk_user_id}")
    logger.debug(f"Found {len(email_addresses)} email addresses for user")
    
    try:
        logger.info("Initializing Supabase connection")
        supabase = await get_supabase()
        
        # Find the primary email address
        primary_email = next((email['email_address'] for email in email_addresses if email['id'] == primary_email_address_id), None)
        logger.info(f"Primary email identified: {primary_email}")
        
        # Get user's full name from Clerk data
        first_name = user_data.get('first_name', '')
        last_name = user_data.get('last_name', '')
        full_name = f"{first_name} {last_name}".strip() or None

        # try:
        #     # Create Stripe customer
        #     stripe_customer = stripe.Customer.create(
        #         email=primary_email,
        #         name=full_name,
        #         metadata={
        #             'signup_date': datetime.now().isoformat()
        #         }
        #     )
        #     logger.info(f"Stripe customer created successfully: {stripe_customer.id}")
            
        #     # Update Clerk user metadata with Stripe customer ID
        #     clerk_api_key = os.getenv('CLERK_SECRET_KEY')
        #     clerk_api_url = f"https://api.clerk.com/v1/users/{clerk_user_id}/metadata"
            
        #     headers = {
        #         "Authorization": f"Bearer {clerk_api_key}",
        #         "Content-Type": "application/json"
        #     }
                
        #     metadata_payload = {
        #         "private_metadata": {
        #             "stripe_customer_id": stripe_customer.id
        #         }
        #     }
            
        #     response = requests.patch(clerk_api_url, json=metadata_payload, headers=headers)
            
        #     if not response.ok:
        #         logger.error(f"Failed to update Clerk metadata: {response.text}")
        #         raise HTTPException(status_code=500, detail="Failed to update Clerk metadata")
                
        #     logger.info("Successfully updated Clerk metadata with Stripe customer ID")
            
        # except stripe.error.StripeError as e:
        #     logger.error(f"Error creating Stripe customer: {str(e)}")
        #     raise HTTPException(status_code=500, detail=f"Failed to create Stripe customer: {str(e)}")

        # Generate a default username from email
        default_username = primary_email.split('@')[0] if primary_email else None
        logger.debug(f"Generated default username: {default_username}")
        
        # Convert timestamps from milliseconds to ISO format
        logger.info("Converting timestamp fields")
        created_at = datetime.fromtimestamp(user_data.get('created_at') / 1000).isoformat() if user_data.get('created_at') else None
        updated_at = datetime.fromtimestamp(user_data.get('updated_at') / 1000).isoformat() if user_data.get('updated_at') else None
        last_login = datetime.fromtimestamp(user_data.get('last_sign_in_at') / 1000).isoformat() if user_data.get('last_sign_in_at') else None
        logger.debug(f"Timestamp conversions - Created: {created_at}, Updated: {updated_at}, Last Login: {last_login}")

        # Prepare user data matching the table schema
        user_record = {
            'user_id': user_data.get('id'),
            'email': primary_email,
            'user_plan': 'free',
        }
        logger.info("Prepared user record for database insertion")
        logger.debug(f"User record data: {user_record}")

        logger.info("Attempting to insert user record into database")
        data, count = await supabase.table('users').insert(user_record).execute()
        
        logger.info(f"User data saved successfully. Affected rows: {count}")
        logger.debug(f"Database response data: {data}")
        return data
    except Exception as e:
        logger.error(f"Error saving user data to database: {str(e)}", exc_info=True)
        logger.error(f"Failed operation details - User ID: {clerk_user_id}, Email: {primary_email if 'primary_email' in locals() else 'unknown'}")
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")
