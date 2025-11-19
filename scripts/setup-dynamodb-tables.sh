#!/bin/bash
set -e

# Setup DynamoDB tables for LLMxt entitlements and payments
# Usage: ./scripts/setup-dynamodb-tables.sh [region]

REGION=${1:-us-east-1}
ENTITLEMENTS_TABLE=${ENTITLEMENTS_TABLE:-llmxt-entitlements}
PAYMENTS_TABLE=${PAYMENTS_TABLE:-llmxt-payments}

echo "Setting up DynamoDB tables in region: $REGION"
echo "Entitlements table: $ENTITLEMENTS_TABLE"
echo "Payments table: $PAYMENTS_TABLE"
echo ""

# Create Entitlements Table
echo "Creating $ENTITLEMENTS_TABLE table..."
aws dynamodb create-table \
  --table-name "$ENTITLEMENTS_TABLE" \
  --attribute-definitions \
    AttributeName=email,AttributeType=S \
  --key-schema \
    AttributeName=email,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region "$REGION" \
  --tags \
    Key=Application,Value=llmxt \
    Key=Component,Value=entitlements \
  || echo "Table $ENTITLEMENTS_TABLE may already exist"

echo ""

# Create Payments Table
echo "Creating $PAYMENTS_TABLE table..."
aws dynamodb create-table \
  --table-name "$PAYMENTS_TABLE" \
  --attribute-definitions \
    AttributeName=payment_id,AttributeType=S \
    AttributeName=email,AttributeType=S \
    AttributeName=created_at,AttributeType=S \
  --key-schema \
    AttributeName=payment_id,KeyType=HASH \
  --global-secondary-indexes \
    "IndexName=email-index,KeySchema=[{AttributeName=email,KeyType=HASH},{AttributeName=created_at,KeyType=RANGE}],Projection={ProjectionType=ALL}" \
  --billing-mode PAY_PER_REQUEST \
  --region "$REGION" \
  --tags \
    Key=Application,Value=llmxt \
    Key=Component,Value=payments \
  || echo "Table $PAYMENTS_TABLE may already exist"

echo ""
echo "Waiting for tables to become active..."
aws dynamodb wait table-exists --table-name "$ENTITLEMENTS_TABLE" --region "$REGION"
aws dynamodb wait table-exists --table-name "$PAYMENTS_TABLE" --region "$REGION"

echo ""
echo "✅ DynamoDB tables created successfully!"
echo ""
echo "Table details:"
aws dynamodb describe-table --table-name "$ENTITLEMENTS_TABLE" --region "$REGION" --query 'Table.[TableName,TableStatus,ItemCount]' --output table
aws dynamodb describe-table --table-name "$PAYMENTS_TABLE" --region "$REGION" --query 'Table.[TableName,TableStatus,ItemCount]' --output table

echo ""
echo "Next steps:"
echo "1. Update your .env file with these table names"
echo "2. Ensure AWS credentials are configured (IAM role or credentials)"
echo "3. Configure Dodo webhook URL: https://your-domain.com/api/webhooks/dodo"
