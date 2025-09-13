"use client"
import type { JobStatusResponse } from '@/types/api'
import { asciiProgress, prettyBytes } from '@/utils/format'

function phaseLabel(phase: string, status: JobStatusResponse['status']) {
  if (status === 'failed') return 'Failed'
  if (status === 'cancelled') return 'Cancelled'
  switch (phase) {
    case 'initializing': return 'Parsing robots.txt, discovering sitemap…'
    case 'crawling': return 'Fetching pages — respecting rate limits…'
    case 'extracting': return 'Extracting content, cleaning markdown…'
    case 'composing': return 'Assembling llms.txt, applying size budget…'
    default: return phase
  }
}

export default function ProgressTerminal({ status }: { status: JobStatusResponse }) {
  const pct = status.progress ?? 0
  const logLines = status.processing_logs?.slice(-200) ?? []
  return (
    <div className="border border-terminal-border bg-terminal-panel p-3">
      <div className="flex items-center justify-between text-sm mb-2">
        <div className="ascii-mono text-terminal-teal">{asciiProgress(pct)}</div>
        <div className="opacity-70">ETA 60–90s typical</div>
      </div>
      <div className="text-sm mb-2">
        <span className="text-terminal-teal">{phaseLabel(status.current_phase, status.status)}</span>
        {status.current_page_url && (
          <span className="opacity-70"> — {status.current_page_url}</span>
        )}
      </div>
      <div className="grid grid-cols-3 gap-3 text-xs mb-2">
        <div className="border border-terminal-border p-2">Discovered: {status.pages_discovered}</div>
        <div className="border border-terminal-border p-2">Processed: {status.pages_processed}</div>
        <div className="border border-terminal-border p-2">Output: {prettyBytes(status.total_size_kb ?? 0)}</div>
      </div>
      <div className="h-56 overflow-auto border border-terminal-border bg-[var(--bg)] p-2 text-xs leading-relaxed">
        {logLines.length === 0 ? (
          <div className="opacity-50">Live logs will appear here…</div>
        ) : (
          logLines.map((l, i) => (
            <div key={i} className="whitespace-pre-wrap">{l}</div>
          ))
        )}
      </div>
    </div>
  )
}
