'use client'

import { useState } from 'react'
import Link from 'next/link'
import { FileText } from 'lucide-react'
import { ThemeToggle } from './theme-toggle'
import { CreditsDisplay } from './credits-display'
import { UpgradeModal } from './upgrade-modal'

export function Navigation() {
  const [showUpgradeModal, setShowUpgradeModal] = useState(false)

  return (
    <>
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 items-center">
          <div className="mr-8 flex items-center">
            <Link href="/" className="flex items-center space-x-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500">
                <FileText className="h-5 w-5 text-white" />
              </div>
              <span className="text-xl font-bold">LLM-TXT</span>
            </Link>
          </div>
          
          <div className="ml-auto flex items-center space-x-4">
            <CreditsDisplay onUpgrade={() => setShowUpgradeModal(true)} />
            <ThemeToggle />
          </div>
        </div>
      </header>

      <UpgradeModal
        open={showUpgradeModal}
        onOpenChange={setShowUpgradeModal}
      />
    </>
  )
}