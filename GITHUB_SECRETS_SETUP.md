# GitHub Secrets Setup Guide

## Required Secrets for Deployment

Your repository has GitHub Actions workflows that need the following secrets to be configured.

### For Backend Deployment (ECR + App Runner)

Add these secrets at https://github.com/sshtomar/llm-txt/settings/secrets/actions

1. **AWS_ACCESS_KEY_ID**
   - Your AWS access key ID
   - Required for: ECR push, App Runner updates

2. **AWS_SECRET_ACCESS_KEY**
   - Your AWS secret access key
   - Required for: ECR push, App Runner updates

### For Frontend Deployment (Amplify)

3. **AMPLIFY_APP_ID**
   - Value: `d18z0bfb4y2t29`
   - Your Amplify app ID (already exists in your AWS account)

## How to Add Secrets

1. Go to: https://github.com/sshtomar/llm-txt/settings/secrets/actions
2. Click "New repository secret"
3. Add each secret with its name and value
4. Click "Add secret"

## Your Current AWS Resources

Based on your AWS account (796973517930):

### Backend (Already Working)
- **App Runner Service**: llm-txt-api
- **URL**: https://hdinqg7vmm.us-east-1.awsapprunner.com
- **ECR Repository**: 796973517930.dkr.ecr.us-east-1.amazonaws.com/llm-txt-api
- **S3 Bucket**: llm-txt-jobs (for persistence)

### Frontend
- **Amplify App ID**: d18z0bfb4y2t29
- **App Name**: llm-txt

## Testing After Setup

### Test Backend Deployment
```bash
# Make a change to backend code
echo "# test" >> README.md
git add . && git commit -m "Test backend deployment"
git push origin main

# Check GitHub Actions
# https://github.com/sshtomar/llm-txt/actions
```

### Test Frontend Deployment
```bash
# Make a change to frontend code
echo "// test" >> web_codex/app/page.tsx
git add . && git commit -m "Test frontend deployment"
git push origin main

# Check Amplify Console
# https://console.aws.amazon.com/amplify/home
```

## Current Workflow Status

1. **Backend Deployment** (`deploy.yml`)
   - Status: Needs AWS secrets
   - Triggers on: Push to main
   - Deploys to: App Runner via ECR

2. **Frontend Deployment** (`deploy-frontend-amplify.yml`)
   - Status: Disabled (commented out auto-trigger)
   - Can be triggered manually via workflow_dispatch
   - Deploys to: AWS Amplify

## Quick Fix Commands

If you want to disable automatic deployments temporarily:

```bash
# Disable all workflows
mkdir -p .github/workflows-disabled
mv .github/workflows/*.yml .github/workflows-disabled/

# Re-enable workflows
mv .github/workflows-disabled/*.yml .github/workflows/
```

## Security Best Practices

1. **Use GitHub Environments** for production secrets
2. **Rotate keys regularly** (every 90 days)
3. **Use IAM roles** with minimal permissions
4. **Enable branch protection** on main branch
5. **Review workflow permissions** regularly

## Alternative: Use OIDC (Recommended)

Instead of AWS keys, use OpenID Connect:

1. Create an IAM role with trust relationship to GitHub
2. Add role ARN as `AWS_ROLE_TO_ASSUME` secret
3. Remove AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY

This is more secure as it doesn't require storing long-lived credentials.