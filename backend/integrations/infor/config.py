"""
Infor ERP Integration Configuration
Supports Infor ERP LN, CloudSuite Industrial (SyteLine), and CloudSuite Industrial Enterprise.
"""
import os


class InforSettings:
    # Infor OS / API Gateway
    INFOR_BASE_URL = os.getenv("INFOR_BASE_URL", "https://mingle-ionapi.inforcloudsuite.com")
    INFOR_TOKEN_URL = os.getenv(
        "INFOR_TOKEN_URL",
        "https://mingle-sso.inforcloudsuite.com/INFOR_TENANT/as/token.oauth2"
    )
    INFOR_CLIENT_ID = os.getenv("INFOR_CLIENT_ID", "")
    INFOR_CLIENT_SECRET = os.getenv("INFOR_CLIENT_SECRET", "")
    INFOR_TENANT_ID = os.getenv("INFOR_TENANT_ID", "INFOR_TENANT")

    # Infor ION API paths
    CONTRACT_API_PATH = os.getenv(
        "INFOR_CONTRACT_API_PATH",
        "/api/contractmgmt/v1/contracts"
    )

    # Risk thresholds (reuse same logic as SAP)
    RISK_THRESHOLD_MEDIUM = int(os.getenv("RISK_THRESHOLD_MEDIUM", "30"))
    RISK_THRESHOLD_HIGH = int(os.getenv("RISK_THRESHOLD_HIGH", "60"))
    RISK_THRESHOLD_CRITICAL = int(os.getenv("RISK_THRESHOLD_CRITICAL", "80"))

    # HTTP
    REQUEST_TIMEOUT = float(os.getenv("INFOR_REQUEST_TIMEOUT", "30.0"))

    # Infor custom field names (User Defined Fields in CSI/LN)
    UDF_RISK_SCORE = os.getenv("INFOR_UDF_RISK_SCORE", "aiRiskScore")
    UDF_RISK_CATEGORY = os.getenv("INFOR_UDF_RISK_CATEGORY", "aiRiskCategory")
    UDF_STATUS = os.getenv("INFOR_UDF_STATUS", "aiStatus")
    UDF_INTENT = os.getenv("INFOR_UDF_INTENT", "aiIntent")
    UDF_EXPOSURE = os.getenv("INFOR_UDF_EXPOSURE", "aiExposure")
    UDF_VALIDATED_DATE = os.getenv("INFOR_UDF_VALIDATED_DATE", "aiValidatedDate")
    UDF_COMPLIANCE = os.getenv("INFOR_UDF_COMPLIANCE", "aiComplianceStatus")


settings = InforSettings()
