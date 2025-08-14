# Insomnia Test Collection Setup Guide

## Quick Start

### 1. Import the Test Collection
1. Open Insomnia
2. Go to **Create** → **Import from File**
3. Select `insomnia_tests.json`
4. The collection will be imported with all 12 test requests

### 2. Set Up Environment
1. In Insomnia, go to **Manage Environments**
2. Select **Development Environment**
3. Verify these settings:
   ```
   base_url: http://127.0.0.1:2025
   proxy_url: http://127.0.0.1:8080
   timeout: 30000
   ```

### 3. Start Your Servers
```bash
# Terminal 1: Start main server
python server_with_cors.py

# Terminal 2: Start CORS proxy (optional)
python cors_proxy.py
```

## Test Execution Order

### Phase 1: Basic Connectivity (Tests 1-2, 11-12)
| Test | Purpose | Expected Result |
|------|---------|-----------------|
| **1. Root Interface** | Test HTML interface | Returns HTML page |
| **2. Health Check** | Verify server status | `{"status": "healthy"}` |
| **11. CORS Proxy Health** | Test proxy status | `{"status": "healthy"}` |
| **12. CORS Proxy Root** | Test proxy routing | Proxied response |

### Phase 2: Core Functionality (Tests 3-7)
| Test | Purpose | Expected Result |
|------|---------|-----------------|
| **3. Initialize Session** | Start research session | Session created with ID |
| **4. Execute Step** | Test individual workflow step | Step execution result |
| **5. Hybrid Execution** | Test controlled workflow | Step-by-step results |
| **6. Run All** | Complete workflow test | Full research results |
| **7. Direct Invoke** | Direct graph execution | Graph output |

### Phase 3: Session Management (Tests 8-9)
| Test | Purpose | Expected Result |
|------|---------|-----------------|
| **8. Reset Session** | Clear current session | Session reset confirmation |
| **9. Export Data** | Export session results | JSON data export |

### Phase 4: Error Handling (Test 10)
| Test | Purpose | Expected Result |
|------|---------|-----------------|
| **10. Error Test** | Test invalid input handling | Error response with details |

## Real Test Data Examples

### Music Research Topics
- **David Bowie**: Musical evolution and influence
- **The Beatles**: Impact on music production
- **Queen**: Freddie Mercury's vocal technique
- **Pink Floyd**: Concept albums and progressive rock

### Schema Examples
```json
{
  "type": "object",
  "properties": {
    "musical_phases": {
      "type": "array",
      "items": {"type": "string"}
    },
    "influential_albums": {
      "type": "array", 
      "items": {"type": "string"}
    },
    "cultural_impact": {
      "type": "string"
    }
  },
  "required": ["musical_phases", "cultural_impact"]
}
```

## Expected Response Patterns

### Successful Research Response
```json
{
  "success": true,
  "info": {
    "musical_phases": ["Glam Rock", "Berlin Trilogy", "Pop Era"],
    "influential_albums": ["The Rise and Fall of Ziggy Stardust", "Low"],
    "cultural_impact": "Revolutionary influence on gender expression and music"
  },
  "loop_step": 3,
  "messages": [...]
}
```

### Error Response
```json
{
  "success": false,
  "error": "Invalid extraction schema: missing required fields",
  "details": {...}
}
```

## Testing Tips

### 1. Environment Variables
Ensure these are set in your `.env` file:
```
OPENAI_API_KEY=your_openai_key
TAVILY_API_KEY=your_tavily_key
```

### 2. Timeout Settings
- **Development**: 30 seconds
- **Production**: 60 seconds
- **Long workflows**: May take 2-3 minutes

### 3. Response Validation
- Check HTTP status codes (200, 400, 500)
- Verify JSON response structure
- Monitor response times
- Check for CORS headers when using proxy

### 4. Debugging
- Enable debug logging in server
- Check server console for errors
- Monitor LangSmith traces
- Use browser dev tools for CORS issues

## Advanced Testing

### 1. Load Testing
- Run multiple concurrent requests
- Test rate limiting behavior
- Monitor memory usage

### 2. Edge Cases
- Very long topics (>1000 characters)
- Complex nested schemas
- Empty or malformed requests
- Network timeouts

### 3. Integration Testing
- Test MCP server integration
- Verify external API calls
- Check caching behavior

## Troubleshooting

### Common Issues
| Issue | Solution |
|-------|----------|
| **Connection refused** | Check if servers are running on correct ports |
| **CORS errors** | Use CORS proxy or check server CORS settings |
| **Timeout errors** | Increase timeout or check API key validity |
| **Invalid schema** | Verify JSON schema format and required fields |
| **Empty responses** | Check API keys and external service availability |

### Server Status Check
```bash
# Check if servers are running
curl http://127.0.0.1:2025/health
curl http://127.0.0.1:8080/health
```

This test collection provides comprehensive coverage of all API endpoints with real-world test data and scenarios.
