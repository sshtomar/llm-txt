'use client'

import { useState, forwardRef, useImperativeHandle } from 'react'
import { ChevronDown, ChevronUp, Loader2, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { PreviewPanel } from '@/components/preview-panel'
import {
  createGeneration,
  getJobStatus,
  downloadResult,
  GenerationResponse,
  JobStatusResponse,
  ApiError,
} from '@/lib/api'
import { generateRequestSchema, GenerateRequest } from '@/lib/validators'
import { useCredit, hasCreditsRemaining } from '@/lib/credits'

interface GeneratorCardProps {
  url: string
  isGenerating: boolean
  onGeneratingChange: (generating: boolean) => void
  onNeedUpgrade?: () => void
}

export interface GeneratorCardRef {
  triggerGenerate: () => void
}

export const GeneratorCard = forwardRef<GeneratorCardRef, GeneratorCardProps>(
  ({ url, isGenerating, onGeneratingChange, onNeedUpgrade }, ref) => {
    const [showOptions, setShowOptions] = useState(false)
    const [options, setOptions] = useState({
      max_pages: 100,
      max_depth: 3,
      full_version: false,
      respect_robots: true,
    })
    const [error, setError] = useState('')
    const [jobData, setJobData] = useState<JobStatusResponse | null>(null)
    const [previewContent, setPreviewContent] = useState('')

    const handleGenerate = async () => {
      if (!url) return

      // Check if user has credits remaining
      if (!hasCreditsRemaining()) {
        setError('No credits remaining. Please upgrade to Pro to continue.')
        onNeedUpgrade?.()
        return
      }

      try {
        setError('')

        // Use a credit before starting generation
        if (!useCredit()) {
          setError('No credits remaining. Please upgrade to Pro to continue.')
          onNeedUpgrade?.()
          return
        }

        onGeneratingChange(true)
        console.log('Starting generation for URL:', url)

        // Validate request
        const request: GenerateRequest = generateRequestSchema.parse({
          url,
          ...options,
        })
        console.log('Request validated:', request)

        // Create actual generation job
        const response: GenerationResponse = await createGeneration(request)
        console.log('Generation started:', response)

        // Poll for job status and update UI
        pollJobStatus(response.job_id)
      } catch (err: any) {
        console.error('Generation failed:', err)
        if (err.errors && err.errors[0]) {
          setError(err.errors[0].message)
        } else if (err.message) {
          setError(err.message)
        } else {
          setError('Failed to generate. Please check your URL and try again.')
        }
        onGeneratingChange(false)
      }
    }

    const pollJobStatus = async (jobId: string) => {
      const maxPolls = 120 // 2 minutes max polling
      let pollCount = 0

      const poll = async () => {
        try {
          const status = await getJobStatus(jobId)
          setJobData(status)

          if (status.status === 'completed') {
            // Job completed successfully - fetch the actual generated content
            onGeneratingChange(false)
            try {
              const result = await downloadResult(jobId, 'llm.txt')
              setPreviewContent(result.content)
            } catch (downloadErr) {
              console.error('Failed to fetch generated content:', downloadErr)
              // Fallback to a completion message if download fails
              setPreviewContent(`# Generation Complete

The llm.txt file has been generated successfully for ${url}.

**Job ID**: ${jobId}
**Pages Crawled**: ${status.pages_crawled || 0}
**Total Size**: ${status.total_size_kb?.toFixed(1) || '0'}KB

Use the download button above to get your generated file.`)
            }
          } else if (status.status === 'failed') {
            onGeneratingChange(false)
            setError(status.message || 'Generation failed')
          } else if (
            status.status === 'running' ||
            status.status === 'pending'
          ) {
            // Continue polling if still processing
            pollCount++
            if (pollCount < maxPolls) {
              setTimeout(poll, 1000) // Poll every second
            } else {
              onGeneratingChange(false)
              setError('Generation timed out')
            }
          }
        } catch (err) {
          console.error('Failed to get job status:', err)
          onGeneratingChange(false)
          setError('Failed to get job status')
        }
      }

      poll()
    }

    // Expose the triggerGenerate function to parent component
    useImperativeHandle(ref, () => ({
      triggerGenerate: handleGenerate,
    }))

    return (
      <div className="w-full max-w-4xl">
        {/* Preview/Demo Card */}
        <div className="overflow-hidden rounded-xl border border-border bg-card shadow-sm">
          <div className="border-b border-border bg-muted px-4 py-3">
            <div className="flex items-center gap-2">
              <div className="h-3 w-3 rounded-full bg-red-400"></div>
              <div className="h-3 w-3 rounded-full bg-yellow-400"></div>
              <div className="h-3 w-3 rounded-full bg-green-400"></div>
              <div className="flex-1 text-center">
                <span className="font-mono text-sm text-muted-foreground">
                  llm.txt
                </span>
              </div>
            </div>
          </div>

          {!isGenerating && !previewContent && (
            <div className="p-6 text-center">
              <div className="mb-4 text-muted-foreground">
                <svg
                  className="mx-auto h-16 w-16"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="1.5"
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
              </div>
              <p className="text-sm text-muted-foreground">
                Enter a documentation URL above to see a live preview of your
                generated llm.txt file
              </p>
            </div>
          )}

          {isGenerating && (
            <div className="p-6">
              <div className="mb-4 flex items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
              </div>
              <div className="text-center">
                <p className="mb-2 text-sm font-medium text-foreground">
                  {jobData?.message || 'Starting generation...'}
                </p>
                {jobData && (
                  <div className="h-2 w-full rounded-full bg-muted">
                    <div
                      className="h-2 rounded-full bg-primary transition-all duration-300"
                      style={{ width: `${jobData.progress * 100}%` }}
                    />
                  </div>
                )}
              </div>
            </div>
          )}

          {previewContent && (
            <div className="p-6">
              <PreviewPanel
                content={previewContent}
                jobId={jobData?.job_id || ''}
                showFullVersion={options.full_version}
              />
            </div>
          )}

          {error && (
            <div className="p-6">
              <div className="flex items-center space-x-2 rounded-lg bg-destructive/10 p-4 text-destructive">
                <AlertCircle className="h-5 w-5 flex-shrink-0" />
                <span className="text-sm">{error}</span>
              </div>
            </div>
          )}
        </div>

        {/* Advanced Options */}
        <div className="mt-6">
          <Button
            variant="ghost"
            onClick={() => setShowOptions(!showOptions)}
            className="w-full justify-between text-muted-foreground hover:text-foreground"
          >
            <span className="text-sm">Advanced Options</span>
            {showOptions ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </Button>

          {showOptions && (
            <div className="mt-4 space-y-4 rounded-lg border bg-muted p-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label
                    htmlFor="max_pages"
                    className="mb-1 block text-sm font-medium text-foreground"
                  >
                    Max Pages
                  </label>
                  <Input
                    id="max_pages"
                    type="number"
                    min="1"
                    max="1000"
                    value={options.max_pages}
                    onChange={(e) =>
                      setOptions({
                        ...options,
                        max_pages: parseInt(e.target.value) || 100,
                      })
                    }
                    className="text-sm"
                  />
                </div>

                <div>
                  <label
                    htmlFor="max_depth"
                    className="mb-1 block text-sm font-medium text-foreground"
                  >
                    Depth
                  </label>
                  <Input
                    id="max_depth"
                    type="number"
                    min="1"
                    max="10"
                    value={options.max_depth}
                    onChange={(e) =>
                      setOptions({
                        ...options,
                        max_depth: parseInt(e.target.value) || 3,
                      })
                    }
                    className="text-sm"
                  />
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex items-center space-x-2">
                  <input
                    id="full_version"
                    type="checkbox"
                    checked={options.full_version}
                    onChange={(e) =>
                      setOptions({ ...options, full_version: e.target.checked })
                    }
                    className="rounded border-input text-primary focus:ring-ring"
                  />
                  <label
                    htmlFor="full_version"
                    className="text-sm text-foreground"
                  >
                    Generate llms-full.txt (uncompressed version)
                  </label>
                </div>

                <div className="flex items-center space-x-2">
                  <input
                    id="respect_robots"
                    type="checkbox"
                    checked={options.respect_robots}
                    onChange={(e) =>
                      setOptions({
                        ...options,
                        respect_robots: e.target.checked,
                      })
                    }
                    className="rounded border-input text-primary focus:ring-ring"
                  />
                  <label
                    htmlFor="respect_robots"
                    className="text-sm text-foreground"
                  >
                    Respect robots.txt (recommended)
                  </label>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    )
  }
)

GeneratorCard.displayName = 'GeneratorCard'
