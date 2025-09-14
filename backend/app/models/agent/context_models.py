"""
Context models for architecture and service information.

This module defines models for storing and managing GCP project
architecture context, service registries, and performance baselines.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field


class ServiceEndpoint(BaseModel):
    """Represents a service endpoint configuration."""
    name: str = Field(..., description="Endpoint name")
    url: str = Field(..., description="Endpoint URL")
    method: str = Field("GET", description="HTTP method")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Required parameters")
    dependencies: Optional[List[str]] = Field(None, description="Dependent endpoints")


class ServiceRegistry(BaseModel):
    """
    Registry of GCP services and their configurations.
    
    This tracks available services, their endpoints, and relationships.
    """
    service_id: str = Field(..., description="Unique service identifier")
    service_name: str = Field(..., description="Human-readable service name")
    service_type: str = Field(..., description="Type of GCP service (e.g., cloud_run, gce_instance)")
    endpoints: List[ServiceEndpoint] = Field(default_factory=list, description="Available API endpoints")
    labels: Dict[str, str] = Field(default_factory=dict, description="Service labels and metadata")
    dependencies: List[str] = Field(default_factory=list, description="Dependent services")
    health_status: str = Field("unknown", description="Current health status")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "service_id": "svc_cloud_run_001",
                "service_name": "user-auth-service",
                "service_type": "cloud_run_revision",
                "endpoints": [
                    {
                        "name": "health_check",
                        "url": "https://user-auth-service-xyz.run.app/health",
                        "method": "GET"
                    }
                ],
                "labels": {
                    "environment": "production",
                    "team": "auth-team"
                },
                "dependencies": ["svc_cloud_sql_001"],
                "health_status": "healthy"
            }
        }


class PerformanceBaseline(BaseModel):
    """
    Performance baseline data for services and resources.
    
    This stores normal performance metrics for anomaly detection.
    """
    service_id: str = Field(..., description="Associated service identifier")
    metric_name: str = Field(..., description="Name of the performance metric")
    baseline_value: float = Field(..., description="Normal/baseline value")
    threshold_min: Optional[float] = Field(None, description="Minimum acceptable threshold")
    threshold_max: Optional[float] = Field(None, description="Maximum acceptable threshold")
    unit: str = Field("", description="Unit of measurement")
    measurement_period: str = Field("1h", description="Period over which baseline was calculated")
    last_calculated: datetime = Field(default_factory=datetime.utcnow, description="When baseline was last calculated")
    sample_size: int = Field(0, description="Number of samples used for baseline")
    
    class Config:
        json_schema_extra = {
            "example": {
                "service_id": "svc_cloud_run_001",
                "metric_name": "response_time_ms",
                "baseline_value": 150.5,
                "threshold_min": 100.0,
                "threshold_max": 500.0,
                "unit": "milliseconds",
                "measurement_period": "1h",
                "sample_size": 1000
            }
        }


class ArchitectureContext(BaseModel):
    """
    Complete architecture context for a GCP project.
    
    This aggregates all architectural information needed for
    intelligent log investigation and analysis.
    """
    project_id: str = Field(..., description="GCP project identifier")
    context_id: str = Field(..., description="Unique context identifier")
    services: List[ServiceRegistry] = Field(default_factory=list, description="Registered services")
    performance_baselines: List[PerformanceBaseline] = Field(default_factory=list, description="Performance baselines")
    service_dependencies: Dict[str, List[str]] = Field(default_factory=dict, description="Service dependency mapping")
    data_flows: List[Dict[str, Any]] = Field(default_factory=list, description="Data flow patterns")
    infrastructure_layout: Dict[str, Any] = Field(default_factory=dict, description="Infrastructure configuration")
    failure_patterns: List[Dict[str, Any]] = Field(default_factory=list, description="Known failure patterns")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    version: str = Field("1.0", description="Context schema version")
    
    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "my-gcp-project",
                "context_id": "ctx_001",
                "services": [
                    {
                        "service_id": "svc_001",
                        "service_name": "api-gateway",
                        "service_type": "cloud_run_revision",
                        "dependencies": ["svc_002", "svc_003"]
                    }
                ],
                "service_dependencies": {
                    "svc_001": ["svc_002", "svc_003"],
                    "svc_002": ["svc_004"]
                },
                "data_flows": [
                    {
                        "source": "external",
                        "target": "api-gateway",
                        "protocol": "https",
                        "port": 443
                    }
                ]
            }
        }


class QueryContext(BaseModel):
    """
    Context for processing a specific query.
    
    This provides query-specific context that supplements
    the general architecture context.
    """
    query_id: str = Field(..., description="Unique query identifier")
    user_intent: Optional[str] = Field(None, description="Detected user intent")
    relevant_services: List[str] = Field(default_factory=list, description="Services relevant to this query")
    time_context: Optional[Dict[str, str]] = Field(None, description="Time-related context")
    severity_focus: Optional[List[str]] = Field(None, description="Severity levels of interest")
    investigation_scope: str = Field("single_service", description="Scope of investigation")
    complexity_level: str = Field("simple", description="Query complexity level")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query_id": "q_001",
                "user_intent": "troubleshoot_authentication_errors",
                "relevant_services": ["cloud_run_revision", "cloud_sql"],
                "time_context": {
                    "range": "last_hour",
                    "focus": "recent_errors"
                },
                "severity_focus": ["ERROR", "CRITICAL"],
                "investigation_scope": "multi_service",
                "complexity_level": "complex"
            }
        }
