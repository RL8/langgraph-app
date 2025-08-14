"""
Base classes and utilities for MCP servers.

This module provides the foundation for implementing MCP servers
that integrate with external music data sources.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import aiohttp
from aiohttp import ClientSession, ClientTimeout

logger = logging.getLogger(__name__)


@dataclass
class MCPConfig:
    """Configuration for MCP servers."""
    
    # Rate limiting - More conservative for Wikidata
    requests_per_minute: int = 30
    requests_per_hour: int = 500
    
    # Caching
    cache_ttl_seconds: int = 3600  # 1 hour
    
    # Timeouts
    request_timeout_seconds: int = 30
    
    # Retry settings
    max_retries: int = 3
    retry_delay_seconds: int = 2
    exponential_backoff: bool = True
    
    # API specific settings
    user_agent: str = "MusicDiscoveryMCP/1.0"


@dataclass
class RateLimiter:
    """Simple rate limiter for API requests."""
    
    requests_per_minute: int
    requests_per_hour: int
    
    def __post_init__(self):
        self.minute_requests: List[datetime] = []
        self.hour_requests: List[datetime] = []
    
    def can_make_request(self) -> bool:
        """Check if a request can be made without exceeding rate limits."""
        now = datetime.now()
        
        # Clean old requests
        self.minute_requests = [req for req in self.minute_requests 
                              if now - req < timedelta(minutes=1)]
        self.hour_requests = [req for req in self.hour_requests 
                            if now - req < timedelta(hours=1)]
        
        # Check limits
        if len(self.minute_requests) >= self.requests_per_minute:
            return False
        if len(self.hour_requests) >= self.requests_per_hour:
            return False
        
        return True
    
    def record_request(self):
        """Record a request for rate limiting."""
        now = datetime.now()
        self.minute_requests.append(now)
        self.hour_requests.append(now)


@dataclass
class CacheEntry:
    """Cache entry with TTL."""
    
    data: Any
    timestamp: datetime
    ttl_seconds: int
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return datetime.now() - self.timestamp > timedelta(seconds=self.ttl_seconds)


class SimpleCache:
    """Simple in-memory cache with TTL."""
    
    def __init__(self, default_ttl_seconds: int = 3600):
        self.cache: Dict[str, CacheEntry] = {}
        self.default_ttl = default_ttl_seconds
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        if entry.is_expired():
            del self.cache[key]
            return None
        
        return entry.data
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        """Set value in cache with TTL."""
        ttl = ttl_seconds or self.default_ttl
        self.cache[key] = CacheEntry(
            data=value,
            timestamp=datetime.now(),
            ttl_seconds=ttl
        )
    
    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
    
    def cleanup_expired(self):
        """Remove expired entries from cache."""
        expired_keys = [
            key for key, entry in self.cache.items() 
            if entry.is_expired()
        ]
        for key in expired_keys:
            del self.cache[key]


class BaseMCPServer(ABC):
    """Base class for MCP servers."""
    
    def __init__(self, config: MCPConfig):
        self.config = config
        self.rate_limiter = RateLimiter(
            requests_per_minute=config.requests_per_minute,
            requests_per_hour=config.requests_per_hour
        )
        self.cache = SimpleCache(config.cache_ttl_seconds)
        self.session: Optional[ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        timeout = ClientTimeout(total=self.config.request_timeout_seconds)
        self.session = ClientSession(
            timeout=timeout,
            headers={"User-Agent": self.config.user_agent}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def _make_request(self, url: str, params: Optional[Dict] = None, 
                          headers: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request with rate limiting and retries."""
        if not self.session:
            raise RuntimeError("Server not initialized. Use async context manager.")
        
        # Check rate limits
        if not self.rate_limiter.can_make_request():
            logger.warning("Rate limit exceeded, waiting...")
            await asyncio.sleep(2)
        
        # Make request with retries
        for attempt in range(self.config.max_retries):
            try:
                self.rate_limiter.record_request()
                
                async with self.session.get(url, params=params, headers=headers) as response:
                    if response.status == 429:
                        # Handle rate limiting
                        logger.warning("Rate limited (HTTP 429)")
                        await asyncio.sleep(2)
                        continue
                    
                    elif response.status != 200:
                        error_text = await response.text()
                        logger.error(f"HTTP {response.status}: {error_text}")
                        raise Exception(f"HTTP {response.status}: {error_text}")
                    
                    data = await response.json()
                    return data
                    
            except Exception as e:
                if attempt == self.config.max_retries - 1:
                    logger.error(f"All retry attempts failed: {e}")
                    raise Exception(f"Request failed after {self.config.max_retries} attempts: {e}")
                
                # Simple delay
                delay = self.config.retry_delay_seconds
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                await asyncio.sleep(delay)
    
    def _get_cache_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
        return "|".join(key_parts)
    
    @abstractmethod
    async def search(self, query: str, **kwargs) -> Dict[str, Any]:
        """Search for data. Must be implemented by subclasses."""
        pass
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information."""
        return {
            "name": self.__class__.__name__,
            "version": "1.0.0",
            "capabilities": self.get_capabilities()
        }
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Get list of server capabilities. Must be implemented by subclasses."""
        pass
