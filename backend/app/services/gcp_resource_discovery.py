from __future__ import annotations

from typing import Any, Dict, List, Optional
import os
import asyncio
import aiohttp
import ssl
from datetime import datetime
import json

from ..api.data.gcpApiEndpoints import GCP_API_ENDPOINTS


class GCPResourceDiscovery:
    """
    Service to discover available GCP resources in a project.
    Uses the GCP API endpoints configuration to intelligently discover resources.
    """
    
    def __init__(self):
        self.api_key = os.getenv("GCP_API_KEY")
        self.access_token = os.getenv("GCP_ACCESS_TOKEN")
        self.project_id = None
        
        # Create SSL context for macOS compatibility
        self.ssl_context = ssl.create_default_context()
        # On macOS, we might need to disable certificate verification for development
        if os.name == 'posix' and os.uname().sysname == 'Darwin':
            try:
                # Try to use system certificates first
                self.ssl_context.check_hostname = True
                self.ssl_context.verify_mode = ssl.CERT_REQUIRED
            except Exception:
                # Fallback for development environments
                self.ssl_context.check_hostname = False
                self.ssl_context.verify_mode = ssl.CERT_NONE
        
    async def discover_resources(
        self,
        project_id: str,
        resource_types: Optional[List[str]] = None,
        access_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Discover available GCP resources in a project.
        
        Args:
            project_id: GCP project ID
            resource_types: Specific resource types to discover (optional)
            access_token: OAuth access token for GCP API calls
            
        Returns:
            Dict containing discovered resources and metadata
        """
        self.project_id = project_id
        
        try:
            # Use provided access token or fall back to environment variable
            if not access_token:
                access_token = self.access_token or os.getenv("GCP_ACCESS_TOKEN")
            
            if not access_token:
                return {
                    "success": False,
                    "error": "No access token provided for GCP API calls",
                    "project_id": project_id,
                    "discovered_resources": {},
                    "discovery_summary": {
                        "total_resource_types": 0,
                        "resource_types_discovered": [],
                        "errors": ["No access token available"]
                    }
                }
            
            # Validate project_id
            if not project_id or project_id == "None":
                return {
                    "success": False,
                    "error": "Invalid project ID provided",
                    "project_id": project_id,
                    "discovered_resources": {},
                    "discovery_summary": {
                        "total_resource_types": 0,
                        "resource_types_discovered": [],
                        "errors": ["Invalid project ID"]
                    }
                }
            
            # Determine which resource types to discover
            if resource_types:
                target_types = [rt for rt in resource_types if rt in GCP_API_ENDPOINTS]
            else:
                # Discover all major resource types
                target_types = [
                    "cloud_run_revision",
                    "gce_instance", 
                    "cloud_function",
                    "gae_app",
                    "k8s_container",
                    "gcs_bucket",
                    "cloudsql_database",
                    "bigquery_dataset",
                    "pubsub_topic",
                    "dataflow_job"
                ]
            
            discovered_resources = {}
            discovery_errors = []
            
            # Discover resources for each type
            for resource_type in target_types:
                try:
                    if resource_type in GCP_API_ENDPOINTS:
                        resources = await self._discover_resource_type(resource_type, access_token, project_id)
                        if resources:
                            discovered_resources[resource_type] = resources
                    else:
                        discovery_errors.append(f"Unknown resource type: {resource_type}")
                except Exception as e:
                    discovery_errors.append(f"Error discovering {resource_type}: {str(e)}")
            
            # Get project-level information
            project_info = await self._get_project_info(project_id, access_token)
            
            return {
                "success": True,
                "project_id": project_id,
                "discovered_resources": discovered_resources,
                "project_info": project_info,
                "discovery_summary": {
                    "total_resource_types": len(discovered_resources),
                    "resource_types_discovered": list(discovered_resources.keys()),
                    "errors": discovery_errors
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error in resource discovery: {e}")
            return {
                "success": False,
                "error": str(e),
                "project_id": project_id,
                "discovered_resources": {},
                "discovery_summary": {
                    "total_resource_types": 0,
                    "resource_types_discovered": [],
                    "errors": [str(e)]
                }
            }
    
    async def _discover_resource_type(self, resource_type: str, access_token: str, project_id: str) -> Dict[str, Any]:
        """Discover resources of a specific type."""
        print(f"🔍 Resource Discovery: Discovering {resource_type} for project_id={project_id}")
        
        if resource_type not in GCP_API_ENDPOINTS:
            print(f"❌ Resource Discovery: Unknown resource type {resource_type}")
            return {}
        
        resource_config = GCP_API_ENDPOINTS[resource_type]
        discovered = {}
        
        # Discover each field for this resource type
        for field_name, field_config in resource_config.items():
            try:
                if field_config.get("endpoint"):
                    endpoint = field_config["endpoint"]
                    
                    if callable(endpoint):
                        # Dynamic endpoint that needs parameters
                        if field_config.get("depends_on"):
                            # This field depends on other fields, skip for now
                            print(f"🔍 Resource Discovery: Skipping {field_name} (depends on {field_config.get('depends_on')})")
                            continue
                        else:
                            # Simple endpoint - pass the project_id parameter
                            url = endpoint(project_id)
                            print(f"🔍 Resource Discovery: Generated URL for {field_name}: {url}")
                    else:
                        # Static endpoint
                        url = endpoint
                        print(f"🔍 Resource Discovery: Using static URL for {field_name}: {url}")
                    
                    if url and not url.startswith("#"):
                        # Make API call
                        print(f"🔍 Resource Discovery: Making API call to {url}")
                        values = await self._call_gcp_api(url, access_token, field_config.get("transform"))
                        if values:
                            discovered[field_name] = values
                            print(f"✅ Resource Discovery: Successfully discovered {field_name}: {len(values) if isinstance(values, list) else 'data'}")
                        else:
                            print(f"⚠️ Resource Discovery: No values returned for {field_name}")
                    else:
                        print(f"🔍 Resource Discovery: Skipping {field_name} (invalid URL: {url})")
                    
                elif field_config.get("transform"):
                    # Static data transformation
                    print(f"🔍 Resource Discovery: Using static transform for {field_name}")
                    values = field_config["transform"]({})
                    if values:
                        discovered[field_name] = values
                        print(f"✅ Resource Discovery: Static transform successful for {field_name}")
                        
            except Exception as e:
                print(f"❌ Resource Discovery: Error discovering field {field_name} for {resource_type}: {e}")
                continue
        
        print(f"🔍 Resource Discovery: Completed discovery for {resource_type}, found {len(discovered)} fields")
        return discovered
    
    async def _call_gcp_api(self, url: str, access_token: str, transform_func: Optional[callable] = None) -> Optional[List[str]]:
        """Make a call to GCP API endpoint."""
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # For development, try without SSL verification first (more reliable)
            try:
                connector = aiohttp.TCPConnector(ssl=False)
                async with aiohttp.ClientSession(connector=connector) as session:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            # Apply transformation if provided
                            if transform_func and callable(transform_func):
                                return transform_func(data)
                            else:
                                return data
                        else:
                            if response.status == 403:
                                print(f"⚠️ Resource Discovery: Permission denied for {url} - skipping this resource")
                            elif response.status == 404:
                                print(f"⚠️ Resource Discovery: Resource not found for {url} - skipping this resource")
                            else:
                                print(f"⚠️ Resource Discovery: API call failed: {response.status} - {url}")
                            return None
            except Exception as fallback_error:
                print(f"Fallback API call failed for {url}: {fallback_error}")
                return None
                        
        except Exception as e:
            print(f"Error calling GCP API {url}: {e}")
            return None
    
    async def _get_project_info(self, project_id: str, access_token: str) -> Dict[str, Any]:
        """Get basic project information."""
        try:
            url = f"https://cloudresourcemanager.googleapis.com/v1/projects/{project_id}"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # For development, use SSL bypass (more reliable)
            try:
                connector = aiohttp.TCPConnector(ssl=False)
                async with aiohttp.ClientSession(connector=connector) as session:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            return {
                                "project_id": data.get("projectId"),
                                "name": data.get("name"),
                                "display_name": data.get("displayName"),
                                "state": data.get("state"),
                                "create_time": data.get("createTime"),
                                "labels": data.get("labels", {})
                            }
                        else:
                            return {"error": f"Failed to get project info: {response.status}"}
            except Exception as fallback_error:
                print(f"Project info call failed: {fallback_error}")
                return {"error": f"API call failed: {str(fallback_error)}"}
                        
        except Exception as e:
            print(f"Error getting project info: {e}")
            return {"error": str(e)}
    
    async def _get_access_token(self) -> Optional[str]:
        """Get GCP access token using service account or other methods."""
        # This is a placeholder - in production you'd implement proper authentication
        # Options include:
        # 1. Service account key file
        # 2. Application Default Credentials
        # 3. OAuth2 flow
        # 4. Workload Identity
        
        # For now, return the API key if available
        return self.api_key
    
    async def get_resource_summary(self, project_id: str, access_token: str) -> Dict[str, Any]:
        """Get a summary of available resources without full discovery."""
        try:
            # Quick discovery of major resource types
            major_types = [
                "cloud_run_revision",
                "gce_instance",
                "cloud_function",
                "gae_app"
            ]
            
            summary = {}
            for resource_type in major_types:
                try:
                    resources = await self._discover_resource_type(resource_type, access_token, project_id)
                    if resources:
                        # Count total resources
                        total_count = 0
                        for field_name, values in resources.items():
                            if isinstance(values, list):
                                total_count += len(values)
                        
                        summary[resource_type] = {
                            "available": True,
                            "total_count": total_count,
                            "fields": list(resources.keys())
                        }
                    else:
                        summary[resource_type] = {"available": False}
                        
                except Exception:
                    summary[resource_type] = {"available": False, "error": "Discovery failed"}
            
            return {
                "success": True,
                "project_id": project_id,
                "resource_summary": summary,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "project_id": project_id
            }
    
    async def validate_resource_access(
        self,
        project_id: str,
        resource_type: str,
        resource_name: str,
        access_token: str
    ) -> Dict[str, Any]:
        """Validate access to a specific resource."""
        try:
            if resource_type not in GCP_API_ENDPOINTS:
                return {
                    "success": False,
                    "error": f"Unknown resource type: {resource_type}"
                }
            
            # Try to access the specific resource
            resource_config = GCP_API_ENDPOINTS[resource_type]
            
            # Find an endpoint that can validate this resource
            validation_endpoint = None
            for field_name, field_config in resource_config.items():
                if field_config.get("endpoint") and callable(field_config["endpoint"]):
                    try:
                        # Try to construct endpoint with the resource name
                        if "name" in field_name:
                            validation_endpoint = field_config["endpoint"](project_id, resource_name)
                            break
                    except:
                        continue
            
            if validation_endpoint:
                # Try to access the resource
                result = await self._call_gcp_api(validation_endpoint, access_token)
                if result is not None:
                    return {
                        "success": True,
                        "resource_type": resource_type,
                        "resource_name": resource_name,
                        "accessible": True,
                        "details": result
                    }
                else:
                    return {
                        "success": True,
                        "resource_type": resource_type,
                        "resource_name": resource_name,
                        "accessible": False,
                        "reason": "API call failed"
                    }
            else:
                return {
                    "success": True,
                    "resource_type": resource_type,
                    "resource_name": resource_name,
                    "accessible": False,
                    "reason": "No validation endpoint available"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "resource_type": resource_type,
                "resource_name": resource_name
            }
