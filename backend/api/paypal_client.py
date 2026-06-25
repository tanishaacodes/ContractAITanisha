"""
PayPal client configuration for ContractAI payment integration.
Supports both sandbox and live environments.
"""

from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment, LiveEnvironment
from django.conf import settings


def paypal_client():
    """
    Initialize and return PayPal HTTP client.
    Automatically switches between sandbox and live environments based on settings.

    Returns:
        PayPalHttpClient: Configured PayPal client instance
    """
    if settings.PAYPAL_MODE == "live":
        environment = LiveEnvironment(
            client_id=settings.PAYPAL_CLIENT_ID,
            client_secret=settings.PAYPAL_CLIENT_SECRET
        )
    else:
        environment = SandboxEnvironment(
            client_id=settings.PAYPAL_CLIENT_ID,
            client_secret=settings.PAYPAL_CLIENT_SECRET
        )

    return PayPalHttpClient(environment)
