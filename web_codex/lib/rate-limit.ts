type Bucket = { tokens: number; lastRefill: number }

// Simple in-memory token bucket per IP. Not durable, but fine for a single node.
const buckets = new Map<string, Bucket>()

// 1 token every 30s, capacity 2
const REFILL_INTERVAL_MS = 30_000
const CAPACITY = 2

export function consume(ip: string, cost = 1): { ok: boolean; retryAfter?: number } {
  const now = Date.now()
  const b = buckets.get(ip) || { tokens: CAPACITY, lastRefill: now }

  // Refill tokens based on elapsed time
  const elapsed = now - b.lastRefill
  if (elapsed > 0) {
    const refill = Math.floor(elapsed / REFILL_INTERVAL_MS)
    if (refill > 0) {
      b.tokens = Math.min(CAPACITY, b.tokens + refill)
      b.lastRefill = b.lastRefill + refill * REFILL_INTERVAL_MS
    }
  }

  if (b.tokens >= cost) {
    b.tokens -= cost
    buckets.set(ip, b)
    return { ok: true }
  }

  // Compute retry-after based on next refill time
  const nextAt = b.lastRefill + REFILL_INTERVAL_MS
  const retryAfter = Math.max(0, Math.ceil((nextAt - now) / 1000))
  buckets.set(ip, b)
  return { ok: false, retryAfter }
}

export function getClientIp(req: Request): string {
  const fwd = req.headers.get('x-forwarded-for') || ''
  const first = fwd.split(',').map(s => s.trim()).filter(Boolean)[0]
  return first || req.headers.get('x-real-ip') || req.headers.get('cf-connecting-ip') || 'unknown'
}

