# Publishing Guide for llms-txt MCP Server

## Prerequisites

### 1. NPM Account Setup
```bash
# Create account at https://www.npmjs.com/signup
# Then login locally:
npm login

# Verify login:
npm whoami
```

### 2. PyPI Account Setup
```bash
# Create account at https://pypi.org/account/register/
# Create API token at https://pypi.org/manage/account/token/

# Save token to ~/.pypirc:
cat > ~/.pypirc << 'EOF'
[pypi]
username = __token__
password = pypi-YOUR-TOKEN-HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR-TEST-TOKEN-HERE
EOF

chmod 600 ~/.pypirc
```

## Manual Publishing

### Step 1: Test on Test PyPI (Optional but Recommended)
```bash
# Build package (already done)
python -m build

# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Test installation from Test PyPI
pip install --index-url https://test.pypi.org/simple/ --no-deps llms-txt
```

### Step 2: Publish to PyPI
```bash
# Upload to PyPI
twine upload dist/*

# Verify at: https://pypi.org/project/llms-txt/
```

### Step 3: Publish to NPM
```bash
cd mcp-package

# Publish
npm publish --access public

# Verify at: https://www.npmjs.com/package/@llms-txt/mcp
```

### Step 4: Create GitHub Release
```bash
# Tag the release
git tag -a v0.1.0 -m "Release v0.1.0: Initial MCP server release"
git push origin v0.1.0

# Create release on GitHub
gh release create v0.1.0 \
  --title "v0.1.0 - Initial MCP Server Release" \
  --notes "$(cat <<'EOF'
# llms-txt MCP Server v0.1.0

First release of the llms-txt MCP server!

## Installation

### Via NPM (Recommended)
\`\`\`bash
npx @llms-txt/mcp@latest
\`\`\`

### Via PyPI
\`\`\`bash
pip install llms-txt
llms-txt-mcp
\`\`\`

## Features
- ✅ Generate llms.txt files from documentation sites
- ✅ Works with Claude Desktop, VS Code, Cursor
- ✅ Configurable API endpoints and timeouts
- ✅ S3-backed job persistence
- ✅ Respects robots.txt and rate limits

## Configuration

Add to Claude Desktop config:
\`\`\`json
{
  "mcpServers": {
    "llms-txt": {
      "command": "npx",
      "args": ["@llms-txt/mcp@latest"]
    }
  }
}
\`\`\`

## Links
- [NPM Package](https://www.npmjs.com/package/@llms-txt/mcp)
- [PyPI Package](https://pypi.org/project/llms-txt/)
- [Documentation](https://github.com/sshtomar/llm-txt/blob/main/MCP_README.md)
EOF
)"
```

## Automated Publishing via GitHub Actions

### Setup GitHub Secrets

Go to: https://github.com/sshtomar/llm-txt/settings/secrets/actions

Add these secrets:
1. `NPM_TOKEN` - Get from https://www.npmjs.com/settings/USERNAME/tokens
2. `PYPI_API_TOKEN` - Get from https://pypi.org/manage/account/token/
3. `TEST_PYPI_API_TOKEN` - Get from https://test.pypi.org/manage/account/token/ (optional)

### Trigger Publishing Workflow

#### Option 1: Manual Trigger
```bash
gh workflow run publish.yml \
  --repo sshtomar/llm-txt \
  -f version=0.1.0 \
  -f publish_npm=true \
  -f publish_pypi=true
```

#### Option 2: Create Release (Auto-triggers)
```bash
# Creating a release on GitHub will automatically publish to both NPM and PyPI
gh release create v0.1.0 \
  --title "v0.1.0" \
  --notes-file RELEASE_NOTES.md
```

## Testing Installation

### Test NPM Package
```bash
# Using npx
npx @llms-txt/mcp@latest --help

# Or install globally
npm install -g @llms-txt/mcp
llms-txt-mcp --help
```

### Test PyPI Package
```bash
# Create fresh environment
python3 -m venv test-env
source test-env/bin/activate

# Install and test
pip install llms-txt
llms-txt-mcp --help
```

### Test with Claude Desktop

1. Update config at `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "llms-txt": {
      "command": "npx",
      "args": ["@llms-txt/mcp@0.1.0"],
      "env": {
        "LLM_TXT_API_BASE_URL": "https://hdinqg7vmm.us-east-1.awsapprunner.com"
      }
    }
  }
}
```

2. Restart Claude Desktop

3. Test by asking: "Generate a llms.txt for https://react.dev"

## Version Updates

To release a new version:

1. Update version in both files:
   - `pyproject.toml`: `version = "0.2.0"`
   - `mcp-package/package.json`: `"version": "0.2.0"`

2. Commit and push changes

3. Follow publishing steps above with new version number

## Troubleshooting

### NPM Publishing Issues
- **Authentication error**: Run `npm login` again
- **Permission denied**: Make sure you have access to `@llms-txt` scope
- **Package exists**: Increment version number

### PyPI Publishing Issues
- **Authentication error**: Check `~/.pypirc` file
- **Package exists**: Increment version number
- **Invalid token**: Generate new token on PyPI

### GitHub Actions Issues
- **Missing secrets**: Add secrets in repository settings
- **Workflow not found**: Make sure `.github/workflows/publish.yml` is committed
- **Permission denied**: Check repository permissions

## Current Build Status

✅ Python package built: `dist/llms_txt-0.1.0-py3-none-any.whl`
✅ Python package built: `dist/llms_txt-0.1.0.tar.gz`
✅ Package validation passed: `twine check dist/*`
✅ NPM dry-run passed

**Ready to publish!**