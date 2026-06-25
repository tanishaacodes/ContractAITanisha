"""
SAP Integration Configuration

Manages SAP S/4HANA connection settings and credentials.
"""
import os
from decouple import config


class SAPConfig:
    """SAP S/4HANA Configuration Settings"""

    # SAP System URLs
    SAP_BASE_URL = config('SAP_BASE_URL', default='https://your-sap-system.com/sap/opu/odata/sap')
    SAP_TOKEN_URL = config('SAP_TOKEN_URL', default='https://your-sap-system.com/sap/bc/sec/oauth2/token')

    # OAuth2 Credentials
    SAP_CLIENT_ID = config('SAP_CLIENT_ID', default='')
    SAP_CLIENT_SECRET = config('SAP_CLIENT_SECRET', default='')

    # SAP System Identifiers
    SAP_SYSTEM_ID = config('SAP_SYSTEM_ID', default='S4H_PRD_100')
    SAP_CLIENT = config('SAP_CLIENT', default='100')

    # OData Service Endpoints
    CONTRACT_SERVICE = 'API_PURCHASECONTRACT_PROCESS_SRV'
    SALES_CONTRACT_SERVICE = 'API_SALES_CONTRACT_SRV'

    # Timeout and Retry Settings
    REQUEST_TIMEOUT = config('SAP_REQUEST_TIMEOUT', default=30, cast=int)
    MAX_RETRIES = config('SAP_MAX_RETRIES', default=3, cast=int)
    RETRY_BACKOFF = config('SAP_RETRY_BACKOFF', default=2, cast=int)

    # Feature Flags
    ENABLE_CSRF_TOKEN = config('SAP_ENABLE_CSRF', default=True, cast=bool)
    ENABLE_ETAG = config('SAP_ENABLE_ETAG', default=True, cast=bool)

    # Risk Thresholds
    RISK_THRESHOLD_LOW = config('SAP_RISK_THRESHOLD_LOW', default=30, cast=int)
    RISK_THRESHOLD_MEDIUM = config('SAP_RISK_THRESHOLD_MEDIUM', default=60, cast=int)
    RISK_THRESHOLD_HIGH = config('SAP_RISK_THRESHOLD_HIGH', default=80, cast=int)

    # SAP Custom Field Names (Z-fields for AI data)
    Z_FIELD_RISK_SCORE = 'Z_AI_RISK_SCORE'
    Z_FIELD_RISK_CATEGORY = 'Z_AI_RISK_CATEGORY'
    Z_FIELD_STATUS = 'Z_AI_STATUS'
    Z_FIELD_INTENT = 'Z_AI_INTENT'
    Z_FIELD_EXPOSURE = 'Z_AI_EXPOSURE'
    Z_FIELD_VALIDATED_DATE = 'Z_AI_VALIDATED_DATE'
    Z_FIELD_COMPLIANCE = 'Z_AI_COMPLIANCE'

    @classmethod
    def validate(cls):
        """Validate required configuration is present"""
        if not cls.SAP_CLIENT_ID or not cls.SAP_CLIENT_SECRET:
            raise ValueError(
                "SAP credentials not configured. "
                "Please set SAP_CLIENT_ID and SAP_CLIENT_SECRET in environment."
            )
        return True

    @classmethod
    def get_contract_service_url(cls):
        """Get full OData service URL for contracts"""
        return f"{cls.SAP_BASE_URL}/{cls.CONTRACT_SERVICE}"

    @classmethod
    def is_production(cls):
        """Check if running against production SAP system"""
        return 'PRD' in cls.SAP_SYSTEM_ID


settings = SAPConfig()
