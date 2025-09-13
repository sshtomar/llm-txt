export default function ValueProps() {
  const items = [
    {
      title: 'Stop copying and pasting docs into ChatGPT.',
      body:
        'Documentation sites are massive, messy, and built for humans — not LLMs. We crawl, clean, and compress them into context‑ready files.',
    },
    {
      title: 'Your LLM context windows are precious.',
      body:
        '2M tokens go fast when you paste entire sites. Get clean, prioritized content that fits your budget.',
    },
    {
      title: 'Respect the robots.',
      body:
        'We follow robots.txt, throttle politely, and never overwhelm servers. Professional crawling for professional developers.',
    },
  ] as const

  return (
    <section className="mx-auto max-w-6xl px-6 pb-8">
      <h2 className="mb-4">Why you need this</h2>
      <div className="grid md:grid-cols-3 gap-4">
        {items.map((it) => (
          <div key={it.title} className="vp-card border border-[var(--border)] bg-[var(--panel)] p-4">
            <div className="text-sm font-medium text-[var(--accent)] mb-1">{it.title}</div>
            <div className="text-sm text-[var(--fg)] opacity-80">{it.body}</div>
          </div>
        ))}
      </div>
    </section>
  )
}
