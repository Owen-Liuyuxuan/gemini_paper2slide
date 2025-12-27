"""
Cache management for expensive operations.

Provides disk-based caching for API responses and intermediate results.
"""

import hashlib
import json
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from src.utils.config_loader import get_config
from src.utils.logger import get_logger

logger = get_logger("cache_manager")


class CacheManager:
    """
    Disk-based cache manager with TTL support.
    
    Caches Python objects using pickle and provides automatic expiration.
    
    Attributes:
        cache_dir: Directory for cache files
        ttl_hours: Time-to-live in hours
        enabled: Whether caching is enabled
    """
    
    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        ttl_hours: Optional[int] = None,
        enabled: Optional[bool] = None
    ) -> None:
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Cache directory (default from config)
            ttl_hours: Time-to-live in hours (default from config)
            enabled: Enable/disable caching (default from config)
        """
        cache_config = get_config("cache", {})
        
        self.enabled = enabled if enabled is not None else cache_config.get("enabled", True)
        self.cache_dir = cache_dir or Path(cache_config.get("cache_dir", ".cache"))
        self.ttl_hours = ttl_hours or cache_config.get("ttl_hours", 24)
        
        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Cache initialized at {self.cache_dir} with TTL={self.ttl_hours}h")
    
    def _get_cache_path(self, key: str) -> Path:
        """
        Get cache file path for a given key.
        
        Args:
            key: Cache key
        
        Returns:
            Path to cache file
        """
        # Hash the key to create a valid filename
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"
    
    def _is_expired(self, cache_path: Path) -> bool:
        """
        Check if cache file is expired.
        
        Args:
            cache_path: Path to cache file
        
        Returns:
            True if expired, False otherwise
        """
        if not cache_path.exists():
            return True
        
        # Check file modification time
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        expiry_time = mtime + timedelta(hours=self.ttl_hours)
        
        return datetime.now() > expiry_time
    
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value from cache.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found/expired
        
        Example:
            >>> cache = CacheManager()
            >>> result = cache.get("paper_analysis_xyz")
        """
        if not self.enabled:
            return None
        
        cache_path = self._get_cache_path(key)
        
        if self._is_expired(cache_path):
            logger.debug(f"Cache miss or expired for key: {key}")
            return None
        
        try:
            with open(cache_path, 'rb') as f:
                value = pickle.load(f)
            logger.debug(f"Cache hit for key: {key}")
            return value
        except Exception as e:
            logger.warning(f"Failed to load cache for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any) -> None:
        """
        Store value in cache.
        
        Args:
            key: Cache key
            value: Value to cache (must be picklable)
        
        Example:
            >>> cache = CacheManager()
            >>> cache.set("paper_analysis_xyz", analysis_result)
        """
        if not self.enabled:
            return
        
        cache_path = self._get_cache_path(key)
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(value, f)
            logger.debug(f"Cached value for key: {key}")
        except Exception as e:
            logger.warning(f"Failed to cache value for key {key}: {e}")
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache and is not expired.
        
        Args:
            key: Cache key
        
        Returns:
            True if exists and not expired, False otherwise
        """
        if not self.enabled:
            return False
        
        cache_path = self._get_cache_path(key)
        return cache_path.exists() and not self._is_expired(cache_path)
    
    def delete(self, key: str) -> None:
        """
        Delete cached value.
        
        Args:
            key: Cache key
        """
        if not self.enabled:
            return
        
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            cache_path.unlink()
            logger.debug(f"Deleted cache for key: {key}")
    
    def clear(self) -> None:
        """
        Clear all cached values.
        """
        if not self.enabled:
            return
        
        count = 0
        for cache_file in self.cache_dir.glob("*.cache"):
            cache_file.unlink()
            count += 1
        
        logger.info(f"Cleared {count} cache files")
    
    def clear_expired(self) -> None:
        """
        Remove expired cache files.
        """
        if not self.enabled:
            return
        
        count = 0
        for cache_file in self.cache_dir.glob("*.cache"):
            if self._is_expired(cache_file):
                cache_file.unlink()
                count += 1
        
        logger.info(f"Removed {count} expired cache files")