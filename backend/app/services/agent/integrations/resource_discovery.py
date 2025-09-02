"""
GCP Resource Discovery

Discovers available GCP resources for enhanced filtering capabilities.
Handles API errors gracefully and provides fallback options.
"""

import aiohttp
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class GCPResourceDiscovery:
    """
    Discovers available GCP resources to enhance log filtering capabilities.
    """
    
    def __init__(self):
        self.project_id = None
        self.discovered_resources = {}
    
    async def get_resource_summary(self, project_id: str, access_token: str) -> Dict[str, Any]:
        """
        Get a summary of available GCP resources for the project.
        
        Args:
            project_id: GCP project ID
            access_token: OAuth2 access token
            
        Returns:
            Dictionary containing discovered resources
        """
        self.project_id = project_id
        
        # Discover different resource types
        cloud_run_services = await self._discover_cloud_run_services(access_token)
        gce_instances = await self._discover_gce_instances(access_token)
        cloud_functions = await self._discover_cloud_functions(access_token)
        app_engine_services = await self._discover_app_engine_services(access_token)
        
        return {
            "summary": {
                "cloud_run_services": len(cloud_run_services),
                "gce_instances": len(gce_instances),
                "cloud_functions": len(cloud_functions),
                "app_engine_services": len(app_engine_services)
            },
            "cloud_run_services": cloud_run_services,
            "gce_instances": gce_instances,
            "cloud_functions": cloud_functions,
            "app_engine_services": app_engine_services
        }
    
    async def _discover_cloud_run_services(self, access_token: str) -> List[str]:
        """Discover Cloud Run services."""
        url = f"https://run.googleapis.com/v1/projects/{self.project_id}/locations/-/services"
        return await self._call_gcp_api(url, access_token, self._transform_cloud_run_services)
    
    async def _discover_gce_instances(self, access_token: str) -> List[str]:
        """Discover GCE instances."""
        url = f"https://compute.googleapis.com/compute/v1/projects/{self.project_id}/aggregated/instances"
        return await self._call_gcp_api(url, access_token, self._transform_gce_instances)
    
    async def _discover_cloud_functions(self, access_token: str) -> List[str]:
        """Discover Cloud Functions."""
        url = f"https://cloudfunctions.googleapis.com/v1/projects/{self.project_id}/locations/-/functions"
        return await self._call_gcp_api(url, access_token, self._transform_cloud_functions)
    
    async def _discover_app_engine_services(self, access_token: str) -> List[str]:
        """Discover App Engine services."""
        url = f"https://appengine.googleapis.com/v1/apps/{self.project_id}/services"
        return await self._call_gcp_api(url, access_token, self._transform_app_engine_services)
    
    async def _call_gcp_api(
        self, 
        url: str, 
        access_token: str, 
        transform_func: Optional[callable] = None
    ) -> Optional[List[str]]:
        """
        Make a call to a GCP API endpoint with error handling.
        
        Args:
            url: API endpoint URL
            access_token: OAuth2 access token
            transform_func: Function to transform the response data
            
        Returns:
            Transformed data or None if error
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        if transform_func:
                            return transform_func(data)
                        return data
                    else:
                        self._handle_api_error(response.status, url)
                        return None
        except Exception as e:
            logger.error(f"Error calling GCP API {url}: {str(e)}")
            return None
    
    def _handle_api_error(self, status_code: int, url: str):
        """Handle API errors with appropriate logging."""
        if status_code == 403:
            logger.warning(f"⚠️ Resource Discovery: Permission denied for {url} - skipping this resource")
        elif status_code == 404:
            logger.warning(f"⚠️ Resource Discovery: Resource not found for {url} - skipping this resource")
        else:
            logger.warning(f"⚠️ Resource Discovery: API call failed: {status_code} - {url}")
    
    def _transform_cloud_run_services(self, data: Dict[str, Any]) -> List[str]:
        """Transform Cloud Run services response."""
        services = []
        if "items" in data:
            for item in data["items"]:
                if "metadata" in item and "name" in item["metadata"]:
                    services.append(item["metadata"]["name"])
        return services
    
    def _transform_gce_instances(self, data: Dict[str, Any]) -> List[str]:
        """Transform GCE instances response."""
        instances = []
        if "items" in data:
            for zone, zone_data in data["items"].items():
                if "instances" in zone_data:
                    for instance in zone_data["instances"]:
                        if "name" in instance:
                            instances.append(instance["name"])
        return instances
    
    def _transform_cloud_functions(self, data: Dict[str, Any]) -> List[str]:
        """Transform Cloud Functions response."""
        functions = []
        if "functions" in data:
            for func in data["functions"]:
                if "name" in func:
                    # Extract function name from full path
                    name = func["name"].split("/")[-1]
                    functions.append(name)
        return functions
    
    def _transform_app_engine_services(self, data: Dict[str, Any]) -> List[str]:
        """Transform App Engine services response."""
        services = []
        if "services" in data:
            for service in data["services"]:
                if "id" in service:
                    services.append(service["id"])
        return services
