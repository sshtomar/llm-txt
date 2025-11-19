/**
 * Checkout flow utilities
 * Handles email collection and Dodo redirect URL building
 */

/**
 * Get stored email from localStorage or prompt user
 */
export function getOrPromptEmail(): string | null {
  // Check if email already stored
  const stored = localStorage.getItem('llmxt_email')
  if (stored && validateEmail(stored)) {
    return stored
  }

  // Prompt user for email
  const email = window.prompt(
    'Enter your email to complete checkout.\nYou\'ll receive receipts and access at this address:'
  )

  if (!email) return null

  const trimmed = email.trim()
  if (!validateEmail(trimmed)) {
    alert('Please enter a valid email address')
    return null
  }

  // Store for future use
  localStorage.setItem('llmxt_email', trimmed)
  return trimmed
}

/**
 * Simple email validation
 */
function validateEmail(email: string): boolean {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return re.test(email)
}

/**
 * Build Dodo checkout URL with email and metadata
 */
export function buildCheckoutUrl(email: string, source: string = 'unknown'): string {
  const baseUrl = process.env.NEXT_PUBLIC_CHECKOUT_URL
  if (!baseUrl) {
    console.error('NEXT_PUBLIC_CHECKOUT_URL not configured')
    return '#'
  }

  try {
    const url = new URL(baseUrl)

    // Add email parameter (Dodo will prefill this)
    url.searchParams.set('customer_email', email)

    // Add metadata for tracking
    url.searchParams.set('metadata[source]', source)
    url.searchParams.set('metadata[email]', email)

    return url.toString()
  } catch (error) {
    console.error('Invalid NEXT_PUBLIC_CHECKOUT_URL:', error)
    return '#'
  }
}

/**
 * Handle upgrade click with email collection
 */
export function handleUpgradeClick(source: string): boolean {
  const email = getOrPromptEmail()
  if (!email) return false

  const checkoutUrl = buildCheckoutUrl(email, source)
  if (checkoutUrl === '#') {
    alert('Checkout not configured. Please contact support.')
    return false
  }

  // Track the event
  try {
    window.dispatchEvent(new CustomEvent('upgrade_click', {
      detail: { source, email }
    }))
  } catch {}

  // Open checkout in new tab
  window.open(checkoutUrl, '_blank', 'noopener,noreferrer')
  return true
}
