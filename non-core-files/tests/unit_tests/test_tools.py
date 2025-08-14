"""Unit tests for tools functionality."""

import pytest
from unittest.mock import patch, AsyncMock
from agent.tools import search, scrape_website


class TestSearchTool:
    """Test search tool functionality."""

    @pytest.mark.asyncio
    async def test_search_success(self):
        """Test successful search."""
        query = "David Bowie albums"
        
        # Mock successful search response
        mock_response = [
            {"title": "David Bowie Albums", "link": "https://example.com/bowie", "snippet": "Album info"},
            {"title": "Bowie Discography", "link": "https://example.com/discography", "snippet": "Discography info"}
        ]
        
        with patch('agent.tools.search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_response
            
            result = await search(query, config={})
            
            assert len(result) == 2
            assert result[0]["title"] == "David Bowie Albums"

    @pytest.mark.asyncio
    async def test_search_empty_query(self):
        """Test search with empty query."""
        with patch('agent.tools.search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = []
            
            result = await search("", config={})
            
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_search_error_handling(self):
        """Test search error handling."""
        query = "David Bowie"
        
        with patch('agent.tools.search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [{"error": "Search failed"}]
            
            result = await search(query, config={})
            
            assert "error" in result[0]
            assert "Search failed" in result[0]["error"]

    @pytest.mark.asyncio
    async def test_search_rate_limit(self):
        """Test search rate limiting."""
        query = "David Bowie"
        
        with patch('agent.tools.search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [{"error": "Rate limit exceeded"}]
            
            result = await search(query, config={})
            
            assert "error" in result[0]
            assert "Rate limit" in result[0]["error"]


class TestScrapeWebsiteTool:
    """Test website scraping tool functionality."""

    @pytest.mark.asyncio
    async def test_scrape_website_success(self, sample_state):
        """Test successful website scraping."""
        url = "https://example.com/david-bowie"
        
        # Mock successful scraping response
        mock_content = """
        <html>
            <body>
                <h1>David Bowie</h1>
                <p>David Bowie was a British musician and actor.</p>
                <ul>
                    <li>Space Oddity (1969)</li>
                    <li>Ziggy Stardust (1972)</li>
                </ul>
            </body>
        </html>
        """
        
        with patch('agent.tools.scrape_website', new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = "David Bowie was a British musician and actor."
            
            result = await scrape_website(url, state=sample_state, config={})
            
            assert "David Bowie" in result

    @pytest.mark.asyncio
    async def test_scrape_website_invalid_url(self, sample_state):
        """Test scraping with invalid URL."""
        url = "invalid-url"
        
        with patch('agent.tools.scrape_website', new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = "Error scraping website: Invalid URL"
            
            result = await scrape_website(url, state=sample_state, config={})
            
            assert "Error" in result

    @pytest.mark.asyncio
    async def test_scrape_website_network_error(self, sample_state):
        """Test scraping with network error."""
        url = "https://example.com/david-bowie"
        
        with patch('agent.tools.scrape_website', new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = "Error scraping website: Connection timeout"
            
            result = await scrape_website(url, state=sample_state, config={})
            
            assert "Error" in result

    @pytest.mark.asyncio
    async def test_scrape_website_empty_content(self):
        """Test scraping website with empty content."""
        url = "https://example.com/empty"
        
        with patch('agent.tools.scrape_webpage', new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = {
                "content": "",
                "title": "",
                "extracted_text": ""
            }
            
            result = await scrape_website(url)
            
            assert "content" in result
            assert result["content"] == ""

    @pytest.mark.asyncio
    async def test_scrape_website_content_extraction(self):
        """Test that content is properly extracted and cleaned."""
        url = "https://example.com/david-bowie"
        
        # Mock HTML with various elements
        mock_content = """
        <html>
            <head><title>David Bowie</title></head>
            <body>
                <script>var x = 1;</script>
                <style>.hidden { display: none; }</style>
                <h1>David Bowie</h1>
                <p>David Bowie was a British musician and actor.</p>
                <div class="hidden">This should be removed</div>
                <ul>
                    <li>Space Oddity (1969)</li>
                    <li>Ziggy Stardust (1972)</li>
                </ul>
            </body>
        </html>
        """
        
        with patch('agent.tools.scrape_webpage', new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = {
                "content": mock_content,
                "title": "David Bowie",
                "extracted_text": "David Bowie was a British musician and actor. Space Oddity (1969) Ziggy Stardust (1972)"
            }
            
            result = await scrape_website(url)
            
            assert "content" in result
            assert "David Bowie" in result["content"]
            # Should not contain script or style content
            assert "var x = 1" not in result["content"]
            assert "display: none" not in result["content"]
