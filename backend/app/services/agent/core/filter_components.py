"""
Filter Components Library (Phase 3)

HHH: Resource Type Filters

Centralized helpers for constructing resource.type and resource label
clauses. These helpers are used by filter construction nodes (D/M/N)
and later by refinement nodes (S/T).

Important: No hardcoded aliasing or fallback logic. Canonicalization
of resource types must be resolved via the LLM only when requested by
callers. If LLM is unavailable, callers should decide how to proceed.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta, timezone

try:
    # Local import for LLM service
    from .llm_service import LLMService
except Exception:
    # Absolute path form (e.g., LangGraph Studio)
    from app.services.agent.core.llm_service import LLMService


async def canonicalize_resource_types_via_llm(
    identifiers: List[str],
    *,
    llm_service: Optional[LLMService] = None,
) -> List[str]:
    """
    Use the LLM to map arbitrary service identifiers to canonical
    Google Cloud Logging resource.type strings. No local aliasing or
    fallbacks are applied in this function.

    Args:
        identifiers: A list of service or resource identifiers as provided by
                     user/architecture (e.g., ["cloud run", "gke", "gce"]).
        llm_service: Optional LLMService instance. If not provided, a new one
                     will be created. If the LLM is not available in the
                     environment, an exception will be raised.

    Returns:
        A list of canonical resource.type strings as decided by the LLM.
        If the LLM cannot determine valid types, returns an empty list.
    """
    ids = [str(x).strip() for x in (identifiers or []) if str(x).strip()]
    if not ids:
        return []

    svc = llm_service or LLMService()
    if not getattr(svc, "llm", None):
        # Per request: no fallbacks. If the LLM is unavailable, raise.
        raise RuntimeError("LLM unavailable for resource type canonicalization")

    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import JsonOutputParser
    from pydantic import BaseModel, Field

    class CanonicalTypes(BaseModel):
        resource_types: List[str] = Field(default_factory=list, description="Canonical GCP Logging resource.type values")

    parser = JsonOutputParser(pydantic_object=CanonicalTypes)
    prompt = ChatPromptTemplate.from_messages([
        ("system", """
You are an expert on Google Cloud Logging monitored resource types.
Given a list of service or resource identifiers, return ONLY a JSON object with a key
resource_types: an array of canonical resource.type strings (exact values from GCP Logging schema).
Do not invent new values. If an identifier does not correspond to a known resource.type, omit it.
No explanations and no additional keys.
"""),
        ("human", """
Identifiers:
{identifiers}

{format_instructions}
"""),
    ])

    chain = prompt | svc.llm | parser
    result = await chain.ainvoke({
        "identifiers": "\n".join(f"- {i}" for i in ids),
        "format_instructions": parser.get_format_instructions(),
    })
    return list(dict.fromkeys(result.resource_types or []))


def _label_for_service(type_id: str, name: Optional[str]) -> Optional[str]:
    """Return a resource label clause for a service type + optional name."""
    t = (type_id or "").lower()
    if "cloud_run" in t and name:
        return f'resource.labels.service_name="{name}"'
    if ("app_engine" in t or "gae" in t) and name:
        return f'resource.labels.module_id="{name}"'
    # For k8s/GKE, labels are varied (cluster_name, namespace_name, pod_name),
    # avoid asserting without clear signal.
    return None


def build_resource_type_clauses(
    *,
    resource_types: Optional[List[str]] = None,
    # Optional: list of (type, name) tuples for label hints
    service_names: Optional[List[Tuple[str, str]]] = None,
) -> Tuple[List[str], Dict[str, Any]]:
    """
    Build resource.type and label clauses.

    Args:
        resource_types: candidate service types (e.g., ["cloud_run", "gce_instance"]) or
                        keys like "resource.type=cloud_run_revision" (will be parsed).
        service_names: optional tuples of (type, name) to add resource.labels.* when safe

    Returns:
        (clauses, info)
          clauses: list of filter lines (resource.type and label clauses)
          info: { resource_types: [..], labels: [{type,name,label}] }
    """
    types: List[str] = []
    if resource_types:
        for r in resource_types:
            if not r:
                continue
            s = str(r).strip()
            if s.startswith("resource.type="):
                s = s.split("=", 1)[1].strip('"')
            # No local aliasing or fallback; accept as-is and de-duplicate
            if s and s not in types:
                types.append(s)

    # Build resource.type clause(s)
    clauses: List[str] = []
    if len(types) == 1:
        clauses.append(f'resource.type="{types[0]}"')
    elif len(types) > 1:
        ors = " OR ".join([f'resource.type="{t}"' for t in types])
        clauses.append(f"({ors})")

    # Add resource label hints when explicitly provided
    labels_info: List[Dict[str, Any]] = []
    for pair in service_names or []:
        st, name = pair
        st_canon = (st or "")
        label = _label_for_service(st_canon, name)
        if label and label not in clauses:
            clauses.append(label)
            labels_info.append({"type": st_canon, "name": name, "label": label})

    info: Dict[str, Any] = {"resource_types": types, "labels": labels_info}
    return clauses, info


def derive_resource_types_from_state(state: Any) -> List[str]:
    """Collect candidate resource types from AgentState.

    Sources:
      - extracted_entities.services keys like "resource.type=cloud_run_revision"
      - state.services (user-specified services)
      - architecture_context.relevant_services (types)
    """
    types: List[str] = []
    extracted = (getattr(state, "get", None) and state.get("extracted_entities")) or {}
    services = (extracted.get("services") or {})
    for key in services.keys():
        if isinstance(key, str):
            if key.startswith("resource.type="):
                t = key.split("=", 1)[1].strip('"')
                if t and t not in types:
                    types.append(t)

    for s in (state.get("services") or []):
        ss = str(s).strip()
        if ss and ss not in types:
            types.append(ss)

    arch = state.get("architecture_context") or {}
    for s in (arch.get("relevant_services") or []):
        ss = str(s).strip()
        if ss and ss not in types:
            types.append(ss)

    return types


# -----------------------
# III: Temporal Logic
# -----------------------

def _iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def parse_duration(s: str) -> timedelta:
    """Parse a strict duration string like '5m', '30m', '1h', '24h', '7d'.
    Accepted units: m (minutes), h (hours), d (days). No fallbacks.
    """
    if not s or not isinstance(s, str):
        raise ValueError("duration string required")
    s = s.strip().lower()
    if len(s) < 2:
        raise ValueError("invalid duration string")
    num, unit = s[:-1], s[-1]
    try:
        n = int(num)
    except Exception:
        raise ValueError("invalid duration number")
    if n <= 0:
        raise ValueError("duration must be positive")
    if unit == 'm':
        return timedelta(minutes=n)
    if unit == 'h':
        return timedelta(hours=n)
    if unit == 'd':
        return timedelta(days=n)
    raise ValueError("unsupported duration unit")


def parse_time_indicator(indicator: str, *, now: Optional[datetime] = None) -> datetime:
    """Return the start time for a strict set of indicators.
    Supported indicators: 'last_hour', 'last_day', 'last_7_days', '1h', '24h', '7d'.
    Raises on unknown values (no fallbacks).
    """
    if not indicator:
        raise ValueError("time indicator required")
    now = now or datetime.utcnow().replace(tzinfo=timezone.utc)
    s = str(indicator).strip().lower()
    if s in ("last_hour", "1h"):
        return now - timedelta(hours=1)
    if s in ("last_day", "24h"):
        return now - timedelta(days=1)
    if s in ("last_7_days", "7d"):
        return now - timedelta(days=7)
    raise ValueError("unsupported time indicator")


def build_temporal_clauses(
    *,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    window: Optional[str] = None,
    exclude_recent: Optional[str] = None,
    now: Optional[datetime] = None,
) -> Tuple[List[str], Dict[str, Any]]:
    """
    Build timestamp clauses for Logging filters using strict inputs.

    - Provide either (start_time[, end_time]) OR window duration.
    - exclude_recent allows excluding the most recent duration from the end.
      Example: window='30m', exclude_recent='5m' → [now-30m, now-5m)

    Returns: (clauses, info)
      clauses: list like [ 'timestamp>"..."', 'timestamp<="..."' ]
      info: metadata with the resolved times
    """
    now = now or datetime.utcnow().replace(tzinfo=timezone.utc)
    if window and (start_time or end_time):
        raise ValueError("specify either window or explicit start/end, not both")

    if window:
        w = parse_duration(window)
        start = now - w
        if exclude_recent:
            ex = parse_duration(exclude_recent)
            if ex >= w:
                raise ValueError("exclude_recent must be shorter than window")
            end = now - ex
        else:
            end = None
    else:
        start = start_time
        end = end_time

    clauses: List[str] = []
    if start:
        clauses.append(f'timestamp>"{_iso(start)}"')
    if end:
        clauses.append(f'timestamp<="{_iso(end)}"')

    info = {
        "start_time": _iso(start) if start else None,
        "end_time": _iso(end) if end else None,
        "now": _iso(now),
        "window": window,
        "exclude_recent": exclude_recent,
    }
    return clauses, info


def build_temporal_clauses_from_indicators(
    indicators: List[str], *, now: Optional[datetime] = None
) -> Tuple[List[str], Dict[str, Any]]:
    """
    Build simple timestamp lower-bound from a list of time indicators.
    Uses the first supported indicator; raises if none supported.
    Supported indicators are strictly: 'last_hour', 'last_day', 'last_7_days', '1h', '24h', '7d'.
    """
    now = now or datetime.utcnow().replace(tzinfo=timezone.utc)
    for ind in indicators or []:
        try:
            start = parse_time_indicator(ind, now=now)
            clauses = [f'timestamp>"{_iso(start)}"']
            return clauses, {"start_time": _iso(start), "now": _iso(now), "indicator": ind}
        except Exception:
            continue
    raise ValueError("no supported time indicators provided")


# -----------------------
# JJJ: Severity & HTTP Status
# -----------------------

_ALLOWED_SEVERITIES: List[str] = [
    "DEFAULT", "DEBUG", "INFO", "NOTICE", "WARNING", "ERROR", "CRITICAL", "ALERT", "EMERGENCY",
]
_SEVERITY_INDEX: Dict[str, int] = {s: i for i, s in enumerate(_ALLOWED_SEVERITIES)}


def build_severity_clause(severities: List[str]) -> Tuple[List[str], Dict[str, Any]]:
    """
    Build a single severity threshold clause from provided severities.
    Strict behavior: only accepts exact severities in ALLOWED list (case-insensitive).
    Picks the least severe among provided (broadest range) as `severity>=X`.
    Returns empty clauses if none valid provided.
    """
    if not severities:
        return [], {"provided": [], "selected": None}
    # normalize and filter
    norm = [str(s).strip().upper() for s in severities if str(s).strip()]
    valid = [s for s in norm if s in _SEVERITY_INDEX]
    if not valid:
        return [], {"provided": norm, "selected": None}
    selected = min(valid, key=lambda s: _SEVERITY_INDEX[s])
    clause = [f"severity>={selected}"]
    return clause, {"provided": valid, "selected": selected}


def build_http_status_clauses(status_codes: List[str]) -> Tuple[List[str], Dict[str, Any]]:
    """
    Build HTTP status clauses.
    - Supports exact numeric codes (e.g., '404')
    - Supports class ranges '5xx', '4xx', etc., strictly 'Nxx' with N in 1..5
    Returns a list of clauses; does not OR/AND them together (caller composes).
    """
    if not status_codes:
        return [], {"accepted": []}
    clauses: List[str] = []
    accepted: List[str] = []
    for raw in status_codes:
        s = str(raw).strip().lower()
        if not s:
            continue
        if len(s) == 3 and s.endswith("xx") and s[0].isdigit():
            n = int(s[0])
            if 1 <= n <= 5:
                lo, hi = n * 100, n * 100 + 99
                clauses.append(f"(httpRequest.status>={lo} AND httpRequest.status<={hi})")
                accepted.append(s.upper())
            continue
        # exact number
        try:
            num = int(s)
            if 100 <= num <= 599:
                clauses.append(f"httpRequest.status={num}")
                accepted.append(str(num))
        except Exception:
            # ignore invalid token strictly
            continue
    return clauses, {"accepted": accepted}


# -----------------------
# KKK: Content Search
# -----------------------

def _escape_quotes(s: str) -> str:
    return str(s).replace('"', '\\"')


def build_content_contains_clauses(
    keywords: List[str], *, max_items: Optional[int] = None
) -> Tuple[List[str], Dict[str, Any]]:
    """
    Build global full-text search clauses using quoted terms.
    Each clause is a standalone quoted string which matches across common
    payload fields in Logging (text/json/proto payloads and labels).

    Strict behavior: ignores empty values. No stemming or fallbacks.
    """
    items: List[str] = []
    accepted: List[str] = []
    count = 0
    for raw in keywords or []:
        if max_items is not None and count >= max_items:
            break
        s = str(raw).strip()
        if not s:
            continue
        items.append(f'"{_escape_quotes(s)}"')
        accepted.append(s)
        count += 1
    return items, {"accepted": accepted, "count": count}


def _valid_field_path(path: str) -> bool:
    # Strict field path: letters, numbers, underscore, dot separators
    import re
    return bool(re.fullmatch(r"[A-Za-z0-9_]+(\.[A-Za-z0-9_]+)*", path))


def build_json_field_equals_clauses(
    pairs: List[Tuple[str, Any]]
) -> Tuple[List[str], Dict[str, Any]]:
    """
    Build equality clauses for jsonPayload fields.
    Example: ("service", "checkout") -> jsonPayload.service="checkout"
    Strict field path validation; string values are quoted, numbers/bools raw.
    """
    clauses: List[str] = []
    accepted: List[Dict[str, Any]] = []
    for (path, value) in pairs or []:
        p = str(path).strip()
        if not p or not _valid_field_path(p):
            continue
        if isinstance(value, bool) or isinstance(value, int) or isinstance(value, float):
            val = str(value).lower() if isinstance(value, bool) else str(value)
            clauses.append(f"jsonPayload.{p}={val}")
        else:
            clauses.append(f'jsonPayload.{p}="{_escape_quotes(value)}"')
        accepted.append({"path": p, "value": value})
    return clauses, {"accepted": accepted}


# -----------------------
# LLL: Logical Operators & Grouping
# -----------------------

def _clean_items(items: List[str]) -> List[str]:
    return [str(x).strip() for x in (items or []) if str(x).strip()]


def or_group(clauses: List[str]) -> List[str]:
    """Return a single parenthesized OR group if multiple clauses provided.
    - [] → []
    - [A] → [A]
    - [A,B] → ["(A OR B)"]
    """
    cs = _clean_items(clauses)
    if not cs:
        return []
    if len(cs) == 1:
        return [cs[0]]
    return ["(" + " OR ".join(cs) + ")"]


def and_group(clauses: List[str]) -> List[str]:
    """Return a single parenthesized AND group when multiple provided."""
    cs = _clean_items(clauses)
    if not cs:
        return []
    if len(cs) == 1:
        return [cs[0]]
    return ["(" + " AND ".join(cs) + ")"]


def not_clause(clause: str) -> str:
    """Negate a clause with NOT ( ... )."""
    c = str(clause).strip()
    if not c:
        raise ValueError("clause required for NOT")
    return f"NOT ({c})"



def build_textpayload_regex_clauses(
    patterns: List[str]
) -> Tuple[List[str], Dict[str, Any]]:
    """
    Build regex match clauses for textPayload using GCL '=~' operator.
    Patterns are treated as RE2; no escaping is applied (caller must provide
    valid regex). Empty patterns are ignored.
    """
    clauses: List[str] = []
    accepted: List[str] = []
    for pat in patterns or []:
        p = str(pat)
        if not p:
            continue
        clauses.append(f'textPayload=~"{p}"')
        accepted.append(p)
    return clauses, {"accepted": accepted}
