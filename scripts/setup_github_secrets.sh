#!/bin/bash

# Script to help set up GitHub secrets for deployment
# Run this locally, not in CI/CD

echo "🔐 GitHub Secrets Setup Helper"
echo "=============================="
echo ""

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed"
    echo "Install it with: brew install gh"
    echo "Or visit: https://cli.github.com/"
    exit 1
fi

# Check if logged in to GitHub
if ! gh auth status &> /dev/null; then
    echo "❌ Not logged in to GitHub CLI"
    echo "Run: gh auth login"
    exit 1
fi

echo "✅ GitHub CLI is ready"
echo ""

# Function to set a secret
set_secret() {
    local secret_name=$1
    local secret_value=$2

    if [ -z "$secret_value" ]; then
        echo "⏭️  Skipping $secret_name (no value provided)"
    else
        echo "$secret_value" | gh secret set "$secret_name" --repo sshtomar/llm-txt
        echo "✅ Set $secret_name"
    fi
}

# Check current AWS credentials
echo "📋 Checking current AWS configuration..."
if [ -n "$AWS_ACCESS_KEY_ID" ]; then
    echo "Found AWS_ACCESS_KEY_ID in environment"
    ACCESS_KEY=$AWS_ACCESS_KEY_ID
else
    # Try to get from AWS CLI config
    ACCESS_KEY=$(aws configure get aws_access_key_id 2>/dev/null)
fi

if [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "Found AWS_SECRET_ACCESS_KEY in environment"
    SECRET_KEY=$AWS_SECRET_ACCESS_KEY
else
    SECRET_KEY=$(aws configure get aws_secret_access_key 2>/dev/null)
fi

echo ""
echo "🔧 Setting up GitHub Secrets..."
echo "--------------------------------"

# AWS Credentials
if [ -n "$ACCESS_KEY" ] && [ -n "$SECRET_KEY" ]; then
    echo "Using AWS credentials from your environment/config"
    read -p "Add AWS credentials to GitHub? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        set_secret "AWS_ACCESS_KEY_ID" "$ACCESS_KEY"
        set_secret "AWS_SECRET_ACCESS_KEY" "$SECRET_KEY"
    fi
else
    echo "⚠️  No AWS credentials found in environment"
    echo "You'll need to add them manually at:"
    echo "https://github.com/sshtomar/llm-txt/settings/secrets/actions"
fi

# Amplify App ID
echo ""
AMPLIFY_APP_ID="d18z0bfb4y2t29"
echo "Setting Amplify App ID: $AMPLIFY_APP_ID"
set_secret "AMPLIFY_APP_ID" "$AMPLIFY_APP_ID"

# Optional: Cohere API Key
echo ""
if [ -n "$COHERE_API_KEY" ]; then
    read -p "Found COHERE_API_KEY in environment. Add to GitHub? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        set_secret "COHERE_API_KEY" "$COHERE_API_KEY"
    fi
fi

echo ""
echo "✨ Setup complete!"
echo ""
echo "📝 Verify secrets at:"
echo "   https://github.com/sshtomar/llm-txt/settings/secrets/actions"
echo ""
echo "🚀 You can test deployment with:"
echo "   gh workflow run check-setup.yml"
echo "   gh workflow run deploy.yml"