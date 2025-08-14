#!/usr/bin/env python3
"""
CLI script to test MCP servers.

Usage:
    python test_mcp_cli.py --test-search "David Bowie"
    python test_mcp_cli.py --test-index "David Bowie" --artist-id Q5383
    python test_mcp_cli.py --run-all-tests
"""

import asyncio
import argparse
import json
import logging
from typing import Optional

from src.mcp.artist_search import ArtistSearchMCPServer
from src.mcp.artist_index import ArtistIndexMCPServer
from src.mcp.base import MCPConfig

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)


async def test_artist_search(name: str, search_type: str = "name", limit: int = 5):
    """Test artist search MCP server."""
    print(f"🔍 Testing Artist Search: '{name}' (type: {search_type})")
    
    config = MCPConfig(
        requests_per_minute=30,
        requests_per_hour=100,
        cache_ttl_seconds=300
    )
    
    async with ArtistSearchMCPServer(config) as server:
        try:
            result = await server.search(name, search_type=search_type, limit=limit)
            
            if result.get("success"):
                print(f"✅ Success! Found {result['total_results']} results")
                
                for i, artist in enumerate(result['results'][:3], 1):
                    print(f"\n{i}. {artist['name']}")
                    print(f"   Wikidata ID: {artist['wikidata_id']}")
                    print(f"   Genres: {', '.join(artist['genres'][:3])}")
                    print(f"   Country: {artist.get('country', 'Unknown')}")
                    print(f"   Confidence: {artist['confidence_score']:.2f}")
                    
                    if artist.get('description'):
                        desc = artist['description'][:100] + "..." if len(artist['description']) > 100 else artist['description']
                        print(f"   Description: {desc}")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")


async def test_artist_index(artist_name: str, artist_id: Optional[str] = None):
    """Test artist indexing MCP server."""
    print(f"📚 Testing Artist Index: '{artist_name}'")
    
    config = MCPConfig(
        requests_per_minute=30,
        requests_per_hour=100,
        cache_ttl_seconds=300
    )
    
    async with ArtistIndexMCPServer(config) as server:
        try:
            result = await server.search(
                artist_name, 
                artist_id=artist_id,
                enable_web_search=False
            )
            
            if not result.get("error"):
                print(f"✅ Success!")
                print(f"   Wikipedia Pages: {len(result.get('wikipedia_pages', []))}")
                print(f"   Albums Found: {len(result.get('albums_found', []))}")
                print(f"   Songs Found: {len(result.get('songs_found', []))}")
                print(f"   Confidence: {result.get('confidence_score', 0):.2f}")
                print(f"   Status: {result.get('indexing_status', 'unknown')}")
                
                # Show some Wikipedia pages
                for i, page in enumerate(result.get('wikipedia_pages', [])[:2], 1):
                    print(f"\n   Wikipedia Page {i}: {page['title']}")
                    print(f"   URL: {page['url']}")
                    print(f"   Word Count: {page['word_count']}")
                    print(f"   Categories: {', '.join(page['categories'][:3])}")
                
                # Show some albums
                if result.get('albums_found'):
                    print(f"\n   Sample Albums:")
                    for album in result['albums_found'][:3]:
                        print(f"   - {album['title']} ({album['year']})")
                
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")


async def run_all_tests():
    """Run comprehensive tests for both MCP servers."""
    print("🚀 Running Comprehensive MCP Tests...")
    print("=" * 60)
    
    # Test artist search
    search_tests = [
        ("David Bowie", "name"),
        ("rock", "genre"),
        ("1980s", "era"),
        ("United States", "country"),
    ]
    
    print("\n🔍 Testing Artist Search MCP Server:")
    for name, search_type in search_tests:
        await test_artist_search(name, search_type, limit=2)
        await asyncio.sleep(1)  # Rate limiting
    
    # Test artist indexing
    index_tests = [
        ("David Bowie", "Q5383"),
        ("The Beatles", "Q1299"),
        ("Queen", "Q1339"),
    ]
    
    print("\n📚 Testing Artist Index MCP Server:")
    for artist_name, artist_id in index_tests:
        await test_artist_index(artist_name, artist_id)
        await asyncio.sleep(2)  # Rate limiting
    
    print("\n✅ All tests completed!")


def main():
    parser = argparse.ArgumentParser(description="Test MCP servers")
    parser.add_argument("--test-search", help="Test artist search with a name")
    parser.add_argument("--search-type", default="name", choices=["name", "genre", "era", "country"],
                       help="Search type for artist search")
    parser.add_argument("--test-index", help="Test artist indexing with a name")
    parser.add_argument("--artist-id", help="Wikidata ID for artist indexing")
    parser.add_argument("--run-all-tests", action="store_true", help="Run all comprehensive tests")
    parser.add_argument("--limit", type=int, default=5, help="Limit number of results")
    
    args = parser.parse_args()
    
    if args.test_search:
        asyncio.run(test_artist_search(args.test_search, args.search_type, args.limit))
    elif args.test_index:
        asyncio.run(test_artist_index(args.test_index, args.artist_id))
    elif args.run_all_tests:
        asyncio.run(run_all_tests())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
