from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from app.models.project_architecture import (
    ProjectArchitecture,
    ProjectArchitectureCreate,
    ProjectArchitectureUpdate
)
import logging
import asyncio

logger = logging.getLogger(__name__)

class ProjectArchitectureService:
    def __init__(self):
        self.collection_name = "project_architectures"
    
    async def get_collection(self):
        """Get the project architectures collection without blocking the event loop.

        This defers the potentially blocking import work to a background thread
        to satisfy environments that detect sync I/O in async contexts.
        """
        # Import db helpers in a thread to avoid import-time blocking I/O
        def _import_db():
            from app.core.database import db, get_database
            return db, get_database

        db, get_database = await asyncio.to_thread(_import_db)

        logger.info(f"Getting collection. db.database: {db.database}")

        # Try to get database from the global db instance first; if missing, try to connect
        if db.database is None:
            try:
                from app.core.database import connect_to_mongo
                await connect_to_mongo()
                logger.info("Connected to MongoDB via lazy startup")
            except Exception as conn_err:
                logger.warning(f"Lazy MongoDB connect failed: {conn_err}")

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
    
    async def create_architecture(self, architecture_data: ProjectArchitectureCreate) -> ProjectArchitecture:
        """Create a new project architecture"""
        try:
            collection = await self.get_collection()
            logger.info(f"Creating architecture for project: {architecture_data.project_id}")
            
            # Check if architecture already exists for this project
            existing = await collection.find_one({"project_id": architecture_data.project_id})
            logger.info(f"Existing architecture found: {existing is not None}")
            
            if existing:
                # Update existing instead of creating new
                update_data = architecture_data.dict()
                update_data["updated_at"] = datetime.utcnow()
                logger.info(f"Updating existing architecture with data: {update_data}")
                
                result = await collection.update_one(
                    {"project_id": architecture_data.project_id},
                    {"$set": update_data}
                )
                
                logger.info(f"Update result: {result.modified_count} documents modified")
                
                if result.modified_count:
                    updated_doc = await collection.find_one({"project_id": architecture_data.project_id})
                    if updated_doc:
                        logger.info(f"Retrieved updated doc: {updated_doc}")
                        return ProjectArchitecture(**updated_doc)
                    else:
                        raise Exception("Failed to retrieve updated architecture")
                else:
                    raise Exception("Failed to update existing architecture")
            else:
                # Create new architecture
                architecture_dict = architecture_data.dict()
                architecture_dict["created_at"] = datetime.utcnow()
                architecture_dict["updated_at"] = datetime.utcnow()
                logger.info(f"Creating new architecture with data: {architecture_dict}")
                
                result = await collection.insert_one(architecture_dict)
                logger.info(f"Insert result: {result.inserted_id}")
                
                if result.inserted_id:
                    created_doc = await collection.find_one({"_id": result.inserted_id})
                    if created_doc:
                        logger.info(f"Retrieved created doc: {created_doc}")
                        return ProjectArchitecture(**created_doc)
                    else:
                        raise Exception("Failed to retrieve created architecture")
                else:
                    raise Exception("Failed to create architecture")
                    
        except Exception as e:
            logger.error(f"Error creating/updating project architecture: {e}")
            raise
    
    async def get_architecture_by_project(self, project_id: str) -> Optional[ProjectArchitecture]:
        """Get project architecture by project ID"""
        try:
            collection = await self.get_collection()
            doc = await collection.find_one({"project_id": project_id})
            # print(f"Doc loda: {doc}")
            
            if doc:
                return ProjectArchitecture(**doc)
            return None
            
        except Exception as e:
            logger.error(f"Error getting project architecture: {e}")
            raise
    
    async def update_architecture(self, project_id: str, update_data: ProjectArchitectureUpdate) -> Optional[ProjectArchitecture]:
        """Update project architecture"""
        try:
            collection = await self.get_collection()
            
            update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
            if not update_dict:
                return await self.get_architecture_by_project(project_id)
            
            update_dict["updated_at"] = datetime.utcnow()
            
            result = await collection.update_one(
                {"project_id": project_id},
                {"$set": update_dict}
            )
            
            if result.modified_count:
                return await self.get_architecture_by_project(project_id)
            return None
            
        except Exception as e:
            logger.error(f"Error updating project architecture: {e}")
            raise
    
    async def delete_architecture(self, project_id: str) -> bool:
        """Delete project architecture"""
        try:
            collection = await self.get_collection()
            result = await collection.delete_one({"project_id": project_id})
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting project architecture: {e}")
            raise
    
    async def list_architectures(self, skip: int = 0, limit: int = 100) -> List[ProjectArchitecture]:
        """List all project architectures"""
        try:
            collection = self.get_collection()
            cursor = collection.find().skip(skip).limit(limit)
            architectures = []
            
            async for doc in cursor:
                architectures.append(ProjectArchitecture(**doc))
            
            return architectures
            
        except Exception as e:
            logger.error(f"Error listing project architectures: {e}")
            raise

# Create service instance
project_architecture_service = ProjectArchitectureService()
