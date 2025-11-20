import { NextResponse } from 'next/server'
import { validateSession } from '@/lib/sessions'

export async function GET(req: Request) {
  const cookie = req.headers.get('cookie') || ''

  // Extract llmxt_session cookie value
  const match = cookie.match(/(?:^|;\s*)llmxt_session=([^;]+)/)
  if (!match) {
    return NextResponse.json({ plan: 'free' }, {
      headers: { 'Cache-Control': 'no-store' }
    })
  }

  const sessionId = match[1]

  // Handle dev mode
  if (sessionId === 'dev') {
    return NextResponse.json({ plan: 'pro' }, {
      headers: { 'Cache-Control': 'no-store' }
    })
  }

  // Validate session
  try {
    const session = await validateSession(sessionId)

    if (!session) {
      // Session invalid, expired, or revoked
      return NextResponse.json({ plan: 'free' }, {
        headers: { 'Cache-Control': 'no-store' }
      })
    }

    // Return plan from session
    return NextResponse.json({ plan: session.plan === 'free' ? 'free' : 'pro' }, {
      headers: { 'Cache-Control': 'no-store' }
    })
  } catch (error) {
    console.error('Database error validating session:', error)
    // Fail open: allow access if database is down (prevents breaking paying customers)
    // Log this for monitoring
    return NextResponse.json({ plan: 'pro', warning: 'database_unavailable' }, {
      headers: { 'Cache-Control': 'no-store' }
    })
  }
}
