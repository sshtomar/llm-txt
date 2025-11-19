# Payment System Setup Guide

This guide covers the complete setup of the secure payment system using Dodo Payments and DynamoDB for entitlements.

## Architecture Overview

```
User → Frontend → Dodo Checkout → Payment
                                     ↓
                              Webhook → Store in DynamoDB
                                     ↓
                              One-time token → Success redirect
                                     ↓
                              Cookie + Database check → Pro access
```

## Prerequisites

1. AWS Account with DynamoDB access
2. Dodo Payments account
3. Node.js and npm installed
4. AWS CLI configured

## Step 1: DynamoDB Setup

### Create Tables

Run the setup script:

```bash
./scripts/setup-dynamodb-tables.sh us-east-1
```

Or manually create tables:

**Entitlements Table:**
- Table name: `llmxt-entitlements`
- Partition key: `email` (String)
- Billing mode: Pay per request

**Payments Table:**
- Table name: `llmxt-payments`
- Partition key: `payment_id` (String)
- GSI: `email-index` (email as partition key, created_at as sort key)
- Billing mode: Pay per request

### IAM Permissions

Your application needs these DynamoDB permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem",
        "dynamodb:Query"
      ],
      "Resource": [
        "arn:aws:dynamodb:REGION:ACCOUNT:table/llmxt-entitlements",
        "arn:aws:dynamodb:REGION:ACCOUNT:table/llmxt-payments",
        "arn:aws:dynamodb:REGION:ACCOUNT:table/llmxt-payments/index/email-index"
      ]
    }
  ]
}
```

## Step 2: Environment Variables

Copy and configure `.env.example`:

```bash
cp .env.example .env
```

### Required Variables

```bash
# Dodo Payments
NEXT_PUBLIC_CHECKOUT_URL=https://checkout.dodopayments.com/buy/YOUR_PRODUCT_ID?quantity=1&redirect_url=https%3A%2F%2Fyour-domain.com%2Fupgrade%2Fsuccess
DODO_WEBHOOK_SECRET=your-webhook-secret-from-dodo-dashboard

# Entitlement
ENTITLEMENT_SECRET=$(openssl rand -hex 32)
ENTITLEMENT_ALLOW_UNVERIFIED=false  # true for dev, false for production

# Site
NEXT_PUBLIC_SITE_URL=https://your-domain.com

# DynamoDB
AWS_REGION=us-east-1
ENTITLEMENTS_TABLE=llmxt-entitlements
PAYMENTS_TABLE=llmxt-payments

# API Security
HMAC_SECRET=$(openssl rand -hex 32)
REQUIRE_HMAC_SIGNATURE=true
```

## Step 3: Dodo Payments Configuration

### 1. Create Product

In your Dodo dashboard:
1. Go to Products
2. Create a new product (e.g., "Pro Plan")
3. Note the product ID (e.g., `pdt_xxx`)

### 2. Configure Webhook

1. Go to Webhooks in Dodo dashboard
2. Add endpoint: `https://your-domain.com/api/webhooks/dodo`
3. Subscribe to events: `payment.succeeded`, `payment.failed`, `subscription.cancelled`
4. Copy the webhook secret
5. Add secret to `.env` as `DODO_WEBHOOK_SECRET`

### 3. Update Product Mapping

Edit `web_codex/app/api/webhooks/dodo/route.ts`:

```typescript
function determinePlanFromProduct(productId: string): 'free' | 'professional' | 'enterprise' {
  const productMap: Record<string, 'free' | 'professional' | 'enterprise'> = {
    'pdt_YOUR_PRODUCT_ID': 'professional',
    // Add more product IDs as needed
  }
  return productMap[productId] || 'professional'
}
```

## Step 4: Install Dependencies

```bash
cd web_codex
npm install
```

This will install:
- `@aws-sdk/client-dynamodb`
- `@aws-sdk/lib-dynamodb`

## Step 5: Deploy

### Frontend (Vercel/Amplify)

1. Set all environment variables in your hosting platform
2. Deploy the `web_codex` directory
3. Ensure the `/api/webhooks/dodo` route is publicly accessible

### Backend API (if separate)

1. Set `HMAC_SECRET` to match frontend
2. Set `REQUIRE_HMAC_SIGNATURE=true`
3. Deploy your API

## Step 6: Test the Flow

### Local Testing (Without Payment)

1. Set in `.env.local`:
   ```bash
   ENTITLEMENT_ALLOW_UNVERIFIED=true
   ```

2. Start dev server:
   ```bash
   npm run dev
   ```

3. Visit http://localhost:3000/upgrade/success
4. You should get Pro access

### Production Testing (With Real Payment)

1. Make a test purchase using Dodo test mode
2. Check webhook received:
   ```bash
   # Check CloudWatch logs or application logs
   ```

3. Verify database records:
   ```bash
   aws dynamodb get-item \
     --table-name llmxt-entitlements \
     --key '{"email":{"S":"test@example.com"}}'
   ```

4. Test entitlement check:
   ```bash
   curl https://your-domain.com/api/entitlement \
     -H "Cookie: llmxt_pro=BASE64_EMAIL"
   ```

## Security Checklist

- [ ] `ENTITLEMENT_ALLOW_UNVERIFIED=false` in production
- [ ] `DODO_WEBHOOK_SECRET` configured
- [ ] `ENTITLEMENT_SECRET` is cryptographically random (32+ bytes)
- [ ] `HMAC_SECRET` is cryptographically random and shared with backend
- [ ] DynamoDB tables have proper IAM permissions
- [ ] Webhook endpoint is HTTPS only
- [ ] No secrets in client-side code
- [ ] CloudWatch/logging configured for webhook events

## Monitoring

### Key Metrics to Track

1. **Webhook Success Rate**
   - Monitor `/api/webhooks/dodo` response codes
   - Alert on 401 (bad signature) or 500 errors

2. **Database Operations**
   - Monitor DynamoDB throttling
   - Track read/write capacity

3. **Payment Events**
   ```bash
   # Query recent payments
   aws dynamodb scan \
     --table-name llmxt-payments \
     --filter-expression "created_at > :yesterday"
   ```

4. **Entitlement Checks**
   - Monitor `/api/entitlement` response times
   - Alert if database becomes unavailable

## Troubleshooting

### "Payment succeeded but no Pro access"

1. Check webhook logs:
   ```bash
   # Vercel/Amplify logs
   # Look for "Received Dodo webhook" messages
   ```

2. Verify signature:
   - Check `DODO_WEBHOOK_SECRET` matches Dodo dashboard

3. Check database:
   ```bash
   aws dynamodb get-item \
     --table-name llmxt-entitlements \
     --key '{"email":{"S":"USER_EMAIL"}}'
   ```

4. Check email in webhook:
   - Ensure customer_email is passed to Dodo
   - Verify `metadata[email]` is set in checkout URL

### "Token expired" on success redirect

- Tokens expire after 10 minutes
- User must complete redirect within that window
- Check system clocks are synchronized

### "Database unavailable" warning

- System fails open (grants Pro access) to protect paying customers
- Check AWS credentials and IAM permissions
- Verify DynamoDB tables exist and are active

## Rollback Plan

If you need to revert to the old system:

1. Set `ENTITLEMENT_ALLOW_UNVERIFIED=true`
2. Manually set cookies for affected users
3. Fix issues and redeploy
4. Set `ENTITLEMENT_ALLOW_UNVERIFIED=false` again

## Support

For issues with:
- **Dodo Payments**: Contact Dodo support
- **AWS/DynamoDB**: Check AWS Support or documentation
- **Application**: Check application logs and this guide

## Appendix: Database Schema

### Entitlements Table

```typescript
{
  email: string (PK)
  plan: 'free' | 'professional' | 'enterprise'
  payment_id: string
  payment_provider: 'dodo' | 'stripe'
  created_at: string (ISO 8601)
  expires_at?: string (ISO 8601, optional)
  status: 'active' | 'cancelled' | 'expired'
  metadata?: object
}
```

### Payments Table

```typescript
{
  payment_id: string (PK)
  email: string (GSI partition key)
  amount: number
  currency: string
  provider: 'dodo' | 'stripe'
  status: 'succeeded' | 'failed' | 'pending'
  product_id: string
  created_at: string (GSI sort key)
  webhook_received_at: string
  metadata?: object
}
```
