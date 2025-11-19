"use client"
import type { JobStatusResponse } from '@/types/api'
import { prettyBytes } from '@/utils/format'
import PreviewTabs from './PreviewTabs'
import { buildCheckoutUrl } from '@/lib/checkout'
import { useEmailModal } from '@/hooks/useEmailModal'
import EmailModal from './EmailModal'

import { useEffect, useState } from 'react'

export default function ResultsPanel({ job }: { job: JobStatusResponse }) {
  const sizeLabel = job.total_size_kb ? prettyBytes(job.total_size_kb) : '—'
  const [isPro, setIsPro] = useState(false)
  const { isOpen, getEmail, handleSubmit: handleEmailSubmit, handleClose } = useEmailModal()

  useEffect(() => {
    fetch('/api/entitlement', { cache: 'no-store' })
      .then(r => r.json())
      .then(j => setIsPro(j?.plan === 'pro'))
      .catch(() => setIsPro(false))
  }, [])

  const handleUpgradeClick = async () => {
    const email = await getEmail()
    if (!email) return

    const checkoutUrl = buildCheckoutUrl(email, 'results')
    if (checkoutUrl === '#') {
      alert('Checkout not configured. Please contact support.')
      return
    }

    try {
      window.dispatchEvent(new CustomEvent('upgrade_click', {
        detail: { source: 'results', email }
      }))
    } catch {}

    window.open(checkoutUrl, '_blank', 'noopener,noreferrer')
  }
  return (
    <section className="space-y-3">
      <div className="grid grid-cols-2 gap-3">
        <div className="border border-terminal-border p-3 bg-terminal-panel">
          <div className="text-sm mb-1">llms.txt</div>
          <div className="text-xs opacity-70 mb-2">Optimized summary • {sizeLabel}</div>
          {job.llm_txt_url ? (
            <a
              className="px-3 py-1 border border-terminal-border inline-block"
              href={`/v1/generations/${job.job_id}/download/llm.txt?raw=1`}
            >download</a>
          ) : (
            <button disabled className="px-3 py-1 border border-terminal-border opacity-50">download</button>
          )}
        </div>
        <div className="border border-terminal-border p-3 bg-terminal-panel">
          <div className="text-sm mb-1">llms-full.txt</div>
          <div className="text-xs opacity-70 mb-2">Complete version</div>
          {job.llms_full_txt_url ? (
            <a
              className="px-3 py-1 border border-terminal-border inline-block"
              href={`/v1/generations/${job.job_id}/download/llms-full.txt?raw=1`}
            >download</a>
          ) : (
            <button disabled className="px-3 py-1 border border-terminal-border opacity-50">download</button>
          )}
        </div>
      </div>
      <PreviewTabs job={job} />
      {!isPro && (
      <div className="border border-terminal-border bg-terminal-panel p-3 text-sm">
        <div className="mb-1">Get more with the full plan:</div>
        <ul className="list-disc list-inside opacity-80">
          <li>Faster queue and more pages</li>
          <li>Full llms-full.txt access</li>
          <li>Priority help for tricky sites</li>
        </ul>
        <div className="mt-2">
          <button
            className="px-3 py-1 inline-block border border-terminal-border hover:border-terminal-teal"
            onClick={handleUpgradeClick}
          >
            Upgrade — unlimited generations
          </button>
        </div>
      </div>
      )}
      <EmailModal isOpen={isOpen} onClose={handleClose} onSubmit={handleEmailSubmit} />
    </section>
  )
}
