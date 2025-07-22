from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import List, Any
import os
import json
from datetime import datetime
from google.cloud import logging as gcp_logging
from google.oauth2.credentials import Credentials
from google.cloud import resourcemanager_v3
# from ...models.models import LogEntry, LogQuery
from ..helpers.authHelper import get_current_user,get_user_tokens, is_token_expired
from ..routes.auth import refresh_token
from fastapi import Body
# from ...services.deployment_service import GCPDeploymentService

router = APIRouter(tags=["logs"])

# Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Google OAuth2 URLs
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

# GCP Logs endpoints
# 
# UNIFIED FLOW:
# 1. User applies filter -> POST /logs/query (returns both display logs and analysis data)
# 2. Frontend displays logs from response.logs
# 3. User asks question -> POST /logs/analyze (uses response.analysis_data from step 1)
# 
# This ensures the same filtered logs are used for both display and analysis.

@router.post("/logs/query")
async def query_logs(query: Any = Body(...), current_user: str = Depends(get_current_user)):
    """Query GCP logs with pagination - returns both display logs and analysis data"""
    print("query", query)
    
    user_token_data = get_user_tokens(current_user)
    if not user_token_data:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    # Check if token is expired
    if is_token_expired(current_user):
        # Try to refresh
        await refresh_token(current_user)
        user_token_data = get_user_tokens(current_user)
    
    try:
        # Create credentials from token
        credentials = Credentials(
            token=user_token_data["access_token"],
            refresh_token=user_token_data.get("refresh_token"),
            token_uri=GOOGLE_TOKEN_URL,
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET
        )

        # Create logging client
        client = gcp_logging.Client(
            project=query["project_id"],
            credentials=credentials
        )
        
        # Build filter
        filter_str = query.get("filter", "")
        
        # Pagination parameters
        page_size = min(query.get("page_size", 50), 100)  # Cap at 100
        page_token = query.get("page_token", None)
        
        # List entries with pagination
        entries = client.list_entries(
            filter_=filter_str,
            order_by=query.get("order_by", "timestamp desc"),
            page_size=page_size,
            page_token=page_token
        )

        # Convert to response format with essential data only
        logs = []
        analysis_data = {
            "total_entries": 0,
            "severity_distribution": {},
            "resource_types": set(),
            "time_range": {"earliest": None, "latest": None},
            "error_count": 0,
            "warning_count": 0,
            "info_count": 0,
            "logs_for_analysis": []
        }
        
        for entry in entries:
            # Create display log entry
            log_entry = {
                "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
                "severity": str(entry.severity or "DEFAULT"),
                "message": entry.payload.get("message", str(entry.payload)) if isinstance(entry.payload, dict) else str(entry.payload),
                "resource_type": entry.resource.type if entry.resource else None,
                "resource_labels": entry.resource.labels if entry.resource else {},
                "labels": entry.labels or {},
                "insertId": entry.insert_id,
                "logName": entry.log_name
            }
            logs.append(log_entry)

            print("log_entry", log_entry)
            
            # Build analysis data
            analysis_data["total_entries"] += 1
            severity = str(entry.severity or "DEFAULT")
            
            # Track severity distribution
            analysis_data["severity_distribution"][severity] = analysis_data["severity_distribution"].get(severity, 0) + 1
            
            # Track resource types
            if entry.resource and entry.resource.type:
                analysis_data["resource_types"].add(entry.resource.type)
            
            # Track time range
            if entry.timestamp:
                if not analysis_data["time_range"]["earliest"] or entry.timestamp < analysis_data["time_range"]["earliest"]:
                    analysis_data["time_range"]["earliest"] = entry.timestamp
                if not analysis_data["time_range"]["latest"] or entry.timestamp > analysis_data["time_range"]["latest"]:
                    analysis_data["time_range"]["latest"] = entry.timestamp
            
            # Count by severity
            if severity.upper() in ["ERROR", "CRITICAL"]:
                analysis_data["error_count"] += 1
            elif severity.upper() == "WARNING":
                analysis_data["warning_count"] += 1
            elif severity.upper() == "INFO":
                analysis_data["info_count"] += 1
            
            # Store for analysis (same data as display but structured for agent)
            analysis_data["logs_for_analysis"].append(log_entry)

        # Convert sets to lists for JSON serialization
        analysis_data["resource_types"] = list(analysis_data["resource_types"])
        
        # Convert timestamps to ISO format
        if analysis_data["time_range"]["earliest"]:
            analysis_data["time_range"]["earliest"] = analysis_data["time_range"]["earliest"].isoformat()
        if analysis_data["time_range"]["latest"]:
            analysis_data["time_range"]["latest"] = analysis_data["time_range"]["latest"].isoformat()

        # Get next page token if available
        next_page_token = None
        if hasattr(entries, 'next_page_token') and entries.next_page_token:
            next_page_token = entries.next_page_token

        return {
            "logs": logs,  # For display
            "analysis_data": analysis_data,  # For agent analysis
            "pagination": {
                "next_page_token": next_page_token,
                "page_size": page_size,
                "has_more": next_page_token is not None
            },
            "metadata": {
                "total_entries": len(logs),
                "filter_applied": filter_str,
                "project_id": query["project_id"]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying logs: {str(e)}")

# @router.get("/logs/projects")
# async def get_projects(current_user: str = Depends(get_current_user)):
#     """Get list of GCP projects accessible to the user"""
#     user_token_data = get_user_tokens(current_user)
#     if not user_token_data:
#         raise HTTPException(status_code=401, detail="User not authenticated")
    
#     # Check if token is expired
#     if is_token_expired(current_user):
#         # Try to refresh
#         await refresh_token(current_user)
#         user_token_data = get_user_tokens(current_user)
    
#     try:
#         # Create credentials from token
#         credentials = Credentials(
#             token=user_token_data["access_token"],
#             refresh_token=user_token_data.get("refresh_token"),
#             token_uri=GOOGLE_TOKEN_URL,
#             client_id=GOOGLE_CLIENT_ID,
#             client_secret=GOOGLE_CLIENT_SECRET
#         )
        
#         # Create resource manager client
#         client = resourcemanager_v3.ProjectsClient(credentials=credentials)
        
#         # List projects
#         request = resourcemanager_v3.ListProjectsRequest()
#         projects = []
        
#         page_result = client.list_projects(request=request)
#         for project in page_result:
#             projects.append({
#                 "project_id": project.project_id,
#                 "name": project.display_name,
#                 "state": project.state.name
#             })
        
#         return {"projects": projects}
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error fetching projects: {str(e)}")

# @router.post("/logs/summary")
# async def get_log_summary(query: Any = Body(...), current_user: str = Depends(get_current_user)):
#     """Get log summary for agent analysis - returns aggregated data instead of raw logs"""
#     user_token_data = get_user_tokens(current_user)
#     if not user_token_data:
#         raise HTTPException(status_code=401, detail="User not authenticated")
    
#     # Check if token is expired
#     if is_token_expired(current_user):
#         await refresh_token(current_user)
#         user_token_data = get_user_tokens(current_user)
    
#     try:
#         credentials = Credentials(
#             token=user_token_data["access_token"],
#             refresh_token=user_token_data.get("refresh_token"),
#             token_uri=GOOGLE_TOKEN_URL,
#             client_id=GOOGLE_CLIENT_ID,
#             client_secret=GOOGLE_CLIENT_SECRET
#         )

#         client = gcp_logging.Client(
#             project=query["project_id"],
#             credentials=credentials
#         )
        
#         filter_str = query.get("filter", "")
        
#         # Get a larger sample for analysis (but still paginated)
#         page_size = min(query.get("page_size", 1000), 2000)  # Larger for analysis
#         page_token = query.get("page_token", None)
        
#         entries = client.list_entries(
#             filter_=filter_str,
#             order_by=query.get("order_by", "timestamp desc"),
#             page_size=page_size,
#             page_token=page_token
#         )

#         # Create summary data for agent analysis
#         summary = {
#             "total_entries": 0,
#             "severity_distribution": {},
#             "resource_types": set(),
#             "time_range": {"earliest": None, "latest": None},
#             "common_patterns": [],
#             "error_count": 0,
#             "warning_count": 0,
#             "info_count": 0
#         }
        
#         logs_for_analysis = []
        
#         for entry in entries:
#             summary["total_entries"] += 1
            
#             # Track severity
#             severity = str(entry.severity or "DEFAULT")
#             summary["severity_distribution"][severity] = summary["severity_distribution"].get(severity, 0) + 1
            
#             # Track resource types
#             if entry.resource and entry.resource.type:
#                 summary["resource_types"].add(entry.resource.type)
            
#             # Track time range
#             if entry.timestamp:
#                 if not summary["time_range"]["earliest"] or entry.timestamp < summary["time_range"]["earliest"]:
#                     summary["time_range"]["earliest"] = entry.timestamp
#                 if not summary["time_range"]["latest"] or entry.timestamp > summary["time_range"]["latest"]:
#                     summary["time_range"]["latest"] = entry.timestamp
            
#             # Count by severity
#             if severity.upper() in ["ERROR", "CRITICAL"]:
#                 summary["error_count"] += 1
#             elif severity.upper() == "WARNING":
#                 summary["warning_count"] += 1
#             elif severity.upper() == "INFO":
#                 summary["info_count"] += 1
            
#             # Store essential data for analysis
#             log_data = {
#                 "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
#                 "severity": severity,
#                 "message": entry.payload.get("message", str(entry.payload)) if isinstance(entry.payload, dict) else str(entry.payload),
#                 "resource_type": entry.resource.type if entry.resource else None,
#                 "labels": entry.labels or {},
#                 "logName": entry.log_name
#             }
#             logs_for_analysis.append(log_data)

#         # Convert sets to lists for JSON serialization
#         summary["resource_types"] = list(summary["resource_types"])
        
#         # Convert timestamps to ISO format
#         if summary["time_range"]["earliest"]:
#             summary["time_range"]["earliest"] = summary["time_range"]["earliest"].isoformat()
#         if summary["time_range"]["latest"]:
#             summary["time_range"]["latest"] = summary["time_range"]["latest"].isoformat()

#         # Get next page token
#         next_page_token = None
#         if hasattr(entries, 'next_page_token') and entries.next_page_token:
#             next_page_token = entries.next_page_token

#         return {
#             "summary": summary,
#             "logs_for_analysis": logs_for_analysis,
#             "pagination": {
#                 "next_page_token": next_page_token,
#                 "page_size": page_size,
#                 "has_more": next_page_token is not None
#             },
#             "metadata": {
#                 "filter_applied": filter_str,
#                 "project_id": query["project_id"]
#             }
#         }
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error getting log summary: {str(e)}")

# @router.post("/logs/stream")
# async def stream_logs(query: Any = Body(...), current_user: str = Depends(get_current_user)):
#     """Stream logs for large datasets - returns data as it's processed"""
#     user_token_data = get_user_tokens(current_user)
#     if not user_token_data:
#         raise HTTPException(status_code=401, detail="User not authenticated")
    
#     if is_token_expired(current_user):
#         await refresh_token(current_user)
#         user_token_data = get_user_tokens(current_user)
    
#     try:
#         credentials = Credentials(
#             token=user_token_data["access_token"],
#             refresh_token=user_token_data.get("refresh_token"),
#             token_uri=GOOGLE_TOKEN_URL,
#             client_id=GOOGLE_CLIENT_ID,
#             client_secret=GOOGLE_CLIENT_SECRET
#         )

#         client = gcp_logging.Client(
#             project=query["project_id"],
#             credentials=credentials
#         )
        
#         filter_str = query.get("filter", "")
#         page_size = min(query.get("page_size", 100), 500)  # Reasonable chunk size
        
#         def generate_log_stream():
#             """Generator function to stream logs"""
#             try:
#                 entries = client.list_entries(
#                     filter_=filter_str,
#                     order_by=query.get("order_by", "timestamp desc"),
#                     page_size=page_size
#                 )
                
#                 # Send initial metadata
#                 yield f"data: {json.dumps({'type': 'metadata', 'status': 'started'})}\n\n"
                
#                 count = 0
#                 for entry in entries:
#                     log_entry = {
#                         "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
#                         "severity": str(entry.severity or "DEFAULT"),
#                         "message": entry.payload.get("message", str(entry.payload)) if isinstance(entry.payload, dict) else str(entry.payload),
#                         "resource_type": entry.resource.type if entry.resource else None,
#                         "resource_labels": entry.resource.labels if entry.resource else {},
#                         "labels": entry.labels or {},
#                         "insertId": entry.insert_id,
#                         "logName": entry.log_name
#                     }
                    
#                     yield f"data: {json.dumps({'type': 'log', 'data': log_entry})}\n\n"
#                     count += 1
                    
#                     # Send progress updates every 100 entries
#                     if count % 100 == 0:
#                         yield f"data: {json.dumps({'type': 'progress', 'count': count})}\n\n"
                
#                 # Send completion signal
#                 yield f"data: {json.dumps({'type': 'complete', 'total_count': count})}\n\n"
                
#             except Exception as e:
#                 yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        
#         return StreamingResponse(
#             generate_log_stream(),
#             media_type="text/plain",
#             headers={
#                 "Cache-Control": "no-cache",
#                 "Connection": "keep-alive",
#                 "Content-Type": "text/event-stream"
#             }
#         )
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error streaming logs: {str(e)}")

@router.post("/logs/analyze")
async def analyze_logs(query: Any = Body(...), current_user: str = Depends(get_current_user)):
    """Agent endpoint for log analysis - works with analysis data from query endpoint"""
    user_token_data = get_user_tokens(current_user)
    if not user_token_data:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    if is_token_expired(current_user):
        await refresh_token(current_user)
        user_token_data = get_user_tokens(current_user)
    
    try:
        # Extract analysis parameters
        analysis_question = query.get("question", "")
        analysis_data = query.get("analysis_data", {})
        filter_applied = query.get("filter_applied", "")
        project_id = query.get("project_id", "")
        
        if not analysis_data or not analysis_data.get("logs_for_analysis"):
            raise HTTPException(status_code=400, detail="No analysis data provided. Please query logs first.")
        
        # Prepare data for agent analysis
        agent_analysis_data = {
            "question": analysis_question,
            "filter_applied": filter_applied,
            "project_id": project_id,
            "logs": analysis_data["logs_for_analysis"],
            "summary": {
                "total_entries": analysis_data["total_entries"],
                "severity_distribution": analysis_data["severity_distribution"],
                "resource_types": analysis_data["resource_types"],
                "time_range": analysis_data["time_range"],
                "error_count": analysis_data["error_count"],
                "warning_count": analysis_data["warning_count"],
                "info_count": analysis_data["info_count"]
            }
        }

        # TODO: Here you would integrate with your AI agent
        # The agent can now analyze the same logs that are displayed to the user
        return {
            "analysis_data": agent_analysis_data,
            "agent_ready": True,
            "message": f"Log data prepared for agent analysis. {len(analysis_data['logs_for_analysis'])} logs available for analysis.",
            "metadata": {
                "logs_analyzed": len(analysis_data["logs_for_analysis"]),
                "question": analysis_question,
                "filter_applied": filter_applied,
                "project_id": project_id,
                "summary_stats": {
                    "total_entries": analysis_data["total_entries"],
                    "error_count": analysis_data["error_count"],
                    "warning_count": analysis_data["warning_count"],
                    "info_count": analysis_data["info_count"]
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing logs: {str(e)}")

# @router.get("/logs/deployments/{project_id}/{service_id}")
# async def get_deployments(project_id: str, service_id: str, current_user: str = Depends(get_current_user)):
#     """Get deployments/instances for a specific GCP service"""
#     user_token_data = get_user_tokens(current_user)
#     if not user_token_data:
#         raise HTTPException(status_code=401, detail="User not authenticated")
    
#     # Check if token is expired
#     if is_token_expired(current_user):
#         # Try to refresh
#         await refresh_token(current_user)
#         user_token_data = get_user_tokens(current_user)
    
#     try:
#         # Create credentials from token
#         credentials = Credentials(
#             token=user_token_data["access_token"],
#             refresh_token=user_token_data.get("refresh_token"),
#             token_uri=GOOGLE_TOKEN_URL,
#             client_id=GOOGLE_CLIENT_ID,
#             client_secret=GOOGLE_CLIENT_SECRET
#         )

#         # Create deployment service
#         deployment_service = GCPDeploymentService(credentials)
#         print("deployment_service", deployment_service)
        
#         # Get deployments for the specified service
#         deployments = await deployment_service.get_deployments(project_id, service_id)
        
#         return {
#             "deployments": deployments,
#             "service_id": service_id,
#             "project_id": project_id,
#             "count": len(deployments)
#         }
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error fetching deployments: {str(e)}")
