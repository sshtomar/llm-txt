export type JobStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'

export interface GenerationRequest {
  url: string
  max_pages?: number
  max_depth?: number
  full_version?: boolean
  respect_robots?: boolean
  language?: string
}

export interface GenerationResponse {
  job_id: string
  status: JobStatus
  message: string
}

export interface JobStatusResponse {
  job_id: string
  status: JobStatus
  progress: number
  message: string
  created_at: number
  completed_at?: number | null
  current_phase: 'initializing' | 'crawling' | 'extracting' | 'composing' | string
  current_page_url?: string | null
  pages_discovered: number
  pages_processed: number
  processing_logs: string[]
  pages_crawled?: number | null
  total_size_kb?: number | null
  llm_txt_url?: string | null
  llms_full_txt_url?: string | null
}

export interface DownloadResponse { content: string }
