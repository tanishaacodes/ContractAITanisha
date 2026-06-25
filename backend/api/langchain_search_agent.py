import os
"""
LangChain Agent Framework for Smart Search
Simplified implementation using modern LangChain API
"""
from typing import List, Dict, Any, Optional
from langchain_core.tools import Tool
import requests
import json
import re

# Use langchain_ollama if available (newer), fall back gracefully
try:
    from langchain_ollama import OllamaLLM as _OllamaLLM
    _OLLAMA_CLS = _OllamaLLM
except ImportError:
    try:
        from langchain_community.llms import Ollama as _OllamaLLM
        _OLLAMA_CLS = _OllamaLLM
    except ImportError:
        _OLLAMA_CLS = None


class SmartSearchLangChainAgent:
    """
    LangChain-powered agent for intelligent contract search.
    Uses simplified ReAct-style reasoning with modern LangChain.
    """

    def __init__(self, base_url: str = "http://localhost:8002", auth_token: str = None):
        """Initialize LangChain agent with tools."""
        self.base_url = base_url
        self.auth_token = auth_token

        # Initialize LLM (Qwen via Ollama) — falls back to direct HTTP if LangChain unavailable
        self.llm = None
        if _OLLAMA_CLS is not None:
            try:
                self.llm = _OLLAMA_CLS(
                    model="qwen2.5:0.5b",
                    base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                    temperature=0.7
                )
            except Exception:
                self.llm = None

        # Create tools
        self.tools = self._create_tools()
        self.tool_map = {tool.name: tool for tool in self.tools}

        # Chat history for context
        self.chat_history = []

    def _get_headers(self):
        """Get request headers with authentication."""
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers


    def _create_tools(self) -> List[Tool]:
        """Create LangChain tools for the agent."""

        def semantic_search(query: str) -> str:
            """Search contracts using semantic embeddings (FAISS + MiniLM)."""
            try:
                response = requests.post(
                    f"{self.base_url}/api/search-intelligence/semantic/",
                    json={"query": query, "limit": 5},
                    headers=self._get_headers(),
                    timeout=30
                )
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])
                    if results:
                        summary = f"Found {len(results)} contracts:\n"
                        for r in results[:3]:
                            summary += f"- {r.get('title', 'Untitled')}: {r.get('snippet', '')[:100]}...\n"
                        return summary
                    return "No results found."
                return "Search failed."
            except Exception as e:
                return f"Error: {str(e)}"

        def graph_query(query: str) -> str:
            """Query Neo4j knowledge graph for connected risks and relationships."""
            try:
                # Determine query type from input
                query_lower = query.lower()
                if 'high risk' in query_lower or 'risky' in query_lower:
                    query_type = 'high_risk'
                elif 'cascade' in query_lower or 'connected' in query_lower:
                    query_type = 'cascading_fm'
                elif 'obligation' in query_lower:
                    query_type = 'obligations'
                else:
                    query_type = 'connected_risks'

                response = requests.post(
                    f"{self.base_url}/api/search-intelligence/graph-multihop/",
                    json={"query_type": query_type},
                    headers=self._get_headers(),
                    timeout=30
                )
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])
                    if results:
                        summary = f"Graph query found {len(results)} connected nodes:\n"
                        for r in results[:3]:
                            summary += f"- Contract: {r.get('contract', 'N/A')}, Risk: {r.get('risk_score', 0):.2f}\n"
                        return summary
                    return "No graph connections found."
                return "Graph query failed."
            except Exception as e:
                return f"Error: {str(e)}"

        def force_majeure_scorer(contract_id: str) -> str:
            """Score Force Majeure risk for a specific contract."""
            try:
                response = requests.post(
                    f"{self.base_url}/api/search-intelligence/fm-score/",
                    json={"contract_id": int(contract_id)},
                    headers=self._get_headers(),
                    timeout=30
                )
                if response.status_code == 200:
                    data = response.json()
                    score = data.get('overall_fm_risk_score', 0)
                    level = data.get('risk_level', 'UNKNOWN')
                    return f"Force Majeure Risk: {score:.2f} ({level})"
                return "FM scoring failed."
            except Exception as e:
                return f"Error: {str(e)}"

        def get_analytics(query: str = "") -> str:
            """Get portfolio analytics and statistics."""
            try:
                response = requests.get(
                    f"{self.base_url}/api/search-intelligence/analytics/",
                    headers=self._get_headers(),
                    timeout=30
                )
                if response.status_code == 200:
                    data = response.json()
                    summary = data.get('summary', {})
                    return f"Portfolio: {summary.get('total_contracts', 0)} contracts, " \
                           f"{summary.get('high_risk_contracts', 0)} high risk, " \
                           f"{summary.get('total_clauses', 0)} total clauses"
                return "Analytics unavailable."
            except Exception as e:
                return f"Error: {str(e)}"

        def clause_benchmark(clause_text: str) -> str:
            """Benchmark a clause against industry standards."""
            try:
                response = requests.post(
                    f"{self.base_url}/api/search-intelligence/benchmark/",
                    json={"clause_text": clause_text},
                    headers=self._get_headers(),
                    timeout=30
                )
                if response.status_code == 200:
                    data = response.json()
                    rating = data.get('rating', 'UNKNOWN')
                    analysis = data.get('llm_analysis', '')
                    return f"Benchmark Rating: {rating}\nAnalysis: {analysis}"
                return "Benchmarking failed."
            except Exception as e:
                return f"Error: {str(e)}"

        def negotiate_clause(clause_text: str) -> str:
            """Run buyer-supplier negotiation simulation on a clause."""
            try:
                response = requests.post(
                    f"{self.base_url}/api/search-intelligence/negotiate/",
                    json={
                        "clause": clause_text,
                        "rounds": 2,
                        "buyer_personality": "balanced",
                        "supplier_personality": "balanced"
                    },
                    headers=self._get_headers(),
                    timeout=60
                )
                if response.status_code == 200:
                    data = response.json()
                    final_clause = data.get('final_clause', '')
                    improvement = data.get('improvement_score', 0)
                    return f"Negotiation completed. Improvement: {improvement:.1f}%\nFinal: {final_clause[:150]}..."
                return "Negotiation failed."
            except Exception as e:
                return f"Error: {str(e)}"

        # Define tools
        tools = [
            Tool(
                name="SemanticSearch",
                func=semantic_search,
                description="Useful for finding contracts by semantic meaning. Input should be a natural language query."
            ),
            Tool(
                name="GraphQuery",
                func=graph_query,
                description="Useful for finding connected risks, cascading effects, and contract relationships in the knowledge graph. Input should describe what relationships to find."
            ),
            Tool(
                name="ForceMajeureScorer",
                func=force_majeure_scorer,
                description="Useful for scoring Force Majeure risk for a specific contract. Input should be a contract ID number."
            ),
            Tool(
                name="GetAnalytics",
                func=get_analytics,
                description="Useful for getting portfolio statistics and analytics. No input needed."
            ),
            Tool(
                name="ClauseBenchmark",
                func=clause_benchmark,
                description="Useful for comparing a clause against industry benchmarks. Input should be the clause text."
            ),
            Tool(
                name="NegotiateClause",
                func=negotiate_clause,
                description="Useful for simulating buyer-supplier negotiation on a clause. Input should be the clause text."
            )
        ]

        return tools

    def _select_tool_from_query(self, query: str) -> tuple:
        """Intelligently select tool based on query keywords (fallback for small models)."""
        query_lower = query.lower()

        # Keyword-based tool selection
        # Neo4j is now populated with contract/clause data!
        if any(word in query_lower for word in ['force majeure', 'fm risk', 'fm score']):
            return 'GraphQuery', 'high risk force majeure contracts'
        elif any(word in query_lower for word in ['cascade', 'cascading']):
            return 'GraphQuery', 'cascading force majeure risks'
        elif any(word in query_lower for word in ['high risk', 'risky', 'dangerous']):
            return 'GraphQuery', 'high risk contracts'
        elif any(word in query_lower for word in ['connected', 'relationship', 'linked']):
            return 'GraphQuery', 'connected risks and relationships'
        elif any(word in query_lower for word in ['statistics', 'analytics', 'portfolio', 'summary']):
            return 'GetAnalytics', ''
        elif any(word in query_lower for word in ['benchmark', 'compare', 'standard']):
            return 'SemanticSearch', query
        elif any(word in query_lower for word in ['negotiate', 'negotiation']):
            return 'SemanticSearch', query
        else:
            # Default to semantic search for general queries
            return 'SemanticSearch', query

    def search(self, query: str) -> Dict[str, Any]:
        """
        Execute intelligent search with automatic tool selection.
        Falls back to keyword-based tool selection for small models.

        Args:
            query: Natural language search query

        Returns:
            Dict with answer and tool usage information
        """
        try:
            intermediate_steps = []
            tools_used = []

            # Step 1: Use keyword-based tool selection (more reliable for small models)
            tool_name, tool_input = self._select_tool_from_query(query)

            # Step 2: Execute the selected tool
            if tool_name in self.tool_map:
                tool = self.tool_map[tool_name]
                try:
                    observation = tool.func(tool_input if tool_input else query)
                    intermediate_steps.append({
                        'tool': tool_name,
                        'input': tool_input if tool_input else query,
                        'output': observation
                    })
                    tools_used.append(tool_name)

                    # Step 3: Use LLM to format the final answer
                    answer_prompt = f"""Based on the following search results, provide a clear answer to the user's question.

User question: {query}

Tool used: {tool_name}
Results: {observation}

Provide a concise, helpful answer:"""

                    if self.llm is not None:
                        final_answer = self.llm.invoke(answer_prompt)
                    else:
                        # Direct Ollama HTTP fallback
                        resp = requests.post(
                            os.getenv("OLLAMA_BASE_URL", os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")) + "/api/generate",
                            json={"model": "qwen2.5:0.5b", "prompt": answer_prompt, "stream": False},
                            timeout=45
                        )
                        final_answer = resp.json().get("response", observation) if resp.status_code == 200 else observation

                    return {
                        'answer': final_answer,
                        'intermediate_steps': intermediate_steps,
                        'tools_used': tools_used,
                        'success': True
                    }

                except Exception as e:
                    return {
                        'answer': f"Tool execution error: {str(e)}",
                        'intermediate_steps': intermediate_steps,
                        'tools_used': tools_used,
                        'success': False,
                        'error': str(e)
                    }
            else:
                return {
                    'answer': f"Could not find appropriate tool for query: {query}",
                    'intermediate_steps': [],
                    'tools_used': [],
                    'success': False,
                    'error': 'Tool not found'
                }

        except Exception as e:
            return {
                'answer': f"Agent error: {str(e)}",
                'intermediate_steps': [],
                'tools_used': [],
                'success': False,
                'error': str(e)
            }

    def chat(self, message: str) -> str:
        """
        Chat interface with memory.

        Args:
            message: User message

        Returns:
            Agent response
        """
        result = self.search(message)
        return result.get('answer', 'No response generated.')


# Singleton instance
_langchain_agent = None

def get_langchain_search_agent() -> SmartSearchLangChainAgent:
    """Get or create LangChain search agent singleton."""
    global _langchain_agent
    if _langchain_agent is None:
        _langchain_agent = SmartSearchLangChainAgent()
    return _langchain_agent
