from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    database = None

db = Database()

async def connect_to_mongo():
    """Create database connection"""
    try:
        db.client = AsyncIOMotorClient(settings.MONGODB_URL)
        db.database = db.client[settings.DATABASE_NAME]
        
        # Test the connection
        await db.client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
        
    except ConnectionFailure as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()
        logger.info("Disconnected from MongoDB")

def get_database():
    """Get database instance"""
    if db.database is None:
        raise Exception("Database not connected. Call connect_to_mongo() first.")
    return db.database
