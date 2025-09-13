"use client"
import { useMemo, useRef, useState } from 'react'
import { createGeneration, downloadFile, getJobStatus } from '@/api/client'
import { asciiProgress, prettyBytes } from '@/utils/format'

type Preset = { id: string; title: string; url: string }

const PRESETS: Preset[] = [
  { id: 'fastapi', title: 'FastAPI Docs', url: 'https://fastapi.tiangolo.com/' },
  { id: 'python', title: 'Python Docs', url: 'https://docs.python.org/3/' },
  { id: 'nextjs', title: 'Next.js Docs', url: 'https://nextjs.org/docs' },
]

type CardState = {
  status?: 'idle' | 'starting' | 'running' | 'completed' | 'failed'
  jobId?: string
  progress?: number
  phase?: string
  discovered?: number
  processed?: number
  content?: string
  error?: string
  lastRunAt?: number
  copied?: boolean
  sizeKB?: number
  durationSec?: number
}

const COOLDOWN_MS = 10 * 60 * 1000 // 10 minutes

export default function InteractiveDemo() {
  const [runningCount, setRunningCount] = useState(0)
  const allowAnother = runningCount < 2

  return (
    <section className="mx-auto max-w-6xl px-6 pt-4 pb-8">
      <div className="flex items-baseline justify-between mb-3">
        <h2 className="text-xl">Interactive demo</h2>
        <div className="text-xs opacity-70">Live generation • EN only • robots-aware</div>
      </div>
      <div className="grid md:grid-cols-3 gap-4">
        {PRESETS.map(p => (
          <DemoCard key={p.id} preset={p} canStart={allowAnother} onRunningChange={d => setRunningCount(c => Math.max(0, c + d))} />
        ))}
      </div>
    </section>
  )
}

function DemoCard({ preset, canStart, onRunningChange }: { preset: Preset; canStart: boolean; onRunningChange: (delta: number) => void }) {
  const [state, setState] = useState<CardState>(() => {
    try {
      const raw = sessionStorage.getItem(`demo:${preset.id}`)
      return raw ? JSON.parse(raw) : { status: 'idle' }
    } catch {
      return { status: 'idle' }
    }
  })
  const timer = useRef<number | null>(null)

  function save(next: CardState) {
    setState(next)
    try { sessionStorage.setItem(`demo:${preset.id}`, JSON.stringify(next)) } catch {}
  }

  const onCopy = async () => {
    try { await navigator.clipboard.writeText(state.content || '') } catch {}
    save({ ...state, copied: true })
    window.setTimeout(() => save({ ...state, copied: false }), 1200)
  }

  const cooldownRemaining = useMemo(() => {
    if (!state.lastRunAt) return 0
    const left = state.lastRunAt + COOLDOWN_MS - Date.now()
    return Math.max(0, left)
  }, [state.lastRunAt])

  const disabled = state.status === 'running' || !canStart || cooldownRemaining > 0

  async function start() {
    if (disabled) return
    save({ status: 'starting', lastRunAt: Date.now() })
    onRunningChange(1)
    try {
      const res = await createGeneration({ url: preset.url, full_version: true, language: 'en', max_pages: 80, max_depth: 3, respect_robots: true })
      save({ ...state, status: 'running', jobId: res.job_id, progress: 0 })
      poll(res.job_id)
    } catch (e: any) {
      onRunningChange(-1)
      save({ status: 'failed', error: e?.message || 'Failed to start' })
    }
  }

  async function poll(jobId: string) {
    async function step() {
      try {
        const st = await getJobStatus(jobId)
        if (st.status === 'completed') {
          const file = await downloadFile(jobId, 'llms-full.txt')
          const bytes = new TextEncoder().encode(file.content || '').length
          const sizeKB = Math.round(bytes / 1024)
          const durationSec = st.completed_at && st.created_at ? Math.max(0, Math.round(st.completed_at - st.created_at)) : undefined
          onRunningChange(-1)
          save({ status: 'completed', jobId, progress: 1, phase: st.current_phase, discovered: st.pages_discovered, processed: st.pages_processed, content: file.content, lastRunAt: Date.now(), sizeKB, durationSec })
          if (timer.current) window.clearInterval(timer.current)
          timer.current = null
        } else if (st.status === 'failed' || st.status === 'cancelled') {
          onRunningChange(-1)
          save({ status: 'failed', jobId, progress: st.progress, phase: st.current_phase, error: st.message, lastRunAt: Date.now() })
          if (timer.current) window.clearInterval(timer.current)
          timer.current = null
        } else {
          save({ status: 'running', jobId, progress: st.progress, phase: st.current_phase, discovered: st.pages_discovered, processed: st.pages_processed })
        }
      } catch (e: any) {
        onRunningChange(-1)
        save({ status: 'failed', error: e?.message || 'Status error', lastRunAt: Date.now() })
        if (timer.current) window.clearInterval(timer.current)
        timer.current = null
      }
    }
    await step()
    timer.current = window.setInterval(step, 1500)
  }

  function excerpt(text?: string, lines = 20) {
    if (!text) return ''
    const arr = text.split(/\r?\n/)
    const slice = arr.slice(0, lines)
    const more = arr.length > lines ? '\n\n[… truncated …]' : ''
    return slice.join('\n') + more
  }

  return (
    <div className="border border-terminal-border bg-terminal-panel p-3 flex flex-col gap-2">
      <div className="flex items-start justify-between">
        <div className="text-sm text-terminal-teal">{preset.title}</div>
        <div className="flex items-center gap-1">
          <span className="px-2 py-0.5 border border-terminal-border bg-[var(--bg)] text-[10px]">EN</span>
          <span className="px-2 py-0.5 border border-terminal-border bg-[var(--bg)] text-[10px]">Robots</span>
          <span className="px-2 py-0.5 border border-terminal-border bg-[var(--bg)] text-[10px]">Full</span>
        </div>
      </div>
      <div className="flex items-center justify-between -mt-1">
        <a className="text-xs underline opacity-80" href={preset.url} target="_blank" rel="noreferrer">Docs</a>
        {state.status === 'completed' && (
          <div className="text-[10px] opacity-80 flex items-center gap-2">
            {typeof state.sizeKB === 'number' && <span>{prettyBytes(state.sizeKB)}</span>}
            {typeof state.durationSec === 'number' && <span>{state.durationSec}s</span>}
          </div>
        )}
      </div>
      <div className="flex items-center gap-2 text-xs">
        <button disabled={disabled} onClick={start} className="px-2 py-1 border border-terminal-border bg-[var(--bg)] disabled:opacity-50">
          {state.status === 'running' || state.status === 'starting' ? 'Generating…' : 'Generate preview'}
        </button>
        {cooldownRemaining > 0 && (
          <span className="opacity-60">cooldown {Math.ceil(cooldownRemaining/60000)}m</span>
        )}
      </div>

      <div className="text-xs opacity-80">
        {state.status === 'running' ? (
          <div className="flex items-center justify-between">
            <span className="ascii-mono text-terminal-teal">{asciiProgress(state.progress || 0)}</span>
            <span>{state.phase}</span>
          </div>
        ) : state.status === 'failed' ? (
          <div className="text-terminal-red">{state.error || 'Failed'}</div>
        ) : null}
      </div>

      <div className="border border-terminal-border bg-[var(--bg)] p-2 text-xs h-48 overflow-auto whitespace-pre-wrap">
        {state.content ? (
          excerpt(state.content)
        ) : (
          <span className="opacity-60">Preview will appear here after generation.</span>
        )}
      </div>

      <div className="flex items-center gap-2 text-xs">
        <button disabled={!state.content} onClick={onCopy} className={`px-2 py-1 border border-terminal-border ${state.copied ? 'text-terminal-teal' : ''}`}>{state.copied ? 'copied' : 'copy'}</button>
        <a
          role="button"
          aria-disabled={!state.jobId || state.status !== 'completed'}
          className={`px-2 py-1 border border-terminal-border ${state.status === 'completed' ? '' : 'opacity-50 pointer-events-none'}`}
          href={state.jobId ? `/v1/generations/${state.jobId}/download/llms-full.txt` : '#'}
        >download</a>
      </div>
    </div>
  )
}
