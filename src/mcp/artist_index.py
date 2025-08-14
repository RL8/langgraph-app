"""
Artist Indexing MCP Server.

This MCP server provides artist indexing functionality using MediaWiki API
for Wikipedia content and web search for additional references.
"""

import logging
import re
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

from .base import BaseMCPServer, MCPConfig

logger = logging.getLogger(__name__)


@dataclass
class IndexingResult:
    """Structured result for artist indexing."""
    
    artist_id: str
    artist_name: str
    wikipedia_pages: List[Dict[str, Any]]
    web_references: List[Dict[str, Any]]
    albums_found: List[Dict[str, Any]]
    songs_found: List[Dict[str, Any]]
    total_references: int
    confidence_score: float
    indexing_status: str  # "completed", "partial", "failed"


@dataclass
class WikipediaPage:
    """Structured Wikipedia page data."""
    
    page_id: int
    title: str
    url: str
    extract: str
    categories: List[str]
    references: List[str]
    last_modified: str
    word_count: int


@dataclass
class WebReference:
    """Structured web reference data."""
    
    url: str
    title: str
    snippet: str
    domain: str
    relevance_score: float
    content_type: str  # "review", "biography", "discography", etc.


class ArtistIndexMCPServer(BaseMCPServer):
    """MCP server for artist indexing using Wikipedia and web search."""
    
    def __init__(self, config: Optional[MCPConfig] = None):
        super().__init__(config or MCPConfig())
        self.mediawiki_api = "https://en.wikipedia.org/w/api.php"
        # Note: Google CSE will be added later when API key is provided
        self.google_cse_url = "https://www.googleapis.com/customsearch/v1"
    
    def get_capabilities(self) -> List[str]:
        """Get list of server capabilities."""
        return [
            "wikipedia_search",
            "wikipedia_content_extraction",
            "web_search_fallback",
            "reference_extraction",
            "album_song_extraction",
            "confidence_scoring"
        ]
    
    async def search(self, query: str, **kwargs) -> Dict[str, Any]:
        """Index artist using Wikipedia and web search."""
        artist_id = kwargs.get("artist_id")
        artist_name = kwargs.get("artist_name", query)
        
        # Check cache first
        cache_key = self._get_cache_key("artist_index", artist_id, artist_name)
        cached_result = self.cache.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            # Step 1: Search Wikipedia
            wikipedia_results = await self._search_wikipedia(artist_name, **kwargs)
            
            # Step 2: Extract content from Wikipedia pages
            wikipedia_content = await self._extract_wikipedia_content(wikipedia_results, **kwargs)
            
            # Step 3: Web search fallback (when Google CSE is available)
            web_references = []
            if kwargs.get("enable_web_search", True):
                web_references = await self._web_search_fallback(artist_name, **kwargs)
            
            # Step 4: Calculate confidence and create result
            total_refs = len(wikipedia_content) + len(web_references)
            confidence = self._calculate_confidence(wikipedia_content, web_references)
            
            result = IndexingResult(
                artist_id=artist_id or "",
                artist_name=artist_name,
                wikipedia_pages=wikipedia_content,
                web_references=web_references,
                albums_found=[],
                songs_found=[],
                total_references=total_refs,
                confidence_score=confidence,
                indexing_status="completed" if confidence > 0.3 else "partial"
            )
            
            # Cache result
            self.cache.set(cache_key, result.__dict__)
            return result.__dict__
            
        except Exception as e:
            logger.error(f"Artist indexing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "artist_id": artist_id,
                "artist_name": artist_name,
                "indexing_status": "failed"
            }
    
    async def _search_wikipedia(self, artist_name: str, limit: int = 5, **kwargs) -> List[Dict[str, Any]]:
        """Search Wikipedia for artist-related pages."""
        # Search for exact artist name
        search_params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": f'"{artist_name}" musician',
            "srlimit": limit,
            "srnamespace": 0,  # Main namespace only
            "srprop": "snippet|timestamp"
        }
        
        data = await self._make_request(self.mediawiki_api, params=search_params)
        
        results = []
        for item in data.get("query", {}).get("search", []):
            # Filter for relevant pages
            if self._is_relevant_page(item["title"], item["snippet"], artist_name):
                results.append({
                    "page_id": item["pageid"],
                    "title": item["title"],
                    "snippet": item["snippet"],
                    "timestamp": item["timestamp"]
                })
        
        return results
    
    async def _extract_wikipedia_content(self, search_results: List[Dict], 
                                       **kwargs) -> List[Dict[str, Any]]:
        """Extract detailed content from Wikipedia pages."""
        if not search_results:
            return []
        
        # Get page IDs for content extraction
        page_ids = [str(result["page_id"]) for result in search_results]
        
        # Extract content
        content_params = {
            "action": "query",
            "format": "json",
            "pageids": "|".join(page_ids),
            "prop": "extracts|categories|revisions|info",
            "exintro": "1",
            "explaintext": "1",
            "cllimit": 50,
            "rvprop": "timestamp",
            "inprop": "url"
        }
        
        data = await self._make_request(self.mediawiki_api, params=content_params)
        
        pages = []
        for page_id, page_data in data.get("query", {}).get("pages", {}).items():
            if "missing" in page_data:
                continue
                
            # Extract categories
            categories = []
            for cat in page_data.get("categories", []):
                cat_title = cat["title"]
                if cat_title.startswith("Category:"):
                    categories.append(cat_title[9:])  # Remove "Category:" prefix
            
            # Extract references (simplified - could be enhanced)
            references = self._extract_references(page_data.get("extract", ""))
            
            # Calculate word count
            word_count = len(page_data.get("extract", "").split())
            
            page = WikipediaPage(
                page_id=int(page_id),
                title=page_data["title"],
                url=page_data.get("fullurl", ""),
                extract=page_data.get("extract", ""),
                categories=categories,
                references=references,
                last_modified=page_data.get("revisions", [{}])[0].get("timestamp", ""),
                word_count=word_count
            )
            
            pages.append(page.__dict__)
        
        return pages
    
    async def _web_search_fallback(self, artist_name: str, **kwargs) -> List[Dict[str, Any]]:
        """Web search fallback when Wikipedia doesn't have enough content."""
        # This will be implemented when Google CSE API key is provided
        # For now, return empty list
        logger.info("Web search fallback not yet implemented (requires Google CSE API key)")
        return []
    

    

    
    def _extract_references(self, text: str) -> List[str]:
        """Extract references from text."""
        references = []
        
        # Look for common reference patterns
        ref_patterns = [
            r'\[(\d+)\]',  # [1], [2], etc.
            r'\(([^)]+)\)',  # (reference text)
            r'https?://[^\s]+',  # URLs
        ]
        
        for pattern in ref_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                ref = match.group(1) if pattern != r'https?://[^\s]+' else match.group(0)
                if ref and len(ref) > 3:  # Filter out very short references
                    references.append(ref)
        
        return list(set(references))  # Remove duplicates
    
    def _is_relevant_page(self, title: str, snippet: str, artist_name: str) -> bool:
        """Check if a Wikipedia page is relevant to the artist."""
        # Check if artist name appears in title or snippet
        artist_lower = artist_name.lower()
        title_lower = title.lower()
        snippet_lower = snippet.lower()
        
        # Must contain artist name
        if artist_lower not in title_lower and artist_lower not in snippet_lower:
            return False
        
        # Filter out disambiguation pages
        if "disambiguation" in title_lower:
            return False
        
        # Filter out category pages
        if title_lower.startswith("category:"):
            return False
        
        # Filter out user pages
        if title_lower.startswith("user:"):
            return False
        
        return True
    
    def _calculate_confidence(self, wikipedia_content: List[Dict], 
                            web_references: List[Dict]) -> float:
        """Calculate confidence score for indexing result."""
        confidence = 0.0
        
        # Base confidence from Wikipedia content
        if wikipedia_content:
            confidence += 0.4
        
        # Additional confidence from web references
        if web_references:
            confidence += min(len(web_references) * 0.1, 0.3)
        
        # Quality bonus for comprehensive content
        total_content_length = sum(
            len(page.get("extract", "")) for page in wikipedia_content
        )
        if total_content_length > 1000:
            confidence += 0.1
        
        return min(confidence, 1.0)
    

