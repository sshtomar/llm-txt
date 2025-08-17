'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import { ArrowLeft, RefreshCw } from 'lucide-react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { JobSteps } from '@/components/job-steps'
import { PreviewPanel } from '@/components/preview-panel'
import {
  getJobStatus,
  downloadResult,
  JobStatusResponse,
  ApiError,
} from '@/lib/api'

export default function JobStatusPage() {
  const params = useParams()
  const jobId = params.jobId as string

  const [jobData, setJobData] = useState<JobStatusResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [pollingActive, setPollingActive] = useState(true)
  const [previewContent, setPreviewContent] = useState('')
  const [fetchingContent, setFetchingContent] = useState(false)

  const fetchJobStatus = async () => {
    try {
      setError('')
      const status = await getJobStatus(jobId)
      setJobData(status)

      // Stop polling if job is done
      if (status.status === 'completed' || status.status === 'failed') {
        setPollingActive(false)

        // Fetch actual generated content if job completed successfully
        if (
          status.status === 'completed' &&
          !previewContent &&
          !fetchingContent
        ) {
          setFetchingContent(true)
          try {
            const result = await downloadResult(jobId, 'llm.txt')
            setPreviewContent(result.content)
          } catch (contentErr) {
            console.error('Failed to fetch generated content:', contentErr)
            // Set fallback content that includes actual job data
            setPreviewContent(`# Generation Complete

The llm.txt file has been generated successfully.

**Job ID**: ${jobId}
**Pages Crawled**: ${status.pages_crawled || 0}
**Total Size**: ${status.total_size_kb?.toFixed(1) || '0'}KB

Use the download button above to get your generated file.`)
          } finally {
            setFetchingContent(false)
          }
        }
      }
    } catch (err: any) {
      setError(
        err instanceof ApiError ? err.message : 'Failed to fetch job status'
      )
      setPollingActive(false)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchJobStatus()
  }, [jobId])

  useEffect(() => {
    if (!pollingActive) return

    const interval = setInterval(fetchJobStatus, 1500)

    // Stop polling after 60 seconds
    const timeout = setTimeout(() => {
      setPollingActive(false)
    }, 60000)

    return () => {
      clearInterval(interval)
      clearTimeout(timeout)
    }
  }, [pollingActive])

  const handleRetry = () => {
    setPollingActive(true)
    setLoading(true)
    fetchJobStatus()
  }

  if (loading && !jobData) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-b-2 border-primary"></div>
          <p className="text-muted-foreground">Loading job status...</p>
        </div>
      </div>
    )
  }

  if (error && !jobData) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle className="text-red-600">Error</CardTitle>
            <CardDescription>{error}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button onClick={handleRetry} variant="outline" className="w-full">
              <RefreshCw className="mr-2 h-4 w-4" />
              Retry
            </Button>
            <Button asChild variant="ghost" className="w-full">
              <Link href="/">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Home
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-7xl px-6 py-8">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Button asChild variant="ghost" size="sm">
              <Link href="/">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back
              </Link>
            </Button>

            <div>
              <h1 className="text-2xl font-bold">Job Status</h1>
              <p className="text-muted-foreground">ID: {jobId}</p>
            </div>
          </div>

          {pollingActive && (
            <div className="flex items-center space-x-2 text-sm text-muted-foreground">
              <div className="h-2 w-2 animate-pulse rounded-full bg-blue-500"></div>
              <span>Live updates</span>
            </div>
          )}
        </div>

        <div className="grid gap-8 lg:grid-cols-3">
          {/* Left side - Job progress */}
          <div>
            <Card>
              <CardHeader>
                <CardTitle>Generation Progress</CardTitle>
                <CardDescription>
                  Track your llm.txt generation in real-time
                </CardDescription>
              </CardHeader>
              <CardContent>
                {jobData && (
                  <JobSteps
                    currentStatus={jobData.status}
                    progress={jobData.progress}
                    message={jobData.message}
                  />
                )}
              </CardContent>
            </Card>

            {/* Job metadata */}
            {jobData && (
              <Card className="mt-6">
                <CardHeader>
                  <CardTitle className="text-base">Job Details</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Status:</span>
                    <span
                      className={`font-medium ${
                        jobData.status === 'completed'
                          ? 'text-green-600'
                          : jobData.status === 'failed'
                            ? 'text-red-600'
                            : 'text-blue-600'
                      }`}
                    >
                      {jobData.status}
                    </span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Created:</span>
                    <span>
                      {new Date(jobData.created_at * 1000).toLocaleString()}
                    </span>
                  </div>

                  {jobData.completed_at && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Completed:</span>
                      <span>
                        {new Date(jobData.completed_at * 1000).toLocaleString()}
                      </span>
                    </div>
                  )}

                  {jobData.pages_crawled !== undefined && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">
                        Pages Crawled:
                      </span>
                      <span>{jobData.pages_crawled}</span>
                    </div>
                  )}

                  {jobData.total_size_kb !== undefined && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">
                        Output Size:
                      </span>
                      <span>{jobData.total_size_kb.toFixed(1)} KB</span>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </div>

          {/* Right side - Preview */}
          <div>
            {jobData?.status === 'completed' && previewContent ? (
              <PreviewPanel
                content={previewContent}
                jobId={jobId}
                showFullVersion={true}
              />
            ) : jobData?.status === 'completed' && fetchingContent ? (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Preview</CardTitle>
                  <CardDescription>
                    Loading generated content...
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="rounded-md bg-muted/50 p-8 text-center">
                    <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-lg bg-muted">
                      <div className="h-8 w-8 animate-spin rounded bg-muted-foreground/20"></div>
                    </div>
                    <p className="text-muted-foreground">
                      Fetching your generated content...
                    </p>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Preview</CardTitle>
                  <CardDescription>
                    Preview will be available when generation completes
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="rounded-md bg-muted/50 p-8 text-center">
                    <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-lg bg-muted">
                      <div className="h-8 w-8 animate-pulse rounded bg-muted-foreground/20"></div>
                    </div>
                    <p className="text-muted-foreground">
                      {jobData?.status === 'failed'
                        ? 'Generation failed - no preview available'
                        : 'Waiting for generation to complete...'}
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
