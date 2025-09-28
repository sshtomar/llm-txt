# LLM-TXT Generator

A tool that crawls documentation websites and generates LLM-friendly summaries in `llm.txt` format.

## Features

- 🕷️ **Smart Crawling**: Discovers URLs via sitemaps and crawls politely
- 🤖 **AI-Powered**: Uses Cohere for intelligent summarization
- 📏 **Size Management**: Keeps outputs within configurable size limits
- 🚫 **Respectful**: Honors robots.txt and implements crawl delays
- 🔄 **API & CLI**: Both REST API and command-line interfaces
- ⚡ **Fast**: Async processing with concurrent job handling

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/sshtomar/llm-txt.git
cd llm-txt

# Install dependencies
make install

# Copy environment file and add your Cohere API key
cp .env.example .env
# Edit .env and add your COHERE_API_KEY
```

### CLI Usage

```bash
# Generate llm.txt for a documentation site
llm-txt generate --url https://docs.example.com

# Generate both regular and full versions
llm-txt generate --url https://docs.example.com --full

# Customize crawl parameters
llm-txt generate \
  --url https://docs.example.com \
  --max-pages 50 \
  --max-depth 2 \
  --max-kb 300 \
  --output my-docs.txt
```

### API Usage

```bash
# Start the API server
make dev

# Create a generation job
curl -X POST "http://localhost:8000/v1/generations" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://docs.example.com",
    "max_pages": 100,
    "max_depth": 3,
    "full_version": false
  }'

# Check job status
curl "http://localhost:8000/v1/generations/{job_id}"

# Download results
curl "http://localhost:8000/v1/generations/{job_id}/download/llm.txt"
```

## Configuration

Set these environment variables in `.env`:

```bash
# Required
COHERE_API_KEY=your_api_key_here

# Optional (with defaults)
MAX_PAGES=100
MAX_DEPTH=3
MAX_KB=500
REQUEST_DELAY=1.0
USER_AGENT=llm-txt-generator/0.1.0
```

## Development

```bash
# Install development dependencies
make install

# Run tests
make test

# Type checking
make typecheck

# Format code
make fmt

# Start development server
make dev
```

### Optional: Payments + Lightweight Pro Unlock

Add a simple upgrade flow without accounts:

1. Set the checkout URL env (Amplify or web_codex/.env.local):
   - `NEXT_PUBLIC_CHECKOUT_URL=https://checkout.dodopayments.com/buy/pdt_sao6YQaUrrED1YHn2BVbF?quantity=1&redirect_url=https%3A%2F%2Fdocsforllm.dev%2Fupgrade%2Fsuccess`
2. Configure server-side cookie settings:
   - `ENTITLEMENT_ALLOW_UNVERIFIED=false` (recommended)
   - `ENTITLEMENT_SECRET=<random secret>`
   - The redirect URL should append `?t=<ENTITLEMENT_SECRET>` if unverified is false.
3. On success, Next.js route `/upgrade/success` sets a `llmxt_pro=1` HttpOnly cookie for 30 days and redirects to `/?payment=success`.
4. The UI checks `/api/entitlement` and removes free-tier limits and upgrade prompts for Pro users.

If you prefer the simplest path for demos: set `ENTITLEMENT_ALLOW_UNVERIFIED=true` and omit the `t` token.

### Optional: Enable Google/GitHub Auth in the Frontend

The Next.js frontend (web_codex) supports sign-in with Google and GitHub via NextAuth.

1. Create OAuth apps:
   - GitHub: callback URL `http://localhost:3000/api/auth/callback/github`
   - Google: authorized redirect URI `http://localhost:3000/api/auth/callback/google`
2. Create `web_codex/.env.local` (or set envs) with:
   - `NEXTAUTH_URL=http://localhost:3000`
   - `NEXTAUTH_SECRET=<random 32+ char string>`
   - `GITHUB_ID`, `GITHUB_SECRET`
   - `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
3. Start frontend: `cd web_codex && npm install && npm run dev`
4. Use the Sign in button in the header. The Generate action requires authentication.

## Architecture

```
/api          # FastAPI REST API endpoints
/worker       # Background job processing
/crawler      # Web crawling and content extraction
/composer     # LLM-powered content generation
/cli          # Command-line interface
```

## License

MIT License - see LICENSE file for details.

## MCP Server (IDE Integration)

Expose llm.txt generation to MCP-capable IDEs/tools (Cursor, Claude Code, Codex) via a thin MCP server that calls this repo’s FastAPI API.

- Install: `make install` (adds the `llm-txt-mcp` console script)
- Env vars (optional):
  - `LLM_TXT_API_BASE_URL` (default: `http://localhost:8000`)
  - `LLM_TXT_API_TOKEN` (optional Bearer token)
  - `LLM_TXT_API_TIMEOUT` (default: `180` seconds)

### Configure MCP clients

- Cursor: Settings → MCP Servers → add a server with command `llm-txt-mcp` and set env vars.
- Claude Desktop (`mcp.json` example):

```
{
  "mcpServers": {
    "llm-txt": {
      "command": "llm-txt-mcp",
      "env": {
        "LLM_TXT_API_BASE_URL": "http://localhost:8000"
      }
    }
  }
}
```

Sample config files you can copy:
- `configs/mcp/claude.mcp.json`
- `configs/mcp/cursor.mcp.json`
- `configs/mcp/codex.mcp.json`

### Codex CLI

- Project-level config file added: `.codex/mcp.json`
  - Uses absolute command to your venv: `/Users/explorer/llm-txt/venv/bin/llm-txt-mcp`
  - Edit if your path differs.
- Start backend: `source venv/bin/activate && make dev`
- In Codex, the MCP server `llm-txt` should appear with tool `generate_llms_txt`.
  - Example request (from Codex prompt):
    - “Use tool llm-txt.generate_llms_txt with url=https://docs.example.com, full=true, max_pages=50.”

### Tools exposed

- `generate_llms_txt(url, full?, max_pages?, max_depth?, max_kb?, respect_robots?, language?, wait_seconds?)`
  - Starts a job (`POST /v1/generations`), polls status, downloads results, and returns content and metadata.
- `get_generation_status(job_id)`
- `cancel_generation(job_id)`

Backend remains unchanged; this MCP server is just a translation layer.
