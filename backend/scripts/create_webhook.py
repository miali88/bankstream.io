#!/usr/bin/env python3
"""
Script to create a Nylas webhook for monitoring new emails.
This script can be used to test webhook creation outside of the FastAPI application.
"""

from dotenv import load_dotenv
load_dotenv()

import os
import sys
import json
from nylas import Client
from nylas.models.webhooks import WebhookTriggers
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_webhook():
    """Create a webhook using the Nylas SDK"""
    # Check for required environment variables
    required_vars = ["NYLAS_API_KEY", "NYLAS_API_URI", "NYLAS_WEBHOOK_URL", "NOTIFICATION_EMAIL"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)
    
    # Initialize Nylas client
    nylas = Client(
        api_key=os.environ.get('NYLAS_API_KEY'),
        api_uri=os.environ.get('NYLAS_API_URI')
    )
    
    webhook_url = os.environ.get("NYLAS_WEBHOOK_URL")
    email = os.environ.get("NOTIFICATION_EMAIL")
    
    try:
        # Create the webhook
        response = nylas.webhooks.create(
            request_body={
                "trigger_types": [WebhookTriggers.MESSAGE_CREATED],
                "webhook_url": webhook_url,
                "description": "Email monitoring webhook",
                "notification_email_address": email,
            }
        )
        
        # Print the full response for debugging
        logger.info("Full response from Nylas API:")
        logger.info(f"{response}")
        
        # Check if response is a dictionary or has a data attribute
        if hasattr(response, 'data'):
            webhook_data = response.data
        elif hasattr(response, 'to_dict'):
            webhook_data = response.to_dict()
        else:
            webhook_data = response
            
        # Extract the webhook ID
        webhook_id = None
        if isinstance(webhook_data, dict) and 'id' in webhook_data:
            webhook_id = webhook_data['id']
        elif hasattr(webhook_data, 'id'):
            webhook_id = webhook_data.id
            
        if webhook_id:
            logger.info(f"Successfully created webhook with ID: {webhook_id}")
        else:
            logger.warning("Webhook created but could not extract ID from response")
            
        logger.info(f"Webhook details: {webhook_data}")
        
        return webhook_data
        
    except Exception as e:
        logger.error(f"Error creating webhook: {str(e)}")
        # Print more detailed error information
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

def list_webhooks():
    """List all webhooks"""
    nylas = Client(
        api_key=os.environ.get('NYLAS_API_KEY'),
        api_uri=os.environ.get('NYLAS_API_URI')
    )
    
    try:
        response = nylas.webhooks.list()
        
        # Print the full response for debugging
        logger.info("Full response from Nylas API:")
        logger.info(f"{response}")
        
        # Extract webhooks from response
        webhooks = []
        if hasattr(response, 'data'):
            webhooks = response.data
        elif isinstance(response, list):
            webhooks = response
        
        logger.info(f"Found {len(webhooks)} webhooks:")
        
        for webhook in webhooks:
            # Extract webhook details
            webhook_id = getattr(webhook, 'id', None) if hasattr(webhook, 'id') else webhook.get('id', 'Unknown')
            webhook_url = getattr(webhook, 'webhook_url', None) if hasattr(webhook, 'webhook_url') else webhook.get('webhook_url', 'Unknown')
            status = getattr(webhook, 'status', None) if hasattr(webhook, 'status') else webhook.get('status', 'Unknown')
            
            logger.info(f"ID: {webhook_id}, URL: {webhook_url}, Status: {status}")
            
        return webhooks
        
    except Exception as e:
        logger.error(f"Error listing webhooks: {str(e)}")
        # Print more detailed error information
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

def delete_webhook(webhook_id):
    """Delete a webhook by ID"""
    nylas = Client(
        api_key=os.environ.get('NYLAS_API_KEY'),
        api_uri=os.environ.get('NYLAS_API_URI')
    )
    
    try:
        response = nylas.webhooks.destroy(webhook_id)
        logger.info(f"Successfully deleted webhook with ID: {webhook_id}")
        logger.info(f"Response: {response}")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting webhook: {str(e)}")
        # Print more detailed error information
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

def test_with_mock_payload():
    """Test with a mock webhook payload"""
    nylas = Client(
        api_key=os.environ.get('NYLAS_API_KEY'),
        api_uri=os.environ.get('NYLAS_API_URI')
    )
    
    try:
        # Get a mock webhook payload for message.created
        mock_payload = nylas.webhooks.get_mock_payload(WebhookTriggers.MESSAGE_CREATED)
        
        logger.info("Mock webhook payload for MESSAGE_CREATED:")
        logger.info(json.dumps(mock_payload, indent=2))
        
        # You can use this payload to test your webhook handler
        return mock_payload
        
    except Exception as e:
        logger.error(f"Error getting mock payload: {str(e)}")
        # Print more detailed error information
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage Nylas webhooks")
    parser.add_argument("action", choices=["create", "list", "delete", "mock"], help="Action to perform")
    parser.add_argument("--webhook-id", help="Webhook ID for delete action")
    
    args = parser.parse_args()
    
    if args.action == "create":
        create_webhook()
    elif args.action == "list":
        list_webhooks()
    elif args.action == "delete":
        if not args.webhook_id:
            logger.error("Webhook ID is required for delete action")
            sys.exit(1)
        delete_webhook(args.webhook_id)
    elif args.action == "mock":
        test_with_mock_payload() 