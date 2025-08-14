"""
Artist Search MCP Server

Provides intelligent artist search using Wikidata SPARQL queries with fuzzy matching
and confidence scoring. Focuses on finding likely matches for user-provided artist names.
"""

import asyncio
import re
from typing import Dict, List, Any, Optional
from urllib.parse import quote

import aiohttp

from .base import BaseMCPServer, MCPConfig


class ArtistSearchMCPServer(BaseMCPServer):
    """MCP server for intelligent artist search using Wikidata."""
    
    def __init__(self, config: Optional[MCPConfig] = None):
        super().__init__(config or MCPConfig())
        self.wikidata_url = "https://query.wikidata.org/sparql"
        self.headers = {
            "User-Agent": "MusicApp/1.0 (https://github.com/your-repo; your-email@example.com)",
            "Accept": "application/sparql-results+json"
        }
    
    async def search(self, artist_name: str, search_options: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Search for artists matching the provided name with confidence scoring.
        
        Args:
            artist_name: The artist name to search for
            search_options: Optional parameters for refinement
            
        Returns:
            Dictionary with search results and metadata
        """
        if not artist_name or not artist_name.strip():
            return {
                "results": [],
                "total_results": 0,
                "search_suggestions": ["Please provide an artist name"],
                "error": "Artist name is required"
            }
        
        artist_name = artist_name.strip()
        
        # Multi-step search strategy
        results = []
        
        # Step 1: Exact name search
        exact_results = await self._exact_name_search(artist_name)
        results.extend(exact_results)
        
        # Step 2: Fuzzy name search (if no exact matches or few results)
        if len(results) < 3:
            fuzzy_results = await self._fuzzy_name_search(artist_name)
            results.extend(fuzzy_results)
        
        # Step 3: Partial name search (if still few results)
        if len(results) < 5:
            partial_results = await self._partial_name_search(artist_name)
            results.extend(partial_results)
        
        # Remove duplicates and rank by confidence
        unique_results = self._deduplicate_results(results)
        ranked_results = self._rank_results_by_confidence(unique_results)
        
        # Generate search suggestions
        suggestions = self._generate_search_suggestions(artist_name, ranked_results)
        
        return {
            "results": ranked_results[:10],  # Limit to top 10
            "total_results": len(ranked_results),
            "search_suggestions": suggestions,
            "search_term": artist_name
        }
    
    async def _exact_name_search(self, artist_name: str) -> List[Dict]:
        """Search for exact name matches."""
        query = """
        SELECT ?artist ?artistLabel ?description ?country ?image ?occupation ?birthYear ?deathYear
        WHERE {
          ?artist wdt:P31 wd:Q5 .
          ?artist ?label ?name .
          FILTER(?name = "%s"@en)
          OPTIONAL { ?artist wdt:P27 ?country . }
          OPTIONAL { ?artist wdt:P18 ?image . }
          OPTIONAL { ?artist wdt:P106 ?occupation . }
          OPTIONAL { ?artist wdt:P569 ?birthDate . BIND(YEAR(?birthDate) AS ?birthYear) }
          OPTIONAL { ?artist wdt:P570 ?deathDate . BIND(YEAR(?deathDate) AS ?deathYear) }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en" . }
        }
        LIMIT 10
        """ % artist_name
        
        results = await self._execute_sparql_query(query)
        return [self._process_result(r, "exact", 0.95) for r in results]
    
    async def _fuzzy_name_search(self, artist_name: str) -> List[Dict]:
        """Search for fuzzy name matches using regex patterns."""
        # Create regex pattern for fuzzy matching
        words = artist_name.split()
        if len(words) >= 2:
            pattern = f"{words[0]}.*{words[-1]}"
        else:
            pattern = artist_name
        
        query = """
        SELECT ?artist ?artistLabel ?description ?country ?image ?occupation ?birthYear ?deathYear
        WHERE {
          ?artist wdt:P31 wd:Q5 .
          ?artist wdt:P106 wd:Q639669 .  # Musician
          ?artist ?label ?name .
          FILTER(REGEX(?name, "%s", "i"))
          OPTIONAL { ?artist wdt:P27 ?country . }
          OPTIONAL { ?artist wdt:P18 ?image . }
          OPTIONAL { ?artist wdt:P106 ?occupation . }
          OPTIONAL { ?artist wdt:P569 ?birthDate . BIND(YEAR(?birthDate) AS ?birthYear) }
          OPTIONAL { ?artist wdt:P570 ?deathDate . BIND(YEAR(?deathDate) AS ?deathYear) }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en" . }
        }
        LIMIT 10
        """ % pattern
        
        results = await self._execute_sparql_query(query)
        return [self._process_result(r, "fuzzy", 0.85) for r in results]
    
    async def _partial_name_search(self, artist_name: str) -> List[Dict]:
        """Search for partial name matches."""
        query = """
        SELECT ?artist ?artistLabel ?description ?country ?image ?occupation ?birthYear ?deathYear
        WHERE {
          ?artist wdt:P31 wd:Q5 .
          ?artist wdt:P106 wd:Q639669 .  # Musician
          ?artist ?label ?name .
          FILTER(CONTAINS(LCASE(?name), LCASE("%s")))
          OPTIONAL { ?artist wdt:P27 ?country . }
          OPTIONAL { ?artist wdt:P18 ?image . }
          OPTIONAL { ?artist wdt:P106 ?occupation . }
          OPTIONAL { ?artist wdt:P569 ?birthDate . BIND(YEAR(?birthDate) AS ?birthYear) }
          OPTIONAL { ?artist wdt:P570 ?deathDate . BIND(YEAR(?deathDate) AS ?deathYear) }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en" . }
        }
        LIMIT 10
        """ % artist_name
        
        results = await self._execute_sparql_query(query)
        return [self._process_result(r, "partial", 0.70) for r in results]
    
    async def _execute_sparql_query(self, query: str) -> List[Dict]:
        """Execute SPARQL query with rate limiting and error handling."""
        async with self.rate_limiter:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.wikidata_url,
                        headers=self.headers,
                        data={"query": query, "format": "json"},
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            return data.get("results", {}).get("bindings", [])
                        else:
                            self.logger.error(f"SPARQL query failed: {response.status}")
                            return []
            except Exception as e:
                self.logger.error(f"Error executing SPARQL query: {e}")
                return []
    
    def _process_result(self, result: Dict, match_type: str, base_confidence: float) -> Dict:
        """Process and score a single search result."""
        # Extract basic information
        artist_id = result.get("artist", {}).get("value", "").split("/")[-1]
        name = result.get("artistLabel", {}).get("value", "")
        description = result.get("description", {}).get("value", "")
        country = result.get("country", {}).get("value", "")
        image = result.get("image", {}).get("value", "")
        birth_year = result.get("birthYear", {}).get("value", "")
        death_year = result.get("deathYear", {}).get("value", "")
        
        # Calculate confidence score
        confidence = self._calculate_confidence(
            base_confidence, name, description, country, image, birth_year
        )
        
        return {
            "wikidata_id": artist_id,
            "name": name,
            "description": description,
            "country": country,
            "image_url": image,
            "birth_year": birth_year,
            "death_year": death_year,
            "confidence": confidence,
            "match_type": match_type
        }
    
    def _calculate_confidence(self, base_confidence: float, name: str, 
                            description: str, country: str, image: str, 
                            birth_year: str) -> float:
        """Calculate confidence score based on data completeness."""
        confidence = base_confidence
        
        # Boost confidence for data completeness
        if description:
            confidence += 0.05
        if country:
            confidence += 0.03
        if image:
            confidence += 0.02
        if birth_year:
            confidence += 0.02
        
        # Cap confidence at 1.0
        return min(confidence, 1.0)
    
    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate results based on Wikidata ID."""
        seen_ids = set()
        unique_results = []
        
        for result in results:
            artist_id = result.get("wikidata_id")
            if artist_id and artist_id not in seen_ids:
                seen_ids.add(artist_id)
                unique_results.append(result)
        
        return unique_results
    
    def _rank_results_by_confidence(self, results: List[Dict]) -> List[Dict]:
        """Sort results by confidence score (highest first)."""
        return sorted(results, key=lambda x: x.get("confidence", 0), reverse=True)
    
    def _generate_search_suggestions(self, artist_name: str, results: List[Dict]) -> List[str]:
        """Generate helpful search suggestions based on results."""
        suggestions = []
        
        if not results:
            suggestions.extend([
                f"Try searching for '{artist_name}' with different spelling",
                "Check if the artist name is correct",
                "Try searching for just the first or last name"
            ])
        elif len(results) > 5:
            suggestions.extend([
                "Try adding more specific terms",
                "Consider adding the artist's country or genre"
            ])
        
        return suggestions
