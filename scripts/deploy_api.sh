#!/usr/bin/env bash
set -euo pipefail

# Deploy the FastAPI service to ECR + App Runner.
# Usage:
#   AWS_ACCOUNT_ID=123456789012 AWS_REGION=us-east-1 \
#   ECR_REPO=llm-txt-api APP_RUNNER_SERVICE_ARN=arn:aws:apprunner:... \
#   ./scripts/deploy_api.sh

ECR_REPO=${ECR_REPO:-llm-txt-api}
AWS_REGION=${AWS_REGION:-us-east-1}

if [[ -z "${AWS_ACCOUNT_ID:-}" ]]; then
  echo "ERROR: Set AWS_ACCOUNT_ID env var" >&2
  exit 1
fi

REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
IMAGE_URI="${REGISTRY}/${ECR_REPO}"

echo "==> Logging in to ECR: ${REGISTRY}"
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$REGISTRY"

echo "==> Building image: ${IMAGE_URI}"
GIT_SHA=$(git rev-parse --short HEAD)
docker build -f Dockerfile.api -t "${IMAGE_URI}:latest" -t "${IMAGE_URI}:${GIT_SHA}" .

echo "==> Pushing image tags"
docker push "${IMAGE_URI}:latest"
docker push "${IMAGE_URI}:${GIT_SHA}"

if [[ -n "${APP_RUNNER_SERVICE_ARN:-}" ]]; then
  echo "==> Updating App Runner service"
  aws apprunner update-service \
    --service-arn "$APP_RUNNER_SERVICE_ARN" \
    --source-configuration "ImageRepository={ImageIdentifier=${IMAGE_URI}:latest,ImageRepositoryType=ECR},AutoDeploymentsEnabled=true"
else
  echo "NOTE: APP_RUNNER_SERVICE_ARN not set; skipped App Runner update."
fi

echo "==> Done"

