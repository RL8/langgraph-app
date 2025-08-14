"""
Testing framework for MCP servers.

This module provides utilities to test the MCP servers and validate their functionality.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List
from datetime import datetime

from .artist_search import ArtistSearchMCPServer
from .artist_index import ArtistIndexMCPServer
from .base import MCPConfig

logger = logging.getLogger(__name__)


class MCPTester:
    """Test framework for MCP servers."""
    
    def __init__(self):
        self.test_results = []
        self.config = MCPConfig(
            requests_per_minute=30,  # Lower for testing
            requests_per_hour=100,
            cache_ttl_seconds=300,  # 5 minutes for testing
            request_timeout_seconds=15
        )
    
    async def test_artist_search(self) -> Dict[str, Any]:
        """Test the artist search MCP server."""
        print("🧪 Testing Artist Search MCP Server...")
        
        test_cases = [
            {"name": "David Bowie", "search_type": "name"},
            {"name": "rock", "search_type": "genre"},
            {"name": "1980s", "search_type": "era"},
            {"name": "United States", "search_type": "country"},
        ]
        
        results = []
        async with ArtistSearchMCPServer(self.config) as server:
            for test_case in test_cases:
                print(f"  Testing: {test_case['name']} ({test_case['search_type']})")
                
                try:
                    result = await server.search(
                        test_case["name"], 
                        search_type=test_case["search_type"],
                        limit=3
                    )
                    
                    success = result.get("success", False)
                    total_results = result.get("total_results", 0)
                    
                    test_result = {
                        "test_case": test_case,
                        "success": success,
                        "total_results": total_results,
                        "error": result.get("error"),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    if success and total_results > 0:
                        print(f"    ✅ Success: {total_results} results")
                    else:
                        print(f"    ❌ Failed: {result.get('error', 'No results')}")
                    
                    results.append(test_result)
                    
                except Exception as e:
                    print(f"    ❌ Exception: {e}")
                    results.append({
                        "test_case": test_case,
                        "success": False,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
                
                # Small delay between tests
                await asyncio.sleep(1)
        
        return {
            "server": "artist_search",
            "total_tests": len(test_cases),
            "passed": sum(1 for r in results if r["success"]),
            "failed": sum(1 for r in results if not r["success"]),
            "results": results
        }
    
    async def test_artist_index(self) -> Dict[str, Any]:
        """Test the artist indexing MCP server."""
        print("🧪 Testing Artist Index MCP Server...")
        
        test_cases = [
            {"artist_name": "David Bowie", "artist_id": "Q5383"},
            {"artist_name": "The Beatles", "artist_id": "Q1299"},
            {"artist_name": "Queen", "artist_id": "Q1339"},
        ]
        
        results = []
        async with ArtistIndexMCPServer(self.config) as server:
            for test_case in test_cases:
                print(f"  Testing: {test_case['artist_name']}")
                
                try:
                    result = await server.search(
                        test_case["artist_name"],
                        artist_id=test_case["artist_id"],
                        enable_web_search=False  # Disable for testing
                    )
                    
                    success = not result.get("error")
                    wikipedia_pages = len(result.get("wikipedia_pages", []))
                    albums_found = len(result.get("albums_found", []))
                    songs_found = len(result.get("songs_found", []))
                    confidence = result.get("confidence_score", 0.0)
                    
                    test_result = {
                        "test_case": test_case,
                        "success": success,
                        "wikipedia_pages": wikipedia_pages,
                        "albums_found": albums_found,
                        "songs_found": songs_found,
                        "confidence": confidence,
                        "error": result.get("error"),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    if success and wikipedia_pages > 0:
                        print(f"    ✅ Success: {wikipedia_pages} pages, {albums_found} albums, {songs_found} songs (confidence: {confidence:.2f})")
                    else:
                        print(f"    ❌ Failed: {result.get('error', 'No content found')}")
                    
                    results.append(test_result)
                    
                except Exception as e:
                    print(f"    ❌ Exception: {e}")
                    results.append({
                        "test_case": test_case,
                        "success": False,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
                
                # Small delay between tests
                await asyncio.sleep(2)
        
        return {
            "server": "artist_index",
            "total_tests": len(test_cases),
            "passed": sum(1 for r in results if r["success"]),
            "failed": sum(1 for r in results if not r["success"]),
            "results": results
        }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all MCP server tests."""
        print("🚀 Starting MCP Server Tests...")
        print("=" * 50)
        
        start_time = datetime.now()
        
        # Run tests
        search_results = await self.test_artist_search()
        index_results = await self.test_artist_index()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Compile summary
        summary = {
            "test_run": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration
            },
            "servers": {
                "artist_search": search_results,
                "artist_index": index_results
            },
            "overall": {
                "total_tests": search_results["total_tests"] + index_results["total_tests"],
                "total_passed": search_results["passed"] + index_results["passed"],
                "total_failed": search_results["failed"] + index_results["failed"],
                "success_rate": (search_results["passed"] + index_results["passed"]) / 
                               (search_results["total_tests"] + index_results["total_tests"]) * 100
            }
        }
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        print(f"Duration: {duration:.2f} seconds")
        print(f"Total Tests: {summary['overall']['total_tests']}")
        print(f"Passed: {summary['overall']['total_passed']}")
        print(f"Failed: {summary['overall']['total_failed']}")
        print(f"Success Rate: {summary['overall']['success_rate']:.1f}%")
        
        print(f"\nArtist Search: {search_results['passed']}/{search_results['total_tests']} passed")
        print(f"Artist Index: {index_results['passed']}/{index_results['total_tests']} passed")
        
        return summary
    
    def save_test_results(self, results: Dict[str, Any], filename: str = None):
        """Save test results to a JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"mcp_test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Test results saved to: {filename}")


async def main():
    """Main test runner."""
    tester = MCPTester()
    results = await tester.run_all_tests()
    tester.save_test_results(results)


if __name__ == "__main__":
    asyncio.run(main())


