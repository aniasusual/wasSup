from typing import Optional, List, Dict, Any
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
    
    # ----------------------------
    # Phase 4: Topology Map (WW)
    # ----------------------------
    async def update_topology_map(self, project_id: str, services: list, dependencies: list) -> bool:
        """
        Update the Project Topology Map (WW) for a project.
        Overwrites the topology sections with the provided lists.
        """
        try:
            collection = await self.get_collection()
            update = {
                "topology_services": services,
                "topology_dependencies": dependencies,
                "updated_at": datetime.utcnow()
            }
            res = await collection.update_one({"project_id": project_id}, {"$set": update})
            return res.matched_count > 0
        except Exception as e:
            logger.error(f"Error updating topology map for {project_id}: {e}")
            raise

    async def get_topology_map(self, project_id: str) -> dict:
        """Return the topology map sections or empty defaults."""
        try:
            collection = await self.get_collection()
            doc = await collection.find_one({"project_id": project_id}, {"topology_services": 1, "topology_dependencies": 1, "_id": 0})
            if not doc:
                return {"services": [], "dependencies": []}
            return {
                "services": doc.get("topology_services") or [],
                "dependencies": doc.get("topology_dependencies") or []
            }
        except Exception as e:
            logger.error(f"Error getting topology map for {project_id}: {e}")
            raise

    # ----------------------------
    # Phase 4: Service Registry (XX)
    # ----------------------------
    async def update_service_registry(self, project_id: str, registry: list) -> bool:
        """
        Update the Service Registry (XX) for a project.
        Overwrites the registry with the provided list.
        """
        try:
            collection = await self.get_collection()
            update = {
                "service_registry": registry,
                "updated_at": datetime.utcnow()
            }
            res = await collection.update_one({"project_id": project_id}, {"$set": update})
            return res.matched_count > 0
        except Exception as e:
            logger.error(f"Error updating service registry for {project_id}: {e}")
            raise

    async def get_service_registry(self, project_id: str) -> list:
        """Return the service registry or empty list."""
        try:
            collection = await self.get_collection()
            doc = await collection.find_one({"project_id": project_id}, {"service_registry": 1, "_id": 0})
            if not doc:
                return []
            return doc.get("service_registry") or []
        except Exception as e:
            logger.error(f"Error getting service registry for {project_id}: {e}")
            raise

    # ----------------------------
    # Phase 4: Data Flow Patterns (YY)
    # ----------------------------
    async def update_data_flow_patterns(self, project_id: str, flows: list) -> bool:
        """
        Update Data Flow Patterns (YY) for a project.
        Overwrites the data_flow_patterns with the provided list.
        """
        try:
            collection = await self.get_collection()
            update = {
                "data_flow_patterns": flows,
                "updated_at": datetime.utcnow()
            }
            res = await collection.update_one({"project_id": project_id}, {"$set": update})
            return res.matched_count > 0
        except Exception as e:
            logger.error(f"Error updating data flow patterns for {project_id}: {e}")
            raise

    async def get_data_flow_patterns(self, project_id: str) -> list:
        """Return data flow patterns or empty list."""
        try:
            collection = await self.get_collection()
            doc = await collection.find_one({"project_id": project_id}, {"data_flow_patterns": 1, "_id": 0})
            if not doc:
                return []
            return doc.get("data_flow_patterns") or []
        except Exception as e:
            logger.error(f"Error getting data flow patterns for {project_id}: {e}")
            raise

    # ----------------------------
    # Phase 4: Infrastructure Layout (ZZ)
    # ----------------------------
    async def update_infrastructure_layout(self, project_id: str, infra: list) -> bool:
        """
        Update Infrastructure Layout (ZZ) for a project.
        Overwrites the infrastructure_layout with the provided list.
        """
        try:
            collection = await self.get_collection()
            update = {
                "infrastructure_layout": infra,
                "updated_at": datetime.utcnow()
            }
            res = await collection.update_one({"project_id": project_id}, {"$set": update})
            return res.matched_count > 0
        except Exception as e:
            logger.error(f"Error updating infrastructure layout for {project_id}: {e}")
            raise

    async def get_infrastructure_layout(self, project_id: str) -> list:
        """Return infrastructure layout or empty list."""
        try:
            collection = await self.get_collection()
            doc = await collection.find_one({"project_id": project_id}, {"infrastructure_layout": 1, "_id": 0})
            if not doc:
                return []
            return doc.get("infrastructure_layout") or []
        except Exception as e:
            logger.error(f"Error getting infrastructure layout for {project_id}: {e}")
            raise

    # ----------------------------
    # Phase 4: Performance Baselines (AAA)
    # ----------------------------
    async def update_performance_baselines(self, project_id: str, baselines: list) -> bool:
        """
        Update Performance Baselines (AAA) for a project.
        Overwrites the performance_baselines with the provided list.
        """
        try:
            collection = await self.get_collection()
            update = {
                "performance_baselines": baselines,
                "updated_at": datetime.utcnow()
            }
            res = await collection.update_one({"project_id": project_id}, {"$set": update})
            return res.matched_count > 0
        except Exception as e:
            logger.error(f"Error updating performance baselines for {project_id}: {e}")
            raise

    async def get_performance_baselines(self, project_id: str) -> list:
        """Return performance baselines or empty list."""
        try:
            collection = await self.get_collection()
            doc = await collection.find_one({"project_id": project_id}, {"performance_baselines": 1, "_id": 0})
            if not doc:
                return []
            return doc.get("performance_baselines") or []
        except Exception as e:
            logger.error(f"Error getting performance baselines for {project_id}: {e}")
            raise

    # ----------------------------
    # Phase 4: Failure Patterns (BBB)
    # ----------------------------
    async def update_failure_patterns(self, project_id: str, patterns: list) -> bool:
        """
        Update Failure Patterns (BBB) for a project.
        Overwrites the failure_patterns with the provided list.
        """
        try:
            collection = await self.get_collection()
            update = {
                "failure_patterns": patterns,
                "updated_at": datetime.utcnow()
            }
            res = await collection.update_one({"project_id": project_id}, {"$set": update})
            return res.matched_count > 0
        except Exception as e:
            logger.error(f"Error updating failure patterns for {project_id}: {e}")
            raise

    async def get_failure_patterns(self, project_id: str) -> list:
        """Return failure patterns or empty list."""
        try:
            collection = await self.get_collection()
            doc = await collection.find_one({"project_id": project_id}, {"failure_patterns": 1, "_id": 0})
            if not doc:
                return []
            return doc.get("failure_patterns") or []
        except Exception as e:
            logger.error(f"Error getting failure patterns for {project_id}: {e}")
            raise

    # ----------------------------
    # Phase 10: Context Management Bundle
    # ----------------------------
    async def get_context_management_snapshot(self, project_id: str) -> Dict[str, Any]:
        """Retrieve context-management related sections for a project."""
        try:
            collection = await self.get_collection()
            projection = {
                "context_memory": 1,
                "query_history": 1,
                "query_history_stats": 1,
                "user_preferences": 1,
                "session_state": 1,
                "learning_repository": 1,
                "learning_repository_summary": 1,
                "team_knowledge": 1,
                "team_knowledge_stats": 1,
                "architecture_learning": 1,
                "architecture_learning_meta": 1,
                "preventive_actions": 1,
                "proactive_monitoring_plan": 1,
                "user_feedback_history": 1,
                "architecture_agent_summary": 1,
                "query_classifier_summary": 1,
                "investigation_planner_summary": 1,
                "filter_architect_summary": 1,
                "api_orchestrator_stats": 1,
                "correlation_engine_summary": 1,
                "pattern_analyzer_summary": 1,
                "synthesis_summary": 1,
                "recommendation_summary": 1,
                "context_manager_snapshot": 1,
                "real_time_stream_summary": 1,
                "predictive_analytics_summary": 1,
                "ml_pattern_summary": 1,
                "cross_project_learning_summary": 1,
                "automated_remediation_summary": 1,
                "performance_optimization_summary": 1,
                "_id": 0,
            }
            doc = await collection.find_one({"project_id": project_id}, projection)
            return doc or {}
        except Exception as e:
            logger.error(f"Error getting context management snapshot for {project_id}: {e}")
            raise

    async def update_context_management_snapshot(self, project_id: str, updates: Dict[str, Any]) -> bool:
        """Persist context-management structures for a project."""
        if not updates:
            return True
        try:
            collection = await self.get_collection()
            payload = {**updates, "context_updated_at": datetime.utcnow()}
            res = await collection.update_one({"project_id": project_id}, {"$set": payload})
            return res.matched_count > 0
        except Exception as e:
            logger.error(f"Error updating context management snapshot for {project_id}: {e}")
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
