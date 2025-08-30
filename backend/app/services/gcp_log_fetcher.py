from __future__ import annotations

from typing import Any, Dict, List, Optional
import os
import asyncio
import requests
import ssl
import urllib3
from datetime import datetime, timedelta
import json

# Suppress SSL warnings for development
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class GCPLogFetcher:
    """
    Service to fetch logs directly from GCP Cloud Logging REST API.
    Uses the same approach as the working logs.py file.
    """
    
    def __init__(self):
        # We'll get credentials from the calling context
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
        
    async def fetch_logs(
        self,
        project_id: str,
        search_query: str = "",
        resource_filters: Optional[Dict[str, Any]] = None,
        severity_filters: Optional[List[str]] = None,
        time_range: Optional[Dict[str, str]] = None,
        limit: int = 100,
        access_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch logs from GCP Cloud Logging using REST API.
        
        Args:
            project_id: GCP project ID
            search_query: Text search query for log content
            resource_filters: Filters for GCP resources (e.g., {'resource.type': 'cloud_run_revision'})
            severity_filters: List of severity levels to filter by
            time_range: Time range dict with 'start_time' and 'end_time' in ISO format
            limit: Maximum number of logs to return
            access_token: OAuth access token for authentication
            
        Returns:
            Dict containing logs and metadata
        """
        print(f"🔍 GCP Log Fetcher: Starting fetch for project_id={project_id}")
        print(f"🔍 GCP Log Fetcher: search_query={search_query}")
        print(f"🔍 GCP Log Fetcher: resource_filters={resource_filters}")
        print(f"🔍 GCP Log Fetcher: severity_filters={severity_filters}")
        print(f"🔍 GCP Log Fetcher: time_range={time_range}")
        
        try:
            if not access_token:
                print("❌ GCP Log Fetcher: No access token provided")
                return {
                    "success": False,
                    "error": "Access token required for GCP API calls",
                    "logs": [],
                    "total_fetched": 0,
                    "filter_applied": "",
                    "metadata": {
                        "project_id": project_id,
                        "search_query": search_query,
                        "resource_filters": resource_filters,
                        "severity_filters": severity_filters,
                        "time_range": time_range,
                        "limit": limit
                    }
                }
            
            # Validate project_id
            if not project_id or project_id == "None":
                print(f"❌ GCP Log Fetcher: Invalid project_id: {project_id}")
                return {
                    "success": False,
                    "error": f"Invalid project_id: {project_id}",
                    "logs": [],
                    "total_fetched": 0,
                    "filter_applied": "",
                    "metadata": {
                        "project_id": project_id,
                        "search_query": search_query,
                        "resource_filters": resource_filters,
                        "severity_filters": severity_filters,
                        "time_range": time_range,
                        "limit": limit
                    }
                }
            
            # Build the filter string
            filter_string = self._build_filter_string(
                project_id=project_id,
                search_query=search_query,
                resource_filters=resource_filters or {},
                severity_filters=severity_filters or [],
                time_range=time_range or {}
            )
            
            print(f"🔍 GCP Log Fetcher: Built filter: {filter_string}")
            
            # Make REST API call
            url = "https://logging.googleapis.com/v2/entries:list"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }
            
            body = {
                "resourceNames": [f"projects/{project_id}"],
                "filter": filter_string,
                "orderBy": "timestamp desc",
                "pageSize": min(limit, 1000),  # GCP max is 1000
            }
            
            print(f"🔍 GCP Log Fetcher: Making API call to {url}")
            print(f"🔍 GCP Log Fetcher: Request body: {body}")
            
            # Execute the request with SSL bypass for development
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: requests.post(url, headers=headers, json=body, timeout=60, verify=False)
            )
            
            print(f"🔍 GCP Log Fetcher: Response status: {response.status_code}")
            
            if not response.ok:
                try:
                    detail = response.json()
                except Exception:
                    detail = response.text
                print(f"❌ GCP Log Fetcher: API error {response.status_code}: {detail}")
                raise Exception(f"GCP API error {response.status_code}: {detail}")
            
            data = response.json() or {}
            entries = data.get("entries", [])
            
            print(f"🔍 GCP Log Fetcher: Received {len(entries)} entries")
            
            # Process and format the logs
            formatted_logs = []
            for idx, entry in enumerate(entries[:limit]):
                formatted_logs.append(self._format_log_entry(entry, idx))
            
            print(f"🔍 GCP Log Fetcher: Formatted {len(formatted_logs)} logs")
            
            return {
                "success": True,
                "logs": formatted_logs,
                "total_fetched": len(formatted_logs),
                "filter_applied": filter_string,
                "metadata": {
                    "project_id": project_id,
                    "search_query": search_query,
                    "resource_filters": resource_filters,
                    "severity_filters": severity_filters,
                    "time_range": time_range,
                    "limit": limit
                }
            }
            
        except Exception as e:
            print(f"❌ GCP Log Fetcher: Error fetching logs: {e}")
            return {
                "success": False,
                "error": str(e),
                "logs": [],
                "total_fetched": 0,
                "filter_applied": "",
                "metadata": {
                    "project_id": project_id,
                    "search_query": search_query,
                    "resource_filters": resource_filters,
                    "severity_filters": severity_filters,
                    "time_range": time_range,
                    "limit": limit
                }
            }
    
    def _build_filter_string(
        self,
        project_id: str,
        search_query: str,
        resource_filters: Dict[str, Any],
        severity_filters: List[str],
        time_range: Dict[str, str]
    ) -> str:
        """Build the GCP Cloud Logging filter string."""
        filter_parts = []
        
        # Base project filter - include common resource types
        base_resources = [
            "cloud_run_revision", "cloud_function", "gae_app", "k8s_container",
            "gce_instance", "gcs_bucket", "cloudsql_database", "bigquery_dataset",
            "pubsub_topic", "dataflow_job", "vpc_flow_log", "gce_network"
        ]
        
        resource_type_filter = ' OR '.join([f'resource.type="{rt}"' for rt in base_resources])
        filter_parts.append(f'({resource_type_filter})')
        
        # Add search query if provided
        if search_query.strip():
            # Escape quotes and special characters
            escaped_query = search_query.replace('"', '\\"').replace("'", "\\'")
            filter_parts.append(f'textPayload:"{escaped_query}" OR jsonPayload.message:"{escaped_query}" OR jsonPayload.error:"{escaped_query}" OR jsonPayload.exception:"{escaped_query}"')
        
        # Add resource filters
        for key, value in resource_filters.items():
            if key == "resource.type" and value:
                if isinstance(value, list):
                    resource_types = ' OR '.join([f'resource.type="{rt}"' for rt in value])
                    filter_parts.append(f'({resource_types})')
                else:
                    filter_parts.append(f'resource.type="{value}"')
            elif key.startswith("resource.labels.") and value:
                label_key = key.replace("resource.labels.", "")
                if isinstance(value, list):
                    label_values = ' OR '.join([f'resource.labels.{label_key}="{lv}"' for lv in value])
                    filter_parts.append(f'({label_values})')
                else:
                    filter_parts.append(f'resource.labels.{label_key}="{value}"')
            elif key.startswith("labels.") and value:
                label_key = key.replace("labels.", "")
                if isinstance(value, list):
                    label_values = ' OR '.join([f'labels.{label_key}="{lv}"' for lv in value])
                    filter_parts.append(f'({label_values})')
                else:
                    filter_parts.append(f'labels.{label_key}="{value}"')
        
        # Add severity filters
        if severity_filters:
            severity_conditions = []
            for severity in severity_filters:
                severity_conditions.append(f'severity="{severity.upper()}"')
            filter_parts.append(f'({" OR ".join(severity_conditions)})')
        
        # Add time range filters
        if time_range.get("start_time") or time_range.get("end_time"):
            if time_range.get("start_time"):
                filter_parts.append(f'timestamp>="{time_range["start_time"]}"')
            if time_range.get("end_time"):
                filter_parts.append(f'timestamp<="{time_range["end_time"]}"')
        
        # Combine all filters with AND
        return " AND ".join(filter_parts)
    
    def _format_log_entry(self, entry: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Format a GCP log entry from REST API response."""
        timestamp = entry.get("timestamp")
        severity = entry.get("severity", "DEFAULT")
        json_payload = entry.get("jsonPayload")
        text_payload = entry.get("textPayload")
        
        # Extract message
        message = None
        if isinstance(json_payload, dict):
            message = json_payload.get("message") or str(json_payload)
        elif isinstance(text_payload, str):
            message = text_payload
        else:
            message = str(json_payload or text_payload or "")
        
        # Extract resource info
        resource = entry.get("resource") or {}
        resource_type = resource.get("type", "") if isinstance(resource, dict) else ""
        resource_labels = resource.get("labels", {}) if isinstance(resource, dict) else {}
        
        formatted = {
            "id": entry.get("insertId") or f"entry_{index}",
            "insertId": entry.get("insertId"),
            "timestamp": timestamp,
            "severity": str(severity),
            "resource": {
                "type": resource_type,
                "labels": dict(resource_labels) if isinstance(resource_labels, dict) else {}
            },
            "labels": dict(entry.get("labels", {})) if isinstance(entry.get("labels"), dict) else {},
            "trace": entry.get("trace"),
            "spanId": entry.get("spanId"),
            "traceSampled": entry.get("traceSampled"),
            "sourceLocation": entry.get("sourceLocation"),
            "operation": entry.get("operation"),
            "httpRequest": entry.get("httpRequest"),
            "message": message,
            "textPayload": text_payload if isinstance(text_payload, str) else None,
            "jsonPayload": json_payload if isinstance(json_payload, dict) else None,
            "protoPayload": entry.get("protoPayload"),
            "logName": entry.get("logName"),
            "projectId": entry.get("projectId")
        }
        
        return formatted
    
    async def get_available_resource_types(self, project_id: str, access_token: str) -> List[str]:
        """Get list of available resource types in the project."""
        try:
            # Try to fetch a small sample of logs to see what resource types exist
            url = "https://logging.googleapis.com/v2/entries:list"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }
            
            body = {
                "resourceNames": [f"projects/{project_id}"],
                "filter": "resource.type:*",
                "pageSize": 100,
                "orderBy": "timestamp desc"
            }
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: requests.post(url, headers=headers, json=body, timeout=30, verify=False)
            )
            
            if not response.ok:
                return []
            
            data = response.json() or {}
            entries = data.get("entries", [])
            
            resource_types = set()
            for entry in entries:
                resource = entry.get("resource", {})
                if isinstance(resource, dict) and resource.get("type"):
                    resource_types.add(resource["type"])
            
            return list(resource_types)
            
        except Exception as e:
            print(f"Error getting available resource types: {e}")
            return []
    
    async def get_log_statistics(
        self,
        project_id: str,
        access_token: str,
        time_range: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Get statistics about logs in the project."""
        try:
            # Build time filter
            time_filter = ""
            if time_range:
                if time_range.get("start_time"):
                    time_filter += f' AND timestamp>="{time_range["start_time"]}"'
                if time_range.get("end_time"):
                    time_filter += f' AND timestamp<="{time_range["end_time"]}"'
            
            # Get severity distribution by sampling
            severity_stats = {}
            for severity in ["DEFAULT", "DEBUG", "INFO", "NOTICE", "WARNING", "ERROR", "CRITICAL", "ALERT", "EMERGENCY"]:
                try:
                    severity_filter = f'severity="{severity}"{time_filter}'
                    url = "https://logging.googleapis.com/v2/entries:list"
                    headers = {
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                    }
                    
                    body = {
                        "resourceNames": [f"projects/{project_id}"],
                        "filter": severity_filter,
                        "pageSize": 1
                    }
                    
                    response = await asyncio.get_event_loop().run_in_executor(
                        None, 
                        lambda: requests.post(url, headers=headers, json=body, timeout=30, verify=False)
                    )
                    
                    if response.ok:
                        data = response.json() or {}
                        entries = data.get("entries", [])
                        severity_stats[severity] = len(entries)
                    else:
                        severity_stats[severity] = 0
                        
                except Exception:
                    severity_stats[severity] = 0
            
            return {
                "success": True,
                "project_id": project_id,
                "severity_distribution": severity_stats,
                "time_range": time_range,
                "note": "Statistics are approximate based on sample queries"
            }
            
        except Exception as e:
            print(f"Error getting log statistics: {e}")
            return {
                "success": False,
                "error": str(e),
                "project_id": project_id
            }
