"""
SAP S/4HANA Integration Module for PrimeContractAI

This module provides bi-directional integration between PrimeContractAI
and SAP S/4HANA for contract intelligence and risk scoring.

Features:
- OAuth2 authentication with SAP
- Contract data synchronization via OData APIs
- Risk scoring and intent detection
- Automated contract blocking for high-risk scenarios
- Clause suggestion integration
- Amendment re-evaluation
- Manual override support

Author: PrimeContractAI Team
Version: 1.0.0
"""

from .sap_client import SAPClient
from .sap_contract_service import SAPContractService
from .risk_engine import RiskEngine
from .intent_engine import IntentEngine
from .clause_engine import ClauseEngine

__version__ = "1.0.0"
__all__ = [
    'SAPClient',
    'SAPContractService',
    'RiskEngine',
    'IntentEngine',
    'ClauseEngine',
]
