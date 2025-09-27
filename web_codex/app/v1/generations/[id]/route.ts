import { proxyToUpstream } from '@/lib/upstream'

export async function GET(_req: Request, { params }: { params: { id: string } }) {
  const res = await proxyToUpstream('GET', `/v1/generations/${params.id}`)
  const text = await res.text()
  return new Response(text, { status: res.status, headers: { 'Content-Type': res.headers.get('Content-Type') || 'application/json' } })
}

export async function DELETE(_req: Request, { params }: { params: { id: string } }) {
  const res = await proxyToUpstream('DELETE', `/v1/generations/${params.id}`)
  const text = await res.text()
  return new Response(text, { status: res.status, headers: { 'Content-Type': res.headers.get('Content-Type') || 'application/json' } })
}

