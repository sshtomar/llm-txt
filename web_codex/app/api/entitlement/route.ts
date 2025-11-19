import { NextResponse } from 'next/server'
import { hasProAccess } from '@/lib/db'

export async function GET(req: Request) {
  const cookie = req.headers.get('cookie') || ''

  // Extract llmxt_pro cookie value
  const match = cookie.match(/(?:^|;\s*)llmxt_pro=([^;]+)/)
  if (!match) {
    return NextResponse.json({ plan: 'free' }, {
      headers: { 'Cache-Control': 'no-store' }
    })
  }

  const cookieValue = match[1]

  // Handle dev mode (cookie value = 'dev' or '1')
  if (cookieValue === 'dev' || cookieValue === '1') {
    return NextResponse.json({ plan: 'pro' }, {
      headers: { 'Cache-Control': 'no-store' }
    })
  }

  // Decode email from cookie
  let email: string
  try {
    email = Buffer.from(cookieValue, 'base64url').toString('utf-8')
  } catch (error) {
    console.error('Invalid cookie format')
    return NextResponse.json({ plan: 'free' }, {
      headers: { 'Cache-Control': 'no-store' }
    })
  }

  // Validate email format
  if (!email || !email.includes('@')) {
    return NextResponse.json({ plan: 'free' }, {
      headers: { 'Cache-Control': 'no-store' }
    })
  }

  // Check database for active entitlement
  try {
    const hasPro = await hasProAccess(email)
    return NextResponse.json({ plan: hasPro ? 'pro' : 'free' }, {
      headers: { 'Cache-Control': 'no-store' }
    })
  } catch (error) {
    console.error('Database error checking entitlement:', error)
    // Fail open: allow access if database is down (prevents breaking paying customers)
    // Log this for monitoring
    return NextResponse.json({ plan: 'pro', warning: 'database_unavailable' }, {
      headers: { 'Cache-Control': 'no-store' }
    })
  }
}
