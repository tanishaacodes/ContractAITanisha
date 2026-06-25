"""
Redis Caching Layer for Force Majeure Intelligence Engine
High-performance caching for expensive computations
"""

import json
import logging
import hashlib
from typing import Any, Dict, Optional, Callable
from datetime import timedelta
from functools import wraps

logger = logging.getLogger(__name__)

# Try to import Redis, fallback to in-memory cache if not available
try:
    import redis
    from django.core.cache import cache as django_cache
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using in-memory fallback cache")


class FMCache:
    """Force Majeure caching layer"""

    def __init__(self):
        self.redis_available = REDIS_AVAILABLE
        self.memory_cache = {} if not REDIS_AVAILABLE else None

        # Cache TTL (Time To Live) configurations
        self.ttl_config = {
            'prediction': timedelta(hours=6),      # Risk predictions
            'audit': timedelta(hours=12),          # Clause audits
            'portfolio': timedelta(hours=4),       # Portfolio simulations
            'war_loss': timedelta(hours=8),        # War loss predictions
            'geopolitical': timedelta(hours=1),    # Geopolitical data (changes frequently)
            'external_data': timedelta(minutes=30), # External data sources
            'llm_response': timedelta(days=7),     # LLM-generated clauses (expensive)
            'temporal_forecast': timedelta(hours=12),
            'digital_twin': timedelta(hours=6),
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache

        Args:
            key: Cache key
            default: Default value if key not found

        Returns:
            Cached value or default
        """
        try:
            if self.redis_available:
                value = django_cache.get(key)
                if value is not None:
                    logger.debug(f"Cache HIT: {key}")
                    return value
                logger.debug(f"Cache MISS: {key}")
                return default
            else:
                # In-memory fallback
                value = self.memory_cache.get(key, default)
                logger.debug(f"Memory cache {'HIT' if key in self.memory_cache else 'MISS'}: {key}")
                return value

        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            return default

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[timedelta] = None,
        cache_type: str = 'default'
    ) -> bool:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live (optional)
            cache_type: Cache type for TTL lookup

        Returns:
            Success status
        """
        try:
            # Determine TTL
            if ttl is None:
                ttl = self.ttl_config.get(cache_type, timedelta(hours=1))

            if self.redis_available:
                timeout = int(ttl.total_seconds())
                django_cache.set(key, value, timeout)
                logger.debug(f"Cache SET: {key} (TTL: {timeout}s)")
                return True
            else:
                # In-memory fallback (no TTL support)
                self.memory_cache[key] = value
                logger.debug(f"Memory cache SET: {key}")
                return True

        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            if self.redis_available:
                django_cache.delete(key)
            else:
                if key in self.memory_cache:
                    del self.memory_cache[key]
            logger.debug(f"Cache DELETE: {key}")
            return True

        except Exception as e:
            logger.error(f"Error deleting from cache: {e}")
            return False

    def clear(self, pattern: Optional[str] = None) -> bool:
        """
        Clear cache

        Args:
            pattern: Optional pattern to match keys (e.g., 'fm:prediction:*')

        Returns:
            Success status
        """
        try:
            if self.redis_available:
                if pattern:
                    # Clear matching keys
                    django_cache.delete_pattern(pattern)
                else:
                    # Clear all
                    django_cache.clear()
            else:
                if pattern:
                    # In-memory pattern matching
                    keys_to_delete = [k for k in self.memory_cache.keys() if pattern.replace('*', '') in k]
                    for k in keys_to_delete:
                        del self.memory_cache[k]
                else:
                    self.memory_cache.clear()

            logger.info(f"Cache CLEAR: {pattern or 'all'}")
            return True

        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False

    def get_or_compute(
        self,
        key: str,
        compute_func: Callable,
        ttl: Optional[timedelta] = None,
        cache_type: str = 'default'
    ) -> Any:
        """
        Get from cache or compute if not found

        Args:
            key: Cache key
            compute_func: Function to compute value if not cached
            ttl: Time to live
            cache_type: Cache type for TTL lookup

        Returns:
            Cached or computed value
        """
        # Try to get from cache
        value = self.get(key)

        if value is not None:
            return value

        # Compute value
        logger.debug(f"Computing value for key: {key}")
        value = compute_func()

        # Cache the computed value
        self.set(key, value, ttl, cache_type)

        return value

    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate cache key from arguments

        Args:
            prefix: Key prefix
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Generated cache key
        """
        # Create deterministic string from args
        key_data = {
            'args': args,
            'kwargs': kwargs
        }

        # Hash the data
        key_json = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_json.encode()).hexdigest()[:12]

        return f"fm:{prefix}:{key_hash}"


# Global cache instance
fm_cache = FMCache()


# Decorator for caching function results
def cached(
    cache_type: str = 'default',
    ttl: Optional[timedelta] = None,
    key_prefix: Optional[str] = None
):
    """
    Decorator to cache function results

    Usage:
        @cached(cache_type='prediction', ttl=timedelta(hours=6))
        def expensive_computation(arg1, arg2):
            # ... expensive computation
            return result
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            prefix = key_prefix or func.__name__
            cache_key = fm_cache.generate_key(prefix, *args, **kwargs)

            # Get or compute
            result = fm_cache.get_or_compute(
                cache_key,
                lambda: func(*args, **kwargs),
                ttl,
                cache_type
            )

            return result

        # Add cache control methods to wrapped function
        wrapper.cache_clear = lambda: fm_cache.clear(f"fm:{key_prefix or func.__name__}:*")
        wrapper.cache_key = lambda *args, **kwargs: fm_cache.generate_key(key_prefix or func.__name__, *args, **kwargs)

        return wrapper

    return decorator


# Convenience functions
def cache_fm_prediction(contract_text: str, evidence: Dict, result: Any) -> bool:
    """Cache FM prediction result"""
    key = fm_cache.generate_key('prediction', contract_text[:100], evidence)
    return fm_cache.set(key, result, cache_type='prediction')


def get_cached_prediction(contract_text: str, evidence: Dict) -> Optional[Any]:
    """Get cached FM prediction"""
    key = fm_cache.generate_key('prediction', contract_text[:100], evidence)
    return fm_cache.get(key)


def cache_portfolio_simulation(contracts: List[Dict], n_simulations: int, result: Any) -> bool:
    """Cache portfolio simulation result"""
    key = fm_cache.generate_key('portfolio', len(contracts), n_simulations)
    return fm_cache.set(key, result, cache_type='portfolio')


def get_cached_portfolio_simulation(contracts: List[Dict], n_simulations: int) -> Optional[Any]:
    """Get cached portfolio simulation"""
    key = fm_cache.generate_key('portfolio', len(contracts), n_simulations)
    return fm_cache.get(key)


def cache_llm_response(prompt_hash: str, response: str) -> bool:
    """Cache LLM response (expensive to generate)"""
    key = f"fm:llm:{prompt_hash}"
    return fm_cache.set(key, response, cache_type='llm_response')


def get_cached_llm_response(prompt_hash: str) -> Optional[str]:
    """Get cached LLM response"""
    key = f"fm:llm:{prompt_hash}"
    return fm_cache.get(key)


def cache_external_data(source: str, data: Any) -> bool:
    """Cache external data source"""
    key = f"fm:external:{source}"
    return fm_cache.set(key, data, cache_type='external_data')


def get_cached_external_data(source: str) -> Optional[Any]:
    """Get cached external data"""
    key = f"fm:external:{source}"
    return fm_cache.get(key)


def invalidate_contract_cache(contract_id: str) -> bool:
    """Invalidate all cache entries for a contract"""
    pattern = f"fm:*:*{contract_id}*"
    return fm_cache.clear(pattern)


def get_cache_stats() -> Dict:
    """Get cache statistics"""
    try:
        if fm_cache.redis_available:
            # Redis stats
            info = django_cache._cache.info()
            return {
                'backend': 'redis',
                'connected': True,
                'stats': {
                    'total_keys': info.get('db0', {}).get('keys', 0),
                    'memory_used': info.get('used_memory_human', 'N/A'),
                    'hits': info.get('keyspace_hits', 0),
                    'misses': info.get('keyspace_misses', 0)
                }
            }
        else:
            # In-memory stats
            return {
                'backend': 'in-memory',
                'connected': True,
                'stats': {
                    'total_keys': len(fm_cache.memory_cache),
                    'memory_used': 'N/A'
                }
            }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {
            'backend': 'unknown',
            'connected': False,
            'error': str(e)
        }


# Example usage with expensive FM operations
@cached(cache_type='prediction', ttl=timedelta(hours=6))
def cached_fm_prediction(contract_text: str, contract_value: float, evidence: Dict) -> Dict:
    """
    Cached FM prediction (example)

    This function result will be automatically cached for 6 hours
    """
    from .fm_service import predict_fm_risk
    return predict_fm_risk(contract_text, contract_value, evidence)


@cached(cache_type='portfolio', ttl=timedelta(hours=4))
def cached_portfolio_risk(contracts: List[Dict], n_simulations: int = 10000) -> Dict:
    """
    Cached portfolio risk simulation (example)

    Result cached for 4 hours
    """
    from .portfolio_simulator import portfolio_simulator
    return portfolio_simulator.simulate_portfolio_risk(contracts, n_simulations)
