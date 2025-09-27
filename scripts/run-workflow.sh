#!/bin/bash

echo "🚀 GitHub Workflow Runner"
echo "========================"
echo ""

# Check if gh is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI not installed"
    echo "Install with: brew install gh"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "❌ Not authenticated with GitHub"
    echo "Run: gh auth login"
    exit 1
fi

echo "✅ GitHub CLI ready"
echo ""

# Show available workflows
echo "📋 Available Workflows:"
gh workflow list --repo sshtomar/llm-txt

echo ""
echo "🎯 Quick Commands:"
echo ""
echo "1. Check your setup:"
echo "   gh workflow run check-setup.yml"
echo ""
echo "2. Deploy backend (after adding AWS secrets):"
echo "   gh workflow run deploy.yml"
echo ""
echo "3. Deploy frontend (after adding Amplify secret):"
echo "   gh workflow run deploy-frontend-amplify.yml"
echo ""
echo "4. Watch the latest run:"
echo "   gh run watch"
echo ""
echo "5. View run logs:"
echo "   gh run view --log"

