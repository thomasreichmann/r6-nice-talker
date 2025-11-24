"""
Development cache system for API responses.
Reduces API costs during development by caching message generations.
"""
import json
import hashlib
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from src.config import Config

logger = logging.getLogger(__name__)


class DevCache:
    """
    Simple file-based cache for development.
    Caches API responses to avoid redundant calls during testing.
    """
    
    def __init__(self, cache_dir: str = ".dev_cache", ttl: int = None):
        """
        Initialize the development cache.
        
        Args:
            cache_dir: Directory to store cache files
            ttl: Time-to-live in seconds (default: from config)
        """
        self.cache_dir = Path(cache_dir)
        self.ttl = ttl if ttl is not None else Config.DEV_CACHE_TTL
        self.enabled = Config.DEV_CACHE_ENABLED
        
        if self.enabled:
            self.cache_dir.mkdir(exist_ok=True)
            logger.debug(f"DevCache initialized: dir={cache_dir}, ttl={self.ttl}s")
        else:
            logger.debug("DevCache disabled")
    
    def _generate_key(self, **kwargs) -> str:
        """
        Generate a cache key from parameters.
        
        Args:
            **kwargs: Parameters to hash (persona_name, context, mode, etc.)
        
        Returns:
            Hex string cache key
        """
        # Sort keys for consistent hashing
        sorted_items = sorted(kwargs.items())
        key_string = json.dumps(sorted_items, sort_keys=True)
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    def _get_cache_path(self, key: str) -> Path:
        """Get the file path for a cache key."""
        return self.cache_dir / f"{key}.json"
    
    def get(self, **kwargs) -> Optional[str]:
        """
        Retrieve a value from cache.
        
        Args:
            **kwargs: Parameters to generate cache key
        
        Returns:
            Cached value if found and not expired, None otherwise
        """
        if not self.enabled:
            return None
        
        key = self._generate_key(**kwargs)
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            logger.debug(f"Cache miss: {key[:12]}...")
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check expiration
            if self.is_expired(data.get('timestamp', 0)):
                logger.debug(f"Cache expired: {key[:12]}...")
                cache_path.unlink(missing_ok=True)
                return None
            
            logger.info(f"✓ Cache hit: {key[:12]}...")
            return data.get('value')
            
        except Exception as e:
            logger.warning(f"Error reading cache: {e}")
            return None
    
    def set(self, value: str, **kwargs) -> None:
        """
        Store a value in cache.
        
        Args:
            value: Value to cache
            **kwargs: Parameters to generate cache key
        """
        if not self.enabled:
            return
        
        key = self._generate_key(**kwargs)
        cache_path = self._get_cache_path(key)
        
        data = {
            'value': value,
            'timestamp': time.time(),
            'ttl': self.ttl,
            'metadata': kwargs
        }
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Cached: {key[:12]}...")
            
        except Exception as e:
            logger.warning(f"Error writing cache: {e}")
    
    def is_expired(self, timestamp: float) -> bool:
        """
        Check if a timestamp is expired based on TTL.
        
        Args:
            timestamp: Unix timestamp
        
        Returns:
            True if expired, False otherwise
        """
        age = time.time() - timestamp
        return age > self.ttl
    
    def clear_expired(self) -> int:
        """
        Remove all expired cache files.
        
        Returns:
            Number of files removed
        """
        if not self.enabled or not self.cache_dir.exists():
            return 0
        
        removed = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if self.is_expired(data.get('timestamp', 0)):
                    cache_file.unlink()
                    removed += 1
                    
            except Exception as e:
                logger.warning(f"Error checking cache file {cache_file}: {e}")
        
        if removed > 0:
            logger.info(f"Cleared {removed} expired cache file(s)")
        
        return removed
    
    def clear_all(self) -> int:
        """
        Remove all cache files.
        
        Returns:
            Number of files removed
        """
        if not self.enabled or not self.cache_dir.exists():
            return 0
        
        removed = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
                removed += 1
            except Exception as e:
                logger.warning(f"Error deleting cache file {cache_file}: {e}")
        
        logger.info(f"Cleared all cache ({removed} file(s))")
        return removed
    
    def stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        if not self.enabled or not self.cache_dir.exists():
            return {
                'enabled': False,
                'total_files': 0,
                'valid_files': 0,
                'expired_files': 0,
                'total_size_bytes': 0
            }
        
        total = 0
        valid = 0
        expired = 0
        total_size = 0
        
        for cache_file in self.cache_dir.glob("*.json"):
            total += 1
            total_size += cache_file.stat().st_size
            
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if self.is_expired(data.get('timestamp', 0)):
                    expired += 1
                else:
                    valid += 1
                    
            except Exception:
                pass
        
        return {
            'enabled': True,
            'total_files': total,
            'valid_files': valid,
            'expired_files': expired,
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024)
        }


# Global cache instance
_cache_instance: Optional[DevCache] = None


def get_cache() -> DevCache:
    """Get the global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = DevCache()
    return _cache_instance

