import { NextResponse } from 'next/server'
import { verifyDodoWebhook, extractEmailFromWebhook, generateUpgradeToken, type DodoWebhookEvent } from '@/lib/dodo'
import { recordPayment, createEntitlement, type Payment, type Entitlement } from '@/lib/db'

/**
 * Dodo Payments webhook endpoint
 *
 * Dodo will POST to this endpoint when payments succeed/fail
 * We verify the signature, store the payment, and create entitlements
 */
export async function POST(req: Request) {
  try {
    const signature = req.headers.get('x-dodo-signature')
    const webhookSecret = process.env.DODO_WEBHOOK_SECRET

    if (!webhookSecret) {
      console.error('DODO_WEBHOOK_SECRET not configured')
      return NextResponse.json(
        { error: 'Webhook not configured' },
        { status: 500 }
      )
    }

    // Read raw body for signature verification
    const rawBody = await req.text()

    // Verify webhook signature
    const isValid = verifyDodoWebhook(rawBody, signature, webhookSecret)
    if (!isValid) {
      console.error('Invalid webhook signature')
      return NextResponse.json(
        { error: 'Invalid signature' },
        { status: 401 }
      )
    }

    // Parse event
    const event: DodoWebhookEvent = JSON.parse(rawBody)
    console.log('Received Dodo webhook:', event.type, event.data.payment_id)

    // Extract email from event
    const email = extractEmailFromWebhook(event)
    if (!email) {
      console.error('No email found in webhook event')
      return NextResponse.json(
        { error: 'Email required in webhook' },
        { status: 400 }
      )
    }

    // Handle different event types
    switch (event.type) {
      case 'payment.succeeded':
        await handlePaymentSucceeded(event, email)
        break

      case 'payment.failed':
        await handlePaymentFailed(event, email)
        break

      case 'subscription.cancelled':
        await handleSubscriptionCancelled(event, email)
        break

      default:
        console.log('Unhandled webhook event type:', event.type)
    }

    // Acknowledge webhook
    return NextResponse.json({ received: true })

  } catch (error) {
    console.error('Webhook processing error:', error)
    return NextResponse.json(
      { error: 'Webhook processing failed' },
      { status: 500 }
    )
  }
}

/**
 * Handle successful payment
 */
async function handlePaymentSucceeded(event: DodoWebhookEvent, email: string) {
  const { payment_id, amount, currency, product_id, created_at, metadata } = event.data

  // Record payment
  const payment: Payment = {
    payment_id,
    email,
    amount,
    currency,
    provider: 'dodo',
    status: 'succeeded',
    product_id,
    created_at,
    webhook_received_at: new Date().toISOString(),
    metadata,
  }

  await recordPayment(payment)
  console.log('Payment recorded:', payment_id, email)

  // Determine plan from product_id
  const plan = determinePlanFromProduct(product_id)

  // Create entitlement
  const entitlement: Entitlement = {
    email,
    plan,
    payment_id,
    payment_provider: 'dodo',
    created_at: new Date().toISOString(),
    status: 'active',
    metadata: {
      product_id,
      amount,
      currency,
    },
  }

  await createEntitlement(entitlement)
  console.log('Entitlement created:', email, plan)

  // Generate one-time token for redirect
  const entitlementSecret = process.env.ENTITLEMENT_SECRET
  if (entitlementSecret) {
    const token = generateUpgradeToken(email, payment_id, entitlementSecret)
    const redirectUrl = `${process.env.NEXT_PUBLIC_SITE_URL || ''}/upgrade/success?token=${token}`
    console.log('Upgrade redirect URL generated for:', email)
    // Note: Dodo may support returning redirect_url in webhook response
    // Check Dodo docs for webhook response format
  }
}

/**
 * Handle failed payment
 */
async function handlePaymentFailed(event: DodoWebhookEvent, email: string) {
  const { payment_id, amount, currency, product_id, created_at, metadata } = event.data

  const payment: Payment = {
    payment_id,
    email,
    amount,
    currency,
    provider: 'dodo',
    status: 'failed',
    product_id,
    created_at,
    webhook_received_at: new Date().toISOString(),
    metadata,
  }

  await recordPayment(payment)
  console.log('Failed payment recorded:', payment_id, email)
}

/**
 * Handle subscription cancellation
 */
async function handleSubscriptionCancelled(event: DodoWebhookEvent, email: string) {
  const { updateEntitlementStatus } = await import('@/lib/db')
  await updateEntitlementStatus(email, 'cancelled')
  console.log('Entitlement cancelled for:', email)
}

/**
 * Determine plan tier from Dodo product ID
 */
function determinePlanFromProduct(productId: string): 'free' | 'professional' | 'enterprise' {
  // Map Dodo product IDs to plan tiers
  // Update these based on your actual Dodo product configuration
  const productMap: Record<string, 'free' | 'professional' | 'enterprise'> = {
    'pdt_sao6YQaUrrED1YHn2BVbF': 'professional', // From .env.example
    // Add more product IDs as needed
  }

  return productMap[productId] || 'professional' // Default to professional
}
