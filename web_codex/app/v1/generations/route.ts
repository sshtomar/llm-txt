import { proxyToUpstream } from '@/lib/upstream'
import { consume, getClientIp } from '@/lib/rate-limit'

export async function POST(req: Request) {
  // Simple per-IP rate limit: 1 job/30s, burst 2
  const ip = getClientIp(req)
  const rl = consume(ip, 1)
  if (!rl.ok) {
    return new Response(JSON.stringify({ error: 'Rate limit exceeded' }), {
      status: 429,
      headers: { 'Content-Type': 'application/json', 'Retry-After': String(rl.retryAfter || 30) },
    })
  }

  const body = await req.text()
  const res = await proxyToUpstream('POST', '/v1/generations', {
    headers: { 'Content-Type': 'application/json' },
    body,
  })
  const text = await res.text()
  return new Response(text, { status: res.status, headers: { 'Content-Type': res.headers.get('Content-Type') || 'application/json' } })
}
