from typing import Optional, List
from datetime import datetime, timedelta
from bson import ObjectId
from app.models.user import (
    User,
    UserCreate,
    UserUpdate
)
import logging

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self):
        self.collection_name = "users"
    
    def get_collection(self):
        """Get the users collection"""
        # Import here to avoid circular imports and ensure fresh connection
        from app.core.database import db, get_database
        
        logger.info(f"Getting users collection. db.database: {db.database}")
        
        # Try to get database from the global db instance first
        if db.database is not None:
            logger.info(f"Using global db instance: {db.database}")
            return db.database[self.collection_name]
        
        # Fallback to get_database function
        logger.info("Trying get_database function")
        try:
            database = get_database()
            logger.info(f"get_database result: {database}")
            return database[self.collection_name]
        except Exception as e:
            logger.error(f"Failed to get database: {e}")
            raise Exception(f"Database connection not initialized: {e}")
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        try:
            collection = self.get_collection()
            logger.info(f"Creating user for email: {user_data.email}")
            
            # Check if user already exists
            existing = await collection.find_one({"email": user_data.email})
            if existing:
                # Update existing user instead of creating new
                update_data = user_data.dict()
                update_data["updated_at"] = datetime.utcnow()
                update_data["last_login"] = datetime.utcnow()
                
                result = await collection.update_one(
                    {"email": user_data.email},
                    {"$set": update_data}
                )
                
                if result.modified_count:
                    updated_doc = await collection.find_one({"email": user_data.email})
                    if updated_doc:
                        logger.info(f"Updated existing user: {updated_doc}")
                        return User(**updated_doc)
                    else:
                        raise Exception("Failed to retrieve updated user")
                else:
                    raise Exception("Failed to update existing user")
            else:
                # Create new user
                user_dict = user_data.dict()
                user_dict["created_at"] = datetime.utcnow()
                user_dict["updated_at"] = datetime.utcnow()
                user_dict["last_login"] = datetime.utcnow()
                logger.info(f"Creating new user with data: {user_dict}")
                
                result = await collection.insert_one(user_dict)
                logger.info(f"Insert result: {result.inserted_id}")
                
                if result.inserted_id:
                    created_doc = await collection.find_one({"_id": result.inserted_id})
                    if created_doc:
                        logger.info(f"Retrieved created user: {created_doc}")
                        return User(**created_doc)
                    else:
                        raise Exception("Failed to retrieve created user")
                else:
                    raise Exception("Failed to create user")
                    
        except Exception as e:
            logger.error(f"Error creating/updating user: {e}")
            raise
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            collection = self.get_collection()
            doc = await collection.find_one({"email": email})
            
            if doc:
                return User(**doc)
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            raise
    
    async def get_user_by_google_id(self, google_id: str) -> Optional[User]:
        """Get user by Google ID"""
        try:
            collection = self.get_collection()
            doc = await collection.find_one({"google_id": google_id})
            
            if doc:
                return User(**doc)
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by Google ID: {e}")
            raise
    
    async def update_user(self, email: str, update_data: UserUpdate) -> Optional[User]:
        """Update user"""
        try:
            collection = self.get_collection()
            
            update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
            if not update_dict:
                return await self.get_user_by_email(email)
            
            update_dict["updated_at"] = datetime.utcnow()
            
            result = await collection.update_one(
                {"email": email},
                {"$set": update_dict}
            )
            
            if result.modified_count:
                return await self.get_user_by_email(email)
            return None
            
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            raise
    
    async def update_user_tokens(self, email: str, access_token: str, refresh_token: Optional[str] = None, expires_in: int = 3600) -> Optional[User]:
        """Update user tokens"""
        try:
            collection = self.get_collection()
            
            token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            update_data = {
                "access_token": access_token,
                "token_expires_at": token_expires_at,
                "updated_at": datetime.utcnow(),
                "last_login": datetime.utcnow()
            }
            
            if refresh_token:
                update_data["refresh_token"] = refresh_token
            
            result = await collection.update_one(
                {"email": email},
                {"$set": update_data}
            )
            
            if result.modified_count:
                return await self.get_user_by_email(email)
            return None
            
        except Exception as e:
            logger.error(f"Error updating user tokens: {e}")
            raise
    
    async def delete_user(self, email: str) -> bool:
        """Delete user"""
        try:
            collection = self.get_collection()
            result = await collection.delete_one({"email": email})
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            raise
    
    async def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """List all users"""
        try:
            collection = self.get_collection()
            cursor = collection.find().skip(skip).limit(limit)
            users = []
            
            async for doc in cursor:
                users.append(User(**doc))
            
            return users
            
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            raise

# Create service instance
user_service = UserService()
