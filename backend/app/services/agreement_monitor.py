import logging
from datetime import datetime, timedelta
from backend.app.services.etl.supabase import get_supabase

logger = logging.getLogger(__name__)

async def get_expiring_agreements(days_threshold: int = 7):
    """
    Get agreements that are expiring within the specified number of days
    
    Args:
        days_threshold (int): Number of days before expiration to check for
        
    Returns:
        List of agreements that are expiring soon
    """
    try:
        supabase = await get_supabase()
        
        # Calculate the date range for expiring agreements
        now = datetime.utcnow()
        expiry_threshold = now + timedelta(days=days_threshold)
        
        # Query for agreements expiring soon
        result = await supabase.table('gocardless_agreements')\
            .select('*')\
            .gte('expires_at', now.isoformat())\
            .lte('expires_at', expiry_threshold.isoformat())\
            .execute()
            
        return result.data
    except Exception as e:
        logger.error(f"Error checking for expiring agreements: {str(e)}")
        raise 