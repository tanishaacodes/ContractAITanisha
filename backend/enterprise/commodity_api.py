"""
Real-Time Commodity Price API Integration
Supports multiple data providers: Alpha Vantage, Finnhub, and fallback to mock data
"""
import requests
import logging
from typing import Dict, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from django.conf import settings

logger = logging.getLogger(__name__)


class CommodityPriceAPI:
    """
    Real-time commodity price fetcher with multiple provider support
    """

    # Commodity symbol mappings
    SYMBOL_MAPPINGS = {
        'Steel': {'alpha_vantage': 'STEEL', 'finnhub': 'STEEL'},
        'Copper': {'alpha_vantage': 'COPPER', 'finnhub': 'HG=F'},
        'Oil': {'alpha_vantage': 'WTI', 'finnhub': 'CL=F'},
        'Aluminum': {'alpha_vantage': 'ALUMINUM', 'finnhub': 'ALI=F'},
        'Gold': {'alpha_vantage': 'GOLD', 'finnhub': 'GC=F'},
    }

    def __init__(self):
        # Try to get API keys from settings
        self.alpha_vantage_key = getattr(settings, 'ALPHA_VANTAGE_API_KEY', None)
        self.finnhub_key = getattr(settings, 'FINNHUB_API_KEY', None)

    def get_current_price(self, commodity_name: str) -> Optional[Dict]:
        """
        Get current price for a commodity from available APIs

        Args:
            commodity_name: Name of commodity (e.g., 'Steel', 'Copper')

        Returns:
            Dictionary with price data or None
        """
        # Try Alpha Vantage first
        if self.alpha_vantage_key:
            price_data = self._fetch_from_alpha_vantage(commodity_name)
            if price_data:
                return price_data

        # Try Finnhub as backup
        if self.finnhub_key:
            price_data = self._fetch_from_finnhub(commodity_name)
            if price_data:
                return price_data

        # Fallback to database current price
        logger.warning(f'No API keys configured, using database price for {commodity_name}')
        return self._get_database_price(commodity_name)

    def _fetch_from_alpha_vantage(self, commodity_name: str) -> Optional[Dict]:
        """Fetch from Alpha Vantage API"""
        try:
            symbol = self.SYMBOL_MAPPINGS.get(commodity_name, {}).get('alpha_vantage')
            if not symbol:
                return None

            url = 'https://www.alphavantage.co/query'
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': self.alpha_vantage_key
            }

            response = requests.get(url, params=params, timeout=5)
            data = response.json()

            if 'Global Quote' in data:
                quote = data['Global Quote']
                return {
                    'price': float(quote.get('05. price', 0)),
                    'change': float(quote.get('09. change', 0)),
                    'change_percent': quote.get('10. change percent', '0%'),
                    'volume': int(quote.get('06. volume', 0)),
                    'timestamp': quote.get('07. latest trading day'),
                    'source': 'alpha_vantage'
                }

        except Exception as e:
            logger.error(f'Alpha Vantage API error for {commodity_name}: {e}')

        return None

    def _fetch_from_finnhub(self, commodity_name: str) -> Optional[Dict]:
        """Fetch from Finnhub API"""
        try:
            symbol = self.SYMBOL_MAPPINGS.get(commodity_name, {}).get('finnhub')
            if not symbol:
                return None

            url = f'https://finnhub.io/api/v1/quote'
            params = {
                'symbol': symbol,
                'token': self.finnhub_key
            }

            response = requests.get(url, params=params, timeout=5)
            data = response.json()

            if data.get('c'):  # current price
                return {
                    'price': float(data['c']),
                    'change': float(data.get('d', 0)),
                    'change_percent': f"{data.get('dp', 0):.2f}%",
                    'high': float(data.get('h', 0)),
                    'low': float(data.get('l', 0)),
                    'timestamp': datetime.fromtimestamp(data.get('t', 0)).isoformat(),
                    'source': 'finnhub'
                }

        except Exception as e:
            logger.error(f'Finnhub API error for {commodity_name}: {e}')

        return None

    def _get_database_price(self, commodity_name: str) -> Optional[Dict]:
        """Fallback to database price"""
        try:
            from .models import Commodity
            commodity = Commodity.objects.get(name=commodity_name)

            return {
                'price': float(commodity.current_price),
                'change': 0.0,
                'change_percent': '0%',
                'timestamp': commodity.last_updated.isoformat(),
                'source': 'database',
                'note': 'Using cached database price (no API key configured)'
            }

        except Exception as e:
            logger.error(f'Database fallback error for {commodity_name}: {e}')

        return None

    def update_commodity_prices(self) -> Dict:
        """
        Update all commodity prices from APIs

        Returns:
            Summary of updates
        """
        from .models import Commodity

        updated_count = 0
        failed_count = 0
        results = []

        for commodity in Commodity.objects.all():
            price_data = self.get_current_price(commodity.name)

            if price_data:
                try:
                    # Update price
                    commodity.current_price = Decimal(str(price_data['price']))
                    commodity.save()

                    updated_count += 1
                    results.append({
                        'commodity': commodity.name,
                        'old_price': float(commodity.current_price),
                        'new_price': price_data['price'],
                        'source': price_data['source'],
                        'status': 'updated'
                    })

                    logger.info(f"Updated {commodity.name}: ${price_data['price']} from {price_data['source']}")

                except Exception as e:
                    failed_count += 1
                    logger.error(f"Failed to update {commodity.name}: {e}")
                    results.append({
                        'commodity': commodity.name,
                        'error': str(e),
                        'status': 'failed'
                    })
            else:
                failed_count += 1
                results.append({
                    'commodity': commodity.name,
                    'status': 'no_data'
                })

        return {
            'total': Commodity.objects.count(),
            'updated': updated_count,
            'failed': failed_count,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }


# Singleton instance
commodity_api = CommodityPriceAPI()
