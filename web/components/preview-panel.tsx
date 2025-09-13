'use client'

import { useState } from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { saveAs } from 'file-saver'
import { motion, AnimatePresence } from 'framer-motion'
import { GenerationResult } from '@/lib/types'

interface PreviewPanelProps {
  result: GenerationResult
}

export function PreviewPanel({ result }: PreviewPanelProps) {
  const [activeTab, setActiveTab] = useState<'llm' | 'full'>('llm')
  const [viewMode, setViewMode] = useState<'raw' | 'rendered'>('raw')
  const [searchQuery, setSearchQuery] = useState('')
  const [copied, setCopied] = useState(false)

  const activeContent = activeTab === 'llm' ? result.llmTxt : result.llmsFullTxt
  const activeFilename = activeTab === 'llm' ? 'llm.txt' : 'llms-full.txt'

  const handleDownload = () => {
    if (!activeContent) return
    const blob = new Blob([activeContent.content], { type: 'text/plain;charset=utf-8' })
    saveAs(blob, activeFilename)
  }

  const handleCopy = async () => {
    if (!activeContent) return
    await navigator.clipboard.writeText(activeContent.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const getHighlightedContent = () => {
    if (!activeContent) return ''
    if (!searchQuery) return activeContent.content
    
    const regex = new RegExp(`(${searchQuery})`, 'gi')
    return activeContent.content.replace(regex, '**$1**')
  }

  const estimateTokens = (text: string) => {
    return Math.round(text.length / 4)
  }

  if (!result.llmTxt) return null

  return (
    <div className="terminal-card space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex space-x-4">
          <button
            onClick={() => setActiveTab('llm')}
            className={`px-3 py-1 border transition-colors ${
              activeTab === 'llm'
                ? 'border-terminal-green bg-terminal-green text-black'
                : 'border-terminal-green/30 hover:border-terminal-green'
            }`}
          >
            llm.txt ({Math.round(result.llmTxt.size / 1024)}KB)
          </button>
          {result.llmsFullTxt && (
            <button
              onClick={() => setActiveTab('full')}
              className={`px-3 py-1 border transition-colors ${
                activeTab === 'full'
                  ? 'border-terminal-green bg-terminal-green text-black'
                  : 'border-terminal-green/30 hover:border-terminal-green'
              }`}
            >
              llms-full.txt ({Math.round(result.llmsFullTxt.size / 1024)}KB)
            </button>
          )}
        </div>

        <div className="flex space-x-2">
          <button
            onClick={() => setViewMode(viewMode === 'raw' ? 'rendered' : 'raw')}
            className="px-2 py-1 text-sm border border-terminal-green/30 hover:border-terminal-green transition-colors"
          >
            {viewMode === 'raw' ? 'Raw' : 'Rendered'}
          </button>
        </div>
      </div>

      {activeContent && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm text-terminal-green/70">
            <div className="flex space-x-4">
              <span>{activeContent.content.split('\n').length} lines</span>
              <span>{Math.round(activeContent.size / 1024)}KB</span>
              <span>~{estimateTokens(activeContent.content).toLocaleString()} tokens</span>
            </div>
            <div className="flex space-x-2">
              <button
                onClick={handleCopy}
                className="px-3 py-1 border border-terminal-green/30 hover:border-terminal-green transition-colors"
              >
                {copied ? 'Copied!' : 'Copy'}
              </button>
              <button
                onClick={handleDownload}
                className="px-3 py-1 border border-terminal-green bg-terminal-green text-black hover:bg-transparent hover:text-terminal-green transition-colors"
              >
                Download
              </button>
            </div>
          </div>

          <div className="relative">
            <input
              type="text"
              placeholder="Search in file..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="terminal-input w-full mb-2"
            />
          </div>

          <div className="bg-black border border-terminal-green/30 rounded-lg overflow-hidden">
            <div className="max-h-96 overflow-y-auto p-4">
              {viewMode === 'raw' ? (
                <pre className="text-xs text-terminal-green/90 whitespace-pre-wrap">
                  {getHighlightedContent()}
                </pre>
              ) : (
                <SyntaxHighlighter
                  language="markdown"
                  style={vscDarkPlus}
                  customStyle={{
                    background: 'transparent',
                    fontSize: '0.75rem',
                    margin: 0,
                    padding: 0,
                  }}
                  showLineNumbers
                >
                  {activeContent.content}
                </SyntaxHighlighter>
              )}
            </div>
          </div>

          {result.stats && (
            <div className="grid grid-cols-2 gap-2 text-xs text-terminal-green/70">
              <div>Pages crawled: {result.stats.pagesCrawled}</div>
              <div>Content extracted: {Math.round(result.stats.contentExtracted / 1024)}KB</div>
              <div>Compression ratio: {result.stats.compressionRatio}%</div>
              <div>Generation time: {result.stats.generationTime}s</div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}