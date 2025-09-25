# MCP to API Translation Layer Documentation

## Overview
The MCP server (`llm_txt.mcp.server`) acts as a bridge between LLM clients (Claude Desktop, Cursor, Codex) and the FastAPI backend. This document describes the mapping between MCP tools and API endpoints.

## Architecture Flow
```
LLM Client (Claude/Cursor/Codex)
    ↓ (MCP Protocol over stdio)
MCP Server (llm-txt-mcp)
    ↓ (HTTP REST API)
FastAPI Backend (https://hdinqg7vmm.us-east-1.awsapprunner.com)
```

## MCP Tools to API Endpoint Mapping

### 1. `generate_llms_txt` Tool
**Purpose**: Start a generation job and poll until completion

**MCP Input Parameters**:
- `url` (string, required): URL to crawl
- `full` (boolean, default: false): Generate llms-full.txt too
- `max_pages` (integer, default: 100): Max pages to crawl
- `max_depth` (integer, default: 5): Max crawl depth
- `max_kb` (integer, default: 500): Max size in KB (informational)
- `respect_robots` (boolean, default: true): Respect robots.txt
- `language` (string, default: "en"): Preferred language
- `wait_seconds` (number, optional): Timeout for polling

**API Calls Sequence**:
1. **POST /v1/generations** - Create job
   ```json
   {
     "url": "...",
     "max_pages": 100,
     "max_depth": 5,
     "full_version": false,
     "respect_robots": true,
     "language": "en"
   }
   ```
   Response: `{"job_id": "...", "status": "pending", "message": "..."}`

2. **GET /v1/generations/{job_id}** - Poll status (repeat until complete/failed/timeout)
   Response includes: status, progress, pages_crawled, etc.

3. **GET /v1/generations/{job_id}/download/llm.txt** - Download result (if completed)
   Response: `{"content": "..."}`

4. **GET /v1/generations/{job_id}/download/llms-full.txt** - Download full version (if requested and completed)
   Response: `{"content": "..."}`

**MCP Output**:
```json
{
  "job_id": "uuid",
  "status": "completed|failed|running",
  "message": "...",
  "progress": 0.75,
  "pages_crawled": 50,
  "total_size_kb": 450.5,
  "llm_txt": "content...",
  "llms_full_txt": "content..." // if requested
}
```

### 2. `get_generation_status` Tool
**Purpose**: Check job status without waiting

**MCP Input**:
- `job_id` (string, required): Job identifier

**API Call**:
- **GET /v1/generations/{job_id}**

**MCP Output**: Direct pass-through of API response

### 3. `cancel_generation` Tool
**Purpose**: Cancel a running job

**MCP Input**:
- `job_id` (string, required): Job identifier

**API Call**:
- **DELETE /v1/generations/{job_id}**

**MCP Output**:
```json
{
  "message": "Job cancelled successfully"
}
```

## Error Handling

### API Errors → MCP Errors
- **404 (Job not found)**: Raise RuntimeError with message
- **500 (Server error)**: Raise RuntimeError with details
- **Timeout**: Return with status and timeout message
- **Network errors**: Caught and re-raised as RuntimeError

### Common Issues and Solutions

#### Issue: 404 "Endpoint not found"
**Possible Causes**:
1. Job ID doesn't exist in the job manager
2. Job data not persisting between requests
3. Wrong API base URL

**Solution Checks**:
```bash
# Test API health
curl https://hdinqg7vmm.us-east-1.awsapprunner.com/health

# Create a job
curl -X POST https://hdinqg7vmm.us-east-1.awsapprunner.com/v1/generations \
  -H "Content-Type: application/json" \
  -d '{"url":"https://docs.python.org"}'

# Check job status (use returned job_id)
curl https://hdinqg7vmm.us-east-1.awsapprunner.com/v1/generations/{job_id}
```

## Configuration

### Environment Variables
- `LLM_TXT_API_BASE_URL`: API backend URL (default: http://localhost:8000)
- `LLM_TXT_API_TOKEN`: Bearer token for authentication (optional)
- `LLM_TXT_API_TIMEOUT`: Total wait time in seconds (default: 180)

### MCP Configuration Files
Location varies by IDE:
- **Claude Desktop**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Cursor**: `~/.cursor/mcp.json` or project `.cursor/mcp.json`
- **Codex**: `.codex/mcp.json` in project root

Example configuration:
```json
{
  "mcpServers": {
    "llm-txt": {
      "command": "/path/to/llm-txt-mcp",
      "env": {
        "LLM_TXT_API_BASE_URL": "https://hdinqg7vmm.us-east-1.awsapprunner.com",
        "LLM_TXT_API_TOKEN": "optional-token",
        "LLM_TXT_API_TIMEOUT": "180"
      }
    }
  }
}
```

## Testing the Translation Layer

### Direct MCP Server Test
```bash
# Test initialization
echo '{"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"jsonrpc":"2.0","id":0}' | llm-txt-mcp

# Test tool listing
echo '{"method":"tools/list","params":{},"jsonrpc":"2.0","id":1}' | llm-txt-mcp
```

### Python Test Script
```python
import asyncio
from llm_txt.mcp.server import _tool_generate_llms_txt

async def test():
    result = await _tool_generate_llms_txt(
        url="https://docs.python.org",
        max_pages=5,
        wait_seconds=60
    )
    print(result)

asyncio.run(test())
```

## Debugging Tips

1. **Check API is running**: `curl {base_url}/health`
2. **Verify job creation**: Check if POST returns a job_id
3. **Monitor job status**: Poll the status endpoint manually
4. **Check server logs**: Look for error messages in API logs
5. **Test MCP server directly**: Use echo commands to test stdio communication
6. **Verify environment variables**: Ensure MCP server has correct API URL

## Known Limitations

1. **Polling**: MCP server polls for job completion, not real-time updates
2. **Timeout**: Default 180 seconds may be too short for large sites
3. **Error details**: Some API errors may lose detail in translation
4. **Authentication**: Token-based auth not fully implemented yet
5. **Job persistence**: Jobs may be lost if API server restarts