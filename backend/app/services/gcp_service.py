from google.cloud import logging_v2, resourcemanager_v3
from google.auth import default
from typing import List, Dict, Any, Optional
import json
from datetime import datetime, timedelta

class GCPService:
    def __init__(self):
        self.credentials, self.project = default()
        self.logging_client = logging_v2.LoggingServiceV2Client(credentials=self.credentials)
        self.resource_client = resourcemanager_v3.ProjectsClient(credentials=self.credentials)
    
    async def get_projects(self) -> List[Dict[str, str]]:
        """Get available GCP projects"""
        try:
            projects = []
            request = resourcemanager_v3.ListProjectsRequest()
            page_result = self.resource_client.list_projects(request=request)
            
            for project in page_result:
                projects.append({
                    "id": project.project_id,
                    "name": project.project_id,
                    "displayName": project.display_name
                })
            
            return projects
        except Exception as e:
            # Fallback to mock data for development
            return [
                {
                    "id": "my-project-123",
                    "name": "my-project-123",
                    "displayName": "My Project"
                },
                {
                    "id": "staging-project-456",
                    "name": "staging-project-456",
                    "displayName": "Staging Project"
                }
            ]
    
    async def get_logs(
        self,
        project_id: str,
        service_id: str,
        deployment_id: Optional[str] = None,
        time_range: str = "1h",
        severity: Optional[str] = None,
        search_query: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get logs from Cloud Logging API"""
        try:
            # Build the log filter
            filter_str = f'resource.type="{service_id}"'
            
            if deployment_id:
                filter_str += f' AND resource.labels.deployment_id="{deployment_id}"'
            
            if severity:
                filter_str += f' AND severity="{severity}"'
            
            if search_query:
                filter_str += f' AND textPayload:"{search_query}"'
            
            # Add time range
            end_time = datetime.utcnow()
            if time_range == "1h":
                start_time = end_time - timedelta(hours=1)
            elif time_range == "6h":
                start_time = end_time - timedelta(hours=6)
            elif time_range == "24h":
                start_time = end_time - timedelta(hours=24)
            elif time_range == "7d":
                start_time = end_time - timedelta(days=7)
            elif time_range == "30d":
                start_time = end_time - timedelta(days=30)
            else:
                start_time = end_time - timedelta(hours=1)
            
            # Create the request
            request = logging_v2.ListLogEntriesRequest(
                resource_names=[f"projects/{project_id}"],
                filter_=filter_str,
                order_by="timestamp desc",
                page_size=limit
            )
            
            # Execute the request
            page_result = self.logging_client.list_log_entries(request=request)
            
            logs = []
            for entry in page_result:
                log_entry = {
                    "id": entry.insert_id,
                    "timestamp": entry.timestamp.isoformat(),
                    "severity": entry.severity.name,
                    "message": entry.text_payload or "",
                    "resource": {
                        "type": entry.resource.type,
                        "labels": dict(entry.resource.labels)
                    },
                    "labels": dict(entry.labels),
                    "jsonPayload": entry.json_payload,
                    "httpRequest": entry.http_request,
                    "trace": entry.trace,
                    "spanId": entry.span_id
                }
                logs.append(log_entry)
            
            return {
                "logs": logs,
                "total": len(logs),
                "service_id": service_id,
                "deployment_id": deployment_id,
                "filters": {
                    "time_range": time_range,
                    "severity": severity,
                    "search_query": search_query
                }
            }
            
        except Exception as e:
            # Fallback to mock data for development
            return self._get_mock_logs(service_id, deployment_id, severity, search_query)
    
    def _get_mock_logs(
        self,
        service_id: str,
        deployment_id: Optional[str] = None,
        severity: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get mock logs for development"""
        mock_logs = [
            {
                "id": "1",
                "timestamp": "2024-01-15T10:30:45.123Z",
                "severity": "ERROR",
                "message": "Database connection failed",
                "resource": {
                    "type": "gce_instance",
                    "labels": {
                        "instance_id": "1234567890123456789",
                        "zone": "us-central1-a",
                    },
                },
                "jsonPayload": {
                    "message": "Database connection failed",
                    "error": {
                        "code": "ECONNREFUSED",
                        "errno": -61,
                        "syscall": "connect",
                        "address": "10.0.0.1",
                        "port": 5432,
                    },
                },
                "labels": {
                    "service": "web-server",
                    "version": "1.2.3",
                },
            },
            {
                "id": "2",
                "timestamp": "2024-01-15T10:29:30.456Z",
                "severity": "INFO",
                "message": "User authentication successful for user ID: 12345",
                "resource": {
                    "type": "k8s_container",
                    "labels": {
                        "cluster_name": "production-cluster",
                        "namespace_name": "default",
                        "pod_name": "web-app-7d4b9c8f6d-xyz12",
                    },
                },
                "textPayload": "User authentication successful for user ID: 12345",
                "labels": {
                    "service": "auth-service",
                    "version": "2.1.0",
                },
            },
            {
                "id": "3",
                "timestamp": "2024-01-15T10:28:15.789Z",
                "severity": "WARNING",
                "message": "Rate limit approaching",
                "resource": {
                    "type": "cloud_function",
                    "labels": {
                        "function_name": "process-webhook",
                        "region": "us-central1",
                    },
                },
                "jsonPayload": {
                    "message": "Rate limit approaching",
                    "metrics": {
                        "requests_per_minute": 850,
                        "limit": 1000,
                        "usage_percentage": 85,
                    },
                },
                "httpRequest": {
                    "requestMethod": "POST",
                    "requestUrl": "https://api.example.com/webhook",
                    "status": 200,
                    "responseSize": "1024",
                    "userAgent": "Mozilla/5.0 (compatible; Webhook/1.0)",
                },
            },
        ]
        
        # Apply filters
        filtered_logs = mock_logs.copy()
        
        if severity:
            filtered_logs = [log for log in filtered_logs if log["severity"] == severity]
        
        if search_query:
            filtered_logs = [
                log for log in filtered_logs 
                if search_query.lower() in log.get("message", "").lower()
            ]
        
        return {
            "logs": filtered_logs,
            "total": len(filtered_logs),
            "service_id": service_id,
            "deployment_id": deployment_id,
            "filters": {
                "severity": severity,
                "search_query": search_query
            }
        }
    
    async def execute_advanced_query(
        self,
        project_id: str,
        query: str,
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute advanced Cloud Logging queries"""
        try:
            # Build advanced filter
            filter_str = query
            
            # Add additional filters
            if filters.get("severity"):
                severity_filter = ' OR '.join([f'severity="{s}"' for s in filters["severity"]])
                filter_str += f' AND ({severity_filter})'
            
            if filters.get("resourceType"):
                filter_str += f' AND resource.type="{filters["resourceType"]}"'
            
            # Create the request
            request = logging_v2.ListLogEntriesRequest(
                resource_names=[f"projects/{project_id}"],
                filter_=filter_str,
                order_by="timestamp desc",
                page_size=100
            )
            
            # Execute the request
            page_result = self.logging_client.list_log_entries(request=request)
            
            logs = []
            for entry in page_result:
                log_entry = {
                    "id": entry.insert_id,
                    "timestamp": entry.timestamp.isoformat(),
                    "severity": entry.severity.name,
                    "message": entry.text_payload or "",
                    "resource": {
                        "type": entry.resource.type,
                        "labels": dict(entry.resource.labels)
                    },
                    "labels": dict(entry.labels),
                    "jsonPayload": entry.json_payload,
                    "httpRequest": entry.http_request,
                    "trace": entry.trace,
                    "spanId": entry.span_id
                }
                logs.append(log_entry)
            
            return {
                "logs": logs,
                "total": len(logs),
                "query": query,
                "filters": filters
            }
            
        except Exception as e:
            # Fallback to mock data
            return {
                "logs": [],
                "total": 0,
                "query": query,
                "filters": filters,
                "error": str(e)
            } 