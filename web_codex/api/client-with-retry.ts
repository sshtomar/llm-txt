import type { DownloadResponse, GenerationRequest, GenerationResponse, JobStatusResponse } from '@/types/api'

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, '') || ''
const MAX_RETRIES = 3
const RETRY_DELAY = 1000 // 1 second

async function sleep(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

async function fetchWithRetry(url: string, options?: RequestInit, retries = MAX_RETRIES): Promise<Response> {
  try {
    const res = await fetch(url, options)

    // Retry on 502, 503, 504 (gateway/server errors) or network errors
    if (res.status >= 502 && res.status <= 504 && retries > 0) {
      console.warn(`API error ${res.status}, retrying... (${retries} attempts left)`)
      await sleep(RETRY_DELAY)
      return fetchWithRetry(url, options, retries - 1)
    }

    return res
  } catch (error) {
    // Network error - retry if we have attempts left
    if (retries > 0) {
      console.warn(`Network error, retrying... (${retries} attempts left)`, error)
      await sleep(RETRY_DELAY)
      return fetchWithRetry(url, options, retries - 1)
    }
    throw error
  }
}

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => '')

    // Parse error details if available
    try {
      const errorData = JSON.parse(text)
      throw new Error(errorData.detail || errorData.message || `HTTP ${res.status}`)
    } catch {
      throw new Error(text || `HTTP ${res.status}`)
    }
  }
  return res.json() as Promise<T>
}

export async function createGeneration(payload: GenerationRequest): Promise<GenerationResponse> {
  const res = await fetchWithRetry(`${BASE}/v1/generations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return json(res)
}

export async function getJobStatus(jobId: string): Promise<JobStatusResponse> {
  // Job status checks are critical - use more retries
  const res = await fetchWithRetry(`${BASE}/v1/generations/${jobId}`, { cache: 'no-store' }, 5)
  return json(res)
}

export async function downloadFile(jobId: string, type: 'llm.txt' | 'llms-full.txt'): Promise<DownloadResponse> {
  const res = await fetchWithRetry(`${BASE}/v1/generations/${jobId}/download/${type}`, { cache: 'no-store' })
  return json(res)
}

export async function cancelJob(jobId: string): Promise<{ message: string }> {
  const res = await fetchWithRetry(`${BASE}/v1/generations/${jobId}`, {
    method: 'DELETE',
  })
  return json(res)
}

// Batch status check for multiple jobs
export async function getMultipleJobStatuses(jobIds: string[]): Promise<JobStatusResponse[]> {
  const promises = jobIds.map(id => getJobStatus(id).catch(err => ({
    job_id: id,
    status: 'error' as const,
    message: err.message,
    progress: 0,
    created_at: 0,
  } as JobStatusResponse)))

  return Promise.all(promises)
}

// Health check endpoint
export async function checkApiHealth(): Promise<{ status: string; version: string; timestamp: number }> {
  const res = await fetchWithRetry(`${BASE}/health`)
  return json(res)
}