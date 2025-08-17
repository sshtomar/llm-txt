import { GenerateRequest } from './validators'

export interface GenerationResponse {
  job_id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  message: string
}

export interface JobStatusResponse {
  job_id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  message: string
  created_at: number
  completed_at?: number
  pages_crawled?: number
  total_size_kb?: number
  llm_txt_url?: string
  llms_full_txt_url?: string
}

export interface DownloadResponse {
  content: string
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `/api${endpoint}`

  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  })

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: 'Unknown error' }))
    throw new ApiError(response.status, error.detail || 'Request failed')
  }

  return response.json()
}

export async function createGeneration(
  body: GenerateRequest
): Promise<GenerationResponse> {
  return apiRequest('/generations', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export async function getJobStatus(jobId: string): Promise<JobStatusResponse> {
  return apiRequest(`/generations/${jobId}`)
}

export async function downloadResult(
  jobId: string,
  fileType: 'llm.txt' | 'llms-full.txt'
): Promise<DownloadResponse> {
  return apiRequest(`/generations/${jobId}/download/${fileType}`)
}

export async function cancelJob(jobId: string): Promise<{ message: string }> {
  return apiRequest(`/generations/${jobId}`, {
    method: 'DELETE',
  })
}
