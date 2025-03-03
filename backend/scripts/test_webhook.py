#!/usr/bin/env python3
"""
Script to test the Nylas webhook endpoint directly.
"""

import requests
import json
import logging
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_webhook_challenge():
    """Test the webhook challenge (GET request)"""
    # Get the webhook URL from environment
    webhook_url = os.getenv("NYLAS_WEBHOOK_URL", "http://localhost:8001/api/nylas/webhook")
    
    print(f"\nTesting webhook challenge at: {webhook_url}")
    print(f"This will simulate Nylas sending a challenge to verify your webhook.")
    
    # Send a GET request with a challenge parameter
    try:
        response = requests.get(f"{webhook_url}?challenge=test_challenge", timeout=10)
        
        print(f"\nResponse status code: {response.status_code}")
        print(f"Response body: {response.text}")
        
        logger.info(f"Status code: {response.status_code}")
        logger.info(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("\n✅ Challenge test successful! Your webhook endpoint correctly responded to the challenge.")
        else:
            print(f"\n❌ Challenge test failed with status code {response.status_code}.")
            
        return response
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to webhook URL: {str(e)}")
        print(f"\n❌ Connection failed: {str(e)}")
        print("\nPlease check that:")
        print("1. Your FastAPI application is running")
        print("2. The webhook URL is correct")
        print("3. There are no network issues or firewalls blocking the connection")
        return None

def test_webhook_notification():
    """Test a webhook notification (POST request)"""
    # Get the webhook URL from environment
    webhook_url = os.getenv("NYLAS_WEBHOOK_URL", "http://localhost:8001/api/nylas/webhook")
    
    print(f"\nTesting webhook notification at: {webhook_url}")
    print(f"This will simulate Nylas sending a message.created event to your webhook.")
    
    # Create a mock webhook payload
    payload = {
        "type": "message.created",
        "grant_id": "test_grant_id",
        "message_id": "test_message_id",
        "thread_id": "test_thread_id",
        "object": {
            "id": "test_message_id",
            "subject": "Test Email with AI Assistant",
            "body": "This is a test email. Hey AI, can you help me with something?",
            "from": [{"name": "Test User", "email": "test@example.com"}],
            "to": [{"name": "AI Assistant", "email": "ai@example.com"}],
            "date": 1645556400,
            "unread": True
        },
        "date": 1645556400
    }
    
    print(f"Sending payload: {json.dumps(payload, indent=2)}")
    
    # Send a POST request with the payload
    headers = {
        "Content-Type": "application/json",
        "X-Nylas-Signature": "dummy_signature"  # This won't pass verification, but we've disabled it for testing
    }
    
    try:
        response = requests.post(webhook_url, headers=headers, json=payload, timeout=10)
        
        print(f"\nResponse status code: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Response body: {response.text}")
        
        logger.info(f"Status code: {response.status_code}")
        logger.info(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("\n✅ Notification test successful! Your webhook endpoint correctly processed the notification.")
            try:
                response_json = response.json()
                if response_json.get("status") == "processing":
                    print("The webhook is being processed in the background.")
            except:
                pass
        else:
            print(f"\n❌ Notification test failed with status code {response.status_code}.")
            
        return response
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to webhook URL: {str(e)}")
        print(f"\n❌ Connection failed: {str(e)}")
        print("\nPlease check that:")
        print("1. Your FastAPI application is running")
        print("2. The webhook URL is correct")
        print("3. There are no network issues or firewalls blocking the connection")
        return None

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test the Nylas webhook endpoint")
    parser.add_argument("test_type", choices=["challenge", "notification"], help="Type of test to run")
    parser.add_argument("--url", help="Override the webhook URL")
    
    args = parser.parse_args()
    
    if args.url:
        os.environ["WEBHOOK_TEST_URL"] = args.url
    
    if args.test_type == "challenge":
        test_webhook_challenge()
    elif args.test_type == "notification":
        test_webhook_notification()
