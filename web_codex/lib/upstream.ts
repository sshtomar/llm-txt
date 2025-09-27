import crypto from 'crypto'

export function assertEnv(name: string): string {
  const v = process.env[name]
  if (!v) throw new Error(`${name} is not set`)
  return v
}

export function signRequest(method: string, path: string, ts: string, nonce: string): string {
  const secret = assertEnv('HMAC_SECRET')
  const msg = `${method}\n${path}\n${ts}\n${nonce}`
  return crypto.createHmac('sha256', secret).update(msg).digest('hex')
}

export async function proxyToUpstream(method: string, path: string, init?: RequestInit) {
  const base = assertEnv('LLM_TXT_UPSTREAM_API_BASE_URL').replace(/\/$/, '')
  const url = `${base}${path}`
  const ts = String(Date.now() / 1000)
  const nonce = crypto.randomBytes(12).toString('hex')
  const sig = signRequest(method, path, ts, nonce)

  const headers = new Headers(init?.headers || {})
  headers.set('x-timestamp', ts)
  headers.set('x-nonce', nonce)
  headers.set('x-signature', sig)

  return fetch(url, { ...init, method, headers })
}

