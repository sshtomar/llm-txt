import { NextResponse } from 'next/server'
import { verifyUpgradeToken } from '@/lib/dodo'
import { getEntitlement } from '@/lib/db'
import { createSession, getDeviceInfo } from '@/lib/sessions'

export async function GET(req: Request) {
  const url = new URL(req.url)
  const token = url.searchParams.get('token')
  const allowUnverified = process.env.ENTITLEMENT_ALLOW_UNVERIFIED === 'true'
  const secret = process.env.ENTITLEMENT_SECRET

  // Development mode: allow unverified access for testing
  if (allowUnverified) {
    console.log('[DEV MODE] Setting Pro cookie without verification')
    const res = NextResponse.redirect(new URL('/?payment=success', req.url))
    const maxAge = 60 * 60 * 24 * 30 // 30 days
    res.cookies.set('llmxt_session', 'dev', {
      httpOnly: true,
      sameSite: 'lax',
      secure: process.env.NODE_ENV === 'production',
      maxAge,
      path: '/',
    })
    return res
  }

  // Production mode: verify token and create session
  if (!secret) {
    console.error('ENTITLEMENT_SECRET not configured')
    return NextResponse.redirect(new URL('/?payment=cancel', req.url))
  }

  if (!token) {
    console.error('No token provided')
    return NextResponse.redirect(new URL('/?payment=cancel', req.url))
  }

  // Verify one-time token
  const tokenData = verifyUpgradeToken(token, secret)
  if (!tokenData) {
    console.error('Invalid or expired token')
    return NextResponse.redirect(new URL('/?payment=cancel', req.url))
  }

  const { email, paymentId } = tokenData

  // Verify user has active Pro access in database
  try {
    const entitlement = await getEntitlement(email)
    if (!entitlement || entitlement.status !== 'active' || entitlement.plan === 'free') {
      console.error('No active Pro entitlement for:', email)
      return NextResponse.redirect(new URL('/?payment=cancel', req.url))
    }

    // Create session for this device
    const deviceInfo = getDeviceInfo(req)
    const sessionId = await createSession(email, entitlement.plan, paymentId, deviceInfo)

    // Set session cookie
    const res = NextResponse.redirect(new URL('/?payment=success', req.url))
    const maxAge = 60 * 60 * 24 * 30 // 30 days

    res.cookies.set('llmxt_session', sessionId, {
      httpOnly: true,
      sameSite: 'lax',
      secure: process.env.NODE_ENV === 'production',
      maxAge,
      path: '/',
    })

    console.log('Session created for:', email, 'device:', deviceInfo?.device_name || 'unknown')
    return res

  } catch (error) {
    console.error('Database error during session creation:', error)
    return NextResponse.redirect(new URL('/?payment=cancel', req.url))
  }
}

