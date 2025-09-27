import { proxyToUpstream } from '@/lib/upstream'

export async function GET(_req: Request, { params }: { params: { id: string; file: 'llm.txt' | 'llms-full.txt' } }) {
  const res = await proxyToUpstream('GET', `/v1/generations/${params.id}/download/${params.file}`)
  const text = await res.text()
  // Keep content-type as text/plain for downloads
  return new Response(text, {
    status: res.status,
    headers: {
      'Content-Type': res.headers.get('Content-Type') || 'text/plain; charset=utf-8',
      'Content-Disposition': res.headers.get('Content-Disposition') || `attachment; filename=${params.file}`,
    },
  })
}

