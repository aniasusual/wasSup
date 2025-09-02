"""
Smart LangGraph Agent - Main Entry Point

This module provides the main entry point for the intelligent log analysis agent.
It uses a modular architecture with separate components for different concerns.

The agent is organized into the following modules:
- core/: Core agent logic and state management
- parsers/: Text parsing and NLP capabilities  
- integrations/: GCP API clients and resource discovery
- workflows/: Workflow orchestration and graph building
- nodes/: Individual workflow node implementations
"""

from .agent import SmartLangGraphAgent, AgentState, InvestigationStep

# Backward compatibility exports
LangGraphAgent = SmartLangGraphAgent

__all__ = [
    "SmartLangGraphAgent",
    "LangGraphAgent",  # Backward compatibility
    "AgentState",
    "InvestigationStep"
]
