"""
ContractAI Agent - Now powered by LangGraph StateGraph
This module provides backward-compatible API while using LangGraph orchestration.
"""

import os
import sys
import json
import time
from typing import List
from datetime import datetime

# Setup Django
django_project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, django_project_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_backend.settings')
import django
django.setup()

from core.models import Contract, AnalysisResult

# Import LangGraph-powered agent
from agents.langgraph_agent import analyze_contract_with_langgraph


# ========================================
# BACKWARD-COMPATIBLE WRAPPER CLASS
# ========================================
class ContractAgent:
    """
    ContractAgent now delegates to LangGraph StateGraph for orchestration.
    Maintains backward compatibility with existing API.
    """

    def __init__(self):
        """Initialize the agent - now just a thin wrapper"""
        pass

    async def analyze_contract(self, contract_id: str, mode: str = "full") -> dict:
        """
        Main entry point for contract analysis - now delegates to LangGraph.

        Args:
            contract_id: UUID of contract to analyze
            mode: Analysis mode - "full", "risk", "intent", "summary", "extract", "classify", "suggest"

        Returns:
            dict with analysis results
        """
        # Delegate to LangGraph StateGraph implementation
        return await analyze_contract_with_langgraph(contract_id, mode)



# ========================================
# GLOBAL AGENT INSTANCE (LAZY INITIALIZATION)
# ========================================
_contract_agent = None

def get_contract_agent():
    """Get or create the singleton contract agent instance"""
    global _contract_agent
    if _contract_agent is None:
        _contract_agent = ContractAgent()
    return _contract_agent


# ========================================
# CONVENIENCE FUNCTION FOR API VIEWS (Now uses LangGraph)
# ========================================
async def run_analysis_workflow(contract_id: str, user_query: str = None, mode: str = "full") -> dict:
    """
    Convenience function to run the contract analysis workflow.
    This is what the Django API will call. Now powered by LangGraph.

    Args:
        contract_id: Contract UUID to analyze
        user_query: Optional natural language query from user
        mode: Analysis mode (full, risk, intent, summary, extract, classify, suggest)

    Returns:
        dict with analysis results
    """
    # If user query is provided, try to infer mode
    if user_query:
        query_lower = user_query.lower()
        if "risk" in query_lower:
            mode = "risk"
        elif "intent" in query_lower or "purpose" in query_lower:
            mode = "intent"
        elif "summary" in query_lower or "summarize" in query_lower:
            mode = "summary"
        elif "classify" in query_lower or "type" in query_lower:
            mode = "classify"
        elif "extract" in query_lower or "clause" in query_lower:
            mode = "extract"
        elif "suggest" in query_lower or "improve" in query_lower or "fix" in query_lower:
            mode = "suggest"

    # Run the agent (lazy initialization)
    agent = get_contract_agent()
    result = await agent.analyze_contract(contract_id, mode)
    return result


# ========================================
# CLI TESTING
# ========================================
if __name__ == "__main__":
    import asyncio

    async def test_agent():
        # Test with a sample contract ID
        print("🤖 Testing ContractAI Agent...")
        print("\nEnter a contract ID to test:")
        test_contract_id = input("> ").strip()

        print("\nSelect mode:")
        print("1. Full Analysis")
        print("2. Risk Only")
        print("3. Intent Only")
        print("4. Summary Only")
        print("5. Classify Only")
        print("6. Extract Clauses")

        mode_choice = input("> ").strip()
        mode_map = {
            "1": "full",
            "2": "risk",
            "3": "intent",
            "4": "summary",
            "5": "classify",
            "6": "extract"
        }
        mode = mode_map.get(mode_choice, "full")

        result = await run_analysis_workflow(test_contract_id, mode=mode)
        print("\n" + "="*50)
        print("AGENT RESULT:")
        print("="*50)
        print(json.dumps(result, indent=2))

    asyncio.run(test_agent())
