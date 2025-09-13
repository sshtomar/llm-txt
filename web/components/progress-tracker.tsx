'use client'

import { motion } from 'framer-motion'
import { useEffect, useState } from 'react'

interface ProgressTrackerProps {
  progress: {
    state: string
    message: string
    current?: number
    total?: number
    details?: {
      pagesProcessed?: number
      contentExtracted?: number
      currentUrl?: string
      estimatedSize?: number
    }
  }
}

export function ProgressTracker({ progress }: ProgressTrackerProps) {
  const [logs, setLogs] = useState<string[]>([])
  
  useEffect(() => {
    if (progress.message) {
      setLogs(prev => [...prev.slice(-9), progress.message])
    }
  }, [progress.message])

  const getProgressPercentage = () => {
    if (progress.current && progress.total) {
      return (progress.current / progress.total) * 100
    }
    
    switch (progress.state) {
      case 'initializing': return 10
      case 'crawling': return 40
      case 'processing': return 70
      case 'composing': return 90
      case 'complete': return 100
      default: return 0
    }
  }

  const getStateLabel = () => {
    switch (progress.state) {
      case 'initializing': return 'Initializing'
      case 'crawling': return 'Crawling Pages'
      case 'processing': return 'Processing Content'
      case 'composing': return 'Composing LLM.txt'
      case 'complete': return 'Complete'
      default: return 'Working'
    }
  }

  return (
    <div className="terminal-card space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-bold">{getStateLabel()}</h3>
        <span className="text-sm">
          {progress.current && progress.total 
            ? `${progress.current}/${progress.total}`
            : `${Math.round(getProgressPercentage())}%`
          }
        </span>
      </div>

      <div className="progress-bar">
        <motion.div
          className="progress-bar-fill"
          initial={{ width: 0 }}
          animate={{ width: `${getProgressPercentage()}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
        />
      </div>

      {progress.details && (
        <div className="grid grid-cols-2 gap-2 text-sm">
          {progress.details.pagesProcessed !== undefined && (
            <div>
              <span className="text-terminal-green/70">Pages:</span>{' '}
              {progress.details.pagesProcessed}
            </div>
          )}
          {progress.details.contentExtracted !== undefined && (
            <div>
              <span className="text-terminal-green/70">Extracted:</span>{' '}
              {Math.round(progress.details.contentExtracted / 1024)}KB
            </div>
          )}
          {progress.details.estimatedSize !== undefined && (
            <div>
              <span className="text-terminal-green/70">Est. Size:</span>{' '}
              {Math.round(progress.details.estimatedSize / 1024)}KB
            </div>
          )}
        </div>
      )}

      <div className="bg-black p-3 rounded border border-terminal-green/30 max-h-32 overflow-y-auto">
        <div className="space-y-1 text-xs">
          {logs.map((log, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="text-terminal-green/80"
            >
              <span className="text-terminal-cyan">{'>'}</span> {log}
            </motion.div>
          ))}
          <span className="blink">_</span>
        </div>
      </div>

      {progress.details?.currentUrl && (
        <div className="text-xs text-terminal-green/60 truncate">
          Processing: {progress.details.currentUrl}
        </div>
      )}
    </div>
  )
}