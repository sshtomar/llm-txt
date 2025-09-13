export default function HowItWorksGrid() {
  const steps = [
    {
      title: '1) Paste a docs URL',
      body: 'We validate and normalize the URL, then check robots.txt and discover sitemaps (EN‑only).',
    },
    {
      title: '2) Crawl and extract',
      body: 'Polite, rate‑limited crawl. Markdown‑first extraction that strips navigation and boilerplate; preserves code.',
    },
    {
      title: '3) Compose and download',
      body: 'Prioritize high‑signal sections, apply a size budget, and produce llms.txt (optional llms‑full.txt).',
    },
  ] as const

  return (
    <section className="mx-auto max-w-6xl px-6 pb-8">
      <h2 className="mb-4">How it works</h2>
      <div className="grid md:grid-cols-3 gap-4">
        {steps.map((s) => (
          <div key={s.title} className="vp-card border border-[var(--border)] bg-[var(--panel)] p-4">
            <div className="text-sm font-medium text-[var(--accent)] mb-1">{s.title}</div>
            <div className="text-sm text-[var(--fg)] opacity-80">{s.body}</div>
          </div>
        ))}
      </div>
    </section>
  )
}

