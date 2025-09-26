# llms-txt MCP Server

Generate concise, LLM-friendly text summaries (llms.txt) from any documentation site using MCP (Model Context Protocol).

## What is MCP?

MCP (Model Context Protocol) is a standardized protocol that allows LLMs to interact with external tools and services. This MCP server bridges LLM clients (like Claude Desktop, VS Code, Cursor) with the llms-txt API to generate documentation summaries.

## Installation

### Option 1: Using NPX (Recommended)

The easiest way to use the llms-txt MCP server:

```bash
npx @llms-txt/mcp@latest
```

### Option 2: Install via NPM

```bash
npm install -g @llms-txt/mcp
```

### Option 3: Install via Python/PyPI

```bash
pip install llms-txt
```

Then run the server:

```bash
llms-txt-mcp
```

### Option 4: Install from Source

```bash
git clone https://github.com/sshtomar/llm-txt.git
cd llm-txt
pip install -e .
llms-txt-mcp
```

## Configuration

### Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "llms-txt": {
      "command": "npx",
      "args": ["@llms-txt/mcp@latest"],
      "env": {
        "LLM_TXT_API_BASE_URL": "https://hdinqg7vmm.us-east-1.awsapprunner.com"
      }
    }
  }
}
```

Or with custom API endpoint:

```json
{
  "mcpServers": {
    "llms-txt": {
      "command": "npx",
      "args": [
        "@llms-txt/mcp@latest",
        "--api-url", "http://localhost:8000"
      ]
    }
  }
}
```

### VS Code with Continue

Add to your Continue configuration (`~/.continue/config.json`):

```json
{
  "experimental": {
    "modelContextProtocolServers": [
      {
        "name": "llms-txt",
        "command": "npx",
        "args": ["@llms-txt/mcp@latest"],
        "env": {
          "LLM_TXT_API_BASE_URL": "https://hdinqg7vmm.us-east-1.awsapprunner.com"
        }
      }
    ]
  }
}
```

### Cursor

Add to your Cursor settings:

```json
{
  "mcpServers": {
    "llms-txt": {
      "command": "npx",
      "args": ["@llms-txt/mcp@latest"],
      "env": {
        "LLM_TXT_API_BASE_URL": "https://hdinqg7vmm.us-east-1.awsapprunner.com"
      }
    }
  }
}
```

## Usage

Once configured, the MCP server provides a tool called `generate_llms_txt` that you can use in your LLM conversations:

### In Claude Desktop

```
Please generate a llms.txt summary for the React documentation at https://react.dev
```

Claude will automatically use the MCP tool to:
1. Start a generation job with the llms-txt API
2. Poll for completion
3. Return the generated llms.txt content

### Available Parameters

- `url` (required): The documentation site URL to process
- `max_depth` (optional, default: 2): How many levels deep to crawl
- `include_full_llm_txt` (optional, default: false): Whether to generate the full version

## Configuration Options

### Environment Variables

- `LLM_TXT_API_BASE_URL`: Base URL for the llms-txt API (default: https://hdinqg7vmm.us-east-1.awsapprunner.com)
- `LLM_TXT_API_TOKEN`: Optional bearer token for API authentication
- `LLM_TXT_API_TIMEOUT`: Maximum seconds to wait for job completion (default: 180)

### Command Line Arguments

When running directly:

```bash
llms-txt-mcp --api-url http://localhost:8000 --timeout 300
```

Or with npx:

```bash
npx @llms-txt/mcp@latest --api-url http://localhost:8000 --api-token your-token
```

## Features

- 🚀 **Fast Generation**: Optimized crawling and summarization pipeline
- 🎯 **LLM-Optimized**: Output specifically formatted for LLM consumption
- 🔒 **Respectful Crawling**: Honors robots.txt and rate limits
- 📊 **Size Management**: Automatic content budgeting to stay within token limits
- 🌐 **JavaScript Support**: Falls back to Playwright for JS-heavy sites
- 🔄 **Async Processing**: Non-blocking job queue with status polling

## Examples

### Generate llm.txt for Python docs

```
Generate an llms.txt for https://docs.python.org/3/
```

### Generate with custom depth

```
Generate an llms.txt for https://vuejs.org with max_depth=3
```

### Generate full version

```
Generate both llms.txt and llms-full.txt for https://docs.djangoproject.com
```

## API Endpoints

The MCP server communicates with these API endpoints:

- `POST /v1/generations`: Start a new generation job
- `GET /v1/generations/{job_id}`: Check job status
- `GET /v1/generations/{job_id}/result`: Get generation results

## Development

### Running Locally

1. Clone the repository:

```bash
git clone https://github.com/sshtomar/llm-txt.git
cd llm-txt
```

2. Install dependencies:

```bash
pip install -e ".[dev]"
```

3. Run the MCP server:

```bash
python -m llm_txt.mcp.server
```

### Running with Local API

1. Start the API server:

```bash
make dev
```

2. Run MCP server pointing to local API:

```bash
LLM_TXT_API_BASE_URL=http://localhost:8000 llms-txt-mcp
```

## Docker Support

Run the MCP server in a container:

```bash
docker run -it --rm \
  -e LLM_TXT_API_BASE_URL=https://hdinqg7vmm.us-east-1.awsapprunner.com \
  ghcr.io/sshtomar/llms-txt-mcp:latest
```

## Troubleshooting

### MCP server not connecting

1. Check that the server is running:
```bash
llms-txt-mcp --version
```

2. Verify API connectivity:
```bash
curl https://hdinqg7vmm.us-east-1.awsapprunner.com/health
```

3. Check logs in Claude Desktop:
   - View logs at: `~/Library/Logs/Claude/`

### Jobs timing out

Increase the timeout:

```json
{
  "env": {
    "LLM_TXT_API_TIMEOUT": "300"
  }
}
```

### Authentication errors

Add your API token:

```json
{
  "env": {
    "LLM_TXT_API_TOKEN": "your-api-token"
  }
}
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- [GitHub Repository](https://github.com/sshtomar/llm-txt)
- [PyPI Package](https://pypi.org/project/llms-txt/)
- [NPM Package](https://www.npmjs.com/package/@llms-txt/mcp)
- [API Documentation](https://hdinqg7vmm.us-east-1.awsapprunner.com/docs)
- [MCP Specification](https://modelcontextprotocol.io)

## Support

- **Issues**: [GitHub Issues](https://github.com/sshtomar/llm-txt/issues)
- **Discussions**: [GitHub Discussions](https://github.com/sshtomar/llm-txt/discussions)
- **Email**: support@llm-txt.dev