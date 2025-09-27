import { proxyToUpstream } from '@/lib/upstream'

export async function GET(_req: Request, { params }: { params: { id: string } }) {
  const res = await proxyToUpstream('GET', `/v1/generations/${params.id}`)
  const text = await res.text()
  const cache = res.headers.get('Cache-Control') || 'no-store, no-cache, must-revalidate, max-age=0'
  return new Response(text, {
    status: res.status,
    headers: {
      'Content-Type': res.headers.get('Content-Type') || 'application/json',
      'Cache-Control': cache,
      'Pragma': 'no-cache',
      'Expires': '0',
    },
  })
}

export async function DELETE(_req: Request, { params }: { params: { id: string } }) {
  const res = await proxyToUpstream('DELETE', `/v1/generations/${params.id}`)
  const text = await res.text()
  return new Response(text, {
    status: res.status,
    headers: {
      'Content-Type': res.headers.get('Content-Type') || 'application/json',
      'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0',
      'Pragma': 'no-cache',
      'Expires': '0',
    },
  })
}
