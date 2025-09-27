import Link from 'next/link'
import UrlForm from '@/components/UrlForm'
import type { GenerationResponse } from '@/types/api'

export default function Hero({ onCreated }: { onCreated: (res: GenerationResponse) => void }) {
  return (
    <section className="mx-auto max-w-6xl px-6 pt-10 pb-12">
      <div className="w-full">
        <h1 className="text-3xl md:text-4xl leading-tight mb-3">
          Crawl docs. Compose concise <span className="text-terminal-teal">llms.txt</span>.
        </h1>
        <p className="opacity-80 mb-5 max-w-prose">
          Politely crawls documentation, extracts clean Markdown, and composes an optimized `llms.txt` for LLM context windows — fast, deterministic, and robots-aware.
        </p>
        <div className="mb-4" id="generate">
          <UrlForm onCreated={onCreated} />
        </div>
        <div className="text-xs opacity-70 flex flex-wrap items-center gap-4">
          <div>• Robots-aware</div>
          <div>• Optimized size budget</div>
          <div>• Live progress</div>
        </div>
      </div>
    </section>
  )
}
