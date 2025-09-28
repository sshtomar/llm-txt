"use client"
import { useEffect, useState } from 'react'

export default function Header() {
  const [isPro, setIsPro] = useState(false)
  useEffect(() => {
    fetch('/api/entitlement', { cache: 'no-store' })
      .then(r => r.json())
      .then(j => setIsPro(j?.plan === 'pro'))
      .catch(() => setIsPro(false))
  }, [])
  const checkout = (process.env.NEXT_PUBLIC_CHECKOUT_URL || '#') + (process.env.NEXT_PUBLIC_CHECKOUT_URL ? '&source=header' : '')
  return (
    <header className="border-b border-terminal-border bg-[var(--panel)]">
      <div className="mx-auto max-w-6xl px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="h-6 w-1.5 bg-terminal-teal" />
          <h1 className="text-xl tracking-tight">llms.txt generator</h1>
        </div>
        {!isPro && (
        <a
          href={checkout}
          target="_blank"
          rel="noreferrer"
          onClick={() => {
            try { window.dispatchEvent(new CustomEvent('upgrade_click', { detail: { source: 'header' } })) } catch {}
          }}
          className="px-3 py-1 text-xs border border-terminal-border hover:border-terminal-teal"
        >
          Upgrade
        </a>
        )}
      </div>
    </header>
  )
}
