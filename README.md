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

### Payment System (Dodo Payments + DynamoDB)

The application includes a secure payment system that:
- ✅ Verifies webhooks from Dodo Payments with HMAC signatures
- ✅ Stores entitlements persistently in DynamoDB
- ✅ Uses one-time tokens (not static secrets) for upgrade success
- ✅ Checks database for active Pro status (not just cookies)
- ✅ Collects email before checkout to associate payments with users
- ✅ Prevents cookie-based entitlement bypass attacks

**Quick Setup:**

1. **Set up DynamoDB tables:**
   ```bash
   ./scripts/setup-dynamodb-tables.sh us-east-1
   ```

2. **Configure environment variables** (see `.env.example`):
   ```bash
   DODO_WEBHOOK_SECRET=your-webhook-secret
   ENTITLEMENT_SECRET=$(openssl rand -hex 32)
   ENTITLEMENT_ALLOW_UNVERIFIED=false  # true for dev only
   AWS_REGION=us-east-1
   ENTITLEMENTS_TABLE=llmxt-entitlements
   PAYMENTS_TABLE=llmxt-payments
   ```

3. **Configure Dodo webhook:**
   - URL: `https://your-domain.com/api/webhooks/dodo`
   - Events: `payment.succeeded`, `payment.failed`, `subscription.cancelled`

4. **Install dependencies:**
   ```bash
   cd web_codex && npm install
   ```

📘 **Full setup guide:** See [PAYMENT_SETUP.md](./PAYMENT_SETUP.md) for detailed instructions, security checklist, and troubleshooting.

**Dev testing:** Set `ENTITLEMENT_ALLOW_UNVERIFIED=true` in `.env.local` and visit `/upgrade/success` to unlock Pro locally without payment.

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
