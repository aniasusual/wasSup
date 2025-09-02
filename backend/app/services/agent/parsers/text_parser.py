"""
Robust Text Parser

Enterprise-grade text parser with advanced NLP capabilities for extracting
structured information from natural language queries.
"""

import re
import unicodedata
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from difflib import SequenceMatcher


class RobustTextParser:
    """
    Enterprise-grade text parser with advanced NLP capabilities.
    Handles natural language variations, fuzzy matching, and context understanding.
    """
    
    def __init__(self):
        self._initialize_patterns()
    
    def _initialize_patterns(self):
        """Initialize all pattern dictionaries."""
        self.service_patterns = self._get_service_patterns()
        self.time_patterns = self._get_time_patterns()
        self.severity_patterns = self._get_severity_patterns()
        self.context_keywords = self._get_context_keywords()
    
    def _get_service_patterns(self) -> Dict[str, List[str]]:
        """Get service type patterns for fuzzy matching."""
        return {
            "cloud_run_revision": [
                "cloud run", "cloud_run", "cloudrun", "run", "cloud run revision",
                "cloud run service", "cloud run container", "serverless container"
            ],
            "gce_instance": [
                "gce", "compute", "instance", "vm", "virtual machine", "compute engine",
                "ec2", "virtual machine instance", "compute instance"
            ],
            "cloud_function": [
                "function", "cloud function", "cloudfunction", "lambda", "serverless function",
                "function as a service", "faas"
            ],
            "gae_app": [
                "app engine", "gae", "appengine", "google app engine", "platform as a service",
                "paas", "web app", "application engine"
            ],
            "k8s_container": [
                "kubernetes", "gke", "container", "k8s", "pod", "deployment",
                "cluster", "orchestration", "container orchestration"
            ],
            "cloud_sql": [
                "sql", "database", "mysql", "postgresql", "cloud sql", "managed database",
                "relational database", "rdbms"
            ],
            "bigquery": [
                "bigquery", "big query", "data warehouse", "analytics", "sql analytics",
                "data lake", "etl", "data processing"
            ]
        }
    
    def _get_time_patterns(self) -> Dict[str, List[str]]:
        """Get time range patterns for natural language parsing."""
        return {
            "last_hour": [
                "last hour", "past hour", "1 hr", "1 hour", "last 1 hr", "previous hour",
                "within the hour", "this hour", "current hour", "last 60 minutes"
            ],
            "last_24_hours": [
                "last 24 hours", "past day", "24 hours", "24 hrs", "last day", "previous day",
                "within 24 hours", "last 24h", "past 24 hours", "yesterday to now"
            ],
            "this_week": [
                "this week", "last week", "7 days", "past week", "within a week",
                "last 7 days", "past 7 days", "weekly", "this past week"
            ],
            "yesterday": [
                "yesterday", "past day", "previous day", "day before", "last day",
                "yesterday only", "past 24 hours ending yesterday"
            ],
            "last_30_minutes": [
                "last 30 minutes", "30 min", "30 minutes", "past 30 minutes",
                "within 30 minutes", "last half hour", "past half hour"
            ],
            "last_15_minutes": [
                "last 15 minutes", "15 min", "15 minutes", "past 15 minutes",
                "within 15 minutes", "quarter hour", "past quarter hour"
            ]
        }
    
    def _get_severity_patterns(self) -> Dict[str, List[str]]:
        """Get severity level patterns."""
        return {
            "ERROR": [
                "error", "errors", "err", "critical", "fatal", "failure", "failed",
                "exception", "exceptions", "crash", "crashed", "abort", "aborted"
            ],
            "WARNING": [
                "warning", "warnings", "warn", "caution", "attention", "notice",
                "deprecated", "deprecation", "deprecated warning"
            ],
            "INFO": [
                "info", "information", "informational", "general", "normal", "standard",
                "regular", "routine", "status", "state"
            ],
            "DEBUG": [
                "debug", "debugging", "development", "dev", "trace", "tracing",
                "verbose", "detailed", "diagnostic"
            ]
        }
    
    def _get_context_keywords(self) -> Dict[str, List[str]]:
        """Get context keywords for intent recognition."""
        return {
            "performance": ["slow", "performance", "latency", "response time", "throughput", "bottleneck"],
            "errors": ["error", "failure", "crash", "exception", "bug", "issue", "problem"],
            "security": ["auth", "authentication", "permission", "access denied", "unauthorized", "security"],
            "deployment": ["deploy", "deployment", "rollout", "release", "version", "update"],
            "connectivity": ["connection", "network", "timeout", "unreachable", "offline", "disconnected"],
            "scaling": ["scale", "scaling", "capacity", "load", "traffic", "concurrent users"]
        }
    
    def normalize_text(self, text: str) -> str:
        """Normalize text for consistent processing."""
        if not text:
            return ""
        
        # Convert to lowercase and normalize unicode
        normalized = text.lower().strip()
        normalized = unicodedata.normalize('NFKC', normalized)
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized
    
    def fuzzy_match(self, text: str, patterns: List[str], threshold: float = 0.8) -> List[Tuple[str, float]]:
        """Perform fuzzy matching with confidence scores."""
        if not text or not patterns:
            return []
        
        matches = []
        normalized_text = self.normalize_text(text)
        
        for pattern in patterns:
            normalized_pattern = self.normalize_text(pattern)
            
            # Exact match
            if normalized_pattern in normalized_text:
                matches.append((pattern, 1.0))
                continue
            
            # Fuzzy match using sequence matcher
            similarity = SequenceMatcher(None, normalized_text, normalized_pattern).ratio()
            if similarity >= threshold:
                matches.append((pattern, similarity))
            
            # Partial match (pattern is contained in text)
            if normalized_pattern in normalized_text or normalized_text in normalized_pattern:
                partial_score = min(len(normalized_pattern), len(normalized_text)) / max(len(normalized_pattern), len(normalized_text))
                if partial_score >= threshold:
                    matches.append((pattern, partial_score))
        
        # Sort by confidence score (highest first)
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches
    
    def extract_services_robust(self, text: str) -> List[Dict[str, Any]]:
        """Extract services with confidence scores and context."""
        if not text:
            return []
        
        extracted_services = []
        normalized_text = self.normalize_text(text)
        
        for service_type, patterns in self.service_patterns.items():
            matches = self.fuzzy_match(normalized_text, patterns, threshold=0.6)
            
            if matches:
                best_match = matches[0]
                confidence = best_match[1]
                
                # Boost confidence for exact matches
                if confidence > 0.9:
                    confidence = min(1.0, confidence + 0.1)
                
                extracted_services.append({
                    "type": service_type,
                    "confidence": confidence,
                    "matched_pattern": best_match[0],
                    "context": self._extract_service_context(normalized_text, best_match[0])
                })
        
        # Sort by confidence and remove duplicates
        extracted_services.sort(key=lambda x: x["confidence"], reverse=True)
        
        # Remove lower confidence duplicates of the same service type
        seen_types = set()
        unique_services = []
        for service in extracted_services:
            if service["type"] not in seen_types:
                seen_types.add(service["type"])
                unique_services.append(service)
        
        return unique_services
    
    def extract_time_range_robust(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract time range with confidence and natural language support."""
        if not text:
            return None
        
        normalized_text = self.normalize_text(text)
        now = datetime.utcnow()
        
        # Try exact pattern matching first
        for time_type, patterns in self.time_patterns.items():
            matches = self.fuzzy_match(normalized_text, patterns, threshold=0.7)
            
            if matches:
                best_match = matches[0]
                confidence = best_match[1]
                
                time_info = self._generate_time_range(time_type, now)
                if time_info:
                    time_info["confidence"] = confidence
                    time_info["matched_pattern"] = best_match[0]
                    time_info["extraction_method"] = "pattern_matching"
                    return time_info
        
        # Try relative time expressions
        relative_time = self._extract_relative_time(normalized_text, now)
        if relative_time:
            return relative_time
        
        # Try absolute time expressions
        absolute_time = self._extract_absolute_time(normalized_text, now)
        if absolute_time:
            return absolute_time
        
        return None
    
    def extract_severity_robust(self, text: str) -> List[Dict[str, Any]]:
        """Extract severity levels with confidence scores."""
        if not text:
            return []
        
        extracted_severities = []
        normalized_text = self.normalize_text(text)
        
        for severity_level, patterns in self.severity_patterns.items():
            matches = self.fuzzy_match(normalized_text, patterns, threshold=0.7)
            
            if matches:
                best_match = matches[0]
                confidence = best_match[1]
                
                extracted_severities.append({
                    "level": severity_level,
                    "confidence": confidence,
                    "matched_pattern": best_match[0],
                    "context": self._extract_severity_context(normalized_text, best_match[0])
                })
        
        # Sort by confidence
        extracted_severities.sort(key=lambda x: x["confidence"], reverse=True)
        return extracted_severities
    
    def extract_intent_robust(self, text: str) -> Dict[str, Any]:
        """Extract user intent and context from text."""
        if not text:
            return {"primary_intent": "unknown", "confidence": 0.0, "context": {}}
        
        normalized_text = self.normalize_text(text)
        intent_scores = {}
        
        # Score each intent category
        for intent, keywords in self.context_keywords.items():
            score = 0.0
            keyword_matches = []
            
            for keyword in keywords:
                if keyword in normalized_text:
                    score += 1.0
                    keyword_matches.append(keyword)
            
            if score > 0:
                intent_scores[intent] = {
                    "score": score,
                    "keywords": keyword_matches,
                    "confidence": min(1.0, score / len(keywords))
                }
        
        # Determine primary intent
        if intent_scores:
            primary_intent = max(intent_scores.keys(), key=lambda k: intent_scores[k]["score"])
            primary_confidence = intent_scores[primary_intent]["confidence"]
        else:
            primary_intent = "general_inquiry"
            primary_confidence = 0.5
        
        return {
            "primary_intent": primary_intent,
            "confidence": primary_confidence,
            "context": intent_scores,
            "all_intents": intent_scores
        }
    
    def _extract_service_context(self, text: str, matched_pattern: str) -> Dict[str, Any]:
        """Extract context around service mentions."""
        context = {}
        
        # Look for modifiers
        modifiers = ["production", "staging", "development", "test", "canary", "blue", "green"]
        for modifier in modifiers:
            if modifier in text:
                context["environment"] = modifier
        
        # Look for specific instances
        instance_pattern = r'(\w+)-(\d+)'
        instances = re.findall(instance_pattern, text)
        if instances:
            context["instances"] = instances
        
        return context
    
    def _extract_severity_context(self, text: str, matched_pattern: str) -> Dict[str, Any]:
        """Extract context around severity mentions."""
        context = {}
        
        # Look for frequency indicators
        frequency_patterns = ["only", "just", "all", "including", "exclude", "filter"]
        for pattern in frequency_patterns:
            if pattern in text:
                context["frequency_filter"] = pattern
        
        return context
    
    def _generate_time_range(self, time_type: str, now: datetime) -> Optional[Dict[str, Any]]:
        """Generate time range based on type."""
        time_ranges = {
            "last_hour": (timedelta(hours=1), "last hour", 60),
            "last_24_hours": (timedelta(days=1), "last 24 hours", 1440),
            "this_week": (timedelta(days=7), "this week", 10080),
            "yesterday": (timedelta(days=1), "yesterday", 1440),
            "last_30_minutes": (timedelta(minutes=30), "last 30 minutes", 30),
            "last_15_minutes": (timedelta(minutes=15), "last 15 minutes", 15)
        }
        
        if time_type not in time_ranges:
            return None
        
        delta, description, duration_minutes = time_ranges[time_type]
        start_time = now - delta
        
        # Special handling for yesterday
        if time_type == "yesterday":
            end_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            end_time = now
        
        return {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "description": description,
            "duration_minutes": duration_minutes
        }
    
    def _extract_relative_time(self, text: str, now: datetime) -> Optional[Dict[str, Any]]:
        """Extract relative time expressions."""
        # Handle "X minutes ago", "X hours ago", etc.
        relative_patterns = [
            (r'(\d+)\s*minutes?\s*ago', lambda m: timedelta(minutes=int(m.group(1)))),
            (r'(\d+)\s*hours?\s*ago', lambda m: timedelta(hours=int(m.group(1)))),
            (r'(\d+)\s*days?\s*ago', lambda m: timedelta(days=int(m.group(1)))),
        ]
        
        for pattern, time_func in relative_patterns:
            match = re.search(pattern, text)
            if match:
                delta = time_func(match)
                start_time = now - delta
                return {
                    "start_time": start_time.isoformat(),
                    "end_time": now.isoformat(),
                    "description": f"last {match.group(1)} {'minute' if 'minute' in pattern else 'hour' if 'hour' in pattern else 'day'}",
                    "extraction_method": "relative_time",
                    "confidence": 0.8
                }
        
        return None
    
    def _extract_absolute_time(self, text: str, now: datetime) -> Optional[Dict[str, Any]]:
        """Extract absolute time expressions."""
        # Handle "since 9 AM", "from 2 PM to 4 PM", etc.
        absolute_patterns = [
            (r'since\s+(\d{1,2})\s*(am|pm)', self._parse_time_since),
            (r'from\s+(\d{1,2})\s*(am|pm)\s+to\s+(\d{1,2})\s*(am|pm)', self._parse_time_range),
        ]
        
        for pattern, parser_func in absolute_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result = parser_func(match, now)
                if result:
                    result["extraction_method"] = "absolute_time"
                    result["confidence"] = 0.7
                    return result
        
        return None
    
    def _parse_time_since(self, match, now: datetime) -> Optional[Dict[str, Any]]:
        """Parse 'since X AM/PM' expressions."""
        try:
            hour = int(match.group(1))
            ampm = match.group(2).lower()
            
            if ampm == "pm" and hour != 12:
                hour += 12
            elif ampm == "am" and hour == 12:
                hour = 0
            
            start_time = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            if start_time > now:
                start_time = start_time - timedelta(days=1)
            
            return {
                "start_time": start_time.isoformat(),
                "end_time": now.isoformat(),
                "description": f"since {match.group(1)} {match.group(2).upper()}"
            }
        except:
            return None
    
    def _parse_time_range(self, match, now: datetime) -> Optional[Dict[str, Any]]:
        """Parse 'from X AM to Y PM' expressions."""
        try:
            start_hour = int(match.group(1))
            start_ampm = match.group(2).lower()
            end_hour = int(match.group(3))
            end_ampm = match.group(4).lower()
            
            # Convert to 24-hour format
            if start_ampm == "pm" and start_hour != 12:
                start_hour += 12
            elif start_ampm == "am" and start_hour == 12:
                start_hour = 0
            
            if end_ampm == "pm" and end_hour != 12:
                end_hour += 12
            elif end_ampm == "am" and end_hour == 12:
                end_hour = 0
            
            # Determine if this is today or yesterday
            start_time = now.replace(hour=start_hour, minute=0, second=0, microsecond=0)
            end_time = now.replace(hour=end_hour, minute=0, second=0, microsecond=0)
            
            if start_time > end_time:
                # Crosses midnight
                end_time = end_time + timedelta(days=1)
            
            if start_time > now:
                # This is for yesterday
                start_time = start_time - timedelta(days=1)
                end_time = end_time - timedelta(days=1)
            
            return {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "description": f"from {match.group(1)} {match.group(2).upper()} to {match.group(3)} {match.group(4).upper()}"
            }
        except:
            return None
