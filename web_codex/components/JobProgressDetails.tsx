"use client"

import { JobStatusResponse } from '@/types/api'
import { prettyBytes } from '@/utils/format'

interface JobProgressDetailsProps {
  status: JobStatusResponse
  compact?: boolean
}

export default function JobProgressDetails({ status, compact = false }: JobProgressDetailsProps) {
  const progressPercent = Math.round((status.progress || 0) * 100)

  if (compact) {
    return (
      <div className="text-xs space-y-1">
        <div className="flex justify-between">
          <span className="text-terminal-teal">{status.current_phase}</span>
          <span>{progressPercent}%</span>
        </div>
        {status.pages_discovered && (
          <div className="opacity-80">
            {status.pages_processed}/{status.pages_discovered} pages
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="border border-terminal-border bg-terminal-panel p-3 space-y-2">
      <div className="flex justify-between items-center">
        <h3 className="text-sm font-mono text-terminal-teal">Job Progress</h3>
        <span className="text-xs">{status.job_id?.slice(0, 8)}</span>
      </div>

      {/* Progress bar */}
      <div className="relative h-2 bg-black border border-terminal-border">
        <div
          className="absolute inset-y-0 left-0 bg-terminal-teal transition-all duration-300"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div>
          <span className="opacity-60">Status:</span> <span className="text-terminal-teal">{status.status}</span>
        </div>
        <div>
          <span className="opacity-60">Phase:</span> <span>{status.current_phase}</span>
        </div>
        <div>
          <span className="opacity-60">Progress:</span> <span>{progressPercent}%</span>
        </div>
        {status.pages_discovered && (
          <div>
            <span className="opacity-60">Pages:</span> <span>{status.pages_processed}/{status.pages_discovered}</span>
          </div>
        )}
      </div>

      {/* Current page */}
      {status.current_page_url && (
        <div className="text-xs">
          <span className="opacity-60">Processing:</span>
          <div className="truncate text-terminal-teal">{status.current_page_url}</div>
        </div>
      )}

      {/* Processing logs */}
      {status.processing_logs && status.processing_logs.length > 0 && (
        <div className="text-xs space-y-1">
          <span className="opacity-60">Recent activity:</span>
          <div className="bg-black p-2 border border-terminal-border max-h-20 overflow-y-auto">
            {status.processing_logs.slice(-3).map((log, i) => (
              <div key={i} className="font-mono text-[10px] opacity-80">{log}</div>
            ))}
          </div>
        </div>
      )}

      {/* Completion info */}
      {status.status === 'completed' && (
        <div className="text-xs pt-2 border-t border-terminal-border grid grid-cols-2 gap-2">
          {status.pages_crawled && (
            <div>
              <span className="opacity-60">Crawled:</span> <span>{status.pages_crawled} pages</span>
            </div>
          )}
          {status.total_size_kb && (
            <div>
              <span className="opacity-60">Size:</span> <span>{prettyBytes(status.total_size_kb)}</span>
            </div>
          )}
          {status.created_at && status.completed_at && (
            <div>
              <span className="opacity-60">Duration:</span> <span>{Math.round(status.completed_at - status.created_at)}s</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}