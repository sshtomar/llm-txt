'use client'

import { useState, useEffect } from 'react'

export function Header() {
  const [theme, setTheme] = useState<'dark' | 'light'>('dark')
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    const stored = localStorage.getItem('theme') as 'dark' | 'light' | null
    if (stored) {
      setTheme(stored)
      document.documentElement.classList.toggle('dark', stored === 'dark')
    } else {
      document.documentElement.classList.add('dark')
    }
  }, [])

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark'
    setTheme(newTheme)
    localStorage.setItem('theme', newTheme)
    document.documentElement.classList.toggle('dark', newTheme === 'dark')
  }

  if (!mounted) {
    return (
      <header className="border-b border-terminal-green/30 bg-terminal-darkBg">
        <nav className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-2xl font-bold text-terminal-green">{'>'}_</span>
            <h1 className="text-xl font-bold">LLM.txt Generator</h1>
          </div>
        </nav>
      </header>
    )
  }

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