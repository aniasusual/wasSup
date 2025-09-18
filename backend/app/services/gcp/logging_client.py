"""
GCP Logging API Client (Phase 2 - XXX: API Endpoint)

Provides a minimal async wrapper for `entries:list`:
  POST https://logging.googleapis.com/v2/entries:list

This module focuses on endpoint wiring and essentials; request optimization,
response streaming, and rate limiting are handled in subsequent phases.
"""

from typing import Any, Dict, List, Optional
import httpx
import logging
import asyncio
import random
from datetime import datetime


LOGGING_ENTRIES_LIST_URL = "https://logging.googleapis.com/v2/entries:list"

logger = logging.getLogger(__name__)


class GCPLoggingAPIError(Exception):
    """Raised when a non-success response is returned by the Logging API."""

    def __init__(self, status_code: int, message: str, payload: Optional[Dict[str, Any]] = None):
        super().__init__(f"GCP Logging API error {status_code}: {message}")
        self.status_code = status_code
        self.message = message
        self.payload = payload or {}


class GCPLoggingClient:
    """
    Minimal async client for Google Cloud Logging `entries:list` endpoint.

    Usage:
        client = GCPLoggingClient()
        body = client.build_entries_list_body(project_id, filter_str, page_size=1000)
        data = await client.entries_list(access_token, body)
    """

    def __init__(
        self,
        base_url: str = LOGGING_ENTRIES_LIST_URL,
        timeout: float = 30.0,
        *,
        max_retries: int = 3,
        backoff_base: float = 0.5,
        backoff_max: float = 4.0,
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.backoff_max = backoff_max

    # --------- ZZZ: Request Optimization helpers ---------

    @staticmethod
    def clamp_page_size(page_size: Optional[int]) -> Optional[int]:
        """Clamp page size to Logging API limits (1..1000)."""
        if page_size is None:
            return None
        try:
            ps = int(page_size)
        except Exception:
            return None
        if ps < 1:
            return 1
        if ps > 1000:
            return 1000
        return ps

    @staticmethod
    def default_order_by(order_by: Optional[str]) -> str:
        """Default to newest first when no order provided."""
        return order_by or "timestamp desc"

    @staticmethod
    def build_default_field_mask(
        include_payloads: Optional[list] = None,
        include_operation: bool = False,
        include_trace: bool = True,
    ) -> str:
        """
        Build a $fields mask for partial responses to reduce payload size.

        Args:
            include_payloads: list of payload types to include among
                ["textPayload", "jsonPayload", "protoPayload"]. Defaults to all three.
            include_operation: whether to include operation metadata
            include_trace: whether to include trace/spanId
        Returns:
            A string suitable for the `$fields` query param/body key.
        """
        payloads = include_payloads or ["textPayload", "jsonPayload", "protoPayload"]
        # Always useful base fields
        fields = {
            "logName": True,
            "timestamp": True,
            "receiveTimestamp": True,
            "severity": True,
            "labels": True,
            "resource": True,
        }
        if include_trace:
            fields.update({"trace": True, "spanId": True})
        if include_operation:
            fields.update({"operation": True})
        for p in payloads:
            fields[p] = True

        entries_fields = ",".join([k for k, v in fields.items() if v])
        # nextPageToken is needed for pagination
        return f"entries({entries_fields}),nextPageToken"

    def build_entries_list_body(
        self,
        project_id: str,
        filter_str: Optional[str] = None,
        order_by: Optional[str] = None,  # "timestamp desc" or "timestamp asc"
        page_size: Optional[int] = None,
        page_token: Optional[str] = None,
        resource_names: Optional[List[str]] = None,  # e.g., ["projects/my-project"]
        field_mask: Optional[str] = None,  # kept for compat; applied via query param in entries_list
    ) -> Dict[str, Any]:
        """Build request body for entries:list with sensible defaults."""
        body: Dict[str, Any] = {}

        # Resource scope
        body["resourceNames"] = resource_names or [f"projects/{project_id}"]

        # Filters and ordering
        if filter_str:
            body["filter"] = filter_str
        # Default ordering optimized for recency
        body["orderBy"] = self.default_order_by(order_by)

        # Pagination
        clamped = self.clamp_page_size(page_size)
        if clamped is not None:
            body["pageSize"] = clamped
        if page_token:
            body["pageToken"] = page_token

        return body

    async def entries_list(self, access_token: str, body: Dict[str, Any], *, fields: Optional[str] = None) -> Dict[str, Any]:
        """
        Call entries:list with the provided OAuth2 access token and body.

        Raises GCPLoggingAPIError for non-2xx responses.
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Print request summary and filter preview for debugging (no secrets)
        try:
            flt = str(body.get("filter", ""))
            lines = [l for l in flt.split("\n") if l.strip()]
            preview = "\n".join(lines[:10])
            more = " …" if len(lines) > 10 else ""
            print("entries:list request → orderBy=", body.get("orderBy"),
                  " pageSize=", body.get("pageSize"),
                  " fields_param=", bool(fields),
                  " resourceNames=", body.get("resourceNames"))
            print(f"Filter lines: {len(lines)}{more}\n{preview}")
        except Exception:
            pass
        logger.info("Calling GCP Logging API entries:list")
        params = {"fields": fields} if fields else None
        resp = await self._post_with_retries(self.base_url, headers=headers, json=body, params=params)

        try:
            data = resp.json()
        except Exception:
            logger.error("entries:list returned non-JSON response")
            raise GCPLoggingAPIError(resp.status_code, "Non-JSON response")

        logger.debug("entries:list call succeeded")
        return data

    # --------- BBBB: Rate limiting and retry logic ---------

    @staticmethod
    def _parse_retry_after(value: Optional[str]) -> Optional[float]:
        """Parse Retry-After header into seconds if possible."""
        if not value:
            return None
        # Seconds form
        try:
            return float(value)
        except Exception:
            pass
        # HTTP-date form
        try:
            dt = datetime.strptime(value, "%a, %d %b %Y %H:%M:%S GMT")
            delta = (dt - datetime.utcnow()).total_seconds()
            return max(0.0, delta)
        except Exception:
            return None

    async def _post_with_retries(self, url: str, *, headers: Dict[str, str], json: Dict[str, Any], params: Optional[Dict[str, Any]] = None) -> httpx.Response:
        attempt = 0
        last_exc: Optional[Exception] = None
        while True:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(url, headers=headers, json=json, params=params)

                # Retry on 429 and 5xx (except 501/505 possibly) — keep simple: any 5xx
                if resp.status_code == 429 or (500 <= resp.status_code < 600):
                    attempt += 1
                    if attempt > self.max_retries:
                        try:
                            payload = resp.json()
                        except Exception:
                            payload = {"text": resp.text}
                        msg = payload.get("error", {}).get("message") or payload.get("message") or resp.text
                        raise GCPLoggingAPIError(resp.status_code, msg or "Retry attempts exhausted", payload)

                    # Compute backoff with jitter or respect Retry-After
                    retry_after_hdr = resp.headers.get("Retry-After")
                    retry_after = self._parse_retry_after(retry_after_hdr)
                    if retry_after is None:
                        backoff = min(self.backoff_max, self.backoff_base * (2 ** (attempt - 1)))
                        # jitter in [0.8, 1.2]
                        backoff *= random.uniform(0.8, 1.2)
                    else:
                        backoff = retry_after
                    logger.warning(f"entries:list retry {attempt}/{self.max_retries} after {backoff:.2f}s (status {resp.status_code})")
                    await asyncio.sleep(backoff)
                    continue

                # Success or non-retryable error
                if resp.status_code // 100 != 2:
                    try:
                        payload = resp.json()
                    except Exception:
                        payload = {"text": resp.text}
                    message = payload.get("error", {}).get("message") or payload.get("message") or resp.text
                    logger.error(f"entries:list failed {resp.status_code}: {message}")
                    raise GCPLoggingAPIError(resp.status_code, message or "Unknown error", payload)

                return resp

            except (httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout, httpx.RemoteProtocolError) as e:
                # Retry transient network errors
                attempt += 1
                last_exc = e
                if attempt > self.max_retries:
                    raise GCPLoggingAPIError(0, f"Network error after retries: {str(e)}")
                backoff = min(self.backoff_max, self.backoff_base * (2 ** (attempt - 1)))
                backoff *= random.uniform(0.8, 1.2)
                logger.warning(f"entries:list network retry {attempt}/{self.max_retries} after {backoff:.2f}s: {e}")
                await asyncio.sleep(backoff)

    # --------- ZZZ: Pagination convenience (iterative fetch) ---------

    async def entries_list_paginated(
        self,
        access_token: str,
        project_id: str,
        filter_str: Optional[str] = None,
        *,
        order_by: Optional[str] = None,
        page_size: Optional[int] = 1000,
        max_pages: Optional[int] = None,
        max_entries: Optional[int] = None,
        field_mask: Optional[str] = None,
        resource_names: Optional[List[str]] = None,
        start_page_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Fetch multiple pages from entries:list with sensible defaults.

        Returns a dict with:
          - entries: List[Dict]
          - page_count: int
          - returned: int
          - next_page_token: Optional[str]
        """
        entries: List[Dict[str, Any]] = []
        page_token = start_page_token
        page_count = 0
        returned = 0

        # For compatibility and to avoid 400 errors when selecting nested/message fields,
        # disable partial-response field selection for now.
        # A safe, minimal mask could be reintroduced later.
        eff_field_mask = None

        while True:
            body = self.build_entries_list_body(
                project_id=project_id,
                filter_str=filter_str,
                order_by=order_by,
                page_size=page_size,
                page_token=page_token,
                resource_names=resource_names,
                field_mask=eff_field_mask,
            )

            # Print basic page debug info
            try:
                print("entries:list page attempt → index=", page_count + 1, " has_page_token=", bool(page_token))
            except Exception:
                pass

            data = await self.entries_list(access_token, body, fields=eff_field_mask)
            page_entries = data.get("entries", []) or []
            next_token = data.get("nextPageToken")

            entries.extend(page_entries)
            page_count += 1
            returned += len(page_entries)

            # Print page result summary
            try:
                print("entries:list page result → index=", page_count, " returned=", len(page_entries), " has_next=", bool(next_token))
            except Exception:
                pass

            # Stop conditions
            if max_entries is not None and returned >= max_entries:
                break
            if max_pages is not None and page_count >= max_pages:
                break
            if not next_token:
                break

            page_token = next_token

        next_page_token = page_token if (max_pages or max_entries) else None

        print(f"Entries: {entries}")
        print(f"Page count: {page_count}")
        print(f"Returned: {len(entries[:max_entries] if max_entries else entries)}")
        print(f"Next page token: {next_page_token}")

        return {
            "entries": entries[:max_entries] if max_entries else entries,
            "page_count": page_count,
            "returned": len(entries[:max_entries] if max_entries else entries),
            "next_page_token": next_page_token,
        }

    # --------- AAAA: Response Processing & Streaming helpers ---------

    @staticmethod
    def _extract_payload(entry: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts the first available payload and a human-friendly message string."""
        text = entry.get("textPayload")
        json_p = entry.get("jsonPayload")
        proto = entry.get("protoPayload")

        message: Optional[str] = None
        primary_type: Optional[str] = None
        if isinstance(text, str):
            primary_type = "textPayload"
            message = text
        elif isinstance(json_p, dict):
            primary_type = "jsonPayload"
            # Keep compact string for quick glance; full json preserved separately
            try:
                import json
                message = json.dumps(json_p, separators=(",", ":"))[:500]
            except Exception:
                message = str(json_p)[:500]
        elif isinstance(proto, dict):
            primary_type = "protoPayload"
            message = (proto.get("@type") or "protoPayload")
        else:
            primary_type = None
            message = None

        return {
            "primary_type": primary_type,
            "message": message,
            "textPayload": text,
            "jsonPayload": json_p,
            "protoPayload": proto,
        }

    @staticmethod
    def normalize_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a Logging API entry into a compact, UI-friendly shape.
        Keeps original entry under `_raw` for deep inspection.
        """
        payload = GCPLoggingClient._extract_payload(entry)
        res = entry.get("resource") or {}
        labels = entry.get("labels") or {}
        http_req = entry.get("httpRequest") or {}

        normalized = {
            "timestamp": entry.get("timestamp") or entry.get("receiveTimestamp"),
            "severity": entry.get("severity"),
            "logName": entry.get("logName"),
            "resource_type": res.get("type"),
            "resource_labels": res.get("labels") or {},
            "labels": labels,
            "trace": entry.get("trace"),
            "spanId": entry.get("spanId"),
            "payload_type": payload["primary_type"],
            "message": payload["message"],
            # Useful HTTP request fields when present
            "http": {
                "requestMethod": http_req.get("requestMethod"),
                "requestUrl": http_req.get("requestUrl"),
                "status": http_req.get("status"),
                "latency": http_req.get("latency"),
                "userAgent": http_req.get("userAgent"),
                "remoteIp": http_req.get("remoteIp"),
            } if http_req else None,
            # Preserve full payloads for expand-on-demand UI
            "payload": {
                "textPayload": payload["textPayload"],
                "jsonPayload": payload["jsonPayload"],
                "protoPayload": payload["protoPayload"],
            },
            "_raw": entry,
        }
        return normalized

    @staticmethod
    def normalize_entries(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [GCPLoggingClient.normalize_entry(e) for e in entries]

    async def entries_list_stream(
        self,
        access_token: str,
        project_id: str,
        filter_str: Optional[str] = None,
        *,
        order_by: Optional[str] = None,
        page_size: Optional[int] = 1000,
        max_pages: Optional[int] = None,
        max_entries: Optional[int] = None,
        field_mask: Optional[str] = None,
        resource_names: Optional[List[str]] = None,
        start_page_token: Optional[str] = None,
    ):
        """
        Async generator that yields page-wise normalized results for streaming UIs.

        Yields dict events of forms:
          { "type": "page", "page_index": int, "returned": int, "entries": [...] }
          { "type": "end", "page_count": int, "returned": int, "next_page_token": str|None }
          { "type": "error", "status": int, "message": str }
        """
        page_index = 0
        total_returned = 0
        try:
            result = await self.entries_list_paginated(
                access_token=access_token,
                project_id=project_id,
                filter_str=filter_str,
                order_by=order_by,
                page_size=page_size,
                max_pages=max_pages,
                max_entries=max_entries,
                field_mask=field_mask,
                resource_names=resource_names,
                start_page_token=start_page_token,
            )

            # Emit a single page event with all entries (paginated helper aggregated them)
            norm = self.normalize_entries(result.get("entries", []))
            total_returned = len(norm)
            yield {
                "type": "page",
                "page_index": page_index,
                "returned": total_returned,
                "entries": norm,
            }
            yield {
                "type": "end",
                "page_count": result.get("page_count", 1),
                "returned": total_returned,
                "next_page_token": result.get("next_page_token"),
            }
        except GCPLoggingAPIError as e:
            yield {"type": "error", "status": e.status_code, "message": e.message, "payload": e.payload}
        except Exception as e:  # Fallback error path
            yield {"type": "error", "status": 0, "message": str(e)}
