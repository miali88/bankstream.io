import logging

logger = logging.getLogger(__name__)

def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger.info("Backend server starting up...")
    logger.info(f"Server running on: {API_HOST}:{API_PORT}")
