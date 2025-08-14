# MCP (Model Context Protocol) Servers

This directory contains MCP servers that provide structured access to external music data sources for the music discovery platform.

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │  LangGraph      │    │   External      │
│                 │    │  Workflows      │    │   APIs          │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          │                      │                      │
          ▼                      ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MCP Servers                                 │
│  ┌─────────────────┐  ┌─────────────────┐                      │
│  │ Artist Search   │  │ Artist Index    │                      │
│  │ MCP Server      │  │ MCP Server      │                      │
│  │                 │  │                 │                      │
│  │ • Wikidata      │  │ • Wikipedia     │                      │
│  │ • SPARQL        │  │ • MediaWiki API │                      │
│  │ • Artist data   │  │ • Web search    │                      │
│  └─────────────────┘  │ • Content       │                      │
│                       │   extraction    │                      │
│                       └─────────────────┘                      │
└─────────────────────────────────────────────────────────────────┘
```

## MCP Servers

### 1. Artist Search MCP Server (`artist_search.py`)

**Purpose**: Discover artists using Wikidata SPARQL queries

**Capabilities**:
- Search artists by name (exact and fuzzy matching)
- Filter by genre (rock, pop, jazz, etc.)
- Filter by era (1960s, 1970s, etc.)
- Filter by country
- Return structured artist data with confidence scores

**External Dependencies**:
- Wikidata SPARQL endpoint (public, no API key required)

**Integration Points**:
- FastAPI endpoint: `/api/artists/search`
- LangGraph workflow: Artist discovery

**Example Usage**:
```python
from src.mcp.artist_search import ArtistSearchMCPServer
from src.mcp.base import MCPConfig

config = MCPConfig()
async with ArtistSearchMCPServer(config) as server:
    result = await server.search("David Bowie", search_type="name", limit=5)
    print(f"Found {result['total_results']} artists")
```

### 2. Artist Index MCP Server (`artist_index.py`)

**Purpose**: Index artist content using Wikipedia and web search

**Capabilities**:
- Search Wikipedia for artist pages
- Extract detailed content and metadata
- Extract album and song information
- Web search fallback (when Google CSE is configured)
- Reference extraction and confidence scoring

**External Dependencies**:
- MediaWiki API (Wikipedia) - public, no API key required
- Google Custom Search Engine (optional, requires API key)

**Integration Points**:
- LangGraph workflow: Artist indexing
- FastAPI endpoint: `/api/artists/{id}/index`

**Example Usage**:
```python
from src.mcp.artist_index import ArtistIndexMCPServer
from src.mcp.base import MCPConfig

config = MCPConfig()
async with ArtistIndexMCPServer(config) as server:
    result = await server.search(
        "David Bowie", 
        artist_id="Q5383",
        enable_web_search=False
    )
    print(f"Indexed {len(result['wikipedia_pages'])} Wikipedia pages")
```

## Base Infrastructure (`base.py`)

### Core Components

1. **MCPConfig**: Configuration for rate limiting, caching, and timeouts
2. **RateLimiter**: Simple rate limiting for API requests
3. **SimpleCache**: In-memory cache with TTL
4. **BaseMCPServer**: Abstract base class for all MCP servers

### Features

- **Rate Limiting**: Configurable requests per minute/hour
- **Caching**: TTL-based caching to reduce API calls
- **Retry Logic**: Automatic retries with exponential backoff
- **Error Handling**: Comprehensive error handling and logging
- **Async Support**: Full async/await support for high performance

## Testing Framework (`test_mcp_servers.py`)

Comprehensive testing framework for validating MCP server functionality.

### Test Coverage

- **Artist Search Tests**:
  - Name search (exact and fuzzy)
  - Genre search
  - Era search
  - Country search
  - Result validation

- **Artist Index Tests**:
  - Wikipedia content extraction
  - Album/song extraction
  - Confidence scoring
  - Error handling

### Running Tests

```bash
# Run all tests
python -m src.mcp.test_mcp_servers

# Run specific test
python test_mcp_cli.py --test-search "David Bowie"
python test_mcp_cli.py --test-index "David Bowie" --artist-id Q5383
python test_mcp_cli.py --run-all-tests
```

## Configuration

### Environment Variables

```bash
# Optional: Google Custom Search Engine (for web search fallback)
GOOGLE_CSE_API_KEY=your_api_key
GOOGLE_CSE_ENGINE_ID=your_engine_id

# Optional: Custom rate limits
MCP_REQUESTS_PER_MINUTE=60
MCP_REQUESTS_PER_HOUR=1000
MCP_CACHE_TTL_SECONDS=3600
```

### Default Configuration

```python
MCPConfig(
    requests_per_minute=60,
    requests_per_hour=1000,
    cache_ttl_seconds=3600,
    request_timeout_seconds=30,
    max_retries=3,
    retry_delay_seconds=1,
    user_agent="MusicDiscoveryMCP/1.0"
)
```

## Data Models

### Artist Search Result

```python
@dataclass
class ArtistSearchResult:
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
```

### Indexing Result

```python
@dataclass
class IndexingResult:
    artist_id: str
    artist_name: str
    wikipedia_pages: List[Dict[str, Any]]
    web_references: List[Dict[str, Any]]
    albums_found: List[Dict[str, Any]]
    songs_found: List[Dict[str, Any]]
    total_references: int
    confidence_score: float
    indexing_status: str  # "completed", "partial", "failed"
```

## Performance Considerations

### Rate Limiting

- Wikidata: No strict limits, but be respectful
- MediaWiki API: No strict limits, but be respectful
- Google CSE: 100 queries/day (free tier)

### Caching Strategy

- **Artist Search**: Cache for 1 hour (artist data changes slowly)
- **Artist Index**: Cache for 1 hour (content changes moderately)
- **Wikipedia Content**: Cache for 6 hours (content is relatively stable)

### Optimization Tips

1. **Batch Requests**: Group multiple SPARQL queries when possible
2. **Selective Caching**: Cache expensive operations (Wikipedia content extraction)
3. **Connection Pooling**: Reuse HTTP connections via aiohttp session
4. **Parallel Processing**: Use asyncio for concurrent API calls

## Error Handling

### Common Error Scenarios

1. **Rate Limit Exceeded**: Automatic retry with exponential backoff
2. **Network Timeout**: Retry with increasing delays
3. **API Errors**: Graceful degradation with fallback options
4. **Invalid Data**: Validation and filtering of results

### Error Response Format

```python
{
    "success": False,
    "error": "Rate limit exceeded",
    "retry_after": 60,  # seconds
    "results": []
}
```

## Future Enhancements

### Planned Features

1. **Google CSE Integration**: Web search fallback for better coverage
2. **MusicBrainz Integration**: Additional music metadata
3. **Spotify API Integration**: Real-time music data
4. **Advanced Caching**: Redis-based distributed caching
5. **Metrics & Monitoring**: Performance tracking and alerting

### Extensibility

The MCP server architecture is designed for easy extension:

1. **New Data Sources**: Implement new MCP servers following the base pattern
2. **Custom Parsers**: Add specialized content extraction for different sources
3. **Advanced Filtering**: Implement more sophisticated relevance scoring
4. **Multi-language Support**: Extend to support non-English content

## Integration with LangGraph

The MCP servers integrate seamlessly with LangGraph workflows:

```python
# In LangGraph workflow
from src.mcp.artist_search import ArtistSearchMCPServer

async def search_artists(state):
    async with ArtistSearchMCPServer() as server:
        result = await server.search(state["query"])
        return {"artists": result["results"]}
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **Rate Limiting**: Check configuration and reduce request frequency
3. **Network Issues**: Verify internet connectivity and API endpoints
4. **Memory Usage**: Monitor cache size and adjust TTL settings

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Monitoring

Monitor key metrics:

- Request success rate
- Average response time
- Cache hit rate
- Rate limit violations
- Error frequency by type


