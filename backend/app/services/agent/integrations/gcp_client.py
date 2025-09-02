# """
# GCP Logging Client

# Handles all interactions with Google Cloud Platform Logging API,
# including pagination, error handling, and log parsing.
# """

# import asyncio
# import json
# import logging
# import requests
# from concurrent.futures import ThreadPoolExecutor
# from typing import Any, Dict, List, Optional, AsyncGenerator

# from ..core.state import LogEntry


# logger = logging.getLogger(__name__)


# class GCPLoggingClient:
#     """Client for interacting with GCP Logging API."""
    
#     def __init__(self):
#         self.base_url = "https://logging.googleapis.com/v2/entries:list"
#         self.max_pages = 50  # Safety limit to prevent infinite loops
#         self.page_size = 1000  # Maximum page size for GCP Logging API
#         self.timeout = 60  # Request timeout in seconds
    
#     async def fetch_logs(
#         self,
#         project_id: str,
#         filter_str: str,
#         access_token: str,
#         limit: int = 100,
#         fetch_all: bool = True
#     ) -> List[Dict[str, Any]]:
#         """
#         Fetch logs from GCP Logging API with comprehensive pagination support.
        
#         Args:
#             project_id: GCP project ID
#             filter_str: GCP logging filter string
#             access_token: OAuth2 access token
#             limit: Maximum number of logs to fetch (ignored if fetch_all=True)
#             fetch_all: Whether to fetch all available logs
            
#         Returns:
#             List of parsed log entries
#         """
#         def fetch_logs_sync():
#             return self._fetch_logs_sync(project_id, filter_str, access_token, limit, fetch_all)
        
#         try:
#             with ThreadPoolExecutor() as executor:
#                 result = await asyncio.get_event_loop().run_in_executor(
#                     executor, fetch_logs_sync
#                 )
#             return result
#         except Exception as e:
#             logger.error(f"Error fetching logs from GCP: {str(e)}")
#             return []
    
#     async def fetch_logs_with_streaming(
#         self,
#         project_id: str,
#         filter_str: str,
#         access_token: str,
#         limit: int = 100,
#         fetch_all: bool = True
#     ) -> AsyncGenerator[str, None]:
#         """
#         Fetch logs with streaming progress updates.
        
#         Yields:
#             Progress update strings in SSE format
#         """
#         def fetch_logs_sync():
#             return self._fetch_logs_sync_with_updates(
#                 project_id, filter_str, access_token, limit, fetch_all
#             )
        
#         try:
#             with ThreadPoolExecutor() as executor:
#                 result = await asyncio.get_event_loop().run_in_executor(
#                     executor, fetch_logs_sync
#                 )
            
#             # Yield all updates
#             for update in result:
#                 yield update
                
#         except Exception as e:
#             logger.error(f"Error in streaming log fetch: {str(e)}")
#             yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
#     def _fetch_logs_sync(
#         self,
#         project_id: str,
#         filter_str: str,
#         access_token: str,
#         limit: int,
#         fetch_all: bool
#     ) -> List[Dict[str, Any]]:
#         """Synchronous log fetching implementation."""
#         headers = self._build_headers(access_token)
#         all_logs = []
#         page_token = None
#         page_count = 0
        
#         logger.info(f"Starting comprehensive log fetch from GCP Logging API")
#         logger.info(f"Project: {project_id}")
#         logger.info(f"Filter: {filter_str}")
#         logger.info(f"Fetch all: {fetch_all}")
#         logger.info(f"Initial limit: {limit}")
        
#         while page_count < self.max_pages:
#             page_count += 1
            
#             # Build request body
#             body = self._build_request_body(project_id, filter_str, page_token)
            
#             logger.info(f"Fetching page {page_count} (pageSize: {self.page_size})")
#             if page_token:
#                 logger.info(f"Using pageToken: {page_token[:50]}...")
            
#             # Make API request
#             response = requests.post(
#                 self.base_url, 
#                 headers=headers, 
#                 json=body, 
#                 timeout=self.timeout
#             )
            
#             logger.info(f"GCP API response status: {response.status_code}")
            
#             # Handle response
#             if not response.ok:
#                 self._handle_error_response(response, project_id)
            
#             # Parse response
#             data = response.json() or {}
#             entries = data.get("entries", [])
#             next_page_token = data.get("nextPageToken")
            
#             logger.info(f"Page {page_count} - Received {len(entries)} log entries")
            
#             # Parse and add logs
#             page_logs = self._parse_log_entries(entries, project_id, len(all_logs))
#             all_logs.extend(page_logs)
            
#             logger.info(f"Total logs collected so far: {len(all_logs)}")
            
#             # Check if we should continue fetching
#             if not fetch_all and len(all_logs) >= limit:
#                 all_logs = all_logs[:limit]
#                 logger.info(f"Reached limit of {limit} logs, stopping fetch")
#                 break
            
#             # Check if there are more pages
#             if not next_page_token:
#                 logger.info("No more pages available, fetch complete")
#                 break
            
#             page_token = next_page_token
        
#         if page_count >= self.max_pages:
#             logger.warning(f"Reached maximum page limit ({self.max_pages}), stopping fetch")
        
#         logger.info(f"Comprehensive fetch complete - {len(all_logs)} total logs from {page_count} pages")
#         return all_logs
    
#     def _fetch_logs_sync_with_updates(
#         self,
#         project_id: str,
#         filter_str: str,
#         access_token: str,
#         limit: int,
#         fetch_all: bool
#     ) -> List[str]:
#         """Synchronous log fetching with progress updates."""
#         headers = self._build_headers(access_token)
#         all_logs = []
#         page_token = None
#         page_count = 0
#         updates = []
        
#         logger.info(f"Starting comprehensive streaming log fetch from GCP Logging API")
#         logger.info(f"Project: {project_id}")
#         logger.info(f"Filter: {filter_str}")
#         logger.info(f"Fetch all: {fetch_all}")
#         logger.info(f"Initial limit: {limit}")
        
#         while page_count < self.max_pages:
#             page_count += 1
            
#             # Build request body
#             body = self._build_request_body(project_id, filter_str, page_token)
            
#             logger.info(f"Fetching page {page_count} (pageSize: {self.page_size})")
#             if page_token:
#                 logger.info(f"Using pageToken: {page_token[:50]}...")
            
#             # Make API request
#             response = requests.post(
#                 self.base_url, 
#                 headers=headers, 
#                 json=body, 
#                 timeout=self.timeout
#             )
            
#             logger.info(f"GCP API response status: {response.status_code}")
            
#             # Handle response
#             if not response.ok:
#                 self._handle_error_response(response, project_id)
            
#             # Parse response
#             data = response.json() or {}
#             entries = data.get("entries", [])
#             next_page_token = data.get("nextPageToken")
            
#             logger.info(f"Page {page_count} - Received {len(entries)} log entries")
            
#             # Parse and add logs
#             page_logs = self._parse_log_entries(entries, project_id, len(all_logs))
#             all_logs.extend(page_logs)
            
#             logger.info(f"Total logs collected so far: {len(all_logs)}")
            
#             # Yield progress update
#             update = f"data: {json.dumps({
#                 'type': 'status',
#                 'message': f'Fetched page {page_count}: {len(page_logs)} logs (total: {len(all_logs)})',
#                 'step': 'log_fetching_progress',
#                 'page': page_count,
#                 'total_logs': len(all_logs)
#             })}\n\n"
#             updates.append(update)
            
#             # Check if we should continue fetching
#             if not fetch_all and len(all_logs) >= limit:
#                 all_logs = all_logs[:limit]
#                 logger.info(f"Reached limit of {limit} logs, stopping fetch")
#                 break
            
#             # Check if there are more pages
#             if not next_page_token:
#                 logger.info("No more pages available, fetch complete")
#                 break
            
#             page_token = next_page_token
        
#         if page_count >= self.max_pages:
#             logger.warning(f"Reached maximum page limit ({self.max_pages}), stopping fetch")
        
#         logger.info(f"Comprehensive streaming fetch complete - {len(all_logs)} total logs from {page_count} pages")
#         return updates
    
#     def _build_headers(self, access_token: str) -> Dict[str, str]:
#         """Build HTTP headers for GCP API requests."""
#         return {
#             "Authorization": f"Bearer {access_token}",
#             "Content-Type": "application/json",
#         }
    
#     def _build_request_body(
#         self, 
#         project_id: str, 
#         filter_str: str, 
#         page_token: Optional[str]
#     ) -> Dict[str, Any]:
#         """Build request body for GCP API requests."""
#         body = {
#             "resourceNames": [f"projects/{project_id}"],
#             "filter": filter_str,
#             "orderBy": "timestamp desc",
#             "pageSize": self.page_size,
#         }
        
#         if page_token:
#             body["pageToken"] = page_token
        
#         return body
    
#     def _handle_error_response(self, response: requests.Response, project_id: str):
#         """Handle error responses from GCP API."""
#         try:
#             error_detail = response.json()
#             logger.error(f"GCP API error response: {error_detail}")
#         except Exception:
#             error_detail = response.text
#             logger.error(f"GCP API error text: {error_detail}")
        
#         # Provide more specific error messages
#         if response.status_code == 401:
#             raise Exception("Authentication failed - invalid or expired access token")
#         elif response.status_code == 403:
#             raise Exception(f"Permission denied - insufficient permissions for project {project_id}")
#         elif response.status_code == 400:
#             raise Exception(f"Bad request - invalid filter or parameters: {error_detail}")
#         else:
#             raise Exception(f"GCP API error {response.status_code}: {str(error_detail)}")
    
#     def _parse_log_entries(
#         self, 
#         entries: List[Dict[str, Any]], 
#         project_id: str, 
#         start_index: int
#     ) -> List[Dict[str, Any]]:
#         """Parse raw log entries into structured format."""
#         page_logs = []
        
#         for idx, entry in enumerate(entries):
#             try:
#                 log_entry = LogEntry(entry, project_id)
#                 page_logs.append(log_entry.to_dict())
#             except Exception as parse_error:
#                 logger.warning(f"Failed to parse log entry {start_index + idx}: {str(parse_error)}")
#                 # Still include the raw entry for analysis
#                 page_logs.append({
#                     "id": f"raw_entry_{start_index + idx}",
#                     "timestamp": entry.get("timestamp"),
#                     "severity": entry.get("severity", "DEFAULT"),
#                     "message": f"Raw log entry (parse error: {str(parse_error)})",
#                     "rawEntry": entry,
#                     "projectId": project_id,
#                 })
        
#         return page_logs


"""
GCP Logging Client

Handles all interactions with Google Cloud Platform Logging API,
including pagination, error handling, and log parsing.
"""

import asyncio
import json
import logging
import requests
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, AsyncGenerator

from ..core.state import LogEntry


logger = logging.getLogger(__name__)


class GCPLoggingClient:
    """Client for interacting with GCP Logging API."""
    
    def __init__(self):
        self.base_url = "https://logging.googleapis.com/v2/entries:list"
        self.max_pages = 50  # Safety limit to prevent infinite loops
        self.page_size = 1000  # Maximum page size for GCP Logging API
        self.timeout = 60  # Request timeout in seconds
    
    async def fetch_logs(
        self,
        project_id: str,
        filter_str: str,
        access_token: str,
        limit: int = 100,
        fetch_all: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Fetch logs from GCP Logging API with comprehensive pagination support.
        
        Args:
            project_id: GCP project ID
            filter_str: GCP logging filter string
            access_token: OAuth2 access token
            limit: Maximum number of logs to fetch (ignored if fetch_all=True)
            fetch_all: Whether to fetch all available logs
            
        Returns:
            List of parsed log entries
        """
        def fetch_logs_sync():
            return self._fetch_logs_sync(project_id, filter_str, access_token, limit, fetch_all)
        
        try:
            with ThreadPoolExecutor() as executor:
                result = await asyncio.get_event_loop().run_in_executor(
                    executor, fetch_logs_sync
                )
            return result
        except Exception as e:
            logger.error(f"Error fetching logs from GCP: {str(e)}")
            return []
    
    async def fetch_logs_with_streaming(
        self,
        project_id: str,
        filter_str: str,
        access_token: str,
        limit: int = 100,
        fetch_all: bool = True
    ) -> AsyncGenerator[str, None]:
        """
        Fetch logs with streaming progress updates.
        
        Yields:
            Progress update strings in SSE format
        """
        def fetch_logs_sync():
            return self._fetch_logs_sync_with_updates(
                project_id, filter_str, access_token, limit, fetch_all
            )
        
        try:
            with ThreadPoolExecutor() as executor:
                result = await asyncio.get_event_loop().run_in_executor(
                    executor, fetch_logs_sync
                )
            
            # Yield all updates
            for update in result:
                yield update
                
        except Exception as e:
            logger.error(f"Error in streaming log fetch: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    def _fetch_logs_sync(
        self,
        project_id: str,
        filter_str: str,
        access_token: str,
        limit: int,
        fetch_all: bool
    ) -> List[Dict[str, Any]]:
        """Synchronous log fetching implementation."""
        headers = self._build_headers(access_token)
        all_logs = []
        page_token = None
        page_count = 0
        
        logger.info(f"Starting comprehensive log fetch from GCP Logging API")
        logger.info(f"Project: {project_id}")
        logger.info(f"Filter: {filter_str}")
        logger.info(f"Fetch all: {fetch_all}")
        logger.info(f"Initial limit: {limit}")
        
        while page_count < self.max_pages:
            page_count += 1
            
            # Build request body
            body = self._build_request_body(project_id, filter_str, page_token)
            
            logger.info(f"Fetching page {page_count} (pageSize: {self.page_size})")
            if page_token:
                logger.info(f"Using pageToken: {page_token[:50]}...")
            
            # Make API request
            response = requests.post(
                self.base_url, 
                headers=headers, 
                json=body, 
                timeout=self.timeout
            )
            
            logger.info(f"GCP API response status: {response.status_code}")
            
            # Handle response
            if not response.ok:
                self._handle_error_response(response, project_id)
            
            # Parse response
            data = response.json() or {}
            entries = data.get("entries", [])
            next_page_token = data.get("nextPageToken")
            
            logger.info(f"Page {page_count} - Received {len(entries)} log entries")
            
            # Parse and add logs
            page_logs = self._parse_log_entries(entries, project_id, len(all_logs))
            all_logs.extend(page_logs)
            
            logger.info(f"Total logs collected so far: {len(all_logs)}")
            
            # Check if we should continue fetching
            if not fetch_all and len(all_logs) >= limit:
                all_logs = all_logs[:limit]
                logger.info(f"Reached limit of {limit} logs, stopping fetch")
                break
            
            # Check if there are more pages
            if not next_page_token:
                logger.info("No more pages available, fetch complete")
                break
            
            page_token = next_page_token
        
        if page_count >= self.max_pages:
            logger.warning(f"Reached maximum page limit ({self.max_pages}), stopping fetch")
        
        logger.info(f"Comprehensive fetch complete - {len(all_logs)} total logs from {page_count} pages")
        return all_logs
    
    def _fetch_logs_sync_with_updates(
        self,
        project_id: str,
        filter_str: str,
        access_token: str,
        limit: int,
        fetch_all: bool
    ) -> List[str]:
        """Synchronous log fetching with progress updates."""
        headers = self._build_headers(access_token)
        all_logs = []
        page_token = None
        page_count = 0
        updates = []
        
        logger.info(f"Starting comprehensive streaming log fetch from GCP Logging API")
        logger.info(f"Project: {project_id}")
        logger.info(f"Filter: {filter_str}")
        logger.info(f"Fetch all: {fetch_all}")
        logger.info(f"Initial limit: {limit}")
        
        while page_count < self.max_pages:
            page_count += 1
            
            # Build request body
            body = self._build_request_body(project_id, filter_str, page_token)
            
            logger.info(f"Fetching page {page_count} (pageSize: {self.page_size})")
            if page_token:
                logger.info(f"Using pageToken: {page_token[:50]}...")
            
            # Make API request
            response = requests.post(
                self.base_url, 
                headers=headers, 
                json=body, 
                timeout=self.timeout
            )
            
            logger.info(f"GCP API response status: {response.status_code}")
            
            # Handle response
            if not response.ok:
                self._handle_error_response(response, project_id)
            
            # Parse response
            data = response.json() or {}
            entries = data.get("entries", [])
            next_page_token = data.get("nextPageToken")
            
            logger.info(f"Page {page_count} - Received {len(entries)} log entries")
            
            # Parse and add logs
            page_logs = self._parse_log_entries(entries, project_id, len(all_logs))
            all_logs.extend(page_logs)
            
            logger.info(f"Total logs collected so far: {len(all_logs)}")
            
            # Yield progress update - Fixed the nested f-string issue
            message = f'Fetched page {page_count}: {len(page_logs)} logs (total: {len(all_logs)})'
            update_data = {
                'type': 'status',
                'message': message,
                'step': 'log_fetching_progress',
                'page': page_count,
                'total_logs': len(all_logs)
            }
            update = f"data: {json.dumps(update_data)}\n\n"
            updates.append(update)
            
            # Check if we should continue fetching
            if not fetch_all and len(all_logs) >= limit:
                all_logs = all_logs[:limit]
                logger.info(f"Reached limit of {limit} logs, stopping fetch")
                break
            
            # Check if there are more pages
            if not next_page_token:
                logger.info("No more pages available, fetch complete")
                break
            
            page_token = next_page_token
        
        if page_count >= self.max_pages:
            logger.warning(f"Reached maximum page limit ({self.max_pages}), stopping fetch")
        
        logger.info(f"Comprehensive streaming fetch complete - {len(all_logs)} total logs from {page_count} pages")
        return updates
    
    def _build_headers(self, access_token: str) -> Dict[str, str]:
        """Build HTTP headers for GCP API requests."""
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
    
    def _build_request_body(
        self, 
        project_id: str, 
        filter_str: str, 
        page_token: Optional[str]
    ) -> Dict[str, Any]:
        """Build request body for GCP API requests."""
        body = {
            "resourceNames": [f"projects/{project_id}"],
            "filter": filter_str,
            "orderBy": "timestamp desc",
            "pageSize": self.page_size,
        }
        
        if page_token:
            body["pageToken"] = page_token
        
        return body
    
    def _handle_error_response(self, response: requests.Response, project_id: str):
        """Handle error responses from GCP API."""
        try:
            error_detail = response.json()
            logger.error(f"GCP API error response: {error_detail}")
        except Exception:
            error_detail = response.text
            logger.error(f"GCP API error text: {error_detail}")
        
        # Provide more specific error messages
        if response.status_code == 401:
            raise Exception("Authentication failed - invalid or expired access token")
        elif response.status_code == 403:
            raise Exception(f"Permission denied - insufficient permissions for project {project_id}")
        elif response.status_code == 400:
            raise Exception(f"Bad request - invalid filter or parameters: {error_detail}")
        else:
            raise Exception(f"GCP API error {response.status_code}: {str(error_detail)}")
    
    def _parse_log_entries(
        self, 
        entries: List[Dict[str, Any]], 
        project_id: str, 
        start_index: int
    ) -> List[Dict[str, Any]]:
        """Parse raw log entries into structured format."""
        page_logs = []
        
        for idx, entry in enumerate(entries):
            try:
                log_entry = LogEntry(entry, project_id)
                page_logs.append(log_entry.to_dict())
            except Exception as parse_error:
                logger.warning(f"Failed to parse log entry {start_index + idx}: {str(parse_error)}")
                # Still include the raw entry for analysis
                page_logs.append({
                    "id": f"raw_entry_{start_index + idx}",
                    "timestamp": entry.get("timestamp"),
                    "severity": entry.get("severity", "DEFAULT"),
                    "message": f"Raw log entry (parse error: {str(parse_error)})",
                    "rawEntry": entry,
                    "projectId": project_id,
                })
        
        return page_logs