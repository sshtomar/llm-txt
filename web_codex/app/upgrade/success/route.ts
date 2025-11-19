import { NextResponse } from 'next/server'
import { verifyUpgradeToken } from '@/lib/dodo'
import { hasProAccess } from '@/lib/db'

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
    res.cookies.set('llmxt_pro', 'dev', {
      httpOnly: true,
      sameSite: 'lax',
      secure: process.env.NODE_ENV === 'production',
      maxAge,
      path: '/',
    })
    return res
  }

  // Production mode: verify token and check database
  if (!secret) {
    console.error('ENTITLEMENT_SECRET not configured')
    return NextResponse.redirect(new URL('/?payment=cancel', req.url))
  }

  if (!token) {
    console.error('No token provided')
    return NextResponse.redirect(new URL('/?payment=cancel', req.url))
  }

  // Verify one-time token
  const email = verifyUpgradeToken(token, secret)
  if (!email) {
    console.error('Invalid or expired token')
    return NextResponse.redirect(new URL('/?payment=cancel', req.url))
  }

  // Verify user has active Pro access in database
  try {
    const hasPro = await hasProAccess(email)
    if (!hasPro) {
      console.error('No active Pro entitlement for:', email)
      return NextResponse.redirect(new URL('/?payment=cancel', req.url))
    }

    // Set authenticated cookie with email
    const res = NextResponse.redirect(new URL('/?payment=success', req.url))
    const maxAge = 60 * 60 * 24 * 30 // 30 days

    // Encode email in cookie for entitlement checks
    const cookieValue = Buffer.from(email).toString('base64url')
    res.cookies.set('llmxt_pro', cookieValue, {
      httpOnly: true,
      sameSite: 'lax',
      secure: process.env.NODE_ENV === 'production',
      maxAge,
      path: '/',
    })

    console.log('Pro cookie set for:', email)
    return res

  } catch (error) {
    console.error('Database error during entitlement check:', error)
    return NextResponse.redirect(new URL('/?payment=cancel', req.url))
  }
}

