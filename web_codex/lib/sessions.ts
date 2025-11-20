import crypto from 'crypto'
import { DynamoDBClient } from '@aws-sdk/client-dynamodb'
import { DynamoDBDocumentClient, PutCommand, GetCommand, QueryCommand, UpdateCommand, DeleteCommand } from '@aws-sdk/lib-dynamodb'

/**
 * Session management for secure, non-shareable Pro access
 *
 * Each session is tied to a device/browser and cannot be shared.
 * Sessions expire after 30 days of inactivity.
 */

const client = new DynamoDBClient({
  region: process.env.AWS_REGION || 'us-east-1',
})

const docClient = DynamoDBDocumentClient.from(client)

const SESSIONS_TABLE = process.env.SESSIONS_TABLE || 'llmxt-sessions'
const SESSION_MAX_AGE_DAYS = 30
const MAX_SESSIONS_PER_EMAIL = 3 // Limit devices per account

export interface Session {
  session_id: string // Primary key
  email: string // GSI partition key
  plan: 'free' | 'professional' | 'enterprise'
  payment_id: string
  created_at: string
  last_accessed_at: string
  expires_at: string
  device_info?: {
    user_agent?: string
    ip?: string
    device_name?: string
  }
  status: 'active' | 'revoked' | 'expired'
}

/**
 * Generate a secure session ID
 */
export function generateSessionId(): string {
  return crypto.randomBytes(32).toString('hex')
}

/**
 * Create a new session after payment
 */
export async function createSession(
  email: string,
  plan: 'professional' | 'enterprise',
  paymentId: string,
  deviceInfo?: Session['device_info']
): Promise<string> {
  const sessionId = generateSessionId()
  const now = new Date()
  const expiresAt = new Date(now.getTime() + SESSION_MAX_AGE_DAYS * 24 * 60 * 60 * 1000)

  const session: Session = {
    session_id: sessionId,
    email,
    plan,
    payment_id: paymentId,
    created_at: now.toISOString(),
    last_accessed_at: now.toISOString(),
    expires_at: expiresAt.toISOString(),
    device_info: deviceInfo,
    status: 'active',
  }

  // Check if user has too many active sessions
  const existingSessions = await getUserSessions(email)
  const activeSessions = existingSessions.filter(s => s.status === 'active')

  if (activeSessions.length >= MAX_SESSIONS_PER_EMAIL) {
    // Revoke oldest session
    const oldest = activeSessions.sort((a, b) =>
      new Date(a.last_accessed_at).getTime() - new Date(b.last_accessed_at).getTime()
    )[0]

    await revokeSession(oldest.session_id)
  }

  await docClient.send(
    new PutCommand({
      TableName: SESSIONS_TABLE,
      Item: session,
    })
  )

  return sessionId
}

/**
 * Validate a session and update last accessed time
 */
export async function validateSession(sessionId: string): Promise<Session | null> {
  const result = await docClient.send(
    new GetCommand({
      TableName: SESSIONS_TABLE,
      Key: { session_id: sessionId },
    })
  )

  const session = result.Item as Session | undefined
  if (!session) return null

  // Check if expired
  const now = new Date()
  const expiresAt = new Date(session.expires_at)

  if (now > expiresAt) {
    // Mark as expired
    await docClient.send(
      new UpdateCommand({
        TableName: SESSIONS_TABLE,
        Key: { session_id: sessionId },
        UpdateExpression: 'SET #status = :expired',
        ExpressionAttributeNames: { '#status': 'status' },
        ExpressionAttributeValues: { ':expired': 'expired' },
      })
    )
    return null
  }

  // Check if revoked
  if (session.status !== 'active') {
    return null
  }

  // Update last accessed time and extend expiry
  const newExpiresAt = new Date(now.getTime() + SESSION_MAX_AGE_DAYS * 24 * 60 * 60 * 1000)

  await docClient.send(
    new UpdateCommand({
      TableName: SESSIONS_TABLE,
      Key: { session_id: sessionId },
      UpdateExpression: 'SET last_accessed_at = :now, expires_at = :expires',
      ExpressionAttributeValues: {
        ':now': now.toISOString(),
        ':expires': newExpiresAt.toISOString(),
      },
    })
  )

  // Return updated session
  return {
    ...session,
    last_accessed_at: now.toISOString(),
    expires_at: newExpiresAt.toISOString(),
  }
}

/**
 * Get all sessions for a user
 */
export async function getUserSessions(email: string): Promise<Session[]> {
  const result = await docClient.send(
    new QueryCommand({
      TableName: SESSIONS_TABLE,
      IndexName: 'email-index',
      KeyConditionExpression: 'email = :email',
      ExpressionAttributeValues: { ':email': email },
    })
  )

  return (result.Items || []) as Session[]
}

/**
 * Revoke a session
 */
export async function revokeSession(sessionId: string): Promise<void> {
  await docClient.send(
    new UpdateCommand({
      TableName: SESSIONS_TABLE,
      Key: { session_id: sessionId },
      UpdateExpression: 'SET #status = :revoked',
      ExpressionAttributeNames: { '#status': 'status' },
      ExpressionAttributeValues: { ':revoked': 'revoked' },
    })
  )
}

/**
 * Delete a session completely
 */
export async function deleteSession(sessionId: string): Promise<void> {
  await docClient.send(
    new DeleteCommand({
      TableName: SESSIONS_TABLE,
      Key: { session_id: sessionId },
    })
  )
}

/**
 * Extract device info from request
 */
export function getDeviceInfo(req: Request): Session['device_info'] {
  const userAgent = req.headers.get('user-agent') || undefined
  const ip = getClientIp(req)

  return {
    user_agent: userAgent,
    ip,
    device_name: parseDeviceName(userAgent),
  }
}

/**
 * Get client IP from request
 */
function getClientIp(req: Request): string | undefined {
  const fwd = req.headers.get('x-forwarded-for')
  if (fwd) {
    return fwd.split(',')[0].trim()
  }
  return req.headers.get('x-real-ip') || req.headers.get('cf-connecting-ip') || undefined
}

/**
 * Parse a friendly device name from user agent
 */
function parseDeviceName(userAgent?: string): string | undefined {
  if (!userAgent) return undefined

  // Simple device detection
  if (userAgent.includes('iPhone')) return 'iPhone'
  if (userAgent.includes('iPad')) return 'iPad'
  if (userAgent.includes('Android')) return 'Android'
  if (userAgent.includes('Macintosh')) return 'Mac'
  if (userAgent.includes('Windows')) return 'Windows PC'
  if (userAgent.includes('Linux')) return 'Linux'

  return 'Unknown Device'
}
