"""
MCP Server for ContractAI Platform
Model Context Protocol Server that exposes 5 AI tools for contract analysis.

Tools:
1. extract_clauses - Extract specific contract provisions
2. generate_executive_summary - Create high-level summary
3. classify_contract - Determine contract type
4. calculate_risk_score - Score contract risk
5. mine_contract_intent - Analyze business intent
"""

import os
import sys
import json
import asyncio
import re
from typing import List, Dict, Any
from datetime import datetime
import httpx

# Add Django project to Python path
django_project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, django_project_path)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_backend.settings')
import django
django.setup()

# Now import Django models
from core.models import Contract, AnalysisResult, Clause, Intent
from asgiref.sync import sync_to_async

# Import FastMCP
from mcp.server.fastmcp import FastMCP

# Initialize MCP Server
mcp = FastMCP("ContractAI-Intelligence-Suite")

# Ollama configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
OLLAMA_MODEL = "qwen2.5:7b"


# ========================================
# HELPER: OLLAMA API CALL
# ========================================
async def call_ollama(prompt: str, max_tokens: int = 500, timeout: float = 120.0) -> str:
    """
    Call Ollama API for text generation.

    Args:
        prompt: The prompt to send to the model
        max_tokens: Maximum tokens to generate
        timeout: Request timeout in seconds (default: 120)

    Returns:
        Generated text response
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": 0.3,
                    }
                }
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                error_msg = f"Error: Ollama returned status {response.status_code}"
                print(f"[OLLAMA ERROR] {error_msg}")
                print(f"[OLLAMA ERROR] Response: {response.text}")
                return error_msg

    except Exception as e:
        error_msg = f"Error calling Ollama: {str(e)}"
        print(f"[OLLAMA EXCEPTION] {error_msg}")
        print(f"[OLLAMA EXCEPTION] Exception type: {type(e).__name__}")
        import traceback
        print(f"[OLLAMA EXCEPTION] Traceback:\n{traceback.format_exc()}")
        return error_msg


# ========================================
# TOOL 1: CLAUSE EXTRACTION
# ========================================
@mcp.tool()
async def extract_clauses(contract_id: str, clause_types: List[str]) -> str:
    """
    Extracts specific provisions from a contract.

    Args:
        contract_id: The UUID of the contract to analyze
        clause_types: List of clause types to extract (e.g., ["Liability", "Payment", "Termination"])

    Returns:
        JSON string with extracted clause text
    """
    try:
        # Fetch contract
        contract = await sync_to_async(Contract.objects.get)(id=contract_id)

        # Fetch existing clauses from database
        clauses = await sync_to_async(list)(
            Clause.objects.filter(
                contract_id=contract_id,
                clause_name__in=clause_types
            ).values('clause_name', 'extracted_text', 'confidence')
        )

        if not clauses:
            return json.dumps({
                "status": "no_clauses_found",
                "message": f"No clauses found for types: {', '.join(clause_types)}",
                "contract_filename": contract.original_filename
            })

        # Format results
        extracted = {}
        for clause in clauses:
            extracted[clause['clause_name']] = {
                "text": clause['extracted_text'] or "Not extracted",
                "confidence": clause['confidence'] or 0.0
            }

        return json.dumps({
            "status": "success",
            "contract_filename": contract.original_filename,
            "contract_id": contract_id,
            "extracted_clauses": extracted,
            "total_found": len(clauses)
        }, indent=2)

    except Contract.DoesNotExist:
        return json.dumps({
            "status": "error",
            "message": f"Contract with ID {contract_id} not found"
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Error extracting clauses: {str(e)}"
        })


# ========================================
# TOOL 2: EXECUTIVE SUMMARY GENERATION
# ========================================
@mcp.tool()
async def generate_executive_summary(contract_id: str) -> str:
    """
    Creates a high-level executive summary of the contract.
    Highlights key dates, parties, value, and critical terms.

    Args:
        contract_id: The UUID of the contract to summarize

    Returns:
        JSON string with executive summary
    """
    try:
        # Fetch contract with related data
        contract = await sync_to_async(Contract.objects.select_related('user').get)(id=contract_id)

        # Gather key information
        summary_data = {
            "contract_filename": contract.original_filename,
            "contract_type": contract.contract_type or "Unknown",
            "uploaded_date": contract.uploaded_at.strftime("%Y-%m-%d") if contract.uploaded_at else None,

            # Parties
            "party_a": contract.party_a or "Not specified",
            "party_b": contract.party_b or "Not specified",

            # Financial & Duration
            "contract_value": contract.contract_value or "Not specified",
            "start_date": contract.start_date.strftime("%Y-%m-%d") if contract.start_date else None,
            "end_date": contract.end_date.strftime("%Y-%m-%d") if contract.end_date else None,
            "duration": contract.contract_duration or "Not specified",

            # Legal terms
            "jurisdiction": contract.jurisdiction or "Not specified",
            "payment_terms": contract.payment_terms or "Not specified",
            "liability_level": contract.liability_level or "Not assessed",
            "has_arbitration": contract.has_arbitration,

            # Status
            "workflow_status": contract.status,
        }

        # Extract metadata from contract text if not already populated
        contract_text = contract.full_text or ""

        if contract_text and (
            summary_data["contract_type"] == "Unknown" or
            summary_data["contract_value"] == "Not specified" or
            summary_data["party_a"] == "Not specified" or
            summary_data["duration"] == "Not specified"
        ):
            # Use AI to extract key metadata
            text_excerpt = contract_text[:3500]
            extraction_prompt = f"""You are analyzing a legal contract. Extract ONLY the following specific information. Be concise and precise.

CONTRACT TEXT:
{text_excerpt}

INSTRUCTIONS:
- For CONTRACT_TYPE: Use standard abbreviations like "MSA", "NDA", "SLA", "SOW", "Purchase Agreement", "Service Agreement", etc.
- For PARTY_A and PARTY_B: Extract ONLY the legal entity names (company/organization names), not descriptions
- For CONTRACT_VALUE: Extract the total monetary amount with currency (e.g., "AED 3,300,000.00" or "$50,000")
- For DURATION: Extract the term/period (e.g., "12 months", "3 years", "Valid until 2025-12-31")
- For JURISDICTION: Extract governing law location (e.g., "Dubai", "New York", "England and Wales")
- For PAYMENT_TERMS: Brief summary (e.g., "NET 30", "Monthly installments", "Upon delivery")

RESPOND IN THIS EXACT FORMAT (one value per line):
CONTRACT_TYPE: [type]
PARTY_A: [name only]
PARTY_B: [name only]
CONTRACT_VALUE: [amount with currency]
DURATION: [term/period]
JURISDICTION: [location]
PAYMENT_TERMS: [summary]

If any field cannot be found, write "Not specified" for that field ONLY."""

            extraction_result = await call_ollama(extraction_prompt, max_tokens=250, timeout=150.0)

            # Parse extraction result
            if extraction_result and "Error" not in extraction_result:
                import re

                contract_type_match = re.search(r'CONTRACT_TYPE:\s*(.+?)(?:\n|$)', extraction_result, re.IGNORECASE)
                party_a_match = re.search(r'PARTY_A:\s*(.+?)(?:\n|$)', extraction_result, re.IGNORECASE)
                party_b_match = re.search(r'PARTY_B:\s*(.+?)(?:\n|$)', extraction_result, re.IGNORECASE)
                value_match = re.search(r'CONTRACT_VALUE:\s*(.+?)(?:\n|$)', extraction_result, re.IGNORECASE)
                duration_match = re.search(r'DURATION:\s*(.+?)(?:\n|$)', extraction_result, re.IGNORECASE)
                jurisdiction_match = re.search(r'JURISDICTION:\s*(.+?)(?:\n|$)', extraction_result, re.IGNORECASE)
                payment_match = re.search(r'PAYMENT_TERMS:\s*(.+?)(?:\n|$)', extraction_result, re.IGNORECASE)

                # Update contract_type
                if contract_type_match:
                    extracted_type = contract_type_match.group(1).strip()
                    if extracted_type and extracted_type.lower() != "not specified":
                        summary_data["contract_type"] = extracted_type

                # Update parties
                if party_a_match:
                    extracted_a = party_a_match.group(1).strip()
                    if extracted_a and extracted_a.lower() != "not specified":
                        summary_data["party_a"] = extracted_a

                if party_b_match:
                    extracted_b = party_b_match.group(1).strip()
                    if extracted_b and extracted_b.lower() != "not specified":
                        summary_data["party_b"] = extracted_b

                # Update contract value
                if value_match:
                    extracted_value = value_match.group(1).strip()
                    if extracted_value and extracted_value.lower() != "not specified":
                        summary_data["contract_value"] = extracted_value

                # Update duration
                if duration_match:
                    extracted_duration = duration_match.group(1).strip()
                    if extracted_duration and extracted_duration.lower() != "not specified":
                        summary_data["duration"] = extracted_duration

                # Update jurisdiction
                if jurisdiction_match:
                    extracted_jurisdiction = jurisdiction_match.group(1).strip()
                    if extracted_jurisdiction and extracted_jurisdiction.lower() != "not specified":
                        summary_data["jurisdiction"] = extracted_jurisdiction

                # Update payment terms
                if payment_match:
                    extracted_payment = payment_match.group(1).strip()
                    if extracted_payment and extracted_payment.lower() != "not specified":
                        summary_data["payment_terms"] = extracted_payment

        # Generate AI-enhanced executive summary using Ollama
        if contract_text:
            # Truncate for AI processing
            text_excerpt = contract_text[:3000]

            # Create comprehensive prompt for AI summary
            summary_prompt = f"""You are a legal contract analyst. Generate a comprehensive executive summary for this contract.

Contract Details:
- Filename: {summary_data['contract_filename']}
- Type: {summary_data['contract_type']}
- Parties: {summary_data['party_a']} and {summary_data['party_b']}
- Value: {summary_data['contract_value']}
- Duration: {summary_data['duration']}
- Jurisdiction: {summary_data['jurisdiction']}

Contract Text Excerpt:
{text_excerpt}

Generate a professional executive summary in the following format:

EXECUTIVE SUMMARY

Overview:
[2-3 sentences describing the nature and purpose of this agreement]

Key Parties:
- Party A: [name and role]
- Party B: [name and role]

Financial Terms:
[Summarize payment terms, contract value, and financial obligations]

Duration & Termination:
[Summarize contract duration, start/end dates, and termination conditions]

Critical Legal Provisions:
[List 3-4 most important legal terms, obligations, or restrictions]

Risk Assessment:
[Brief 1-2 sentence assessment of potential risks or concerns]

Recommendations:
[1-2 key recommendations for stakeholders]"""

            # Call Ollama to generate AI summary with extended timeout
            ai_summary = await call_ollama(summary_prompt, max_tokens=800, timeout=240.0)

            # Use AI-generated summary if available, otherwise fall back to structured format
            if ai_summary and len(ai_summary) > 50 and "Error" not in ai_summary:
                summary_text = ai_summary
            else:
                # Fallback to structured summary
                summary_text = f"""
EXECUTIVE SUMMARY: {summary_data['contract_filename']}

This {summary_data['contract_type'] or 'contract'} establishes a legal agreement between {summary_data['party_a']} and {summary_data['party_b']}.

KEY TERMS:
• Contract Value: {summary_data['contract_value']}
• Duration: {summary_data['duration']}
• Payment Terms: {summary_data['payment_terms']}
• Jurisdiction: {summary_data['jurisdiction']}
• Liability Level: {summary_data['liability_level']}

CONTRACT PERIOD:
From {summary_data['start_date'] or 'Not specified'} to {summary_data['end_date'] or 'Not specified'}

LEGAL PROVISIONS:
• Arbitration: {'Included' if summary_data['has_arbitration'] else 'Not included'}
• Governing Law: {summary_data['jurisdiction']}

Current Status: {summary_data['workflow_status']}
                """.strip()
        else:
            # No contract text available - use basic structured format
            summary_text = f"""
EXECUTIVE SUMMARY: {summary_data['contract_filename']}

CONTRACT TYPE: {summary_data['contract_type']}

PARTIES:
- Party A: {summary_data['party_a']}
- Party B: {summary_data['party_b']}

FINANCIAL TERMS:
- Contract Value: {summary_data['contract_value']}
- Payment Terms: {summary_data['payment_terms']}

DURATION:
- Start Date: {summary_data['start_date'] or 'Not specified'}
- End Date: {summary_data['end_date'] or 'Not specified'}
- Duration: {summary_data['duration']}

LEGAL TERMS:
- Jurisdiction: {summary_data['jurisdiction']}
- Liability Level: {summary_data['liability_level']}
- Arbitration Clause: {'Yes' if summary_data['has_arbitration'] else 'No'}

STATUS: {summary_data['workflow_status']}
            """.strip()

        return json.dumps({
            "status": "success",
            "contract_id": contract_id,
            "summary_text": summary_text,
            "summary_data": summary_data
        }, indent=2)

    except Contract.DoesNotExist:
        return json.dumps({
            "status": "error",
            "message": f"Contract with ID {contract_id} not found"
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Error generating summary: {str(e)}"
        })


# ========================================
# TOOL 3: CONTRACT CLASSIFICATION
# ========================================
@mcp.tool()
async def classify_contract(contract_id: str) -> str:
    """
    Determines the contract type using AI classification.
    Updates the contract category in the database.

    Args:
        contract_id: The UUID of the contract to classify

    Returns:
        JSON string with classification results
    """
    try:
        # Fetch contract
        contract = await sync_to_async(Contract.objects.get)(id=contract_id)

        # Check if already classified
        existing_type = contract.contract_type

        # Get fusion scores if available (from existing BERTopic/BERT models)
        fused_scores = contract.fused_scores or {}
        bert_topics = contract.bert_topics or {}

        # If not classified, use AI to classify
        if not existing_type:
            contract_text = contract.full_text or ""
            if contract_text:
                # Truncate for AI processing
                text_excerpt = contract_text[:2000]

                # Create classification prompt
                classification_prompt = f"""You are a legal contract expert. Analyze this contract and classify it into ONE of these categories:

Contract Categories:
- Employment Agreement
- Service Agreement
- Purchase Agreement
- Sales Agreement
- Non-Disclosure Agreement (NDA)
- Consulting Agreement
- Lease Agreement
- Partnership Agreement
- License Agreement
- Supply Agreement
- Construction Agreement
- Maintenance Agreement
- Distribution Agreement
- Technology Agreement
- Other

Contract Filename: {contract.original_filename}

Contract Text:
{text_excerpt}

Respond with ONLY the category name from the list above. No explanations."""

                # Call Ollama for classification
                ai_classification = await call_ollama(classification_prompt, max_tokens=50)

                # Extract classification from response
                ai_classification = ai_classification.strip()

                # Use AI classification
                existing_type = ai_classification
                confidence = 0.85  # AI-based confidence
            else:
                # Fallback based on filename
                filename_lower = contract.original_filename.lower()
                if 'nda' in filename_lower or 'non-disclosure' in filename_lower:
                    existing_type = "Non-Disclosure Agreement (NDA)"
                elif 'service' in filename_lower:
                    existing_type = "Service Agreement"
                elif 'purchase' in filename_lower or 'po' in filename_lower:
                    existing_type = "Purchase Agreement"
                elif 'employment' in filename_lower:
                    existing_type = "Employment Agreement"
                elif 'lease' in filename_lower:
                    existing_type = "Lease Agreement"
                elif 'construction' in filename_lower:
                    existing_type = "Construction Agreement"
                elif 'supply' in filename_lower:
                    existing_type = "Supply Agreement"
                else:
                    existing_type = "Other"
                confidence = 0.60  # Filename-based confidence

        # Determine classification result
        classification_result = {
            "status": "success",
            "contract_id": contract_id,
            "filename": contract.original_filename,
            "classified_as": existing_type,
            "confidence": contract.confidence_score or 0.85,
            "fusion_scores": fused_scores,
            "bert_topics": bert_topics,
            "message": f"Contract classified as: {existing_type}"
        }

        return json.dumps(classification_result, indent=2)

    except Contract.DoesNotExist:
        return json.dumps({
            "status": "error",
            "message": f"Contract with ID {contract_id} not found"
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Error classifying contract: {str(e)}"
        })


# ========================================
# TOOL 4: RISK SCORING
# ========================================
@mcp.tool()
async def calculate_risk_score(contract_id: str) -> str:
    """
    Calculates comprehensive risk score for the contract.
    Analyzes clauses, deviations, and compliance issues.

    Args:
        contract_id: The UUID of the contract to score

    Returns:
        JSON string with risk analysis
    """
    try:
        # Fetch contract with risk analysis
        contract = await sync_to_async(
            lambda: Contract.objects.select_related('risk_analysis').get(id=contract_id)
        )()

        # Check if risk analysis exists
        if hasattr(contract, 'risk_analysis') and contract.risk_analysis:
            risk_analysis = contract.risk_analysis

            # Get clause deviations
            deviations = await sync_to_async(list)(
                risk_analysis.deviations.values('clause_name', 'severity', 'description')
            )

            risk_result = {
                "status": "success",
                "contract_id": contract_id,
                "filename": contract.original_filename,
                "risk_score": risk_analysis.risk_score,
                "risk_level": risk_analysis.risk_level,
                "total_deviations": risk_analysis.total_deviations,
                "risk_breakdown": {
                    "critical_issues": risk_analysis.critical_issues,
                    "medium_issues": risk_analysis.medium_issues,
                    "low_issues": risk_analysis.low_issues
                },
                "deviations": deviations[:10],  # Top 10 deviations
                "analysis_summary": risk_analysis.analysis_summary or "No summary available"
            }
        else:
            # No existing risk analysis - perform AI analysis
            contract_text = contract.full_text or ""
            if not contract_text:
                return json.dumps({
                    "status": "error",
                    "message": "No contract text available for analysis"
                })

            # Truncate contract text to first 2000 characters for analysis
            text_excerpt = contract_text[:2000]

            # AI prompt for risk scoring
            risk_prompt = f"""Analyze this contract excerpt and provide a risk score from 0-100 and risk level.

Contract: {contract.original_filename}
Text: {text_excerpt}

Provide your analysis in this exact format:
RISK_SCORE: [number 0-100]
RISK_LEVEL: [LOW/MEDIUM/HIGH/CRITICAL]
KEY_RISKS: [comma-separated list of 2-3 main risks]

Analysis:"""

            # Call Ollama with extended timeout
            ai_response = await call_ollama(risk_prompt, max_tokens=300, timeout=180.0)

            # Parse AI response
            risk_score = 50  # default
            risk_level = "MEDIUM"  # default
            risk_flags = []

            # Extract risk score
            score_match = re.search(r'RISK_SCORE:\s*(\d+)', ai_response)
            if score_match:
                risk_score = int(score_match.group(1))
                risk_score = min(100, max(0, risk_score))  # Clamp 0-100

            # Extract risk level
            level_match = re.search(r'RISK_LEVEL:\s*(LOW|MEDIUM|HIGH|CRITICAL)', ai_response)
            if level_match:
                risk_level = level_match.group(1)

            # Extract key risks
            risks_match = re.search(r'KEY_RISKS:\s*(.+?)(?:\n|$)', ai_response)
            if risks_match:
                risk_flags = [r.strip() for r in risks_match.group(1).split(',')]

            risk_result = {
                "status": "success",
                "contract_id": contract_id,
                "filename": contract.original_filename,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "deviations": risk_flags,
                "ai_analysis": ai_response,
                "source": "AI-generated (Ollama)"
            }

        return json.dumps(risk_result, indent=2)

    except Contract.DoesNotExist:
        return json.dumps({
            "status": "error",
            "message": f"Contract with ID {contract_id} not found"
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Error calculating risk score: {str(e)}"
        })


# ========================================
# TOOL 5: INTENT MINING
# ========================================
@mcp.tool()
async def mine_contract_intent(contract_id: str) -> str:
    """
    Analyzes the underlying business intent and purpose of the contract.
    Discovers what parties are trying to achieve.

    Args:
        contract_id: The UUID of the contract to analyze

    Returns:
        JSON string with intent analysis
    """
    try:
        # Fetch contract
        contract = await sync_to_async(Contract.objects.get)(id=contract_id)

        # Get associated clauses with intents
        clauses_with_intents = await sync_to_async(list)(
            Clause.objects.filter(contract_id=contract_id)
            .prefetch_related('clause_intents__intent')
            .values(
                'clause_name',
                'clause_intents__intent__name',
                'clause_intents__confidence',
                'clause_intents__is_primary'
            )
        )

        # Aggregate intents
        intent_map = {}
        primary_intents = []

        for clause_data in clauses_with_intents:
            intent_name = clause_data.get('clause_intents__intent__name')
            if intent_name:
                is_primary = clause_data.get('clause_intents__is_primary', False)
                confidence = clause_data.get('clause_intents__confidence', 0.0)

                if intent_name not in intent_map:
                    intent_map[intent_name] = {
                        "confidence": confidence,
                        "occurrence_count": 1,
                        "is_primary": is_primary
                    }
                else:
                    intent_map[intent_name]["occurrence_count"] += 1
                    intent_map[intent_name]["confidence"] = max(
                        intent_map[intent_name]["confidence"],
                        confidence
                    )

                if is_primary:
                    primary_intents.append(intent_name)

        # Determine primary business intent
        if primary_intents:
            primary_intent = primary_intents[0]
        elif intent_map:
            # Pick intent with highest confidence
            primary_intent = max(intent_map.items(), key=lambda x: x[1]['confidence'])[0]
        else:
            # No intents found in database - use AI to analyze
            contract_text = contract.full_text or ""
            if not contract_text:
                primary_intent = "Unknown"
                intent_map = {}
            else:
                # Truncate contract text for analysis
                text_excerpt = contract_text[:2000]

                # AI prompt for intent mining
                intent_prompt = f"""Analyze this contract and identify the main business purpose and intent.

Contract: {contract.original_filename}
Type: {contract.contract_type or 'Unknown'}
Text: {text_excerpt}

Provide your analysis in this exact format:
PRIMARY_INTENT: [one sentence describing the main business purpose]
CONFIDENCE: [number 0-100]
SECONDARY_INTENTS: [comma-separated list of 2-3 other intents if any]

Analysis:"""

                # Call Ollama with extended timeout
                ai_response = await call_ollama(intent_prompt, max_tokens=400, timeout=180.0)

                # Parse AI response
                primary_intent = "Unknown"
                confidence = 0.0

                # Extract primary intent
                intent_match = re.search(r'PRIMARY_INTENT:\s*(.+?)(?:\n|$)', ai_response)
                if intent_match:
                    primary_intent = intent_match.group(1).strip()

                # Extract confidence
                conf_match = re.search(r'CONFIDENCE:\s*(\d+)', ai_response)
                if conf_match:
                    confidence = float(conf_match.group(1)) / 100.0

                # Extract secondary intents
                sec_match = re.search(r'SECONDARY_INTENTS:\s*(.+?)(?:\n|$)', ai_response)
                if sec_match:
                    secondary = [s.strip() for s in sec_match.group(1).split(',')]
                    # Add to intent_map
                    intent_map[primary_intent] = {
                        "confidence": confidence,
                        "occurrence_count": 1,
                        "is_primary": True
                    }
                    for sec_intent in secondary:
                        if sec_intent:
                            intent_map[sec_intent] = {
                                "confidence": confidence * 0.7,
                                "occurrence_count": 1,
                                "is_primary": False
                            }
                else:
                    # Just add primary intent
                    intent_map[primary_intent] = {
                        "confidence": confidence,
                        "occurrence_count": 1,
                        "is_primary": True
                    }

        intent_result = {
            "status": "success",
            "contract_id": contract_id,
            "filename": contract.original_filename,
            "contract_type": contract.contract_type or "Unknown",
            "primary_intent": primary_intent,
            "all_intents": intent_map,
            "total_intents_found": len(intent_map),
            "analysis": f"Primary business intent: {primary_intent}. This contract involves {len(intent_map)} distinct legal intents.",
            "source": "AI-generated (Ollama)" if not clauses_with_intents else "Database"
        }

        return json.dumps(intent_result, indent=2)

    except Contract.DoesNotExist:
        return json.dumps({
            "status": "error",
            "message": f"Contract with ID {contract_id} not found"
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Error mining intent: {str(e)}"
        })


# ========================================
# TOOL 6: CLAUSE IMPROVEMENT SUGGESTIONS
# ========================================
@mcp.tool()
async def suggest_clause_improvements(contract_id: str) -> str:
    """
    Analyzes contract and suggests improvements for problematic clauses.
    Identifies missing, weak, or unfavorable clauses and provides AI-generated suggestions.

    Args:
        contract_id: The UUID of the contract to analyze

    Returns:
        JSON string with clause improvement suggestions
    """
    try:
        # Fetch contract
        contract = await sync_to_async(Contract.objects.get)(id=contract_id)

        # Get contract text
        contract_text = contract.full_text or ""
        if not contract_text:
            return json.dumps({
                "status": "error",
                "message": "No contract text available for analysis"
            })

        # Truncate for AI processing
        text_excerpt = contract_text[:4000]

        # AI prompt for clause improvement suggestions
        improvement_prompt = f"""You are an expert contract attorney. Analyze this contract and suggest improvements.

Contract: {contract.original_filename}
Type: {contract.contract_type or 'Unknown'}

Contract Text:
{text_excerpt}

Analyze the contract and provide suggestions in this EXACT format:

CLAUSE_ISSUES:
1. [Clause Name]: [Issue Description]
   SEVERITY: [HIGH/MEDIUM/LOW]
   CURRENT_TEXT: [Current clause text or "MISSING"]
   SUGGESTED_TEXT: [Your suggested improved clause text]
   RATIONALE: [Why this change improves the contract]

2. [Clause Name]: [Issue Description]
   SEVERITY: [HIGH/MEDIUM/LOW]
   CURRENT_TEXT: [Current clause text or "MISSING"]
   SUGGESTED_TEXT: [Your suggested improved clause text]
   RATIONALE: [Why this change improves the contract]

Provide 3-5 most critical improvement suggestions."""

        # Call Ollama with extended timeout (5 minutes for complex analysis)
        ai_response = await call_ollama(improvement_prompt, max_tokens=1500, timeout=300.0)

        # Parse AI response into structured suggestions
        suggestions = []

        # Split into sections by numbered items
        sections = re.split(r'\n(?=\d+\.\s+\*?\*?[A-Z])', ai_response)

        for section in sections:
            if not section.strip() or 'CLAUSE_ISSUES' in section:
                continue

            # Extract clause name
            clause_match = re.match(r'^(\d+)\.\s+\*?\*?([^:]+?)(?::|\*\*)', section)
            if not clause_match:
                continue

            clause_name = clause_match.group(2).strip()

            # Extract severity
            severity_match = re.search(r'SEVERITY:\s*(HIGH|MEDIUM|LOW)', section, re.IGNORECASE)
            severity = severity_match.group(1).upper() if severity_match else "MEDIUM"

            # Extract current text - look for multiline content after CURRENT_TEXT:
            current_match = re.search(r'CURRENT_TEXT:\s*(.+?)(?=SUGGESTED_TEXT:|$)', section, re.DOTALL | re.IGNORECASE)
            if current_match:
                current_text = current_match.group(1).strip()
                # Clean up formatting
                current_text = re.sub(r'\s+', ' ', current_text)
                # Remove code blocks
                current_text = re.sub(r'```.*?```', '', current_text, flags=re.DOTALL).strip()
                if not current_text or len(current_text) < 5:
                    current_text = "Not specified"
            else:
                current_text = "Not specified"

            # Extract suggested text - look for multiline content after SUGGESTED_TEXT:
            suggested_match = re.search(r'SUGGESTED_TEXT:\s*(.+?)(?=RATIONALE:|$)', section, re.DOTALL | re.IGNORECASE)
            if suggested_match:
                suggested_text = suggested_match.group(1).strip()
                # Clean up formatting
                suggested_text = re.sub(r'\s+', ' ', suggested_text)
                # Remove code blocks
                suggested_text = re.sub(r'```.*?```', '', suggested_text, flags=re.DOTALL).strip()
                if not suggested_text or len(suggested_text) < 10:
                    suggested_text = "See AI analysis below"
            else:
                suggested_text = "See AI analysis below"

            # Extract rationale
            rationale_match = re.search(r'RATIONALE:\s*(.+?)(?=\n\d+\.|$)', section, re.DOTALL | re.IGNORECASE)
            if rationale_match:
                rationale = rationale_match.group(1).strip()
                # Clean up formatting
                rationale = re.sub(r'\s+', ' ', rationale)
            else:
                rationale = "Review AI analysis for details"

            suggestions.append({
                "clause_name": clause_name,
                "severity": severity,
                "current_text": current_text[:500] if len(current_text) > 500 else current_text,
                "suggested_text": suggested_text[:500] if len(suggested_text) > 500 else suggested_text,
                "rationale": rationale[:300] if len(rationale) > 300 else rationale,
                "impact": "Reduces risk" if severity == "HIGH" else "Improves clarity"
            })

        # If parsing failed, create a fallback suggestion with the full AI response
        if not suggestions:
            suggestions.append({
                "clause_name": "General Contract Review",
                "severity": "MEDIUM",
                "current_text": "See full analysis",
                "suggested_text": "See AI recommendations below",
                "rationale": ai_response[:500],
                "impact": "Review AI suggestions for improvements"
            })

        result = {
            "status": "success",
            "contract_id": contract_id,
            "contract_filename": contract.original_filename,
            "total_suggestions": len(suggestions),
            "suggestions": suggestions,
            "ai_analysis": ai_response,
            "critical_count": len([s for s in suggestions if s["severity"] == "HIGH"]),
            "medium_count": len([s for s in suggestions if s["severity"] == "MEDIUM"]),
            "low_count": len([s for s in suggestions if s["severity"] == "LOW"])
        }

        return json.dumps(result, indent=2)

    except Contract.DoesNotExist:
        return json.dumps({
            "status": "error",
            "message": f"Contract with ID {contract_id} not found"
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Error generating suggestions: {str(e)}"
        })


# ========================================
# MCP SERVER RUNNER
# ========================================
if __name__ == "__main__":
    print("🚀 Starting ContractAI MCP Server...")
    print("📋 Available Tools:")
    print("   1. extract_clauses")
    print("   2. generate_executive_summary")
    print("   3. classify_contract")
    print("   4. calculate_risk_score")
    print("   5. mine_contract_intent")
    print("   6. suggest_clause_improvements [NEW]")
    print("\n✅ MCP Server is running on STDIO transport...")

    # Run the MCP server
    mcp.run(transport="stdio")
