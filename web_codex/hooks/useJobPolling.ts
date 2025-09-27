"use client"
import { useCallback, useEffect, useRef, useState } from 'react'
import { getJobStatus } from '@/api/client'
import type { JobStatusResponse } from '@/types/api'

export function useJobPolling(jobId?: string | null, intervalMs = 1500) {
  const [status, setStatus] = useState<JobStatusResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const timer = useRef<number | null>(null)
  const previousJobId = useRef<string | null>(null)

  const poll = useCallback(async () => {
    if (!jobId) return
    try {
      const data = await getJobStatus(jobId)
      setStatus(prev => {
        if (!prev) return data
        const prevLogs = prev.processing_logs || []
        const inLogs = data.processing_logs || []
        const mergedLogs = inLogs.length >= prevLogs.length ? inLogs : prevLogs
        return {
          ...data,
          // Ensure monotonic, non-decreasing values in UI
          progress: Math.max(prev.progress ?? 0, data.progress ?? 0),
          pages_discovered: Math.max(prev.pages_discovered ?? 0, data.pages_discovered ?? 0),
          pages_processed: Math.max(prev.pages_processed ?? 0, data.pages_processed ?? 0),
          processing_logs: mergedLogs,
        }
      })
      setError(null)
      if (['completed', 'failed', 'cancelled'].includes(data.status)) {
        if (timer.current) window.clearInterval(timer.current)
        timer.current = null
      }
    } catch (e: any) {
      setError(e?.message || 'Failed to fetch job status')
    }
  }, [jobId])

  useEffect(() => {
    if (!jobId) {
      // Only reset status if we're clearing the job ID
      if (previousJobId.current !== null) {
        setStatus(null)
        setError(null)
      }
      previousJobId.current = null
      return
    }

    // Only reset status if this is a different job ID
    if (previousJobId.current !== null && previousJobId.current !== jobId) {
      setStatus(null)
      setError(null)
    }
    previousJobId.current = jobId

    // Immediately poll once
    poll()
    // Then on an interval
    timer.current = window.setInterval(poll, intervalMs)
    return () => {
      if (timer.current) window.clearInterval(timer.current)
    }
  }, [jobId, intervalMs, poll])

  return { status, error, refresh: poll }
}
