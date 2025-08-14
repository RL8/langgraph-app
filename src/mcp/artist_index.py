"""
Artist Index MCP Server

Extracts Wikipedia content for artist profiles and dedicated album/song pages.
Focuses on getting high-quality, relevant content from Wikipedia.
"""

import asyncio
import re
from typing import Dict, List, Any, Optional
from urllib.parse import quote, urljoin

import aiohttp
from bs4 import BeautifulSoup

from .base import BaseMCPServer, MCPConfig


class ArtistIndexMCPServer(BaseMCPServer):
    """MCP server for extracting Wikipedia content for artists and their music."""
    
    def __init__(self, config: Optional[MCPConfig] = None):
        super().__init__(config or MCPConfig())
        self.mediawiki_api = "https://en.wikipedia.org/w/api.php"
        self.wikipedia_base = "https://en.wikipedia.org/wiki/"
        self.headers = {
            "User-Agent": "MusicApp/1.0 (https://github.com/your-repo; your-email@example.com)",
            "Accept": "application/json"
        }
    
    async def search(self, artist_name: str, artist_id: Optional[str] = None, 
                    enable_web_search: bool = False) -> Dict[str, Any]:
        """
        Extract Wikipedia content for artist and their music releases.
        
        Args:
            artist_name: The artist name to search for
            artist_id: Optional Wikidata ID for the artist
            enable_web_search: Whether to enable web search fallback
            
        Returns:
            Dictionary with extracted Wikipedia content
        """
        if not artist_name or not artist_name.strip():
            return {
                "wikipedia_pages": [],
                "album_pages": [],
                "song_pages": [],
                "total_pages": 0,
                "confidence": 0.0,
                "status": "error",
                "error": "Artist name is required"
            }
        
        artist_name = artist_name.strip()
        
        try:
            # Step 1: Find artist profile page
            artist_pages = await self._find_artist_pages(artist_name)
            
            # Step 2: Extract content from artist pages
            wikipedia_pages = []
            for page in artist_pages:
                content = await self._extract_page_content(page)
                if content:
                    wikipedia_pages.append(content)
            
            # Step 3: Find album pages (if we have artist info)
            album_pages = []
            if wikipedia_pages:
                albums = self._extract_album_names(wikipedia_pages)
                album_pages = await self._find_album_pages(albums, artist_name)
            
            # Step 4: Find song pages (if we have album info)
            song_pages = []
            if album_pages:
                songs = self._extract_song_names(album_pages)
                song_pages = await self._find_song_pages(songs, artist_name)
            
            # Calculate overall confidence
            total_pages = len(wikipedia_pages) + len(album_pages) + len(song_pages)
            confidence = self._calculate_confidence(wikipedia_pages, album_pages, song_pages)
            
            return {
                "wikipedia_pages": wikipedia_pages,
                "album_pages": album_pages,
                "song_pages": song_pages,
                "total_pages": total_pages,
                "confidence": confidence,
                "status": "completed",
                "artist_name": artist_name,
                "artist_id": artist_id
            }
            
        except Exception as e:
            self.logger.error(f"Error indexing artist {artist_name}: {e}")
            return {
                "wikipedia_pages": [],
                "album_pages": [],
                "song_pages": [],
                "total_pages": 0,
                "confidence": 0.0,
                "status": "error",
                "error": str(e)
            }
    
    async def _find_artist_pages(self, artist_name: str) -> List[Dict]:
        """Find Wikipedia pages for the artist."""
        search_queries = [
            artist_name,
            f"{artist_name} (musician)",
            f"{artist_name} (singer)",
            f"{artist_name} (band)"
        ]
        
        pages = []
        for query in search_queries:
            async with self.rate_limiter:
                try:
                    params = {
                        "action": "query",
                        "list": "search",
                        "srsearch": query,
                        "srlimit": 5,
                        "format": "json"
                    }
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            self.mediawiki_api,
                            params=params,
                            headers=self.headers,
                            timeout=aiohttp.ClientTimeout(total=30)
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                search_results = data.get("query", {}).get("search", [])
                                
                                for result in search_results:
                                    if self._is_relevant_artist_page(result, artist_name):
                                        pages.append({
                                            "page_id": result["pageid"],
                                            "title": result["title"],
                                            "snippet": result["snippet"]
                                        })
                
                except Exception as e:
                    self.logger.error(f"Error searching for {query}: {e}")
                    continue
        
        return pages[:3]  # Limit to top 3 results
    
    def _is_relevant_artist_page(self, result: Dict, artist_name: str) -> bool:
        """Check if a search result is relevant to the artist."""
        title = result.get("title", "").lower()
        snippet = result.get("snippet", "").lower()
        artist_lower = artist_name.lower()
        
        # Skip disambiguation pages
        if "disambiguation" in title:
            return False
        
        # Check if artist name appears in title or snippet
        if artist_lower in title or artist_lower in snippet:
            return True
        
        # Check for common music-related terms
        music_terms = ["musician", "singer", "band", "artist", "album", "song"]
        return any(term in snippet for term in music_terms)
    
    async def _extract_page_content(self, page: Dict) -> Optional[Dict]:
        """Extract content from a Wikipedia page."""
        async with self.rate_limiter:
            try:
                params = {
                    "action": "parse",
                    "pageid": page["page_id"],
                    "prop": "text|sections|categories",
                    "format": "json"
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        self.mediawiki_api,
                        params=params,
                        headers=self.headers,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            parse_data = data.get("parse", {})
                            
                            if parse_data:
                                return {
                                    "page_id": page["page_id"],
                                    "title": page["title"],
                                    "url": f"{self.wikipedia_base}{quote(page['title'].replace(' ', '_'))}",
                                    "content_type": "artist_profile",
                                    "content": self._clean_html_content(parse_data.get("text", {})),
                                    "sections": parse_data.get("sections", []),
                                    "categories": parse_data.get("categories", []),
                                    "word_count": len(self._clean_html_content(parse_data.get("text", {})).split()),
                                    "last_updated": "2024-01-15"  # Would need to extract from page
                                }
                
            except Exception as e:
                self.logger.error(f"Error extracting content from page {page['page_id']}: {e}")
        
        return None
    
    def _clean_html_content(self, html_content: Dict) -> str:
        """Clean HTML content and extract plain text."""
        if isinstance(html_content, dict):
            html = html_content.get("*", "")
        else:
            html = str(html_content)
        
        # Use BeautifulSoup to clean HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text and clean it up
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def _extract_album_names(self, wikipedia_pages: List[Dict]) -> List[str]:
        """Extract album names from artist Wikipedia pages."""
        albums = []
        
        for page in wikipedia_pages:
            content = page.get("content", "")
            
            # Look for album patterns in content
            # This is a simplified approach - could be enhanced with more sophisticated parsing
            album_patterns = [
                r'"([^"]*)"\s*\(album\)',
                r'album\s+"([^"]*)"',
                r'Album:\s*([^\n]*)',
                r'Albums:\s*([^\n]*)'
            ]
            
            for pattern in album_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                albums.extend(matches)
        
        return list(set(albums))[:10]  # Limit to 10 albums
    
    async def _find_album_pages(self, album_names: List[str], artist_name: str) -> List[Dict]:
        """Find Wikipedia pages for albums."""
        album_pages = []
        
        for album_name in album_names:
            search_queries = [
                f"{album_name} ({artist_name} album)",
                f"{album_name} album",
                f"{artist_name} {album_name}"
            ]
            
            for query in search_queries:
                async with self.rate_limiter:
                    try:
                        params = {
                            "action": "query",
                            "list": "search",
                            "srsearch": query,
                            "srlimit": 3,
                            "format": "json"
                        }
                        
                        async with aiohttp.ClientSession() as session:
                            async with session.get(
                                self.mediawiki_api,
                                params=params,
                                headers=self.headers,
                                timeout=aiohttp.ClientTimeout(total=30)
                            ) as response:
                                if response.status == 200:
                                    data = await response.json()
                                    search_results = data.get("query", {}).get("search", [])
                                    
                                    for result in search_results:
                                        if self._is_relevant_album_page(result, album_name, artist_name):
                                            content = await self._extract_page_content({
                                                "page_id": result["pageid"],
                                                "title": result["title"]
                                            })
                                            if content:
                                                content["content_type"] = "album_page"
                                                album_pages.append(content)
                                            break  # Take first relevant result
                    
                    except Exception as e:
                        self.logger.error(f"Error searching for album {album_name}: {e}")
                        continue
        
        return album_pages
    
    def _is_relevant_album_page(self, result: Dict, album_name: str, artist_name: str) -> bool:
        """Check if a search result is relevant to the album."""
        title = result.get("title", "").lower()
        snippet = result.get("snippet", "").lower()
        album_lower = album_name.lower()
        artist_lower = artist_name.lower()
        
        # Skip disambiguation pages
        if "disambiguation" in title:
            return False
        
        # Check if album name appears in title
        if album_lower in title:
            return True
        
        # Check for music-related terms
        music_terms = ["album", "song", "music", "recording"]
        return any(term in snippet for term in music_terms)
    
    def _extract_song_names(self, album_pages: List[Dict]) -> List[str]:
        """Extract song names from album Wikipedia pages."""
        songs = []
        
        for page in album_pages:
            content = page.get("content", "")
            
            # Look for song patterns in content
            song_patterns = [
                r'"([^"]*)"\s*\(song\)',
                r'song\s+"([^"]*)"',
                r'Track\s+\d+[:\s]*([^\n]*)',
                r'(\d+\.\s*[^\n]*)'  # Numbered tracks
            ]
            
            for pattern in song_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                songs.extend(matches)
        
        return list(set(songs))[:20]  # Limit to 20 songs
    
    async def _find_song_pages(self, song_names: List[str], artist_name: str) -> List[Dict]:
        """Find Wikipedia pages for songs."""
        song_pages = []
        
        for song_name in song_names:
            search_queries = [
                f"{song_name} ({artist_name} song)",
                f"{song_name} song",
                f"{artist_name} {song_name}"
            ]
            
            for query in search_queries:
                async with self.rate_limiter:
                    try:
                        params = {
                            "action": "query",
                            "list": "search",
                            "srsearch": query,
                            "srlimit": 3,
                            "format": "json"
                        }
                        
                        async with aiohttp.ClientSession() as session:
                            async with session.get(
                                self.mediawiki_api,
                                params=params,
                                headers=self.headers,
                                timeout=aiohttp.ClientTimeout(total=30)
                            ) as response:
                                if response.status == 200:
                                    data = await response.json()
                                    search_results = data.get("query", {}).get("search", [])
                                    
                                    for result in search_results:
                                        if self._is_relevant_song_page(result, song_name, artist_name):
                                            content = await self._extract_page_content({
                                                "page_id": result["pageid"],
                                                "title": result["title"]
                                            })
                                            if content:
                                                content["content_type"] = "song_page"
                                                song_pages.append(content)
                                            break  # Take first relevant result
                    
                    except Exception as e:
                        self.logger.error(f"Error searching for song {song_name}: {e}")
                        continue
        
        return song_pages[:10]  # Limit to 10 songs
    
    def _is_relevant_song_page(self, result: Dict, song_name: str, artist_name: str) -> bool:
        """Check if a search result is relevant to the song."""
        title = result.get("title", "").lower()
        snippet = result.get("snippet", "").lower()
        song_lower = song_name.lower()
        artist_lower = artist_name.lower()
        
        # Skip disambiguation pages
        if "disambiguation" in title:
            return False
        
        # Check if song name appears in title
        if song_lower in title:
            return True
        
        # Check for music-related terms
        music_terms = ["song", "single", "track", "music", "lyrics"]
        return any(term in snippet for term in music_terms)
    
    def _calculate_confidence(self, wikipedia_pages: List[Dict], 
                            album_pages: List[Dict], song_pages: List[Dict]) -> float:
        """Calculate confidence score based on content quality and quantity."""
        confidence = 0.0
        
        # Base confidence from artist pages
        if wikipedia_pages:
            confidence += 0.4
        
        # Additional confidence from album pages
        if album_pages:
            confidence += min(len(album_pages) * 0.1, 0.3)
        
        # Additional confidence from song pages
        if song_pages:
            confidence += min(len(song_pages) * 0.05, 0.2)
        
        # Quality boost for comprehensive content
        total_pages = len(wikipedia_pages) + len(album_pages) + len(song_pages)
        if total_pages >= 5:
            confidence += 0.1
        
        return min(confidence, 1.0)
    

