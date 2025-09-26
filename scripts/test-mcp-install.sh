#!/bin/bash
# Test script for MCP server installation

set -e

echo "Testing llms-txt MCP Server Installation"
echo "========================================="

# Test Python installation
echo ""
echo "1. Testing Python package installation..."
if command -v llms-txt-mcp &> /dev/null; then
    echo "✓ llms-txt-mcp command is available"
else
    echo "✗ llms-txt-mcp command not found"
    echo "  Try: pip install -e ."
fi

# Test Python module
echo ""
echo "2. Testing Python module import..."
python3 -c "import llm_txt.mcp.server" 2>/dev/null && echo "✓ Python module imports successfully" || echo "✗ Python module import failed"

# Test npm package
echo ""
echo "3. Testing NPM package..."
cd mcp-package
if [ -f "package.json" ]; then
    echo "✓ package.json exists"

    # Check if executable exists
    if [ -f "bin/llms-txt-mcp.js" ]; then
        echo "✓ Executable bin/llms-txt-mcp.js exists"

        # Make it executable
        chmod +x bin/llms-txt-mcp.js

        # Test running it
        echo ""
        echo "4. Testing MCP server startup (will run for 3 seconds)..."
        timeout 3 node bin/llms-txt-mcp.js 2>&1 | head -5 || true
    else
        echo "✗ Executable bin/llms-txt-mcp.js not found"
    fi
else
    echo "✗ package.json not found"
fi

echo ""
echo "========================================="
echo "Installation test complete!"