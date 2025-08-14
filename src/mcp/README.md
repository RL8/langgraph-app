# MCP (Model Context Protocol) Servers

This directory contains MCP servers that provide intelligent artist search and Wikipedia content extraction for the music discovery platform.

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Input    │    │  MCP Servers    │    │   External      │
│   Artist Name   │───▶│                 │───▶│   APIs          │
└─────────────────┘    │  • Artist       │    │                 │
                       │    Search       │    │  • Wikidata     │
                       │  • Artist       │    │  • Wikipedia    │
                       │    Index        │    │  • MediaWiki    │
                       └─────────────────┘    └─────────────────┘
```

## MCP Servers

### 1. Artist Search MCP Server (`artist_search.py`)

**Purpose**: Intelligent artist discovery using Wikidata with fuzzy matching and confidence scoring

**Key Features**:
- **Multi-step search strategy**: Exact → Fuzzy → Partial matching
- **Confidence scoring**: Based on data completeness and match quality
- **Smart suggestions**: Helpful search refinements for users
- **Error handling**: Graceful handling of edge cases

**Search Strategy**:
1. **Exact Match**: Direct name lookup (confidence: 0.95)
2. **Fuzzy Match**: Handle misspellings with regex patterns (confidence: 0.85)
3. **Partial Match**: Substring search for broader results (confidence: 0.70)

**External Dependencies**:
- Wikidata SPARQL endpoint (public, no API key required)

**Example Usage**:
```python
from src.mcp.artist_search import ArtistSearchMCPServer

async with ArtistSearchMCPServer() as server:
    result = await server.search("David Bowie")
    print(f"Found {result['total_results']} artists")
    
    for artist in result['results']:
        print(f"{artist['name']} - Confidence: {artist['confidence']:.2f}")
```

**Response Structure**:
```json
{
    "results": [
        {
            "wikidata_id": "Q5383",
            "name": "David Bowie",
            "description": "English musician and actor",
            "country": "United Kingdom",
            "image_url": "...",
            "birth_year": "1947",
            "death_year": "2016",
            "confidence": 0.95,
            "match_type": "exact"
        }
    ],
    "total_results": 1,
    "search_suggestions": ["Try 'David Bowie'", "Try 'Bowie'"],
    "search_term": "David Bowie"
}
```

### 2. Artist Index MCP Server (`artist_index.py`)

**Purpose**: Extract Wikipedia content for artist profiles and dedicated album/song pages

**Content Types**:
- **Artist Profile Pages**: Main biography and career information
- **Album Pages**: Dedicated pages for individual albums
- **Song Pages**: Dedicated pages for individual songs

**Extraction Process**:
1. **Artist Profile Search**: Find main artist Wikipedia pages
2. **Album Discovery**: Extract album names from artist content
3. **Album Page Search**: Find dedicated album Wikipedia pages
4. **Song Discovery**: Extract song names from album content
5. **Song Page Search**: Find dedicated song Wikipedia pages

**External Dependencies**:
- MediaWiki API (Wikipedia) - public, no API key required

**Example Usage**:
```python
from src.mcp.artist_index import ArtistIndexMCPServer

async with ArtistIndexMCPServer() as server:
    result = await server.search("David Bowie")
    print(f"Indexed {result['total_pages']} pages")
    print(f"Confidence: {result['confidence']:.2f}")
```

**Response Structure**:
```json
{
    "wikipedia_pages": [
        {
            "page_id": 12345,
            "title": "David Bowie",
            "url": "https://en.wikipedia.org/wiki/David_Bowie",
            "content_type": "artist_profile",
            "content": "English musician and actor...",
            "word_count": 15000,
            "last_updated": "2024-01-15"
        }
    ],
    "album_pages": [...],
    "song_pages": [...],
    "total_pages": 15,
    "confidence": 0.85,
    "status": "completed",
    "artist_name": "David Bowie"
}
```

## Base Infrastructure (`base.py`)

### Core Components

1. **MCPConfig**: Configuration for rate limiting, caching, and timeouts
2. **RateLimiter**: Simple rate limiting for API requests
3. **SimpleCache**: In-memory cache with TTL support
4. **BaseMCPServer**: Abstract base class with common functionality

### Configuration Options

```python
from src.mcp.base import MCPConfig

config = MCPConfig(
    rate_limit_per_minute=60,    # Requests per minute
    rate_limit_per_hour=1000,    # Requests per hour
    cache_ttl=3600,              # Cache TTL in seconds
    request_timeout=30           # Request timeout in seconds
)
```

## Testing

### CLI Testing Tool

```bash
# Test artist search
python test_mcp_cli.py --search "David Bowie"

# Test artist indexing
python test_mcp_cli.py --index "David Bowie"

# Test full workflow
python test_mcp_cli.py --workflow "David Bowie"

# Interactive testing
python test_mcp_cli.py --interactive

# Debug mode
python test_mcp_cli.py --search "David Bowie" --debug
```

### Automated Tests

```bash
# Run all tests
pytest src/mcp/test_mcp_servers.py -v

# Test specific components
pytest src/mcp/test_mcp_servers.py::TestArtistSearchMCPServer -v
pytest src/mcp/test_mcp_servers.py::TestArtistIndexMCPServer -v
```

### Test Coverage

| Component | Test Coverage | Key Test Areas |
|-----------|---------------|----------------|
| **Artist Search** | ✅ Complete | Exact/fuzzy/partial matching, confidence scoring |
| **Artist Index** | ✅ Complete | Wikipedia extraction, content validation |
| **Base Classes** | ✅ Complete | Rate limiting, caching, configuration |

## Performance & Limits

### Rate Limiting
- **Wikidata**: No strict limits, but respectful usage
- **MediaWiki API**: No strict limits, but respectful usage

### Caching Strategy
- **Artist Search**: 1 hour TTL (artist data changes slowly)
- **Artist Index**: 1 hour TTL (content changes moderately)

### Response Times
- **Artist Search**: ~2-3 seconds (Wikidata SPARQL)
- **Artist Index**: ~5-10 seconds (Wikipedia content extraction)

## Error Handling

### Common Error Scenarios

| Error Type | Response | Action |
|------------|----------|--------|
| **Network Issues** | Retry with backoff | Graceful degradation |
| **No Results** | Empty results + suggestions | User guidance |
| **Invalid Input** | Error message | Input validation |
| **Rate Limit** | Respect limits | Automatic throttling |

### Error Response Format

```json
{
    "results": [],
    "total_results": 0,
    "error": "Artist name is required",
    "search_suggestions": ["Please provide an artist name"]
}
```

## Integration Points

### FastAPI Endpoints (Ready for Implementation)
- `POST /api/artists/search` → Artist Search MCP
- `POST /api/artists/{id}/index` → Artist Index MCP

### LangGraph Workflows (Ready for Integration)
```python
# Example integration
from src.mcp.artist_search import ArtistSearchMCPServer
from src.mcp.artist_index import ArtistIndexMCPServer

async def search_artists(state):
    async with ArtistSearchMCPServer() as server:
        result = await server.search(state["artist_name"])
        return {"artists": result["results"]}

async def index_artist(state):
    async with ArtistIndexMCPServer() as server:
        result = await server.search(state["artist_name"], artist_id=state["artist_id"])
        return {"indexing_result": result}
```

## Development

### Adding New Features

1. **Extend BaseMCPServer**: Inherit from base class
2. **Implement Required Methods**: Override abstract methods
3. **Add Tests**: Create comprehensive test coverage
4. **Update Documentation**: Keep README current

### Debugging

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Use debug mode in CLI
python test_mcp_cli.py --search "David Bowie" --debug
```

## Dependencies

```toml
dependencies = [
    "aiohttp>=3.9.0",      # HTTP client for API calls
    "beautifulsoup4>=4.12.0", # HTML parsing for Wikipedia content
]
```

## Success Criteria

### Technical Criteria
- ✅ Multi-step search strategy implemented
- ✅ Confidence scoring system operational
- ✅ Wikipedia content extraction working
- ✅ Comprehensive error handling
- ✅ Rate limiting and caching implemented

### Functional Criteria
- ✅ Artist search returns accurate results
- ✅ Fuzzy matching handles misspellings
- ✅ Wikipedia content extraction functional
- ✅ Content quality validation working
- ✅ User-friendly search suggestions

## Next Steps

1. **Database Integration**: Store search results and indexed content
2. **API Layer**: Create FastAPI endpoints
3. **Frontend Integration**: Connect to React/CopilotKit
4. **Advanced Features**: Add more sophisticated content analysis


