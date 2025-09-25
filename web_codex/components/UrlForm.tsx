"use client"
import { useEffect, useRef, useState } from 'react'
import { createGeneration } from '@/api/client'
import type { GenerationRequest, GenerationResponse } from '@/types/api'

type Props = {
  onCreated: (res: GenerationResponse) => void
  size?: 'md' | 'lg'
}

function isValidUrl(u: string) {
  try { new URL(u); return true } catch { return false }
}

export default function UrlForm({ onCreated, size = 'md' }: Props) {
  const [url, setUrl] = useState('')
  const [advanced, setAdvanced] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [genCount, setGenCount] = useState<number>(0)
  // Toggle to re-enable free trial limits
  const ENABLE_LIMIT = true
  const FREE_LIMIT = 3
  const [opts, setOpts] = useState<Required<Pick<GenerationRequest, 'max_pages' | 'max_depth' | 'full_version' | 'respect_robots'>>>({
    max_pages: 150,
    max_depth: 5,
    full_version: false,
    respect_robots: true,
  })

  const inputRef = useRef<HTMLInputElement>(null)
  const [focused, setFocused] = useState(false)

  useEffect(() => { inputRef.current?.focus() }, [])

  // Load generation count from localStorage
  useEffect(() => {
    try {
      const raw = localStorage.getItem('llm-txt:gen-count')
      setGenCount(raw ? Math.max(0, parseInt(raw, 10)) : 0)
    } catch {}
  }, [])
  useEffect(() => {
    const sync = () => {
      try {
        const raw = localStorage.getItem('llm-txt:gen-count')
        setGenCount(raw ? Math.max(0, parseInt(raw, 10)) : 0)
      } catch {}
    }
    window.addEventListener('storage', sync)
    window.addEventListener('llm-txt:gen-used', sync as EventListener)
    return () => {
      window.removeEventListener('storage', sync)
      window.removeEventListener('llm-txt:gen-used', sync as EventListener)
    }
  }, [])

  async function onSubmit(e?: React.FormEvent) {
    e?.preventDefault()
    setError(null)
    // Enforce free tier limit
    if (ENABLE_LIMIT && genCount >= FREE_LIMIT) {
      setError('Free limit reached (3 generations). Upgrade to continue.')
      return
    }
    if (!isValidUrl(url)) { setError('Please enter a valid URL'); return }
    setLoading(true)
      try {
        const payload: GenerationRequest = { url, ...opts }
        const res = await createGeneration(payload)
        onCreated(res)
      // Increment generation count on successful creation (if limiting enabled)
      if (ENABLE_LIMIT) {
        try {
          const next = genCount + 1
          localStorage.setItem('llm-txt:gen-count', String(next))
          setGenCount(next)
          window.dispatchEvent(new Event('llm-txt:gen-used'))
        } catch {}
      }
    } catch (e: any) {
      setError(e?.message || 'Failed to create job')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const mod = e.ctrlKey || e.metaKey
      if (mod && e.key.toLowerCase() === 'enter') { onSubmit(); e.preventDefault() }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url, opts])

  const isLg = size === 'lg'

  const limitReached = ENABLE_LIMIT && genCount >= FREE_LIMIT
  const trialsLeft = Math.max(0, FREE_LIMIT - genCount)

  return (
    <form onSubmit={onSubmit} className="space-y-3">
      <label className={`block ${isLg ? 'text-base' : 'text-sm'} opacity-80`}>Documentation URL</label>
      <input
        ref={inputRef}
        type="url"
        placeholder="Paste a docs URL, e.g. https://docs.example.com"
        value={url}
        onChange={e=>setUrl(e.target.value)}
        onFocus={()=>setFocused(true)}
        onBlur={()=>setFocused(false)}
        className={`w-full ${isLg ? 'text-lg px-5 py-4' : 'text-base px-4 py-3'} border border-terminal-border bg-[var(--bg)] focus:outline-none focus:ring-0 focus:border-terminal-teal`}
      />
      {error && <p className="text-terminal-red text-sm">{error}</p>}
      <div className="flex items-center gap-3">
        <button disabled={loading || limitReached} className={`btn btn-primary ${isLg ? 'px-5 py-3 text-base' : 'px-4 py-2 text-sm'}`}
          data-cta>
          {limitReached ? 'Upgrade to continue' : (loading ? 'Starting…' : 'Generate llms.txt')}
        </button>
        <button type="button" onClick={()=>setAdvanced(v=>!v)} className="text-sm underline">{advanced ? 'Hide' : 'Show'} advanced options</button>
      </div>
      <div className="text-xs opacity-70">Free trials left: {trialsLeft} / {FREE_LIMIT}</div>
      {limitReached && (
        <div className="text-sm opacity-80 border border-terminal-border p-3 bg-terminal-panel">
          You have reached the free limit of 3 generations. Please upgrade to continue.
          {' '}<a className="underline" href="https://github.com/sshtomar/llm-txt" target="_blank" rel="noreferrer">Learn more</a>
        </div>
      )}
      {/* Trials indicator removed per request */}
      {/* Inline explainer removed per request */}

      {advanced && (
        <div className="grid grid-cols-2 gap-3 border border-terminal-border p-3 bg-terminal-panel">
          <label className="text-sm flex flex-col gap-1">Max pages
            <input type="number" min={1} max={1000} value={opts.max_pages}
              onChange={e=>setOpts(o=>({ ...o, max_pages: Number(e.target.value) }))}
              className="px-3 py-2 bg-[var(--bg)] border border-terminal-border focus:border-terminal-teal outline-none" />
          </label>
          <label className="text-sm flex flex-col gap-1">Max depth
            <input type="number" min={1} max={10} value={opts.max_depth}
              onChange={e=>setOpts(o=>({ ...o, max_depth: Number(e.target.value) }))}
              className="px-3 py-2 bg-[var(--bg)] border border-terminal-border focus:border-terminal-teal outline-none" />
          </label>
          <label className="text-sm flex items-center gap-2 col-span-2">
            <input type="checkbox" checked={opts.full_version}
              onChange={e=>setOpts(o=>({ ...o, full_version: e.target.checked }))} />
            Generate llms-full.txt
          </label>
          <label className="text-sm flex items-center gap-2 col-span-2">
            <input type="checkbox" checked={opts.respect_robots}
              onChange={e=>setOpts(o=>({ ...o, respect_robots: e.target.checked }))} />
            Respect robots.txt
          </label>
        </div>
      )}
    </form>
  )
}
