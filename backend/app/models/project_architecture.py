from pydantic import BaseModel, Field, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from typing import Optional, Any
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Any) -> Any:
        from pydantic_core import core_schema
        return core_schema.no_info_plain_validator_function(cls.validate)

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, _core_schema: Any, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        return {"type": "string"}

class ProjectArchitectureBase(BaseModel):
    project_id: str = Field(..., description="GCP Project ID")
    architecture_prompt: str = Field(..., description="Complete project architecture description")
    created_by: Optional[str] = Field(None, description="User who created this architecture")
    is_active: bool = Field(True, description="Whether this architecture is currently active")

class ProjectArchitectureCreate(ProjectArchitectureBase):
    pass

class ProjectArchitectureUpdate(BaseModel):
    architecture_prompt: Optional[str] = Field(None, description="Updated architecture description")
    is_active: Optional[bool] = Field(None, description="Whether this architecture is currently active")

class ProjectArchitecture(ProjectArchitectureBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    # Phase 4: Architecture Topology (WW)
    topology_services: Optional[list] = Field(default=None, description="List of normalized services in the topology map")
    topology_dependencies: Optional[list] = Field(default=None, description="List of directed dependencies between services")
    # Phase 4: Service Registry (XX)
    service_registry: Optional[list] = Field(default=None, description="Normalized service registry: resources and configurations")
    # Phase 4: Data Flow Patterns (YY)
    data_flow_patterns: Optional[list] = Field(default=None, description="Request paths and communication flows across services")
    # Phase 4: Infrastructure Layout (ZZ)
    infrastructure_layout: Optional[list] = Field(default=None, description="Networks, clusters, databases and related infra components")
    # Phase 4: Performance Baselines (AAA)
    performance_baselines: Optional[list] = Field(default=None, description="Normal performance/error baselines per service")
    # Phase 4: Failure Patterns (BBB)
    failure_patterns: Optional[list] = Field(default=None, description="Historical incident knowledge and common failure patterns")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
