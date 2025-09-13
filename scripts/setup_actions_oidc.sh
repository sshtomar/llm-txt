#!/usr/bin/env bash
set -euo pipefail

# This script creates an IAM role for GitHub Actions OIDC and sets
# GitHub repository secrets/variables via the GitHub CLI (gh).
#
# Requirements:
# - aws CLI configured for account
# - gh CLI authenticated: `gh auth login`
#
# Usage (example):
#   GITHUB_REPO=sshtomar/llm-txt \
#   APP_RUNNER_SERVICE_ARN=arn:aws:apprunner:us-east-1:796973517930:service/llm-txt-api/XXXX \
#   AWS_ACCOUNT_ID=796973517930 AWS_REGION=us-east-1 \
#   ./scripts/setup_actions_oidc.sh

GITHUB_REPO=${GITHUB_REPO:?Set GITHUB_REPO like owner/repo}
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID:?Set AWS_ACCOUNT_ID}
AWS_REGION=${AWS_REGION:-us-east-1}
ROLE_NAME=${ROLE_NAME:-GitHubActionsOIDC}
ECR_REPO=${ECR_REPO:-llm-txt-api}
APP_RUNNER_SERVICE_ARN=${APP_RUNNER_SERVICE_ARN:?Set APP_RUNNER_SERVICE_ARN}

OIDC_PROVIDER_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com"

echo "==> Ensuring IAM OIDC provider exists"
if ! aws iam get-open-id-connect-provider --open-id-connect-provider-arn "$OIDC_PROVIDER_ARN" >/dev/null 2>&1; then
  echo "Creating OIDC provider in account ${AWS_ACCOUNT_ID}"
  aws iam create-open-id-connect-provider \
    --url https://token.actions.githubusercontent.com \
    --client-id-list sts.amazonaws.com \
    --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1 1b511abead59c6ce207077c0bf0e0043f0ca4c2d >/dev/null
else
  echo "OIDC provider already present"
fi

echo "==> Creating/Updating IAM role for GitHub OIDC: ${ROLE_NAME}"
cat > trust-policy.json <<JSON
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"Federated": "${OIDC_PROVIDER_ARN}"},
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {"token.actions.githubusercontent.com:aud": "sts.amazonaws.com"},
        "StringLike": {"token.actions.githubusercontent.com:sub": "repo:${GITHUB_REPO}:*"}
      }
    }
  ]
}
JSON

if aws iam get-role --role-name "$ROLE_NAME" >/dev/null 2>&1; then
  aws iam update-assume-role-policy --role-name "$ROLE_NAME" --policy-document file://trust-policy.json >/dev/null
else
  aws iam create-role --role-name "$ROLE_NAME" --assume-role-policy-document file://trust-policy.json >/dev/null
fi

# Attach minimal permissions for ECR push + App Runner update
cat > permissions-policy.json <<JSON
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:PutImage",
        "ecr:DescribeRepositories",
        "ecr:CreateRepository",
        "ecr:GetDownloadUrlForLayer"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": ["apprunner:DescribeService", "apprunner:UpdateService"],
      "Resource": "${APP_RUNNER_SERVICE_ARN}"
    }
  ]
}
JSON

aws iam put-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-name GitHubActionsEcrApprunner \
  --policy-document file://permissions-policy.json >/dev/null

ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/${ROLE_NAME}"
echo "==> Using role: $ROLE_ARN"

echo "==> Setting GitHub Actions secrets and variables via gh CLI"
gh secret set AWS_ROLE_TO_ASSUME -R "$GITHUB_REPO" -b "$ROLE_ARN"
gh secret set APP_RUNNER_SERVICE_ARN -R "$GITHUB_REPO" -b "$APP_RUNNER_SERVICE_ARN"
gh variable set AWS_REGION -R "$GITHUB_REPO" -b "$AWS_REGION"
gh variable set ECR_REPO -R "$GITHUB_REPO" -b "$ECR_REPO"

echo "==> Done. Push to main or trigger the workflow manually to deploy."

