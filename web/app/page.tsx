'use client'

import { useState } from 'react'
import { GeneratorForm } from '@/components/generator-form'
import { ProgressTracker } from '@/components/progress-tracker'
import { PreviewPanel } from '@/components/preview-panel'
import { GenerationResult } from '@/lib/types'

export default function Home() {
  const [isGenerating, setIsGenerating] = useState(false)
  const [progress, setProgress] = useState<any>(null)
  const [result, setResult] = useState<GenerationResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (url: string, options: any) => {
    setIsGenerating(true)
    setError(null)
    setResult(null)
    setProgress({ state: 'initializing', message: 'Parsing robots.txt, discovering sitemap...' })

    try {
      const response = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, ...options }),
      })

      if (!response.ok) {
        throw new Error('Generation failed')
      }

      const data = await response.json()
      
      // Start polling for progress
      pollProgress(data.jobId)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
      setIsGenerating(false)
    }
  }

  const pollProgress = async (jobId: string) => {
    const eventSource = new EventSource(`/api/progress/${jobId}`)

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      if (data.state === 'complete') {
        setResult(data.result)
        setIsGenerating(false)
        eventSource.close()
      } else if (data.state === 'error') {
        setError(data.message)
        setIsGenerating(false)
        eventSource.close()
      } else {
        setProgress(data)
      }
    }

    eventSource.onerror = () => {
      setError('Connection lost')
      setIsGenerating(false)
      eventSource.close()
    }
  }

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold typing-effect inline-block">
          Generate Optimized LLM Context Files
        </h1>
        <p className="text-terminal-green/70 text-lg">
          Transform documentation sites into compact, AI-ready text files
        </p>
      </div>

      <div className="grid lg:grid-cols-2 gap-8">
        <div className="space-y-6">
          <GeneratorForm onSubmit={handleSubmit} isLoading={isGenerating} />
          
          {isGenerating && progress && (
            <ProgressTracker progress={progress} />
          )}

          {error && (
            <div className="terminal-card border-terminal-red text-terminal-red">
              <p className="font-bold mb-2">Error:</p>
              <p>{error}</p>
            </div>
          )}
        </div>

        <div>
          {result && (
            <PreviewPanel result={result} />
          )}
        </div>
      </div>
    </div>
  )
}