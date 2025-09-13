"use client"

export default function Header() {
  return (
    <header className="border-b border-terminal-border bg-[var(--panel)]">
      <div className="mx-auto max-w-6xl px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="h-6 w-1.5 bg-terminal-teal" />
          <h1 className="text-xl tracking-tight">llm.txt generator</h1>
        </div>
        <nav className="flex items-center gap-4 text-sm">
          <a
            className="hover:underline"
            href="https://github.com/sshtomar/llm-txt"
            target="_blank"
            rel="noreferrer noopener"
          >
            GitHub
          </a>
        </nav>
      </div>
    </header>
  )
}
