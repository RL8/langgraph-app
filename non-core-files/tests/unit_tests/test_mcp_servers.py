"""Unit tests for MCP server functionality."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from src.mcp.artist_search import ArtistSearchMCPServer
from src.mcp.artist_index import ArtistIndexMCPServer
from src.mcp.base import MCPConfig, RateLimiter, SimpleCache


class TestMCPConfig:
    """Test MCP configuration."""

    def test_mcp_config_defaults(self):
        """Test MCP config default values."""
        config = MCPConfig()
        
        assert config.requests_per_minute == 30
        assert config.requests_per_hour == 500
        assert config.cache_ttl_seconds == 3600
        assert config.request_timeout_seconds == 30
        assert config.max_retries == 3

    def test_mcp_config_custom(self):
        """Test MCP config with custom values."""
        config = MCPConfig(
            requests_per_minute=10,
            requests_per_hour=100,
            cache_ttl_seconds=1800
        )
        
        assert config.requests_per_minute == 10
        assert config.requests_per_hour == 100
        assert config.cache_ttl_seconds == 1800


class TestRateLimiter:
    """Test rate limiting functionality."""

    def test_rate_limiter_initialization(self):
        """Test rate limiter initialization."""
        limiter = RateLimiter(requests_per_minute=10, requests_per_hour=100)
        
        assert limiter.requests_per_minute == 10
        assert limiter.requests_per_hour == 100
        assert len(limiter.minute_requests) == 0
        assert len(limiter.hour_requests) == 0

    def test_rate_limiter_can_make_request(self):
        """Test rate limiter allows requests within limits."""
        limiter = RateLimiter(requests_per_minute=2, requests_per_hour=5)
        
        # Should allow first request
        assert limiter.can_make_request() is True
        limiter.record_request()
        
        # Should allow second request
        assert limiter.can_make_request() is True
        limiter.record_request()
        
        # Should block third request
        assert limiter.can_make_request() is False

    def test_rate_limiter_cleanup_old_requests(self):
        """Test rate limiter cleans up old requests."""
        from datetime import datetime, timedelta
        
        limiter = RateLimiter(requests_per_minute=1, requests_per_hour=1)
        
        # Add old request
        old_time = datetime.now() - timedelta(minutes=2)
        limiter.minute_requests.append(old_time)
        limiter.hour_requests.append(old_time)
        
        # Should clean up old requests
        assert limiter.can_make_request() is True


class TestSimpleCache:
    """Test caching functionality."""

    def test_cache_initialization(self):
        """Test cache initialization."""
        cache = SimpleCache(default_ttl_seconds=1800)
        
        assert cache.default_ttl == 1800
        assert len(cache.cache) == 0

    def test_cache_set_and_get(self):
        """Test cache set and get operations."""
        cache = SimpleCache()
        
        # Set value
        cache.set("test_key", "test_value", ttl_seconds=3600)
        
        # Get value
        value = cache.get("test_key")
        assert value == "test_value"

    def test_cache_expiration(self):
        """Test cache expiration."""
        cache = SimpleCache()
        
        # Set value with short TTL
        cache.set("test_key", "test_value", ttl_seconds=1)
        
        # Should be available immediately
        assert cache.get("test_key") == "test_value"
        
        # After expiration, should return None
        import time
        time.sleep(2)
        assert cache.get("test_key") is None

    def test_cache_clear(self):
        """Test cache clearing."""
        cache = SimpleCache()
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        assert len(cache.cache) == 2
        
        cache.clear()
        assert len(cache.cache) == 0


class TestArtistSearchMCPServer:
    """Test artist search MCP server."""

    @pytest.mark.asyncio
    async def test_artist_search_success(self):
        """Test successful artist search."""
        mock_response = {
            "results": [
                {
                    "id": "Q1299",
                    "name": "David Bowie",
                    "description": "British musician",
                    "confidence": 0.95
                }
            ],
            "total_results": 1
        }
        
        with patch('src.mcp.artist_search.ArtistSearchMCPServer._make_sparql_query', 
                  new_callable=AsyncMock) as mock_query:
            mock_query.return_value = mock_response
            
            async with ArtistSearchMCPServer() as server:
                result = await server.search("David Bowie")
                
                assert "results" in result
                assert len(result["results"]) == 1
                assert result["results"][0]["name"] == "David Bowie"
                assert result["results"][0]["id"] == "Q1299"

    @pytest.mark.asyncio
    async def test_artist_search_no_results(self):
        """Test artist search with no results."""
        with patch('src.mcp.artist_search.ArtistSearchMCPServer._make_sparql_query', 
                  new_callable=AsyncMock) as mock_query:
            mock_query.return_value = {"results": [], "total_results": 0}
            
            async with ArtistSearchMCPServer() as server:
                result = await server.search("NonexistentArtist")
                
                assert "results" in result
                assert len(result["results"]) == 0
                assert result["total_results"] == 0

    @pytest.mark.asyncio
    async def test_artist_search_error_handling(self):
        """Test artist search error handling."""
        with patch('src.mcp.artist_search.ArtistSearchMCPServer._make_sparql_query', 
                  new_callable=AsyncMock) as mock_query:
            mock_query.side_effect = Exception("SPARQL query failed")
            
            async with ArtistSearchMCPServer() as server:
                result = await server.search("David Bowie")
                
                assert "error" in result
                assert "SPARQL query failed" in result["error"]


class TestArtistIndexMCPServer:
    """Test artist index MCP server."""

    @pytest.mark.asyncio
    async def test_artist_index_success(self):
        """Test successful artist indexing."""
        mock_wikipedia_response = {
            "title": "David Bowie",
            "content": "David Bowie was a British musician and actor.",
            "albums": ["Space Oddity", "Ziggy Stardust"],
            "songs": ["Space Oddity", "Starman"]
        }
        
        with patch('src.mcp.artist_index.ArtistIndexMCPServer._search_wikipedia', 
                  new_callable=AsyncMock) as mock_wiki:
            mock_wiki.return_value = mock_wikipedia_response
            
            async with ArtistIndexMCPServer() as server:
                result = await server.search("David Bowie", artist_id="Q1299")
                
                assert "title" in result
                assert "content" in result
                assert "albums" in result
                assert "songs" in result
                assert result["title"] == "David Bowie"

    @pytest.mark.asyncio
    async def test_artist_index_wikipedia_not_found(self):
        """Test artist indexing when Wikipedia page not found."""
        with patch('src.mcp.artist_index.ArtistIndexMCPServer._search_wikipedia', 
                  new_callable=AsyncMock) as mock_wiki:
            mock_wiki.return_value = None
            
            async with ArtistIndexMCPServer() as server:
                result = await server.search("NonexistentArtist", artist_id="Q9999")
                
                assert "error" in result
                assert "Wikipedia page not found" in result["error"]

    @pytest.mark.asyncio
    async def test_artist_index_error_handling(self):
        """Test artist indexing error handling."""
        with patch('src.mcp.artist_index.ArtistIndexMCPServer._search_wikipedia', 
                  new_callable=AsyncMock) as mock_wiki:
            mock_wiki.side_effect = Exception("Wikipedia API failed")
            
            async with ArtistIndexMCPServer() as server:
                result = await server.search("David Bowie", artist_id="Q1299")
                
                assert "error" in result
                assert "Wikipedia API failed" in result["error"]
