from typing import Dict, Optional, List
import logging
from datetime import datetime
from fastapi import HTTPException

# Configure logging
logger = logging.getLogger(__name__)

async def store_nylas_credentials(supabase, user_id: str, grant_id: str):
    """Store Nylas credentials in Supabase"""
    try:
        data = {
            'user_id': user_id,
            'grant_id': grant_id,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        result = await supabase.table('nylas_credentials').upsert(data).execute()
        logger.info(f"Stored Nylas credentials for user {user_id}")
        return result.data
    except Exception as e:
        logger.error(f"Error storing Nylas credentials: {str(e)}")
        raise

async def get_nylas_credentials(supabase, user_id: str) -> Optional[str]:
    """Retrieve Nylas grant_id for a user"""
    try:
        result = await supabase.table('nylas_credentials') \
            .select('grant_id') \
            .eq('user_id', user_id) \
            .single() \
            .execute()
        
        return result.data['grant_id'] if result.data else None
    except Exception as e:
        logger.error(f"Error retrieving Nylas credentials: {str(e)}")
        return None

class EmailAssistant:
    def __init__(self, nylas_client, supabase, openai_client):
        self.nylas = nylas_client
        self.supabase = supabase
        self.ai = openai_client
        
    async def process_incoming_email(self, webhook_data: Dict):
        """Process incoming email webhook data"""
        try:
            # Log the webhook data
            logger.info(f"Processing webhook data: {webhook_data}")
            
            # Extract webhook type
            webhook_type = webhook_data.get('type', 'unknown')
            logger.info(f"Webhook type: {webhook_type}")
            
            # Check if this is a test payload
            is_test = webhook_data.get('grant_id') == 'test_grant_id'
            if is_test:
                logger.info("Detected test payload, skipping actual processing")
                return {"status": "success", "message": "Test payload received and validated"}
            
            # Handle different webhook types
            if webhook_type == 'message.created':
                await self._process_message_created(webhook_data)
            elif webhook_type == 'message.updated':
                await self._process_message_updated(webhook_data)
            elif webhook_type == 'message.opened':
                logger.info(f"Message opened event received: {webhook_data.get('message_id')}")
            else:
                logger.info(f"Unhandled webhook type: {webhook_type}")
                
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
            
    async def _process_message_created(self, webhook_data: Dict):
        """Process a message.created webhook"""
        try:
            # Extract relevant information
            thread_id = webhook_data.get('thread_id')
            message_id = webhook_data.get('message_id')
            grant_id = webhook_data.get('grant_id')
            
            if not all([thread_id, message_id, grant_id]):
                logger.error(f"Missing required fields in webhook data: {webhook_data}")
                return
                
            logger.info(f"Processing new message: {message_id} from thread: {thread_id}")
            
            # Fetch the message content
            message = await self.nylas.messages.get(grant_id, message_id)
            
            # Check if this is an AI trigger
            if not self._is_ai_trigger(message):
                logger.debug(f"Message {message_id} is not an AI trigger")
                return
                
            # Get thread context
            thread_messages = await self.nylas.threads.get(grant_id, thread_id)
            context = await self._get_conversation_context(thread_id)
            
            # Generate AI response
            response = await self._generate_response(message, thread_messages, context)
            
            # Send the response
            await self._send_response(grant_id, thread_id, response)
            
            # Update context
            await self._update_conversation_context(thread_id, message, response)
            
            logger.info(f"Successfully processed new message {message_id}")
            
        except Exception as e:
            logger.error(f"Error processing message.created: {str(e)}")
            raise
            
    async def _process_message_updated(self, webhook_data: Dict):
        """Process a message.updated webhook"""
        # Similar to _process_message_created but for updates
        logger.info(f"Message updated: {webhook_data.get('message_id')}")
        # Implement specific logic for message updates if needed
    
    def _is_ai_trigger(self, message: Dict) -> bool:
        """Check if message contains AI trigger phrase"""
        trigger_phrases = ["Hey AI", "AI Assistant", "@AI"]
        subject = message.get('subject', '').lower()
        body = message.get('body', '').lower()
        
        return any(phrase.lower() in subject or phrase.lower() in body 
                  for phrase in trigger_phrases)
    
    async def _get_conversation_context(self, thread_id: str) -> Dict:
        """Retrieve conversation context from Supabase"""
        try:
            result = await self.supabase.table('email_conversations') \
                .select('context') \
                .eq('thread_id', thread_id) \
                .single() \
                .execute()
            
            return result.data.get('context', {}) if result.data else {}
        except Exception as e:
            logger.error(f"Error fetching context: {str(e)}")
            return {}
    
    async def _generate_response(self, message: Dict, thread: Dict, context: Dict) -> str:
        """Generate AI response using context and message content"""
        try:
            # Prepare conversation history
            history = self._prepare_conversation_history(thread)
            
            # Generate response using OpenAI
            response = await self.ai.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a helpful email assistant. Respond professionally and concisely."},
                    *history,
                    {"role": "user", "content": message.get('body', '')}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I apologize, but I encountered an error processing your request. Please try again later."
    
    async def _send_response(self, grant_id: str, thread_id: str, response: str):
        """Send AI response email"""
        try:
            await self.nylas.messages.send(grant_id, {
                "subject": "Re: " + thread_id,
                "body": response,
                "thread_id": thread_id
            })
        except Exception as e:
            logger.error(f"Error sending response: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to send email response")
    
    async def _update_conversation_context(self, thread_id: str, message: Dict, response: str):
        """Update conversation context in Supabase"""
        try:
            context = {
                'last_interaction': datetime.utcnow().isoformat(),
                'last_message': message.get('body', ''),
                'last_response': response
            }
            
            await self.supabase.table('email_conversations') \
                .upsert({
                    'thread_id': thread_id,
                    'context': context,
                    'updated_at': datetime.utcnow().isoformat()
                }) \
                .execute()
                
        except Exception as e:
            logger.error(f"Error updating context: {str(e)}")
    
    def _prepare_conversation_history(self, thread: Dict) -> List[Dict]:
        """Prepare conversation history for AI context"""
        history = []
        for message in thread.get('messages', [])[-5:]:  # Last 5 messages
            role = "assistant" if message.get('is_ai_response') else "user"
            history.append({
                "role": role,
                "content": message.get('body', '')
            })
        return history
