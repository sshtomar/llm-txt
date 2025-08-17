'use client'

import { useState, useRef } from 'react'
import { ArrowRight, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { GeneratorCard, GeneratorCardRef } from '@/components/generator-card'
import { UpgradeModal } from '@/components/upgrade-modal'

export function Hero() {
  const [url, setUrl] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [showUpgradeModal, setShowUpgradeModal] = useState(false)
  const generatorCardRef = useRef<GeneratorCardRef>(null)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (url && generatorCardRef.current) {
      generatorCardRef.current.triggerGenerate()
    }
  }

  return (
    <>
      <section className="py-20 lg:py-32">
        <div className="container">
          <div className="mx-auto max-w-4xl">
            <div className="mb-12 text-center">
              <div className="mb-4 inline-flex items-center rounded-full border bg-muted px-3 py-1 text-sm">
                <Sparkles className="mr-2 h-3 w-3 text-blue-600" />
                Make your site AI-friendly in under 90 seconds
              </div>
              
              <h1 className="mb-6 text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
                Generate <span className="gradient-text">llm.txt</span> from any docs
              </h1>
              
              <p className="mx-auto max-w-2xl text-lg text-muted-foreground">
                Convert documentation sites into clean, structured text files optimized for
                Large Language Models. Perfect for training, context, and retrieval.
              </p>
            </div>

            {/* URL Input Form */}
            <form onSubmit={handleSubmit} className="mb-8">
              <div className="flex gap-2">
                <Input
                  type="url"
                  placeholder="https://docs.example.com"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  disabled={isGenerating}
                  className="flex-1 text-base"
                  required
                />
                <Button
                  type="submit"
                  size="lg"
                  disabled={!url || isGenerating}
                  className="bg-gradient-to-r from-blue-600 to-cyan-600 text-white hover:from-blue-700 hover:to-cyan-700"
                >
                  {isGenerating ? (
                    'Generating...'
                  ) : (
                    <>
                      Generate
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </>
                  )}
                </Button>
              </div>
              <p className="mt-2 text-sm text-muted-foreground">
                Enter a documentation URL to get started. We'll crawl and convert it for you.
              </p>
            </form>

            {/* Generator Card */}
            <GeneratorCard
              ref={generatorCardRef}
              url={url}
              isGenerating={isGenerating}
              onGeneratingChange={setIsGenerating}
              onNeedUpgrade={() => setShowUpgradeModal(true)}
            />
          </div>
        </div>
      </section>

      <UpgradeModal
        open={showUpgradeModal}
        onOpenChange={setShowUpgradeModal}
      />
    </>
  )
}