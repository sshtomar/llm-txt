import { DynamoDBClient } from '@aws-sdk/client-dynamodb'
import { DynamoDBDocumentClient, PutCommand, GetCommand, UpdateCommand, QueryCommand } from '@aws-sdk/lib-dynamodb'

/**
 * DynamoDB client for entitlement and payment tracking
 */

const client = new DynamoDBClient({
  region: process.env.AWS_REGION || 'us-east-1',
})

const docClient = DynamoDBDocumentClient.from(client)

const ENTITLEMENTS_TABLE = process.env.ENTITLEMENTS_TABLE || 'llmxt-entitlements'
const PAYMENTS_TABLE = process.env.PAYMENTS_TABLE || 'llmxt-payments'

export interface Entitlement {
  email: string
  plan: 'free' | 'professional' | 'enterprise'
  payment_id: string
  payment_provider: 'dodo' | 'stripe'
  created_at: string
  expires_at?: string
  status: 'active' | 'cancelled' | 'expired'
  metadata?: Record<string, any>
}

export interface Payment {
  payment_id: string
  email: string
  amount: number
  currency: string
  provider: 'dodo' | 'stripe'
  status: 'succeeded' | 'failed' | 'pending'
  product_id: string
  created_at: string
  webhook_received_at: string
  metadata?: Record<string, any>
}

/**
 * Store a payment record from webhook
 */
export async function recordPayment(payment: Payment): Promise<void> {
  await docClient.send(
    new PutCommand({
      TableName: PAYMENTS_TABLE,
      Item: payment,
    })
  )
}

/**
 * Create or update entitlement for a user
 */
export async function createEntitlement(entitlement: Entitlement): Promise<void> {
  await docClient.send(
    new PutCommand({
      TableName: ENTITLEMENTS_TABLE,
      Item: entitlement,
    })
  )
}

/**
 * Get user's current entitlement
 */
export async function getEntitlement(email: string): Promise<Entitlement | null> {
  const result = await docClient.send(
    new GetCommand({
      TableName: ENTITLEMENTS_TABLE,
      Key: { email },
    })
  )

  return result.Item as Entitlement | null
}

/**
 * Check if user has active Pro entitlement
 */
export async function hasProAccess(email: string): Promise<boolean> {
  const entitlement = await getEntitlement(email)

  if (!entitlement) return false
  if (entitlement.status !== 'active') return false
  if (entitlement.plan === 'free') return false

  // Check expiry if present
  if (entitlement.expires_at) {
    const expiryDate = new Date(entitlement.expires_at)
    if (expiryDate < new Date()) return false
  }

  return true
}

/**
 * Update entitlement status (for cancellations)
 */
export async function updateEntitlementStatus(
  email: string,
  status: 'active' | 'cancelled' | 'expired'
): Promise<void> {
  await docClient.send(
    new UpdateCommand({
      TableName: ENTITLEMENTS_TABLE,
      Key: { email },
      UpdateExpression: 'SET #status = :status, updated_at = :now',
      ExpressionAttributeNames: {
        '#status': 'status',
      },
      ExpressionAttributeValues: {
        ':status': status,
        ':now': new Date().toISOString(),
      },
    })
  )
}

/**
 * Get payment by ID
 */
export async function getPayment(paymentId: string): Promise<Payment | null> {
  const result = await docClient.send(
    new GetCommand({
      TableName: PAYMENTS_TABLE,
      Key: { payment_id: paymentId },
    })
  )

  return result.Item as Payment | null
}

/**
 * Get all payments for a user (for admin/support)
 */
export async function getUserPayments(email: string): Promise<Payment[]> {
  const result = await docClient.send(
    new QueryCommand({
      TableName: PAYMENTS_TABLE,
      IndexName: 'email-index',
      KeyConditionExpression: 'email = :email',
      ExpressionAttributeValues: {
        ':email': email,
      },
      ScanIndexForward: false, // Most recent first
    })
  )

  return (result.Items || []) as Payment[]
}
