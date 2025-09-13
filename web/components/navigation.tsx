'use client'

import { useTheme } from './theme-provider'

export function Navigation() {
  const { theme, toggleTheme } = useTheme()

  return (
    <header className="border-b border-terminal-green/30 bg-terminal-darkBg">
      <nav className="container mx-auto px-4 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="text-2xl font-bold text-terminal-green">{'>'}_</span>
          <h1 className="text-xl font-bold">LLM.txt Generator</h1>
        </div>
        
        <div className="flex items-center space-x-6">
          <a 
            href="https://github.com/yourusername/llm-txt"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-terminal-cyan transition-colors"
          >
            GitHub
          </a>
          <a 
            href="/docs"
            className="hover:text-terminal-cyan transition-colors"
          >
            Docs
          </a>
          <button
            onClick={toggleTheme}
            className="px-3 py-1 border border-terminal-green hover:bg-terminal-green hover:text-black transition-colors"
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? '☀' : '☾'}
          </button>
        </div>
      </nav>
    </header>
  )
}