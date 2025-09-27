import { proxyToUpstream } from '@/lib/upstream'

export async function GET(req: Request, { params }: { params: { id: string; file: 'llm.txt' | 'llms-full.txt' } }) {
  const url = new URL(req.url)
  const search = url.search || ''
  const res = await proxyToUpstream('GET', `/v1/generations/${params.id}/download/${params.file}${search}`)
  const text = await res.text()
  // Keep content-type as text/plain for downloads
  return new Response(text, {
    status: res.status,
    headers: {
      'Content-Type': res.headers.get('Content-Type') || 'text/plain; charset=utf-8',
      'Content-Disposition': res.headers.get('Content-Disposition') || `attachment; filename=${params.file}`,
      'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0',
      'Pragma': 'no-cache',
      'Expires': '0',
    },
  })
}
