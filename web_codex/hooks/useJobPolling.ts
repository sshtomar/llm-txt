"use client"
import { useCallback, useEffect, useRef, useState } from 'react'
import { getJobStatus } from '@/api/client'
import type { JobStatusResponse } from '@/types/api'

export function useJobPolling(jobId?: string | null, intervalMs = 1500) {
  const [status, setStatus] = useState<JobStatusResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const timer = useRef<number | null>(null)

  const poll = useCallback(async () => {
    if (!jobId) return
    try {
      const data = await getJobStatus(jobId)
      setStatus(data)
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
    if (!jobId) return
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

