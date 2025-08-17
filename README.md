# LLM-TXT Generator

A tool that crawls documentation websites and generates LLM-friendly summaries in `llm.txt` format.

## Features

- 🕷️ **Smart Crawling**: Discovers URLs via sitemaps and crawls politely
- 🤖 **AI-Powered**: Uses Anthropic Claude for intelligent summarization
- 📏 **Size Management**: Keeps outputs within configurable size limits
- 🚫 **Respectful**: Honors robots.txt and implements crawl delays
- 🔄 **API & CLI**: Both REST API and command-line interfaces
- ⚡ **Fast**: Async processing with concurrent job handling

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd llm-txt

# Install dependencies
make install

# Copy environment file and add your Anthropic API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
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
ANTHROPIC_API_KEY=your_api_key_here

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