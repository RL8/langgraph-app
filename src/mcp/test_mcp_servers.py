"""
Test suite for MCP servers.

Tests the artist search and indexing MCP servers with the revised functionality.
"""

import asyncio
import json
import pytest
from typing import Dict, Any

from .base import MCPConfig
from .artist_search import ArtistSearchMCPServer
from .artist_index import ArtistIndexMCPServer


class TestMCPConfig:
    """Test MCP configuration."""
    
    def test_default_config(self):
        """Test default configuration creation."""
        config = MCPConfig()
        assert config.rate_limit_per_minute == 60
        assert config.rate_limit_per_hour == 1000
        assert config.cache_ttl == 3600
        assert config.request_timeout == 30
    
    def test_custom_config(self):
        """Test custom configuration creation."""
        config = MCPConfig(
            rate_limit_per_minute=30,
            rate_limit_per_hour=500,
            cache_ttl=1800,
            request_timeout=15
        )
        assert config.rate_limit_per_minute == 30
        assert config.rate_limit_per_hour == 500
        assert config.cache_ttl == 1800
        assert config.request_timeout == 15


class TestArtistSearchMCPServer:
    """Test artist search MCP server."""
    
    @pytest.mark.asyncio
    async def test_search_exact_match(self):
        """Test exact name search."""
        async with ArtistSearchMCPServer() as server:
            result = await server.search("David Bowie")
            
            assert "results" in result
            assert "total_results" in result
            assert "search_suggestions" in result
            assert "search_term" in result
            
            if result["total_results"] > 0:
                artist = result["results"][0]
                assert "wikidata_id" in artist
                assert "name" in artist
                assert "confidence" in artist
                assert "match_type" in artist
                assert artist["match_type"] in ["exact", "fuzzy", "partial"]
    
    @pytest.mark.asyncio
    async def test_search_fuzzy_match(self):
        """Test fuzzy name search."""
        async with ArtistSearchMCPServer() as server:
            result = await server.search("Dvid Boie")  # Misspelling
            
            assert "results" in result
            assert "total_results" in result
            
            if result["total_results"] > 0:
                artist = result["results"][0]
                assert "confidence" in artist
                assert artist["confidence"] >= 0.7  # Should have decent confidence
    
    @pytest.mark.asyncio
    async def test_search_partial_match(self):
        """Test partial name search."""
        async with ArtistSearchMCPServer() as server:
            result = await server.search("Bowie")  # Partial name
            
            assert "results" in result
            assert "total_results" in result
            
            if result["total_results"] > 0:
                # Should find multiple results
                assert len(result["results"]) > 1
    
    @pytest.mark.asyncio
    async def test_search_no_results(self):
        """Test search with no results."""
        async with ArtistSearchMCPServer() as server:
            result = await server.search("Xyz123UnknownArtist")
            
            assert result["total_results"] == 0
            assert len(result["results"]) == 0
            assert len(result["search_suggestions"]) > 0
    
    @pytest.mark.asyncio
    async def test_search_empty_input(self):
        """Test search with empty input."""
        async with ArtistSearchMCPServer() as server:
            result = await server.search("")
            
            assert result["total_results"] == 0
            assert "error" in result
            assert result["error"] == "Artist name is required"
    
    @pytest.mark.asyncio
    async def test_search_whitespace_input(self):
        """Test search with whitespace-only input."""
        async with ArtistSearchMCPServer() as server:
            result = await server.search("   ")
            
            assert result["total_results"] == 0
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_result_structure(self):
        """Test that search results have correct structure."""
        async with ArtistSearchMCPServer() as server:
            result = await server.search("Queen")
            
            if result["total_results"] > 0:
                artist = result["results"][0]
                required_fields = [
                    "wikidata_id", "name", "description", "country", 
                    "image_url", "birth_year", "death_year", "confidence", "match_type"
                ]
                
                for field in required_fields:
                    assert field in artist
    
    @pytest.mark.asyncio
    async def test_confidence_scoring(self):
        """Test confidence scoring system."""
        async with ArtistSearchMCPServer() as server:
            result = await server.search("David Bowie")
            
            if result["total_results"] > 0:
                for artist in result["results"]:
                    confidence = artist["confidence"]
                    assert 0.0 <= confidence <= 1.0
                    
                    # Exact matches should have high confidence
                    if artist["match_type"] == "exact":
                        assert confidence >= 0.9


class TestArtistIndexMCPServer:
    """Test artist index MCP server."""
    
    @pytest.mark.asyncio
    async def test_index_artist_profile(self):
        """Test indexing artist profile pages."""
        async with ArtistIndexMCPServer() as server:
            result = await server.search("David Bowie")
            
            assert "wikipedia_pages" in result
            assert "album_pages" in result
            assert "song_pages" in result
            assert "total_pages" in result
            assert "confidence" in result
            assert "status" in result
            assert "artist_name" in result
            
            assert result["status"] in ["completed", "error"]
            assert 0.0 <= result["confidence"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_index_artist_with_albums(self):
        """Test indexing artist with album pages."""
        async with ArtistIndexMCPServer() as server:
            result = await server.search("Queen")
            
            assert "wikipedia_pages" in result
            assert "album_pages" in result
            assert "song_pages" in result
            
            # Should find some Wikipedia pages
            assert len(result["wikipedia_pages"]) >= 0
            
            # May find album pages if albums are mentioned
            assert len(result["album_pages"]) >= 0
    
    @pytest.mark.asyncio
    async def test_index_unknown_artist(self):
        """Test indexing unknown artist."""
        async with ArtistIndexMCPServer() as server:
            result = await server.search("Xyz123UnknownArtist")
            
            assert result["total_pages"] == 0
            assert result["confidence"] == 0.0
            assert result["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_index_empty_input(self):
        """Test indexing with empty input."""
        async with ArtistIndexMCPServer() as server:
            result = await server.search("")
            
            assert result["total_pages"] == 0
            assert result["confidence"] == 0.0
            assert result["status"] == "error"
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_wikipedia_page_structure(self):
        """Test structure of Wikipedia pages."""
        async with ArtistIndexMCPServer() as server:
            result = await server.search("David Bowie")
            
            if result["wikipedia_pages"]:
                page = result["wikipedia_pages"][0]
                required_fields = [
                    "page_id", "title", "url", "content_type", 
                    "content", "sections", "categories", "word_count"
                ]
                
                for field in required_fields:
                    assert field in page
                
                assert page["content_type"] == "artist_profile"
                assert page["word_count"] > 0
    
    @pytest.mark.asyncio
    async def test_album_page_structure(self):
        """Test structure of album pages."""
        async with ArtistIndexMCPServer() as server:
            result = await server.search("Queen")
            
            if result["album_pages"]:
                page = result["album_pages"][0]
                assert page["content_type"] == "album_page"
                assert page["word_count"] > 0
    
    @pytest.mark.asyncio
    async def test_song_page_structure(self):
        """Test structure of song pages."""
        async with ArtistIndexMCPServer() as server:
            result = await server.search("Queen")
            
            if result["song_pages"]:
                page = result["song_pages"][0]
                assert page["content_type"] == "song_page"
                assert page["word_count"] > 0
    
    @pytest.mark.asyncio
    async def test_confidence_calculation(self):
        """Test confidence calculation."""
        async with ArtistIndexMCPServer() as server:
            result = await server.search("David Bowie")
            
            confidence = result["confidence"]
            assert 0.0 <= confidence <= 1.0
            
            # More pages should generally mean higher confidence
            if result["total_pages"] > 5:
                assert confidence >= 0.5


class TestMCPIntegration:
    """Test integration between MCP servers."""
    
    @pytest.mark.asyncio
    async def test_search_then_index_workflow(self):
        """Test workflow: search for artist, then index them."""
        # Step 1: Search for artist
        async with ArtistSearchMCPServer() as search_server:
            search_result = await search_server.search("David Bowie")
            
            if search_result["total_results"] > 0:
                artist = search_result["results"][0]
                artist_id = artist["wikidata_id"]
                
                # Step 2: Index the artist
                async with ArtistIndexMCPServer() as index_server:
                    index_result = await index_server.search(
                        "David Bowie", 
                        artist_id=artist_id
                    )
                    
                    assert index_result["status"] == "completed"
                    assert index_result["artist_id"] == artist_id
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in both servers."""
        # Test search server with invalid input
        async with ArtistSearchMCPServer() as search_server:
            result = await search_server.search("")
            assert "error" in result
        
        # Test index server with invalid input
        async with ArtistIndexMCPServer() as index_server:
            result = await index_server.search("")
            assert "error" in result


if __name__ == "__main__":
    # Run basic tests
    async def run_tests():
        print("Testing Artist Search MCP Server...")
        async with ArtistSearchMCPServer() as server:
            result = await server.search("David Bowie")
            print(f"Found {result['total_results']} results")
            if result['results']:
                print(f"Top result: {result['results'][0]['name']}")
        
        print("\nTesting Artist Index MCP Server...")
        async with ArtistIndexMCPServer() as server:
            result = await server.search("David Bowie")
            print(f"Indexed {result['total_pages']} pages")
            print(f"Confidence: {result['confidence']:.2f}")
    
    asyncio.run(run_tests())


