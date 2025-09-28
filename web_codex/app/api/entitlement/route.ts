import { NextResponse } from 'next/server'

export async function GET(req: Request) {
  const cookie = req.headers.get('cookie') || ''
  const pro = /(?:^|;\s*)llmxt_pro=1(?:;|$)/.test(cookie)
  const body = JSON.stringify({ plan: pro ? 'pro' : 'free' })
  return new Response(body, { status: 200, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' } })
}
