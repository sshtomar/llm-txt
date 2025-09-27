"use client"
import Header from '@/components/Header'
import Hero from '@/components/Hero'
// import SecondHero from '@/components/SecondHero'
import HowItWorksGrid from '@/components/HowItWorksGrid'
import ValueProps from '@/components/ValueProps'
import InteractiveDemo from '@/components/InteractiveDemo'
import ProgressTerminal from '@/components/ProgressTerminal'
import ResultsPanel from '@/components/ResultsPanel'
import Footer from '@/components/Footer'
import { useJobPolling } from '@/hooks/useJobPolling'
import type { GenerationResponse } from '@/types/api'
import { useEffect, useState } from 'react'

export default function Page() {
  const [jobId, setJobId] = useState<string | null>(null)
  const { status, error } = useJobPolling(jobId)
  const [toast, setToast] = useState<{ kind: 'success' | 'info' | 'error'; msg: string } | null>(null)

  useEffect(() => {
    if (error) console.error(error)
  }, [error])

  // Detect payment return and show a friendly toast
  useEffect(() => {
    try {
      const url = new URL(window.location.href)
      const payment = url.searchParams.get('payment')
      if (payment === 'success') {
        setToast({ kind: 'success', msg: 'Thanks for upgrading — you’re all set.' })
      } else if (payment === 'cancel') {
        setToast({ kind: 'info', msg: 'Checkout canceled. You can upgrade anytime.' })
      }
      if (payment) {
        url.searchParams.delete('payment')
        window.history.replaceState({}, '', url.toString())
      }
    } catch {}
  }, [])

  function onCreated(res: GenerationResponse) {
    setJobId(res.job_id)
  }

  const isDone = status && ['completed', 'failed', 'cancelled'].includes(status.status)

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      {toast && (
        <section className="mx-auto max-w-6xl px-6 pt-3 w-full">
          <div className={`border p-3 text-sm ${toast.kind === 'success' ? 'border-terminal-teal text-terminal-teal' : toast.kind === 'error' ? 'border-terminal-red text-terminal-red' : 'border-terminal-border opacity-80'}`}>
            <div className="flex items-center justify-between gap-3">
              <div>{toast.msg}</div>
              <button className="opacity-70 hover:opacity-100" onClick={() => setToast(null)}>×</button>
            </div>
          </div>
        </section>
      )}
      <Hero onCreated={onCreated} />
      {/* Status directly under the CTA */}
      <section className="mx-auto max-w-6xl px-6 pb-6 w-full">
        <h2 className="mb-3">Status</h2>
        <div className="text-xs opacity-70 mb-3">Shortcuts: Ctrl+Enter generate • / search • Ctrl+C copy • Ctrl+D download</div>
        {status ? (
          <ProgressTerminal status={status} />
        ) : (
          <div className="border border-dashed border-terminal-border p-6 text-sm opacity-60">
            Status will appear here after you start a job.
          </div>
        )}
      </section>

      {status && isDone && status.status === 'completed' && (
        <section className="mx-auto max-w-6xl px-6 pb-8">
          <ResultsPanel job={status} />
        </section>
      )}

      {/* How it works (card grid) */}
      <HowItWorksGrid />

      {/* Pipeline diagram (public SVG; responsive) */}
      <section className="mx-auto max-w-6xl px-6 pb-12">
        <div className="border border-terminal-border bg-terminal-panel p-3">
          <img
            src="/llm-pipeline-fixed-flow.svg"
            alt="llms.txt pipeline diagram"
            className="w-full h-auto"
          />
        </div>
      </section>

      {process.env.NEXT_PUBLIC_DEMO_ENABLED === 'true' && (
        <InteractiveDemo />
      )}

      {status && status.status === 'failed' && (
        <section className="mx-auto max-w-6xl px-6 pb-6">
          <div className="border border-terminal-red p-3 text-terminal-red">{status.message || 'Job failed'}</div>
        </section>
      )}

      <ValueProps />
      <Footer />
    </div>
  )
}
