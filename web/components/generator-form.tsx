'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

interface GeneratorFormProps {
  onSubmit: (url: string, options: any) => void
  isLoading: boolean
}

export function GeneratorForm({ onSubmit, isLoading }: GeneratorFormProps) {
  const [url, setUrl] = useState('')
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [depth, setDepth] = useState(2)
  const [maxSize, setMaxSize] = useState(800)
  const [includePatterns, setIncludePatterns] = useState('')
  const [excludePatterns, setExcludePatterns] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!url) return

    onSubmit(url, {
      depth,
      maxSize,
      includePatterns: includePatterns ? includePatterns.split(',').map(p => p.trim()) : [],
      excludePatterns: excludePatterns ? excludePatterns.split(',').map(p => p.trim()) : [],
    })
  }

  const isValidUrl = (str: string) => {
    try {
      new URL(str)
      return true
    } catch {
      return false
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="terminal-card space-y-4">
        <div>
          <label htmlFor="url" className="block text-sm mb-2">
            Documentation URL
          </label>
          <input
            id="url"
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://docs.example.com"
            className="terminal-input w-full"
            required
            disabled={isLoading}
          />
          {url && !isValidUrl(url) && (
            <p className="text-terminal-red text-sm mt-1">Please enter a valid URL</p>
          )}
        </div>

        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="text-sm hover:text-terminal-cyan transition-colors"
        >
          {showAdvanced ? '▼' : '▶'} Advanced Options
        </button>

        <AnimatePresence>
          {showAdvanced && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="space-y-4 overflow-hidden"
            >
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="depth" className="block text-sm mb-2">
                    Crawl Depth
                  </label>
                  <input
                    id="depth"
                    type="number"
                    min="1"
                    max="5"
                    value={depth}
                    onChange={(e) => setDepth(Number(e.target.value))}
                    className="terminal-input w-full"
                    disabled={isLoading}
                  />
                </div>
                <div>
                  <label htmlFor="maxSize" className="block text-sm mb-2">
                    Max Size (KB)
                  </label>
                  <input
                    id="maxSize"
                    type="number"
                    min="100"
                    max="5000"
                    value={maxSize}
                    onChange={(e) => setMaxSize(Number(e.target.value))}
                    className="terminal-input w-full"
                    disabled={isLoading}
                  />
                </div>
              </div>

              <div>
                <label htmlFor="include" className="block text-sm mb-2">
                  Include Patterns (comma-separated)
                </label>
                <input
                  id="include"
                  type="text"
                  value={includePatterns}
                  onChange={(e) => setIncludePatterns(e.target.value)}
                  placeholder="/api/*, /guides/*"
                  className="terminal-input w-full"
                  disabled={isLoading}
                />
              </div>

              <div>
                <label htmlFor="exclude" className="block text-sm mb-2">
                  Exclude Patterns (comma-separated)
                </label>
                <input
                  id="exclude"
                  type="text"
                  value={excludePatterns}
                  onChange={(e) => setExcludePatterns(e.target.value)}
                  placeholder="/changelog/*, /blog/*"
                  className="terminal-input w-full"
                  disabled={isLoading}
                />
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <button
          type="submit"
          disabled={isLoading || !url || !isValidUrl(url)}
          className="terminal-button w-full disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <span className="flex items-center justify-center">
              <span className="animate-pulse">Generating...</span>
            </span>
          ) : (
            'Generate LLM.txt'
          )}
        </button>
      </div>
    </form>
  )
}