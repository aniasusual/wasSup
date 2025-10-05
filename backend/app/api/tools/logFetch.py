"""
GCP Cloud Logging Helper Module

This module provides utilities for fetching logs from Google Cloud Logging API.
The LLM agent decides what filters to use and calls this tool directly.
"""

from typing import Callable, Optional, Dict, List, Any
import requests
from fastapi import HTTPException, status
from agno.tools import tool

def logger_hook(function_name: str, function_call: Callable, arguments: Dict[str, Any]):
    """Hook function that wraps the tool execution"""
    print(f"About to call {function_name} with arguments: {arguments}")
    result = function_call(**arguments)
    print(f"Function call completed with result: {result}")
    return result

class GCPLoggingHelper:
    """Helper class for interacting with GCP Cloud Logging API."""
    
    BASE_URL = "https://logging.googleapis.com/v2/entries:list"
    
    def __init__(self, access_token: str, project_id: str):
        """
        Initialize the GCP Logging Helper.
        
        Args:
            access_token: GCP OAuth2 access token
            project_id: GCP project ID
        """
        self.access_token = access_token
        self.project_id = project_id
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }



    @tool(tool_hooks=[logger_hook],show_result=True)
    def fetch_logs(
        self,
        filter_str: str,
        order_by: str = "timestamp desc",
        page_size: int = 100,
        page_token: Optional[str] = None,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """
        Fetch logs from GCP Cloud Logging API.
        
        This method is called directly by the LLM agent with the filter string
        it constructs based on the investigation context.
        
        """
        body = {
            "resourceNames": [f"projects/{self.project_id}"],
            "filter": filter_str,
            "orderBy": order_by,
            "pageSize": min(page_size, 1000),  # API max is 1000
        }
        
        if page_token:
            body["pageToken"] = page_token
        
        try:
            response = requests.post(
                self.BASE_URL,
                headers=self.headers,
                json=body,
                timeout=timeout
            )
            response.raise_for_status()
            result = response.json()
            
            # Add basic summary
            entries = result.get("entries", [])
            result["summary"] = self._generate_basic_summary(entries)

            print(f"result: {result}")
            
            return result
            
        except requests.exceptions.Timeout:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Request to GCP Cloud Logging API timed out"
            )
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.text if hasattr(e, 'response') else str(e)
            raise HTTPException(
                status_code=e.response.status_code if hasattr(e, 'response') else status.HTTP_502_BAD_GATEWAY,
                detail=f"GCP Cloud Logging API error: {error_detail}"
            )
        except requests.exceptions.RequestException as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to fetch logs from GCP: {str(e)}"
            )
    
    def _generate_basic_summary(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate basic summary statistics from log entries.
        
        Args:
            entries: List of log entries
            
        Returns:
            Dict containing basic statistics
        """
        if not entries:
            return {"total_entries": 0}
        
        severity_counts = {}
        resource_types = set()
        
        for entry in entries:
            # Count severities
            severity = entry.get("severity", "DEFAULT")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Collect resource types
            resource = entry.get("resource", {})
            resource_type = resource.get("type")
            if resource_type:
                resource_types.add(resource_type)
        
        return {
            "total_entries": len(entries),
            "severity_counts": severity_counts,
            "resource_types": list(resource_types),
        }


def get_logging_helper(access_token: str, project_id: str) -> GCPLoggingHelper:
    """
    Factory function to create a GCPLoggingHelper instance.
    
    Args:
        access_token: GCP OAuth2 access token
        project_id: GCP project ID
        
    Returns:
        Configured GCPLoggingHelper instance
    """
    return GCPLoggingHelper(access_token=access_token, project_id=project_id)