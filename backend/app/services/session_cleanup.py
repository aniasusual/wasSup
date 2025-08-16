import asyncio
import logging
from datetime import datetime
from .conversation_manager import conversation_manager

logger = logging.getLogger(__name__)


async def cleanup_expired_sessions():
    """Periodically cleanup expired conversation sessions."""
    while True:
        try:
            before_count = len(conversation_manager.sessions)
            conversation_manager.cleanup_expired_sessions()
            after_count = len(conversation_manager.sessions)
            
            if before_count != after_count:
                logger.info(f"Cleaned up {before_count - after_count} expired sessions")
            
            # Run cleanup every hour
            await asyncio.sleep(3600)
            
        except Exception as e:
            logger.error(f"Error during session cleanup: {e}")
            await asyncio.sleep(300)  # Wait 5 minutes before retrying


def start_cleanup_task():
    """Start the session cleanup task."""
    loop = asyncio.get_event_loop()
    loop.create_task(cleanup_expired_sessions())
    logger.info("Session cleanup task started")
