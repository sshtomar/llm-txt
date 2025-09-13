"use client"
import { useEffect, useMemo, useRef, useState } from 'react'
import { downloadFile } from '@/api/client'
import { saveTextAsFile } from '@/utils/download'
import type { JobStatusResponse } from '@/types/api'
import { domainFromUrl } from '@/utils/format'
import ReactMarkdown from 'react-markdown'

type TabKey = 'llm.txt' | 'llms-full.txt'

export default function PreviewTabs({ job }: { job: JobStatusResponse }) {
  const tabs: TabKey[] = useMemo(() => {
    const t: TabKey[] = ['llm.txt']
    if (job.llms_full_txt_url) t.push('llms-full.txt')
    return t
  }, [job.llms_full_txt_url])
  const [active, setActive] = useState<TabKey>(tabs[0])
  const [content, setContent] = useState<string>('')
  const [search, setSearch] = useState('')
  const [raw, setRaw] = useState(true)
  const searchRef = useRef<HTMLInputElement>(null)
  const [copied, setCopied] = useState(false)

  async function load(tab: TabKey) {
    const { content } = await downloadFile(job.job_id, tab)
    setContent(content)
  }

  useEffect(() => { load(active) }, [active])

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const mod = e.ctrlKey || e.metaKey
      if (mod && e.key.toLowerCase() === 'd') { doDownload(); e.preventDefault() }
      if (mod && e.key.toLowerCase() === 'c') { handleCopy(); e.preventDefault() }
      if (!mod && e.key === '/') { searchRef.current?.focus(); e.preventDefault() }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [content])

  function labelFor(t: TabKey) {
    return t === 'llm.txt' ? 'llms.txt' : t
  }

  function doDownload() {
    const domain = domainFromUrl(job.current_page_url || '')
    const ts = new Date().toISOString().replace(/[:.]/g, '-')
    const name = `${domain || 'site'}-${active === 'llm.txt' ? 'llms.txt' : active}-${ts}.txt`
    saveTextAsFile(name, content)
  }

  function handleCopy() {
    try {
      void navigator.clipboard.writeText(content)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1500)
    } catch {}
  }

  const filtered = useMemo(() => {
    if (!search) return content
    try {
      const re = new RegExp(search.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi')
      return content.replace(re, (m) => `<<${m}>>`)
    } catch { return content }
  }, [content, search])

  const stats = useMemo(() => {
    const lines = content ? content.split(/\r?\n/).length : 0
    const chars = content?.length || 0
    const tokens = Math.round(chars / 4)
    return { lines, chars, tokens }
  }, [content])

  return (
    <div className="border border-terminal-border">
      <div className="flex items-center justify-between bg-terminal-panel px-3 py-2 border-b border-terminal-border">
        <div className="flex items-center gap-2 text-sm">
          {tabs.map(t => (
            <button key={t} onClick={()=>setActive(t)}
              className={`px-3 py-1 border ${active===t? 'bg-[var(--bg)]' : 'bg-terminal-panel'} border-terminal-border`}>
              {labelFor(t)}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2 text-sm">
          <input ref={searchRef} value={search} onChange={e=>setSearch(e.target.value)}
            placeholder="/ search" className="px-2 py-1 bg-[var(--bg)] border border-terminal-border" />
          <button onClick={()=>setRaw(r=>!r)} className="px-2 py-1 border border-terminal-border">{raw ? 'rendered' : 'raw'}</button>
          <button onClick={handleCopy} className={`px-2 py-1 border border-terminal-border ${copied ? 'bg-terminal-panel text-terminal-teal' : ''}`}>{copied ? 'copied' : 'copy'}</button>
          <button onClick={doDownload} className="px-2 py-1 border border-terminal-border">download</button>
        </div>
      </div>
      {copied && (
        <div className="px-3 py-1 text-xs text-terminal-teal border-b border-terminal-border bg-terminal-panel" role="status" aria-live="polite">
          Copied to clipboard
        </div>
      )}
      <div className="px-3 py-1 text-xs opacity-70 border-b border-terminal-border bg-terminal-panel">
        Ready • {stats.lines.toLocaleString()} lines • ~{stats.tokens.toLocaleString()} tokens
      </div>
      <div className="h-[28rem] overflow-auto bg-[var(--bg)] p-4 text-sm leading-relaxed">
        {raw ? (
          <pre className="whitespace-pre-wrap">{filtered.split('<<').map((chunk, i) => {
            if (i === 0) return chunk
            const [highlight, rest] = chunk.split('>>')
            return (<>
              <mark key={`m-${i}`} className="bg-yellow-300/40 text-inherit">{highlight}</mark>
              {rest}
            </>)
          })}</pre>
        ) : (
          <div className="prose prose-invert max-w-none">
            <ReactMarkdown>{content}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  )
}
