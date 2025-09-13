"use client"
import type { JobStatusResponse } from '@/types/api'
import { prettyBytes } from '@/utils/format'
import PreviewTabs from './PreviewTabs'

export default function ResultsPanel({ job }: { job: JobStatusResponse }) {
  const sizeLabel = job.total_size_kb ? prettyBytes(job.total_size_kb) : '—'
  return (
    <section className="space-y-3">
      <div className="grid grid-cols-2 gap-3">
        <div className="border border-terminal-border p-3 bg-terminal-panel">
          <div className="text-sm mb-1">llms.txt</div>
          <div className="text-xs opacity-70 mb-2">Optimized summary • {sizeLabel}</div>
          {job.llm_txt_url ? (
            <a className="px-3 py-1 border border-terminal-border inline-block" href={job.llm_txt_url}>download</a>
          ) : (
            <button disabled className="px-3 py-1 border border-terminal-border opacity-50">download</button>
          )}
        </div>
        <div className="border border-terminal-border p-3 bg-terminal-panel">
          <div className="text-sm mb-1">llms-full.txt</div>
          <div className="text-xs opacity-70 mb-2">Complete version</div>
          {job.llms_full_txt_url ? (
            <a className="px-3 py-1 border border-terminal-border inline-block" href={job.llms_full_txt_url}>download</a>
          ) : (
            <button disabled className="px-3 py-1 border border-terminal-border opacity-50">download</button>
          )}
        </div>
      </div>
      <PreviewTabs job={job} />
    </section>
  )
}
