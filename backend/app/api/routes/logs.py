from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from typing import List, Any
import os
import json
from datetime import datetime
from google.cloud import logging as gcp_logging
from google.oauth2.credentials import Credentials
from google.cloud import resourcemanager_v3

from ..helpers.authHelper import get_current_user,get_user_tokens, is_token_expired
from ..routes.auth import refresh_token
from fastapi import Body


import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

from ..data.gcpApiEndpoints import GCP_API_ENDPOINTS



router = APIRouter(tags=["logs"])
logger = logging.getLogger(__name__)


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


@router.post("/logs/fetch")
async def fetch_logs(query: Any = Body(...), current_user: str = Depends(get_current_user)):
    """
    Fetch logs from GCP and return in frontend-compatible format (logs, nextPageToken, totalEntries).
    """
    user_token_data = await get_user_tokens(current_user)
    if not user_token_data:
        raise HTTPException(status_code=401, detail="User not authenticated")

    if is_token_expired(current_user):
        await refresh_token(current_user)
        user_token_data = await get_user_tokens(current_user)

    def fetch_logs_sync():
        try:
            # Build request to Logging REST API to reliably capture nextPageToken
            import requests

            filter_str = query.get("filter", "")
            page_size = query.get("pageSize", 1000)
            page_token = query.get("pageToken", None)
            order_by = query.get("orderBy", "timestamp desc")
            project_id = query["projectId"]


            logger.info(
                f"Fetching logs via REST with filter: {filter_str}, page_size: {page_size}, page_token: {page_token}"
            )

            url = "https://logging.googleapis.com/v2/entries:list"
            headers = {
                "Authorization": f"Bearer {user_token_data['access_token']}",
                "Content-Type": "application/json",
            }
            body = {
                "resourceNames": [f"projects/{project_id}"],
                "filter": filter_str,
                "orderBy": order_by,
                "pageSize": page_size,
            }
            if page_token:
                body["pageToken"] = page_token

            resp = requests.post(url, headers=headers, json=body, timeout=60)
            if not resp.ok:
                try:
                    detail = resp.json()
                except Exception:
                    detail = resp.text
                raise HTTPException(status_code=resp.status_code, detail=str(detail))

            data = resp.json() or {}
            entries = data.get("entries", [])
            next_page_token = data.get("nextPageToken")

            logs = []
            for idx, entry in enumerate(entries):
                # entry is a dict from REST response
                timestamp = entry.get("timestamp")
                severity = entry.get("severity", "DEFAULT")
                json_payload = entry.get("jsonPayload")
                text_payload = entry.get("textPayload")
                message = None
                if isinstance(json_payload, dict):
                    message = json_payload.get("message") or str(json_payload)
                elif isinstance(text_payload, str):
                    message = text_payload
                else:
                    message = str(json_payload or text_payload or "")

                resource = entry.get("resource") or {}
                resource_type = resource.get("type", "") if isinstance(resource, dict) else ""
                resource_labels = resource.get("labels", {}) if isinstance(resource, dict) else {}

                logs.append(
                    {
                        "id": entry.get("insertId") or f"entry_{idx}",
                        "timestamp": timestamp,
                        "severity": str(severity),
                        "message": message,
                        "resource": {
                            "type": resource_type,
                            "labels": dict(resource_labels) if isinstance(resource_labels, dict) else {},
                        },
                        "labels": dict(entry.get("labels", {})) if isinstance(entry.get("labels"), dict) else {},
                        "jsonPayload": json_payload if isinstance(json_payload, dict) else None,
                        "textPayload": text_payload if isinstance(text_payload, str) else None,
                        "httpRequest": entry.get("httpRequest"),
                        "traceId": entry.get("trace"),
                        "spanId": entry.get("spanId"),
                        "logName": entry.get("logName"),
                        "projectId": project_id,
                    }
                )

            logger.info(f"Successfully fetched {len(logs)} logs via REST")



            return {
                "logs": logs,
                "nextPageToken": next_page_token,
                "totalEntries": len(logs),
            }

        except Exception as e:
            logger.error(f"Error in fetch_logs_sync: {str(e)}", exc_info=True)
            raise e

    try:
        # Run the synchronous GCP call in a thread pool to avoid blocking
        with ThreadPoolExecutor() as executor:
            result = await asyncio.get_event_loop().run_in_executor(
                executor, fetch_logs_sync
            )
        return result

    except Exception as e:
        logger.error(f"Error fetching logs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching logs: {str(e)}")
    

    
@router.get("/logs/projects")
async def get_projects(current_user: str = Depends(get_current_user)):
    """Get list of GCP projects accessible to the user"""
    user_token_data = await get_user_tokens(current_user)
    if not user_token_data:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    # Check if token is expired
    if is_token_expired(current_user):
        # Try to refresh
        await refresh_token(current_user)
        user_token_data = await get_user_tokens(current_user)
    
    try:
        # Create credentials from token
        credentials = Credentials(
            token=user_token_data["access_token"],
            refresh_token=user_token_data.get("refresh_token"),
            token_uri=GOOGLE_TOKEN_URL,
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET
        )
        
        # Create resource manager client
        client = resourcemanager_v3.ProjectsClient(credentials=credentials)
        
        # List projects
        request = resourcemanager_v3.ListProjectsRequest()
        projects = []
        
        page_result = client.list_projects(request=request)
        for project in page_result:
            projects.append({
                "project_id": project.project_id,
                "name": project.display_name,
                "state": project.state.name
            })
        
        return {"projects": projects}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching projects: {str(e)}")


@router.post("/logs/gcp-resource-options")
async def gcp_resource_options(
    request: dict = Body(...),
    current_user: str = Depends(get_current_user)
):
    """
    Fetch GCP resource options for a given resourceType and label using backend GCP_API_ENDPOINTS config.
    Handles dependencies for nested endpoints (e.g., serviceName, version, etc).
    """
    try:
        # Extract parameters from request body
        resourceType = request.get("resourceType")
        label = request.get("label") 
        projectId = request.get("projectId")
        dependencies = request.get("dependencies", {})
        
        if not resourceType or not label or not projectId:
            return {"options": [], "message": "Missing required parameters: resourceType, label, or projectId"}
        
        user_token_data = await get_user_tokens(current_user)
        if not user_token_data:
            raise HTTPException(status_code=401, detail="User not authenticated")
            
        if is_token_expired(current_user):
            await refresh_token(current_user)
            user_token_data = await get_user_tokens(current_user)
        
        # Find the API config for this resourceType and label
        api_config = GCP_API_ENDPOINTS.get(resourceType, {}).get(label)
        if not api_config or not api_config.get("endpoint"):
            return {"options": [], "message": f"No API endpoint configured for {resourceType}.{label}"}
        
        # Build the endpoint URL, handling dependencies
        endpoint_func = api_config["endpoint"]
        
        # Handle special cases where no API call is needed
        if endpoint_func is None or (isinstance(endpoint_func, str) and endpoint_func.startswith("#")):
            # Handle static data cases like uptime check locations
            transform_func = api_config.get("transform")
            if transform_func:
                options = transform_func({})
                return {"options": options, "message": "Static data"}
            return {"options": [], "message": "No data available"}
        
        # Compose args for endpoint function
        args = [projectId]
        depends_on = api_config.get("depends_on")  # Note: should be "depends_on", not "dependsOn"
        
        if depends_on:
            if isinstance(depends_on, str):
                dep_val = dependencies.get(depends_on)
                if not dep_val:
                    return {"options": [], "message": f"Dependency '{depends_on}' not provided"}
                args.append(dep_val)
            elif isinstance(depends_on, list):
                for dep in depends_on:
                    dep_val = dependencies.get(dep)
                    if not dep_val:
                        return {"options": [], "message": f"Dependency '{dep}' not provided"}
                    args.append(dep_val)
        
        # Generate endpoint URL
        try:
            endpoint_url = endpoint_func(*args)
        except Exception as e:
            return {"options": [], "message": f"Failed to generate endpoint URL: {str(e)}"}
        
        if isinstance(endpoint_url, str) and endpoint_url.startswith("#"):
            return {"options": [], "message": f"API not available: {endpoint_url}"}
        
        # Make the request to Google API
        import requests
        headers = {
            "Authorization": f"Bearer {user_token_data['access_token']}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(endpoint_url, headers=headers, timeout=30)
        
        
        if not response.ok:
            error_msg = f"API call failed: {response.status_code}"
            try:
                error_detail = response.json()
                error_msg += f" - {error_detail}"
            except:
                error_msg += f" - {response.text[:200]}"
            return {"options": [], "message": error_msg}
        
        try:
            data = response.json()
        except Exception as e:
            return {"options": [], "message": f"Failed to parse JSON response: {str(e)}"}
        
        # Transform the data using the transform function
        transform_func = api_config.get("transform")
        if transform_func:
            try:
                options = transform_func(data)
            except Exception as e:
                return {"options": [], "message": f"Transform function failed: {str(e)}"}
        else:
            # If no transform function, try to extract common patterns
            if isinstance(data, dict):
                if "items" in data:
                    options = [item.get("name", item.get("id", str(item))) for item in data["items"] if isinstance(item, dict)]
                elif "services" in data:
                    options = [item.get("name", item.get("id", str(item))) for item in data["services"] if isinstance(item, dict)]
                elif "clusters" in data:
                    options = [item.get("name", item.get("id", str(item))) for item in data["clusters"] if isinstance(item, dict)]
                else:
                    options = list(data.keys()) if data else []
            else:
                options = data if isinstance(data, list) else []
        
        # Ensure options is a list of strings
        if not isinstance(options, list):
            options = []
        
        # Filter out None, empty strings, and ensure all items are strings
        options = [str(opt) for opt in options if opt is not None and str(opt).strip()]
        
        
        return {
            "options": options, 
            "message": f"success - {len(options)} items found",
            "debug": {
                "endpoint": endpoint_url,
                "raw_data_keys": list(data.keys()) if isinstance(data, dict) else "not_dict",
                "transform_used": transform_func is not None
            }
        }
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        return {"options": [], "message": f"Unexpected error: {str(e)}"}
    