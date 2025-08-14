#!/usr/bin/env python3
"""
CLI tool for testing MCP servers.

Provides interactive testing of the artist search and indexing MCP servers.
"""

import asyncio
import argparse
import json
import sys
from typing import Dict, Any

# Add src to path for imports
sys.path.insert(0, 'src')

from mcp.artist_search import ArtistSearchMCPServer
from mcp.artist_index import ArtistIndexMCPServer
from mcp.base import MCPConfig


async def test_artist_search(artist_name: str, debug: bool = False) -> Dict[str, Any]:
    """Test artist search functionality."""
    print(f"\n🔍 Searching for artist: '{artist_name}'")
    print("=" * 50)
    
    async with ArtistSearchMCPServer() as server:
        result = await server.search(artist_name)
        
        if debug:
            print(f"Raw result: {json.dumps(result, indent=2)}")
        
        print(f"Total results: {result['total_results']}")
        print(f"Search term: {result['search_term']}")
        
        if result.get('error'):
            print(f"❌ Error: {result['error']}")
            return result
        
        if result['total_results'] == 0:
            print("❌ No results found")
            if result['search_suggestions']:
                print("💡 Suggestions:")
                for suggestion in result['search_suggestions']:
                    print(f"   - {suggestion}")
            return result
        
        print(f"✅ Found {result['total_results']} results")
        
        for i, artist in enumerate(result['results'][:5], 1):
            print(f"\n{i}. {artist['name']}")
            print(f"   Wikidata ID: {artist['wikidata_id']}")
            print(f"   Description: {artist['description'][:100]}...")
            print(f"   Country: {artist['country']}")
            print(f"   Confidence: {artist['confidence']:.2f}")
            print(f"   Match type: {artist['match_type']}")
            
            if artist.get('birth_year'):
                print(f"   Birth year: {artist['birth_year']}")
            if artist.get('death_year'):
                print(f"   Death year: {artist['death_year']}")
        
        if result['search_suggestions']:
            print(f"\n💡 Search suggestions:")
            for suggestion in result['search_suggestions']:
                print(f"   - {suggestion}")
        
        return result


async def test_artist_index(artist_name: str, artist_id: str = None, debug: bool = False) -> Dict[str, Any]:
    """Test artist indexing functionality."""
    print(f"\n📚 Indexing artist: '{artist_name}'")
    if artist_id:
        print(f"   Wikidata ID: {artist_id}")
    print("=" * 50)
    
    async with ArtistIndexMCPServer() as server:
        result = await server.search(artist_name, artist_id=artist_id)
        
        if debug:
            print(f"Raw result: {json.dumps(result, indent=2)}")
        
        print(f"Status: {result['status']}")
        print(f"Total pages: {result['total_pages']}")
        print(f"Confidence: {result['confidence']:.2f}")
        
        if result.get('error'):
            print(f"❌ Error: {result['error']}")
            return result
        
        if result['status'] == 'error':
            print("❌ Indexing failed")
            return result
        
        # Wikipedia pages
        print(f"\n📄 Wikipedia Pages: {len(result['wikipedia_pages'])}")
        for i, page in enumerate(result['wikipedia_pages'][:3], 1):
            print(f"   {i}. {page['title']}")
            print(f"      URL: {page['url']}")
            print(f"      Word count: {page['word_count']}")
            print(f"      Content type: {page['content_type']}")
        
        # Album pages
        print(f"\n💿 Album Pages: {len(result['album_pages'])}")
        for i, page in enumerate(result['album_pages'][:3], 1):
            print(f"   {i}. {page['title']}")
            print(f"      URL: {page['url']}")
            print(f"      Word count: {page['word_count']}")
            print(f"      Content type: {page['content_type']}")
        
        # Song pages
        print(f"\n🎵 Song Pages: {len(result['song_pages'])}")
        for i, page in enumerate(result['song_pages'][:3], 1):
            print(f"   {i}. {page['title']}")
            print(f"      URL: {page['url']}")
            print(f"      Word count: {page['word_count']}")
            print(f"      Content type: {page['content_type']}")
        
        return result


async def test_full_workflow(artist_name: str, debug: bool = False) -> Dict[str, Any]:
    """Test complete workflow: search then index."""
    print(f"\n🔄 Full Workflow Test: '{artist_name}'")
    print("=" * 60)
    
    # Step 1: Search for artist
    search_result = await test_artist_search(artist_name, debug)
    
    if search_result.get('error') or search_result['total_results'] == 0:
        print("❌ Search failed, cannot proceed with indexing")
        return search_result
    
    # Step 2: Index the first result
    top_artist = search_result['results'][0]
    artist_id = top_artist['wikidata_id']
    
    print(f"\n🎯 Indexing top result: {top_artist['name']} ({artist_id})")
    
    index_result = await test_artist_index(artist_name, artist_id, debug)
    
    # Summary
    print(f"\n📊 Workflow Summary:")
    print(f"   Search results: {search_result['total_results']}")
    print(f"   Indexed pages: {index_result['total_pages']}")
    print(f"   Index confidence: {index_result['confidence']:.2f}")
    
    return {
        "search": search_result,
        "index": index_result
    }


async def interactive_test():
    """Interactive testing mode."""
    print("🎵 MCP Server Interactive Testing")
    print("=" * 40)
    
    while True:
        print("\nOptions:")
        print("1. Test artist search")
        print("2. Test artist indexing")
        print("3. Test full workflow")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            artist_name = input("Enter artist name: ").strip()
            if artist_name:
                await test_artist_search(artist_name)
        
        elif choice == "2":
            artist_name = input("Enter artist name: ").strip()
            artist_id = input("Enter Wikidata ID (optional): ").strip() or None
            if artist_name:
                await test_artist_index(artist_name, artist_id)
        
        elif choice == "3":
            artist_name = input("Enter artist name: ").strip()
            if artist_name:
                await test_full_workflow(artist_name)
        
        elif choice == "4":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please enter 1-4.")


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(description="Test MCP servers for music app")
    parser.add_argument("--search", help="Test artist search with given name")
    parser.add_argument("--index", help="Test artist indexing with given name")
    parser.add_argument("--artist-id", help="Wikidata ID for indexing")
    parser.add_argument("--workflow", help="Test full workflow with given name")
    parser.add_argument("--interactive", "-i", action="store_true", help="Start interactive mode")
    parser.add_argument("--debug", "-d", action="store_true", help="Show debug information")
    
    args = parser.parse_args()
    
    if args.interactive:
        asyncio.run(interactive_test())
    elif args.search:
        asyncio.run(test_artist_search(args.search, args.debug))
    elif args.index:
        asyncio.run(test_artist_index(args.index, args.artist_id, args.debug))
    elif args.workflow:
        asyncio.run(test_full_workflow(args.workflow, args.debug))
    else:
        # Default: test with David Bowie
        print("🎵 Testing MCP servers with default artist: David Bowie")
        asyncio.run(test_full_workflow("David Bowie", args.debug))


if __name__ == "__main__":
    main()
