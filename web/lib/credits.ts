export interface UserCredits {
  remaining: number
  total: number
  isPro: boolean
  lastReset?: number
}

const CREDITS_KEY = 'llm-txt-credits'
const DEFAULT_CREDITS = 3

export function getCredits(): UserCredits {
  if (typeof window === 'undefined') {
    return { remaining: DEFAULT_CREDITS, total: DEFAULT_CREDITS, isPro: false }
  }

  try {
    const stored = localStorage.getItem(CREDITS_KEY)
    if (!stored) {
      const defaultCredits = {
        remaining: DEFAULT_CREDITS,
        total: DEFAULT_CREDITS,
        isPro: false,
      }
      localStorage.setItem(CREDITS_KEY, JSON.stringify(defaultCredits))
      return defaultCredits
    }

    const credits: UserCredits = JSON.parse(stored)

    // Ensure credits have valid structure
    if (
      typeof credits.remaining !== 'number' ||
      typeof credits.total !== 'number'
    ) {
      return resetCredits()
    }

    return credits
  } catch (error) {
    console.error('Failed to get credits:', error)
    return resetCredits()
  }
}

export function useCredit(): boolean {
  const credits = getCredits()

  if (credits.isPro) {
    return true // Pro users have unlimited credits
  }

  if (credits.remaining <= 0) {
    return false // No credits remaining
  }

  const updatedCredits = {
    ...credits,
    remaining: credits.remaining - 1,
  }

  localStorage.setItem(CREDITS_KEY, JSON.stringify(updatedCredits))
  return true
}

export function resetCredits(): UserCredits {
  const defaultCredits = {
    remaining: DEFAULT_CREDITS,
    total: DEFAULT_CREDITS,
    isPro: false,
  }

  if (typeof window !== 'undefined') {
    localStorage.setItem(CREDITS_KEY, JSON.stringify(defaultCredits))
  }

  return defaultCredits
}

export function upgradeToPro(): void {
  const credits = getCredits()
  const proCredits = {
    ...credits,
    isPro: true,
    remaining: Infinity,
  }

  localStorage.setItem(CREDITS_KEY, JSON.stringify(proCredits))
}

export function hasCreditsRemaining(): boolean {
  const credits = getCredits()
  return credits.isPro || credits.remaining > 0
}
