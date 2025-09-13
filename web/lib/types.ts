export interface GenerationResult {
  llmTxt: {
    content: string
    size: number
    downloadUrl?: string
  }
  llmsFullTxt?: {
    content: string
    size: number
    downloadUrl?: string
  }
  stats?: {
    pagesCrawled: number
    contentExtracted: number
    compressionRatio: number
    generationTime: number
  }
}

export interface GenerationOptions {
  depth: number
  maxSize: number
  includePatterns: string[]
  excludePatterns: string[]
}

export interface ProgressUpdate {
  state: 'initializing' | 'crawling' | 'processing' | 'composing' | 'complete' | 'error'
  message: string
  current?: number
  total?: number
  details?: {
    pagesProcessed?: number
    contentExtracted?: number
    currentUrl?: string
    estimatedSize?: number
  }
  result?: GenerationResult
}