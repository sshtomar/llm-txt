import crypto from 'crypto'

/**
 * Dodo Payments webhook verification and utilities
 */

export interface DodoWebhookEvent {
  type: 'payment.succeeded' | 'payment.failed' | 'subscription.created' | 'subscription.cancelled'
  data: {
    payment_id: string
    customer_email?: string
    customer_name?: string
    amount: number
    currency: string
    product_id: string
    created_at: string
    metadata?: Record<string, string>
  }
}

/**
 * Verify Dodo Payments webhook signature
 * Dodo signs webhooks with HMAC-SHA256
 */
export function verifyDodoWebhook(
  payload: string,
  signature: string | null,
  secret: string
): boolean {
  if (!signature) return false

  try {
    const expectedSignature = crypto
      .createHmac('sha256', secret)
      .update(payload)
      .digest('hex')

    return crypto.timingSafeEqual(
      Buffer.from(signature),
      Buffer.from(expectedSignature)
    )
  } catch (error) {
    console.error('Webhook verification failed:', error)
    return false
  }
}

/**
 * Generate a one-time token for upgrade success redirect
 * Format: base64url(email:expiry:hmac)
 */
export function generateUpgradeToken(email: string, secret: string): string {
  const expiry = Date.now() + 10 * 60 * 1000 // 10 minutes
  const data = `${email}:${expiry}`
  const hmac = crypto
    .createHmac('sha256', secret)
    .update(data)
    .digest('base64url')

  const token = Buffer.from(`${data}:${hmac}`).toString('base64url')
  return token
}

/**
 * Verify and decode an upgrade token
 * Returns email if valid, null if expired/invalid
 */
export function verifyUpgradeToken(token: string, secret: string): string | null {
  try {
    const decoded = Buffer.from(token, 'base64url').toString('utf-8')
    const parts = decoded.split(':')

    if (parts.length !== 3) return null

    const [email, expiryStr, receivedHmac] = parts
    const expiry = parseInt(expiryStr, 10)

    // Check expiry
    if (Date.now() > expiry) {
      console.log('Token expired')
      return null
    }

    // Verify HMAC
    const data = `${email}:${expiryStr}`
    const expectedHmac = crypto
      .createHmac('sha256', secret)
      .update(data)
      .digest('base64url')

    if (!crypto.timingSafeEqual(
      Buffer.from(receivedHmac),
      Buffer.from(expectedHmac)
    )) {
      console.log('Invalid HMAC')
      return null
    }

    return email
  } catch (error) {
    console.error('Token verification failed:', error)
    return null
  }
}

/**
 * Extract email from Dodo webhook event
 */
export function extractEmailFromWebhook(event: DodoWebhookEvent): string | null {
  // Try customer_email first
  if (event.data.customer_email) {
    return event.data.customer_email
  }

  // Try metadata
  if (event.data.metadata?.email) {
    return event.data.metadata.email
  }

  return null
}
