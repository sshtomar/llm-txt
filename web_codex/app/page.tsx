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

  useEffect(() => {
    if (error) console.error(error)
  }, [error])

  function onCreated(res: GenerationResponse) {
    setJobId(res.job_id)
  }

  const isDone = status && ['completed', 'failed', 'cancelled'].includes(status.status)

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
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
