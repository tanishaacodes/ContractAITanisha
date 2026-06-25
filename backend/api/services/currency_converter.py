"""
Currency Conversion Service
============================
Provides real-time currency conversion for contract exposure calculations.

Features:
- Multi-currency support (INR, USD, EUR, GBP, etc.)
- Exchange rate caching (1-hour TTL)
- Fallback to static rates if API unavailable
- Free tier: exchangerate-api.com (1500 requests/month)

Usage:
    from api.services.currency_converter import CurrencyConverter

    converter = CurrencyConverter()
    usd_amount = converter.convert(1000000, 'INR', 'USD')
    formatted = converter.format_amount(usd_amount, 'USD')
"""

import logging
import time
from typing import Dict, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


class CurrencyConverter:
    """
    Currency conversion with exchange rate caching.

    Uses exchangerate-api.com free tier (no API key required for basic access).
    Falls back to static rates if API is unavailable.
    """

    # Fallback exchange rates (relative to USD)
    FALLBACK_RATES = {
        'USD': 1.0,
        'INR': 83.0,
        'EUR': 0.92,
        'GBP': 0.79,
        'AUD': 1.52,
        'CAD': 1.35,
        'SGD': 1.34,
        'JPY': 148.0,
        'CNY': 7.24
    }

    # Cache configuration
    CACHE_TTL = 3600  # 1 hour

    def __init__(self):
        """Initialize converter with empty cache"""
        self._cache = {}
        self._cache_timestamp = {}
        self._api_available = True

    def get_exchange_rate(self, from_currency: str, to_currency: str) -> float:
        """
        Get exchange rate from one currency to another.

        Args:
            from_currency: Source currency code (e.g., 'INR')
            to_currency: Target currency code (e.g., 'USD')

        Returns:
            Exchange rate as float
        """
        if from_currency == to_currency:
            return 1.0

        # Check cache
        cache_key = f"{from_currency}_{to_currency}"
        if self._is_cache_valid(cache_key):
            logger.debug(f"Using cached rate for {cache_key}")
            return self._cache[cache_key]

        # Try to fetch from API
        try:
            rate = self._fetch_from_api(from_currency, to_currency)
            if rate:
                self._cache[cache_key] = rate
                self._cache_timestamp[cache_key] = time.time()
                logger.info(f"Fetched rate from API: {cache_key} = {rate}")
                return rate
        except Exception as e:
            logger.warning(f"API fetch failed for {cache_key}: {e}")

        # Fallback to static rates
        rate = self._get_fallback_rate(from_currency, to_currency)
        logger.info(f"Using fallback rate: {cache_key} = {rate}")
        return rate

    def convert(
        self,
        amount: float,
        from_currency: str,
        to_currency: str
    ) -> float:
        """
        Convert amount from one currency to another.

        Args:
            amount: Amount to convert
            from_currency: Source currency
            to_currency: Target currency

        Returns:
            Converted amount
        """
        if from_currency == to_currency:
            return amount

        rate = self.get_exchange_rate(from_currency, to_currency)
        converted = amount * rate
        return round(converted, 2)

    def format_amount(
        self,
        amount: float,
        currency: str,
        include_symbol: bool = True
    ) -> str:
        """
        Format amount with currency symbol and proper notation.

        Args:
            amount: Amount to format
            currency: Currency code
            include_symbol: Whether to include currency symbol

        Returns:
            Formatted string
        """
        symbols = {
            'USD': '$',
            'INR': '₹',
            'EUR': '€',
            'GBP': '£',
            'AUD': 'A$',
            'CAD': 'C$',
            'SGD': 'S$',
            'JPY': '¥',
            'CNY': '¥'
        }

        symbol = symbols.get(currency, currency + ' ')

        # Format based on currency
        if currency == 'INR':
            # Indian numbering system
            if amount >= 10000000:  # 1 Crore
                formatted = f"{amount / 10000000:.2f} Cr"
            elif amount >= 100000:  # 1 Lakh
                formatted = f"{amount / 100000:.2f} L"
            else:
                formatted = f"{amount:,.2f}"
        elif currency in ['JPY', 'CNY']:
            # No decimal places for these
            formatted = f"{int(amount):,}"
        else:
            # Western numbering
            if amount >= 1000000000:  # Billion
                formatted = f"{amount / 1000000000:.2f}B"
            elif amount >= 1000000:  # Million
                formatted = f"{amount / 1000000:.2f}M"
            else:
                formatted = f"{amount:,.2f}"

        if include_symbol:
            return f"{symbol}{formatted}"
        return formatted

    def get_supported_currencies(self) -> Dict[str, str]:
        """
        Get list of supported currencies.

        Returns:
            Dict of currency code -> name
        """
        return {
            'USD': 'US Dollar',
            'INR': 'Indian Rupee',
            'EUR': 'Euro',
            'GBP': 'British Pound',
            'AUD': 'Australian Dollar',
            'CAD': 'Canadian Dollar',
            'SGD': 'Singapore Dollar',
            'JPY': 'Japanese Yen',
            'CNY': 'Chinese Yuan'
        }

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached rate is still valid"""
        if cache_key not in self._cache:
            return False

        age = time.time() - self._cache_timestamp.get(cache_key, 0)
        return age < self.CACHE_TTL

    def _fetch_from_api(
        self,
        from_currency: str,
        to_currency: str
    ) -> Optional[float]:
        """
        Fetch exchange rate from API.

        Uses exchangerate-api.com free tier.
        """
        if not self._api_available:
            return None

        try:
            import requests

            # Use free tier endpoint (no API key required)
            url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"

            response = requests.get(url, timeout=3)
            response.raise_for_status()

            data = response.json()
            rates = data.get('rates', {})

            if to_currency in rates:
                return float(rates[to_currency])

            logger.warning(f"Currency {to_currency} not found in API response")
            return None

        except ImportError:
            logger.warning("requests library not installed, using fallback rates")
            self._api_available = False
            return None
        except Exception as e:
            logger.warning(f"API request failed: {e}")
            # Don't mark API as unavailable for transient errors
            return None

    def _get_fallback_rate(
        self,
        from_currency: str,
        to_currency: str
    ) -> float:
        """
        Get exchange rate from fallback rates.

        Converts via USD as intermediate currency.
        """
        if from_currency not in self.FALLBACK_RATES:
            logger.warning(f"Unknown currency {from_currency}, treating as USD")
            from_rate = 1.0
        else:
            from_rate = self.FALLBACK_RATES[from_currency]

        if to_currency not in self.FALLBACK_RATES:
            logger.warning(f"Unknown currency {to_currency}, treating as USD")
            to_rate = 1.0
        else:
            to_rate = self.FALLBACK_RATES[to_currency]

        # Convert via USD: from -> USD -> to
        rate = to_rate / from_rate
        return rate

    def clear_cache(self):
        """Clear exchange rate cache (useful for testing)"""
        self._cache.clear()
        self._cache_timestamp.clear()
        logger.info("Currency exchange rate cache cleared")


# Singleton instance
_converter_instance = None

def get_converter() -> CurrencyConverter:
    """Get global currency converter instance"""
    global _converter_instance
    if _converter_instance is None:
        _converter_instance = CurrencyConverter()
    return _converter_instance


# Convenience functions
def convert_currency(
    amount: float,
    from_currency: str,
    to_currency: str
) -> float:
    """Convert amount between currencies"""
    converter = get_converter()
    return converter.convert(amount, from_currency, to_currency)


def format_currency(
    amount: float,
    currency: str,
    include_symbol: bool = True
) -> str:
    """Format amount with currency"""
    converter = get_converter()
    return converter.format_amount(amount, currency, include_symbol)


def get_exchange_rate(from_currency: str, to_currency: str) -> float:
    """Get current exchange rate"""
    converter = get_converter()
    return converter.get_exchange_rate(from_currency, to_currency)
