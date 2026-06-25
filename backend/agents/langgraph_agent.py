"""
LangGraph Agent for ContractAI Platform with Proper StateGraph Implementation
Uses LangGraph for orchestration with conditional routing and state management.
"""

import os
import sys
import json
import time
from typing import TypedDict, Annotated, List, Literal
from datetime import datetime
import operator

# Setup Django
django_project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, django_project_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
import django
django.setup()

from core.models import Contract, AnalysisResult

# Import LangGraph components
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# Import our MCP tools
from agents.mcp_server import (
    extract_clauses,
    generate_executive_summary,
    classify_contract,
    calculate_risk_score,
    mine_contract_intent,
    suggest_clause_improvements
)


# ========================================
# STATE DEFINITION
# ========================================
class ContractAnalysisState(TypedDict):
    """
    State object that flows through the LangGraph.
    Each node reads from and writes to this state.
    """
    # Input
    contract_id: str
    mode: str  # full, risk, intent, summary, extract, classify, suggest

    # Intermediate results (no accumulation needed, just replace)
    classification: dict
    risk_analysis: dict
    extracted_clauses: dict
    intent_analysis: dict
    executive_summary: dict
    clause_suggestions: dict

    # Metadata
    tools_used: Annotated[list, operator.add]
    errors: Annotated[list, operator.add]

    # Control flow
    next_step: str
    completed: bool


# ========================================
# AGENT NODES (Each tool becomes a node)
# ========================================

async def classify_node(state: ContractAnalysisState) -> ContractAnalysisState:
    """Node for contract classification."""
    try:
        result = await classify_contract(state["contract_id"])
        return {
            **state,
            "classification": json.loads(result),
            "tools_used": state.get("tools_used", []) + ["classify_contract"],
            "next_step": "risk"  # Route to risk analysis next
        }
    except Exception as e:
        return {
            **state,
            "errors": state.get("errors", []) + [{"node": "classify", "error": str(e)}],
            "next_step": "risk"  # Continue even if this fails
        }


async def risk_node(state: ContractAnalysisState) -> ContractAnalysisState:
    """Node for risk scoring."""
    try:
        result = await calculate_risk_score(state["contract_id"])
        return {
            **state,
            "risk_analysis": json.loads(result),
            "tools_used": state.get("tools_used", []) + ["calculate_risk"],
            "next_step": "extract"
        }
    except Exception as e:
        return {
            **state,
            "errors": state.get("errors", []) + [{"node": "risk", "error": str(e)}],
            "next_step": "extract"
        }


async def extract_node(state: ContractAnalysisState) -> ContractAnalysisState:
    """Node for clause extraction."""
    try:
        result = await extract_clauses(
            state["contract_id"],
            ["Liability", "Payment Terms", "Termination", "Indemnity", "Confidentiality"]
        )
        return {
            **state,
            "extracted_clauses": json.loads(result),
            "tools_used": state.get("tools_used", []) + ["extract_clauses"],
            "next_step": "intent"
        }
    except Exception as e:
        return {
            **state,
            "errors": state.get("errors", []) + [{"node": "extract", "error": str(e)}],
            "next_step": "intent"
        }


async def intent_node(state: ContractAnalysisState) -> ContractAnalysisState:
    """Node for intent mining."""
    try:
        result = await mine_contract_intent(state["contract_id"])
        return {
            **state,
            "intent_analysis": json.loads(result),
            "tools_used": state.get("tools_used", []) + ["mine_intent"],
            "next_step": "summary"
        }
    except Exception as e:
        return {
            **state,
            "errors": state.get("errors", []) + [{"node": "intent", "error": str(e)}],
            "next_step": "summary"
        }


async def summary_node(state: ContractAnalysisState) -> ContractAnalysisState:
    """Node for executive summary generation."""
    try:
        result = await generate_executive_summary(state["contract_id"])
        return {
            **state,
            "executive_summary": json.loads(result),
            "tools_used": state.get("tools_used", []) + ["generate_summary"],
            "next_step": "suggestions"
        }
    except Exception as e:
        return {
            **state,
            "errors": state.get("errors", []) + [{"node": "summary", "error": str(e)}],
            "next_step": "suggestions"
        }


async def suggestions_node(state: ContractAnalysisState) -> ContractAnalysisState:
    """Node for clause improvement suggestions."""
    try:
        result = await suggest_clause_improvements(state["contract_id"])
        return {
            **state,
            "clause_suggestions": json.loads(result),
            "tools_used": state.get("tools_used", []) + ["suggest_improvements"],
            "next_step": "save"
        }
    except Exception as e:
        return {
            **state,
            "errors": state.get("errors", []) + [{"node": "suggestions", "error": str(e)}],
            "next_step": "save"
        }


async def save_node(state: ContractAnalysisState) -> ContractAnalysisState:
    """Node for saving results to database."""
    try:
        # Collect results
        results = {}

        if state.get("classification"):
            results["classification"] = state["classification"]

        if state.get("risk_analysis"):
            results["risk_analysis"] = state["risk_analysis"]

        if state.get("extracted_clauses"):
            results["extracted_clauses"] = state["extracted_clauses"]

        if state.get("intent_analysis"):
            results["intent_analysis"] = state["intent_analysis"]

        if state.get("executive_summary"):
            results["executive_summary"] = state["executive_summary"]

        if state.get("clause_suggestions"):
            results["clause_suggestions"] = state["clause_suggestions"]

        # Save to database
        await save_analysis_results(state["contract_id"], results, state.get("tools_used", []))

        return {
            **state,
            "completed": True,
            "next_step": "end"
        }
    except Exception as e:
        return {
            **state,
            "errors": state.get("errors", []) + [{"node": "save", "error": str(e)}],
            "completed": True,
            "next_step": "end"
        }


# ========================================
# CONDITIONAL ROUTING LOGIC
# ========================================

def router(state: ContractAnalysisState) -> Literal["classify", "risk", "intent", "summary", "extract", "suggestions", "save", "end"]:
    """
    Router function that determines next node based on mode and current state.
    This enables conditional execution based on analysis mode.
    """
    mode = state.get("mode", "full")
    next_step = state.get("next_step", "")

    # If explicitly set to end
    if next_step == "end":
        return "end"

    # Mode-specific routing
    if mode == "full" or mode == "auto":
        # Full analysis: follow the complete pipeline
        if next_step == "risk":
            return "risk"
        elif next_step == "extract":
            return "extract"
        elif next_step == "intent":
            return "intent"
        elif next_step == "summary":
            return "summary"
        elif next_step == "suggestions":
            return "suggestions"
        elif next_step == "save":
            return "save"
        else:
            return "classify"  # Start with classification

    elif mode == "risk":
        # Risk-only mode
        if next_step == "save":
            return "save"
        return "risk"

    elif mode == "intent":
        if next_step == "save":
            return "save"
        return "intent"

    elif mode == "summary":
        if next_step == "save":
            return "save"
        return "summary"

    elif mode == "classify":
        if next_step == "save":
            return "save"
        return "classify"

    elif mode == "extract":
        if next_step == "save":
            return "save"
        return "extract"

    elif mode == "suggest" or mode == "suggestions":
        if next_step == "save":
            return "save"
        return "suggestions"

    # Default: go to save
    return "save"


# ========================================
# GRAPH CONSTRUCTION
# ========================================

def build_contract_analysis_graph() -> StateGraph:
    """
    Build the LangGraph StateGraph for contract analysis.

    Returns:
        Compiled StateGraph ready for execution
    """
    # Initialize the graph with state schema
    workflow = StateGraph(ContractAnalysisState)

    # Add all nodes
    workflow.add_node("classify", classify_node)
    workflow.add_node("risk", risk_node)
    workflow.add_node("extract", extract_node)
    workflow.add_node("intent", intent_node)
    workflow.add_node("summary", summary_node)
    workflow.add_node("suggestions", suggestions_node)
    workflow.add_node("save", save_node)

    # Set entry point with conditional routing
    workflow.set_conditional_entry_point(
        router,
        {
            "classify": "classify",
            "risk": "risk",
            "intent": "intent",
            "summary": "summary",
            "extract": "extract",
            "suggestions": "suggestions",
            "save": "save",
            "end": END
        }
    )

    # Add conditional edges from each node back to router
    for node_name in ["classify", "risk", "extract", "intent", "summary", "suggestions"]:
        workflow.add_conditional_edges(
            node_name,
            router,
            {
                "classify": "classify",
                "risk": "risk",
                "intent": "intent",
                "summary": "summary",
                "extract": "extract",
                "suggestions": "suggestions",
                "save": "save",
                "end": END
            }
        )

    # Save node always goes to END
    workflow.add_edge("save", END)

    # Compile with checkpointing for state persistence
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


# ========================================
# GLOBAL GRAPH INSTANCE
# ========================================
_graph = None

def get_graph():
    """Get or create the singleton graph instance."""
    global _graph
    if _graph is None:
        _graph = build_contract_analysis_graph()
    return _graph


# ========================================
# MAIN EXECUTION INTERFACE
# ========================================

async def analyze_contract_with_langgraph(contract_id: str, mode: str = "full") -> dict:
    """
    Analyze a contract using the LangGraph StateGraph.

    Args:
        contract_id: UUID of the contract
        mode: Analysis mode (full, risk, intent, summary, extract, classify, suggest)

    Returns:
        dict with analysis results and metadata
    """
    start_time = time.time()

    try:
        # Verify contract exists
        await Contract.objects.aget(id=contract_id)

        # Initialize state
        initial_state: ContractAnalysisState = {
            "contract_id": contract_id,
            "mode": mode,
            "classification": {},
            "risk_analysis": {},
            "extracted_clauses": {},
            "intent_analysis": {},
            "executive_summary": {},
            "clause_suggestions": {},
            "tools_used": [],
            "errors": [],
            "next_step": "",
            "completed": False
        }

        # Get graph instance
        graph = get_graph()

        # Execute the graph
        config = {"configurable": {"thread_id": f"contract-{contract_id}"}}
        final_state = await graph.ainvoke(initial_state, config)

        # Calculate execution time
        execution_time = time.time() - start_time

        # Build response
        results = {}

        if final_state.get("classification"):
            results["classification"] = final_state["classification"]

        if final_state.get("risk_analysis"):
            results["risk_analysis"] = final_state["risk_analysis"]

        if final_state.get("extracted_clauses"):
            results["extracted_clauses"] = final_state["extracted_clauses"]

        if final_state.get("intent_analysis"):
            results["intent_analysis"] = final_state["intent_analysis"]

        if final_state.get("executive_summary"):
            results["executive_summary"] = final_state["executive_summary"]

        if final_state.get("clause_suggestions"):
            results["clause_suggestions"] = final_state["clause_suggestions"]

        return {
            "status": "success",
            "contract_id": contract_id,
            "mode": mode,
            "results": results,
            "tools_used": final_state.get("tools_used", []),
            "errors": final_state.get("errors", []),
            "execution_time_seconds": round(execution_time, 2),
            "graph_execution": "completed"
        }

    except Contract.DoesNotExist:
        return {
            "status": "error",
            "message": f"Contract {contract_id} not found",
            "execution_time_seconds": round(time.time() - start_time, 2)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"LangGraph execution error: {str(e)}",
            "execution_time_seconds": round(time.time() - start_time, 2)
        }


# ========================================
# DATABASE PERSISTENCE
# ========================================

async def save_analysis_results(contract_id: str, results: dict, tools_used: List[str]):
    """Save analysis results to the AnalysisResult model and update Contract metadata."""
    try:
        risk_data = results.get("risk_analysis", {})
        intent_data = results.get("intent_analysis", {})
        summary_data = results.get("executive_summary", {})
        classification_data = results.get("classification", {})
        clauses_data = results.get("extracted_clauses", {})

        # Save to AnalysisResult
        analysis_data = {
            "contract_id": contract_id,
            "executive_summary": summary_data.get("summary_text", ""),
            "risk_score": risk_data.get("risk_score"),
            "risk_level": risk_data.get("risk_level"),
            "risk_flags": risk_data.get("deviations", []),
            "extracted_clauses": clauses_data.get("extracted_clauses", {}),
            "agent_metadata": {
                "classification": classification_data.get("classified_as"),
                "classification_confidence": classification_data.get("confidence"),
                "intent_analysis": intent_data.get("all_intents", {}),
                "langgraph": True,
                "version": "2.0"
            },
            "primary_intent": intent_data.get("primary_intent"),
            "intent_confidence": intent_data.get("all_intents", {}).get(
                intent_data.get("primary_intent", ""), {}
            ).get("confidence"),
            "agent_version": "2.0-langgraph",
            "tools_used": tools_used,
        }

        await AnalysisResult.objects.aupdate_or_create(
            contract_id=contract_id,
            defaults=analysis_data
        )

        # Update Contract model with extracted metadata from summary
        contract_updates = {}

        # Update classification if available
        if classification_data.get("classified_as"):
            contract_updates["contract_type"] = classification_data["classified_as"]

        # Update metadata from summary_data if available
        if summary_data:
            summary_metadata = summary_data.get("summary_data", {})
            if summary_metadata:
                if summary_metadata.get("contract_value"):
                    contract_updates["contract_value"] = summary_metadata["contract_value"]

                party_a = summary_metadata.get("party_a")
                party_b = summary_metadata.get("party_b")

                if party_a:
                    contract_updates["party_a"] = party_a
                if party_b:
                    contract_updates["party_b"] = party_b

                # Update party_name with combined parties for backward compatibility
                if party_a and party_b:
                    contract_updates["party_name"] = f"{party_a} & {party_b}"
                elif party_a:
                    contract_updates["party_name"] = party_a
                elif party_b:
                    contract_updates["party_name"] = party_b

                if summary_metadata.get("duration"):
                    contract_updates["contract_duration"] = summary_metadata["duration"]
                if summary_metadata.get("jurisdiction"):
                    contract_updates["jurisdiction"] = summary_metadata["jurisdiction"]
                if summary_metadata.get("payment_terms"):
                    contract_updates["payment_terms"] = summary_metadata["payment_terms"]
                if summary_metadata.get("liability_level"):
                    contract_updates["liability_level"] = summary_metadata["liability_level"]
                if "has_arbitration" in summary_metadata:
                    contract_updates["has_arbitration"] = summary_metadata["has_arbitration"]

        # Apply updates to Contract model if any
        if contract_updates:
            await Contract.objects.filter(id=contract_id).aupdate(**contract_updates)

    except Exception as e:
        print(f"Error saving LangGraph results: {str(e)}")


# ========================================
# CONVENIENCE WRAPPER (maintains backward compatibility)
# ========================================

async def run_analysis_workflow(contract_id: str, user_query: str = None, mode: str = "full") -> dict:
    """
    Convenience function for backward compatibility with existing API.
    Now uses LangGraph under the hood.
    """
    # Infer mode from user query if provided
    if user_query:
        query_lower = user_query.lower()
        if any(word in query_lower for word in ["risk", "risky", "dangerous"]):
            mode = "risk"
        elif any(word in query_lower for word in ["intent", "purpose", "goal"]):
            mode = "intent"
        elif any(word in query_lower for word in ["summary", "overview", "tldr"]):
            mode = "summary"
        elif any(word in query_lower for word in ["classify", "type", "category"]):
            mode = "classify"
        elif any(word in query_lower for word in ["extract", "clause", "provision"]):
            mode = "extract"
        elif any(word in query_lower for word in ["suggest", "improve", "recommendation"]):
            mode = "suggest"

    # Execute with LangGraph
    return await analyze_contract_with_langgraph(contract_id, mode)
