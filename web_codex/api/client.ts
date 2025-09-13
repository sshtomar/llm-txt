import type { DownloadResponse, GenerationRequest, GenerationResponse, JobStatusResponse } from '@/types/api'

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, '') || ''

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(text || `HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

export async function createGeneration(payload: GenerationRequest): Promise<GenerationResponse> {
  const res = await fetch(`${BASE}/v1/generations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return json(res)
}

export async function getJobStatus(jobId: string): Promise<JobStatusResponse> {
  const res = await fetch(`${BASE}/v1/generations/${jobId}`, { cache: 'no-store' })
  return json(res)
}

export async function downloadFile(jobId: string, type: 'llm.txt' | 'llms-full.txt'): Promise<DownloadResponse> {
  const res = await fetch(`${BASE}/v1/generations/${jobId}/download/${type}`, { cache: 'no-store' })
  return json(res)
}

