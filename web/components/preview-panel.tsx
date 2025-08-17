'use client'

import { useState } from 'react'
import { Copy, Download, Check, ExternalLink } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { downloadResult } from '@/lib/api'

interface PreviewPanelProps {
  content: string
  jobId: string
  showFullVersion?: boolean
}

export function PreviewPanel({
  content,
  jobId,
  showFullVersion,
}: PreviewPanelProps) {
  const [activeTab, setActiveTab] = useState<'llm.txt' | 'llms-full.txt'>(
    'llm.txt'
  )
  const [copied, setCopied] = useState(false)
  const [downloading, setDownloading] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const handleDownload = async () => {
    if (!jobId) return

    try {
      setDownloading(true)

      // Fetch actual generated content from the backend
      const result = await downloadResult(jobId, activeTab)
      const blob = new Blob([result.content], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = activeTab
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Download failed:', err)
    } finally {
      setDownloading(false)
    }
  }

  const lines = content.split('\n')
  const maxLines = 25
  const displayLines = lines.slice(0, maxLines)
  const isExpanded = lines.length <= maxLines

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-base">Preview</CardTitle>
            <CardDescription>Generated content preview</CardDescription>
          </div>

          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleCopy}
              disabled={copied}
            >
              {copied ? (
                <Check className="h-4 w-4" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={handleDownload}
              disabled={downloading}
            >
              <Download className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Tabs */}
        {showFullVersion && (
          <div className="flex space-x-1 rounded-md bg-muted p-1">
            <button
              onClick={() => setActiveTab('llm.txt')}
              className={`rounded-sm px-3 py-1 text-sm transition-colors ${
                activeTab === 'llm.txt'
                  ? 'bg-background text-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              llm.txt
            </button>
            <button
              onClick={() => setActiveTab('llms-full.txt')}
              className={`rounded-sm px-3 py-1 text-sm transition-colors ${
                activeTab === 'llms-full.txt'
                  ? 'bg-background text-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              llms-full.txt
            </button>
          </div>
        )}
      </CardHeader>

      <CardContent className="pt-0">
        <div className="relative">
          <pre className="code-preview max-h-[32rem] overflow-x-auto overflow-y-auto rounded-md bg-muted/50 p-4 text-sm">
            <code>
              {displayLines.map((line, index) => (
                <div key={index} className="line">
                  {line || ' '}
                </div>
              ))}
              {!isExpanded && (
                <div className="italic text-muted-foreground">
                  ... and {lines.length - maxLines} more lines
                </div>
              )}
            </code>
          </pre>

          {/* Fade overlay for long content */}
          {!isExpanded && (
            <div className="pointer-events-none absolute bottom-0 left-0 right-0 h-12 bg-gradient-to-t from-muted/50 to-transparent" />
          )}
        </div>

        {jobId && (
          <div className="mt-4 flex items-center justify-between text-sm text-muted-foreground">
            <span>Job ID: {jobId.slice(0, 8)}...</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => window.open(`/status/${jobId}`, '_blank')}
            >
              View Full Status
              <ExternalLink className="ml-1 h-3 w-3" />
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
