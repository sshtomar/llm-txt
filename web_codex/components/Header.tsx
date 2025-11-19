"use client"
import { useEffect, useState } from 'react'
import { handleUpgradeClick } from '@/lib/checkout'

export default function Header() {
  const [isPro, setIsPro] = useState(false)
  useEffect(() => {
    fetch('/api/entitlement', { cache: 'no-store' })
      .then(r => r.json())
      .then(j => setIsPro(j?.plan === 'pro'))
      .catch(() => setIsPro(false))
  }, [])

  const onUpgradeClick = (e: React.MouseEvent) => {
    e.preventDefault()
    handleUpgradeClick('header')
  }

  return (
    <header className="border-b border-terminal-border bg-[var(--panel)]">
      <div className="mx-auto max-w-6xl px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="h-6 w-1.5 bg-terminal-teal" />
          <h1 className="text-xl tracking-tight">llms.txt generator</h1>
        </div>
        {!isPro && (
          <div className="flex items-center gap-2">
            <button
              onClick={onUpgradeClick}
              className="px-3 py-1 text-xs border border-terminal-border hover:border-terminal-teal"
            >
              Upgrade
            </button>
            {process.env.NODE_ENV !== 'production' && (
              <a
                href="/upgrade/success"
                className="px-2 py-1 text-[11px] border border-dashed border-terminal-border opacity-70 hover:opacity-100"
                title="Dev-only: set a local Pro cookie"
              >
                Unlock Pro (dev)
              </a>
            )}
          </div>
        )}
      </div>
    </header>
  )
}
