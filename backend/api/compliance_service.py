import os
"""
Compliance Mapping Service
==========================
LLM-powered detection of compliance framework applicability to contract intents.
Automatically maps intents to GDPR, SOX, HIPAA, and GST requirements.

Workflow:
1. Get all intents from contract clauses
2. Get all active compliance requirements
3. For each (intent, requirement) pair, use LLM to detect applicability
4. Create IntentComplianceMapping records
5. Calculate aggregate compliance scores
6. Save to ContractComplianceAnalysis
"""

import requests
import json
import time
import logging
from typing import Dict, List, Tuple
from django.db import transaction
from django.utils import timezone
from django.db.models import Avg, Count
from core.models import (
    Contract, Intent, ClauseIntent, Clause,
    ComplianceFramework, ComplianceRequirement,
    IntentComplianceMapping, ContractComplianceAnalysis
)

logger = logging.getLogger(__name__)


class ComplianceDetectionService:
    """Service for detecting compliance framework applicability using LLM"""

    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")) + "/api/generate"
        self.model_name = "qwen2.5:0.5b"
        self.timeout = 30  # 30s per LLM call — keyword pre-filter reduces total calls
        self.temperature = 0.2  # Low temperature for consistent compliance assessment
        self.max_retries = 3  # Retry on database locks
        self.retry_delay = 2  # Seconds between retries

    def detect_requirement_applicability(
        self,
        intent: Intent,
        requirement: ComplianceRequirement,
        clause_text: str
    ) -> Dict:
        """
        Detect if a compliance requirement applies to an intent.

        Args:
            intent: Intent model instance
            requirement: ComplianceRequirement model instance
            clause_text: Text of the clause to analyze

        Returns:
            Dict with:
            - relevance_score (0-1): LLM confidence requirement applies
            - compliance_status: COMPLIANT/PARTIAL/NON_COMPLIANT/NEEDS_REVIEW
            - analysis_summary: Explanation
            - gap_description: What's missing (if non-compliant)
            - recommendation: How to achieve compliance
            - risk_score: Risk score (0-1)
        """

        prompt = f"""Assess if this compliance requirement applies to the contract clause.

REQUIREMENT: {requirement.framework.code} {requirement.requirement_code} - {requirement.requirement_name} ({requirement.criticality})
INTENT: {intent.name}
CLAUSE: {clause_text[:800]}

Return ONLY valid JSON:
{{
    "relevance_score": 0.0-1.0,
    "compliance_status": "COMPLIANT|PARTIAL|NON_COMPLIANT|NEEDS_REVIEW",
    "analysis_summary": "Brief assessment (max 50 words)",
    "gap_description": "What's missing (if any)",
    "recommendation": "Brief fix (max 30 words)",
    "risk_score": 0.0-1.0
}}

JSON:"""

        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": self.temperature,
                    "options": {
                        "num_predict": 200  # Limit to 200 tokens for concise JSON response
                    }
                },
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '').strip()
                compliance_data = self._extract_json(response_text)

                if compliance_data and 'relevance_score' in compliance_data:
                    # Validate and normalize fields
                    return self._normalize_compliance_data(compliance_data)
                else:
                    logger.warning(f"Invalid compliance response for intent {intent.id}")
                    return self._get_default_response()
            else:
                logger.error(f"Ollama request failed with status {response.status_code}")
                return self._get_default_response()

        except requests.exceptions.Timeout:
            logger.error(f"LLM request timed out for intent {intent.name}")
            return self._get_default_response()
        except Exception as e:
            logger.error(f"Error detecting compliance: {str(e)}")
            return self._get_default_response()

    def _batch_check_requirements(self, intent, requirements, clause_text: str) -> list:
        """
        Check multiple requirements against one intent in a single LLM call.
        Returns a list of result dicts in the same order as requirements.
        Falls back to safe defaults on failure.
        """
        req_list = "\n".join([
            f"{i+1}. [{req.framework.code}] {req.requirement_name} ({req.criticality})"
            for i, req in enumerate(requirements)
        ])

        prompt = f"""Assess compliance for this contract clause against each requirement. Return ONLY a JSON array.

INTENT: {intent.name}
CLAUSE: {clause_text[:600]}

REQUIREMENTS:
{req_list}

Return a JSON array with one object per requirement, in the SAME ORDER:
[{{"relevance_score":0.0,"compliance_status":"COMPLIANT","analysis_summary":"brief","gap_description":"","recommendation":"","risk_score":0.0}},...]

Status options: COMPLIANT, PARTIAL, NON_COMPLIANT, NEEDS_REVIEW
JSON array:"""

        default = [self._get_default_response() for _ in requirements]
        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.1,
                    "options": {"num_predict": min(80 * len(requirements), 800)},
                },
                timeout=60
            )
            if response.status_code != 200:
                return default

            response_text = response.json().get('response', '').strip()
            import re
            # Extract JSON array
            match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if not match:
                return default
            import json
            arr = json.loads(match.group())
            # Pad or truncate to match requirements count
            results = []
            for i, req in enumerate(requirements):
                if i < len(arr) and isinstance(arr[i], dict):
                    results.append(self._normalize_compliance_data(arr[i]))
                else:
                    results.append(self._get_default_response())
            return results
        except Exception as e:
            logger.error(f"Batch compliance check failed: {e}")
            return default

    def _extract_json(self, text: str) -> Dict:
        """Extract JSON from LLM response, handling markdown code blocks and common errors"""
        try:
            # Remove markdown code blocks if present
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0]
            elif '```' in text:
                text = text.split('```')[1].split('```')[0]

            text = text.strip()

            # Clean up common LLM JSON errors
            # Remove trailing commas before } or ]
            import re
            text = re.sub(r',\s*}', '}', text)
            text = re.sub(r',\s*]', ']', text)

            # Remove control characters except newlines and tabs
            text = ''.join(char for char in text if ord(char) >= 32 or char in ['\n', '\t'])

            # Check if JSON is incomplete (truncated)
            # Count opening and closing braces/brackets
            open_braces = text.count('{')
            close_braces = text.count('}')
            open_brackets = text.count('[')
            close_brackets = text.count(']')

            # Auto-complete truncated JSON
            if open_braces > close_braces or open_brackets > close_brackets:
                logger.warning("Detected incomplete JSON - attempting to auto-complete")
                # Close any open strings first
                if text.count('"') % 2 != 0:
                    text += '"'
                # Close brackets and braces
                text += ']' * (open_brackets - close_brackets)
                text += '}' * (open_braces - close_braces)

            return json.loads(text)
        except (json.JSONDecodeError, IndexError) as e:
            logger.error(f"JSON decode error: {str(e)}")
            logger.error(f"Problematic text: {text[:200]}")
            return None

    def _normalize_compliance_data(self, data: Dict) -> Dict:
        """Normalize and validate compliance data from LLM"""
        normalized = {
            'relevance_score': max(0.0, min(1.0, float(data.get('relevance_score', 0.0)))),
            'compliance_status': data.get('compliance_status', 'NEEDS_REVIEW'),
            'analysis_summary': str(data.get('analysis_summary', 'Manual review required'))[:500],
            'gap_description': str(data.get('gap_description', '')) or None,
            'recommendation': str(data.get('recommendation', ''))[:500],
            'risk_score': max(0.0, min(1.0, float(data.get('risk_score', 0.5))))
        }

        # Validate compliance_status
        valid_statuses = ['COMPLIANT', 'PARTIAL', 'NON_COMPLIANT', 'NOT_APPLICABLE', 'NEEDS_REVIEW']
        if normalized['compliance_status'] not in valid_statuses:
            normalized['compliance_status'] = 'NEEDS_REVIEW'

        return normalized

    def _get_default_response(self) -> Dict:
        """Default response when LLM fails"""
        return {
            'relevance_score': 0.0,
            'compliance_status': 'NEEDS_REVIEW',
            'analysis_summary': 'Automated analysis unavailable - manual review required',
            'gap_description': None,
            'recommendation': 'Please manually review this intent against the requirement',
            'risk_score': 0.5
        }

    @transaction.atomic
    def analyze_contract_compliance(self, contract_id: str) -> Dict:
        """
        Main method: Analyze contract for compliance with all active frameworks.

        Process:
        1. Get all intents for contract
        2. Get all active requirements
        3. For each (intent, requirement) pair, detect applicability
        4. Create IntentComplianceMapping records
        5. Calculate aggregate scores
        6. Generate summary

        Args:
            contract_id: UUID of contract to analyze

        Returns:
            Dict with success status, metrics, and statistics
        """
        try:
            start_time = time.time()
            contract = Contract.objects.get(id=contract_id)

            logger.info(f"Starting compliance analysis for contract: {contract.original_filename}")

            # Get all intents for this contract
            contract_clauses = Clause.objects.filter(contract=contract, found=True)

            # Get unique intent IDs (MySQL-compatible approach)
            unique_intent_ids = ClauseIntent.objects.filter(
                clause__in=contract_clauses
            ).values_list('intent_id', flat=True).distinct()

            if not unique_intent_ids:
                return {
                    'success': False,
                    'error': 'No intents found for this contract. Run intent mining first.'
                }

            # Get unique intents
            unique_intents = Intent.objects.filter(id__in=unique_intent_ids)

            # Get all active compliance requirements
            active_frameworks = ComplianceFramework.objects.filter(is_active=True)
            active_requirements = ComplianceRequirement.objects.filter(
                framework__in=active_frameworks,
                is_active=True
            ).select_related('framework')

            if not active_requirements.exists():
                return {
                    'success': False,
                    'error': 'No active compliance requirements configured'
                }

            logger.info(
                f"Analyzing {unique_intents.count()} intents "
                f"against {active_requirements.count()} requirements"
            )

            # Clear existing mappings for this contract (with retry on lock timeout)
            for retry in range(self.max_retries):
                try:
                    IntentComplianceMapping.objects.filter(contract=contract).delete()
                    break  # Success - exit retry loop
                except Exception as e:
                    if '1205' in str(e) and retry < self.max_retries - 1:  # Lock timeout
                        logger.warning(f"Database lock timeout, retrying... (attempt {retry + 1}/{self.max_retries})")
                        time.sleep(self.retry_delay)
                    else:
                        raise  # Re-raise if not a lock error or out of retries

            mappings_created = 0
            framework_stats = {}
            all_risk_scores = []

            # Batch approach: one LLM call per intent covering ALL requirements at once
            # This replaces N*28 LLM calls with N calls (5x-28x faster)
            for intent in unique_intents:
                clause_intent_link = ClauseIntent.objects.filter(
                    intent=intent,
                    clause__in=contract_clauses
                ).select_related('clause').first()

                if not clause_intent_link:
                    continue

                clause_text = clause_intent_link.clause.extracted_text or ""
                if not clause_text.strip():
                    continue

                # Keyword pre-filter requirements for this intent
                clause_words = set(clause_text.lower().split())
                intent_words = set(intent.name.lower().split())
                relevant_reqs = []
                for req in active_requirements:
                    req_keywords = set(
                        (req.requirement_name + ' ' + req.framework.code).lower().split()
                    )
                    overlap = req_keywords & (clause_words | intent_words)
                    if overlap or req.criticality in ('HIGH', 'CRITICAL'):
                        relevant_reqs.append(req)

                if not relevant_reqs:
                    continue

                # Single batch LLM call for all relevant requirements
                batch_results = self._batch_check_requirements(intent, relevant_reqs, clause_text)

                for req, result in zip(relevant_reqs, batch_results):
                    if result.get('relevance_score', 0) >= 0.4:
                        mapping = IntentComplianceMapping.objects.create(
                            intent=intent,
                            requirement=req,
                            contract=contract,
                            relevance_score=result['relevance_score'],
                            compliance_status=result['compliance_status'],
                            analysis_summary=result.get('analysis_summary', ''),
                            gap_description=result.get('gap_description', ''),
                            recommendation=result.get('recommendation', ''),
                            risk_score=result['risk_score']
                        )
                        mappings_created += 1
                        all_risk_scores.append(result['risk_score'])

                        framework_code = req.framework.code
                        if framework_code not in framework_stats:
                            framework_stats[framework_code] = {
                                'total': 0, 'compliant': 0, 'partial': 0, 'non_compliant': 0
                            }
                        framework_stats[framework_code]['total'] += 1
                        if mapping.compliance_status == 'COMPLIANT':
                            framework_stats[framework_code]['compliant'] += 1
                        elif mapping.compliance_status == 'PARTIAL':
                            framework_stats[framework_code]['partial'] += 1
                        elif mapping.compliance_status == 'NON_COMPLIANT':
                            framework_stats[framework_code]['non_compliant'] += 1

            # Calculate aggregate compliance analysis
            analysis = self._calculate_aggregate_compliance(contract, framework_stats)

            duration = time.time() - start_time

            logger.info(
                f"Compliance analysis complete for {contract.original_filename} "
                f"(created {mappings_created} mappings in {duration:.1f}s)"
            )

            return {
                'success': True,
                'contract_id': contract_id,
                'intents_analyzed': unique_intents.count(),
                'requirements_checked': active_requirements.count(),
                'mappings_created': mappings_created,
                'framework_stats': framework_stats,
                'overall_score': analysis.overall_compliance_score,
                'compliance_risk_score': analysis.compliance_risk_score,
                'duration_seconds': duration
            }

        except Contract.DoesNotExist:
            return {'success': False, 'error': 'Contract not found'}
        except Exception as e:
            logger.error(f"Error analyzing compliance: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}

    def _calculate_aggregate_compliance(
        self,
        contract: Contract,
        framework_stats: Dict
    ) -> ContractComplianceAnalysis:
        """Calculate and save aggregate compliance metrics"""

        # Get all mappings for this contract
        mappings = IntentComplianceMapping.objects.filter(contract=contract)

        total = mappings.count()
        compliant = mappings.filter(compliance_status='COMPLIANT').count()
        partial = mappings.filter(compliance_status='PARTIAL').count()
        non_compliant = mappings.filter(compliance_status='NON_COMPLIANT').count()

        # Calculate weighted compliance score (0-100)
        if total > 0:
            compliance_score = (
                (compliant * 100) +
                (partial * 50) +
                (non_compliant * 0)
            ) / total
        else:
            compliance_score = 0.0

        # Calculate framework-specific scores
        framework_scores = {}
        for framework_code, stats in framework_stats.items():
            if stats['total'] > 0:
                framework_scores[framework_code] = {
                    'score': (
                        (stats['compliant'] * 100) +
                        (stats['partial'] * 50)
                    ) / stats['total'],
                    'coverage': stats['total'],
                    'compliant': stats['compliant'],
                    'partial': stats['partial'],
                    'non_compliant': stats['non_compliant']
                }

        # Count violations by criticality
        critical_violations = mappings.filter(
            compliance_status__in=['NON_COMPLIANT', 'PARTIAL'],
            requirement__criticality='CRITICAL'
        ).count()

        high_violations = mappings.filter(
            compliance_status__in=['NON_COMPLIANT', 'PARTIAL'],
            requirement__criticality='HIGH'
        ).count()

        medium_violations = mappings.filter(
            compliance_status__in=['NON_COMPLIANT', 'PARTIAL'],
            requirement__criticality='MEDIUM'
        ).count()

        low_violations = mappings.filter(
            compliance_status__in=['NON_COMPLIANT', 'PARTIAL'],
            requirement__criticality='LOW'
        ).count()

        # Calculate compliance risk score (0-1)
        avg_risk = mappings.aggregate(avg_risk=Avg('risk_score'))['avg_risk'] or 0.0

        # Create or update analysis
        analysis, created = ContractComplianceAnalysis.objects.update_or_create(
            contract=contract,
            defaults={
                'overall_compliance_score': compliance_score,
                'total_requirements_checked': total,
                'compliant_count': compliant,
                'partial_count': partial,
                'non_compliant_count': non_compliant,
                'framework_scores': framework_scores,
                'compliance_risk_score': avg_risk,
                'critical_violations': critical_violations,
                'high_violations': high_violations,
                'medium_violations': medium_violations,
                'low_violations': low_violations,
                'analysis_completed_at': timezone.now(),
                'analysis_duration_seconds': 0.0,  # Updated by caller
            }
        )

        return analysis
