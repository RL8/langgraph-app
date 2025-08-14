"""
Artist Search MCP Server.

This MCP server provides artist discovery functionality using Wikidata SPARQL queries.
It can search for artists by name, filter by genre, era, and other criteria.
"""

import logging
import urllib.parse
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from .base import BaseMCPServer, MCPConfig

logger = logging.getLogger(__name__)


@dataclass
class ArtistSearchResult:
    """Structured result for artist search."""
    
    wikidata_id: str
    name: str
    aliases: List[str]
    description: Optional[str]
    genres: List[str]
    birth_date: Optional[str]
    death_date: Optional[str]
    country: Optional[str]
    image_url: Optional[str]
    wikipedia_url: Optional[str]
    musicbrainz_id: Optional[str]
    spotify_id: Optional[str]
    confidence_score: float


class ArtistSearchMCPServer(BaseMCPServer):
    """MCP server for artist discovery using Wikidata."""
    
    def __init__(self, config: Optional[MCPConfig] = None):
        super().__init__(config or MCPConfig())
        self.wikidata_endpoint = "https://query.wikidata.org/sparql"
    
    def get_capabilities(self) -> List[str]:
        """Get list of server capabilities."""
        return [
            "artist_search_by_name",
            "artist_search_by_genre", 
            "artist_search_by_era",
            "artist_search_by_country",
            "artist_details_by_id"
        ]
    
    async def search(self, query: str, **kwargs) -> Dict[str, Any]:
        """Search for artists using Wikidata SPARQL."""
        search_type = kwargs.get("search_type", "name")
        
        # Check cache first
        cache_key = self._get_cache_key("artist_search", query, search_type, **kwargs)
        cached_result = self.cache.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            if search_type == "name":
                results = await self._search_by_name(query, **kwargs)
            elif search_type == "genre":
                results = await self._search_by_genre(query, **kwargs)
            elif search_type == "era":
                results = await self._search_by_era(query, **kwargs)

            else:
                raise ValueError(f"Unknown search type: {search_type}")
            
            # Cache results
            self.cache.set(cache_key, results)
            return results
            
        except Exception as e:
            logger.error(f"Artist search failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": []
            }
    
    async def _search_by_name(self, name: str, limit: int = 10, 
                            min_confidence: float = 0.5, **kwargs) -> Dict[str, Any]:
        """Search for artists by name."""
        sparql_query = """
        SELECT DISTINCT ?artist ?artistLabel ?description ?birthDate ?deathDate ?country ?countryLabel ?image
        WHERE {
          ?artist wdt:P31 wd:Q5 ;  # Human
                  wdt:P106 wd:Q639669 .  # Occupation: musician
          
          # Get labels
          ?artist rdfs:label ?artistLabel .
          FILTER(LANG(?artistLabel) = "en")
          
          # Name matching (exact or contains)
          FILTER(CONTAINS(LCASE(?artistLabel), LCASE(?searchName)))
          
          # Get description
          OPTIONAL { ?artist schema:description ?description . FILTER(LANG(?description) = "en") }
          
          # Get birth/death dates
          OPTIONAL { ?artist wdt:P569 ?birthDate }
          OPTIONAL { ?artist wdt:P570 ?deathDate }
          
          # Get country
          OPTIONAL { ?artist wdt:P27 ?country . ?country rdfs:label ?countryLabel . FILTER(LANG(?countryLabel) = "en") }
          
          # Get images
          OPTIONAL { ?artist wdt:P18 ?image }
        }
        ORDER BY DESC(?birthDate)
        LIMIT ?limit
        """
        
        # Prepare query with direct substitution
        query = sparql_query.replace("?searchName", f'"{name}"').replace("?limit", str(limit))
        
        # Prepare parameters
        params = {
            "query": query,
            "format": "json"
        }
        
        # Make request
        logger.debug(f"Making SPARQL request with query: {query[:200]}...")
        data = await self._make_request(self.wikidata_endpoint, params=params)
        
        # Parse results
        results = []
        for binding in data.get("results", {}).get("bindings", []):
            artist = self._parse_artist_binding(binding)
            if artist.confidence_score >= min_confidence:
                results.append(artist.__dict__)
        
        return {
            "success": True,
            "query": name,
            "total_results": len(results),
            "results": results
        }
    
    async def _search_by_genre(self, genre: str, limit: int = 10, **kwargs) -> Dict[str, Any]:
        """Search for artists by genre."""
        sparql_query = """
        SELECT DISTINCT ?artist ?artistLabel ?description ?birthDate ?deathDate ?country ?countryLabel ?image
        WHERE {
          ?artist wdt:P31 wd:Q5 ;  # Human
                  wdt:P106 wd:Q639669 ;  # Occupation: musician
                  wdt:P136 ?genre .  # Genre
          
          # Genre matching
          ?genre rdfs:label ?genreLabel .
          FILTER(LANG(?genreLabel) = "en")
          FILTER(CONTAINS(LCASE(?genreLabel), LCASE('{genre}')))
          
          # Get labels
          ?artist rdfs:label ?artistLabel .
          FILTER(LANG(?artistLabel) = "en")
          
          # Get description
          OPTIONAL { ?artist schema:description ?description . FILTER(LANG(?description) = "en") }
          
          # Get birth/death dates
          OPTIONAL { ?artist wdt:P569 ?birthDate }
          OPTIONAL { ?artist wdt:P570 ?deathDate }
          
          # Get country
          OPTIONAL { ?artist wdt:P27 ?country . ?country rdfs:label ?countryLabel . FILTER(LANG(?countryLabel) = "en") }
          
          # Get images
          OPTIONAL { ?artist wdt:P18 ?image }
        }
        ORDER BY DESC(?birthDate)
        LIMIT {limit}
        """
        
        # Prepare query with direct substitution
        query = sparql_query.replace("{genre}", genre).replace("{limit}", str(limit))
        
        # Prepare parameters
        params = {
            "query": query,
            "format": "json"
        }
        
        # Make request
        logger.debug(f"Making genre SPARQL request with query: {query[:200]}...")
        data = await self._make_request(self.wikidata_endpoint, params=params)
        
        # Parse results
        results = []
        for binding in data.get("results", {}).get("bindings", []):
            artist = self._parse_artist_binding(binding)
            results.append(artist.__dict__)
        
        return {
            "success": True,
            "query": genre,
            "total_results": len(results),
            "results": results
        }
    
    async def _search_by_era(self, era: str, limit: int = 10, **kwargs) -> Dict[str, Any]:
        """Search for artists by era (decade, century, etc.)."""
        # This is a simplified implementation - could be enhanced with more sophisticated era matching
        sparql_query = """
        SELECT DISTINCT ?artist ?artistLabel ?description ?birthDate ?deathDate ?country ?countryLabel ?image
        WHERE {
          ?artist wdt:P31 wd:Q5 ;  # Human
                  wdt:P106 wd:Q639669 .  # Occupation: musician
          
          # Era filtering (simplified - could be enhanced)
          ?artist wdt:P569 ?birthDate .
          FILTER(YEAR(?birthDate) >= {start_year} && YEAR(?birthDate) <= {end_year})
          
          # Get labels
          ?artist rdfs:label ?artistLabel .
          FILTER(LANG(?artistLabel) = "en")
          
          # Get description
          OPTIONAL { ?artist schema:description ?description . FILTER(LANG(?description) = "en") }
          
          # Get death date
          OPTIONAL { ?artist wdt:P570 ?deathDate }
          
          # Get country
          OPTIONAL { ?artist wdt:P27 ?country . ?country rdfs:label ?countryLabel . FILTER(LANG(?countryLabel) = "en") }
          
          # Get images
          OPTIONAL { ?artist wdt:P18 ?image }
        }
        ORDER BY ?birthDate
        LIMIT {limit}
        """
        
        # Simple era mapping
        era_mapping = {
            "1960s": (1960, 1969),
            "1970s": (1970, 1979),
            "1980s": (1980, 1989),
            "1990s": (1990, 1999),
            "2000s": (2000, 2009),
            "2010s": (2010, 2019),
            "2020s": (2020, 2029),
        }
        
        start_year, end_year = era_mapping.get(era.lower(), (1900, 2029))
        
        # Prepare query with direct substitution
        query = sparql_query.replace("{start_year}", str(start_year)).replace("{end_year}", str(end_year)).replace("{limit}", str(limit))
        
        # Prepare parameters
        params = {
            "query": query,
            "format": "json"
        }
        
        # Make request
        logger.debug(f"Making era SPARQL request with query: {query[:200]}...")
        data = await self._make_request(self.wikidata_endpoint, params=params)
        
        # Parse results
        results = []
        for binding in data.get("results", {}).get("bindings", []):
            artist = self._parse_artist_binding(binding)
            results.append(artist.__dict__)
        
        return {
            "success": True,
            "query": era,
            "total_results": len(results),
            "results": results
        }
    

    
    def _parse_artist_binding(self, binding: Dict[str, Any]) -> ArtistSearchResult:
        """Parse SPARQL binding into structured artist result."""
        # Extract Wikidata ID
        artist_uri = binding.get("artist", {}).get("value", "")
        wikidata_id = artist_uri.split("/")[-1] if artist_uri else ""
        
        # Extract basic info
        name = binding.get("artistLabel", {}).get("value", "")
        description = binding.get("description", {}).get("value")
        birth_date = binding.get("birthDate", {}).get("value")
        death_date = binding.get("deathDate", {}).get("value")
        
        # Extract country
        country = binding.get("countryLabel", {}).get("value")
        
        # Extract images and URLs
        image_url = binding.get("image", {}).get("value")
        
        # For simplified query, we'll use empty lists for now
        genres = []
        aliases = []
        wikipedia_url = None
        musicbrainz_id = None
        spotify_id = None
        
        # Calculate confidence score (simplified)
        confidence_score = 0.5  # Base score
        if description:
            confidence_score += 0.2
        if image_url:
            confidence_score += 0.1
        if country:
            confidence_score += 0.1
        
        return ArtistSearchResult(
            wikidata_id=wikidata_id,
            name=name,
            aliases=aliases,
            description=description,
            genres=genres,
            birth_date=birth_date,
            death_date=death_date,
            country=country,
            image_url=image_url,
            wikipedia_url=wikipedia_url,
            musicbrainz_id=musicbrainz_id,
            spotify_id=spotify_id,
            confidence_score=min(confidence_score, 1.0)
        )
