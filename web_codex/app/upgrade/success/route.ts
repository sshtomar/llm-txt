import { NextResponse } from 'next/server'

export async function GET(req: Request) {
  const url = new URL(req.url)
  const token = url.searchParams.get('t')
  const allowUnverified = process.env.ENTITLEMENT_ALLOW_UNVERIFIED === 'true'
  const secret = process.env.ENTITLEMENT_SECRET

  if (!allowUnverified && (!secret || token !== secret)) {
    // Do not set cookie without verification
    return NextResponse.redirect(new URL('/?payment=cancel', req.url))
  }

  const res = NextResponse.redirect(new URL('/?payment=success', req.url))
  const maxAge = 60 * 60 * 24 * 30 // 30 days
  res.cookies.set('llmxt_pro', '1', {
    httpOnly: true,
    sameSite: 'lax',
    secure: process.env.NODE_ENV === 'production',
    maxAge,
    path: '/',
  })
  return res
}

