'use client'

import { useState, useEffect } from 'react'
import { Crown, Zap } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { getCredits, UserCredits } from '@/lib/credits'

interface CreditsDisplayProps {
  onUpgrade?: () => void
}

export function CreditsDisplay({ onUpgrade }: CreditsDisplayProps) {
  const [credits, setCredits] = useState<UserCredits>({
    remaining: 3,
    total: 3,
    isPro: false,
  })

  useEffect(() => {
    const updateCredits = () => {
      setCredits(getCredits())
    }

    updateCredits()

    // Listen for storage changes to update credits across tabs
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'llm-txt-credits') {
        updateCredits()
      }
    }

    window.addEventListener('storage', handleStorageChange)

    // Also update on focus in case credits changed in another tab
    window.addEventListener('focus', updateCredits)

    return () => {
      window.removeEventListener('storage', handleStorageChange)
      window.removeEventListener('focus', updateCredits)
    }
  }, [])

  if (credits.isPro) {
    return (
      <div className="flex items-center gap-2 rounded-lg bg-gradient-to-r from-amber-50 to-orange-50 px-3 py-2 text-sm">
        <Crown className="h-4 w-4 text-amber-600" />
        <span className="font-medium text-amber-900">Pro</span>
        <span className="text-amber-700">Unlimited generations</span>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-2 rounded-lg bg-muted px-3 py-2 text-sm">
        <Zap className="h-4 w-4 text-blue-600" />
        <span className="font-medium text-foreground">
          {credits.remaining} credit{credits.remaining !== 1 ? 's' : ''} left
        </span>
      </div>

      {credits.remaining === 0 && (
        <Button
          onClick={onUpgrade}
          size="sm"
          className="bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:from-blue-700 hover:to-purple-700"
        >
          <Crown className="mr-1 h-3 w-3" />
          Upgrade to Pro
        </Button>
      )}

      {credits.remaining > 0 && credits.remaining <= 1 && (
        <Button
          onClick={onUpgrade}
          variant="outline"
          size="sm"
          className="border-blue-200 text-blue-700 hover:bg-blue-50"
        >
          <Crown className="mr-1 h-3 w-3" />
          Upgrade
        </Button>
      )}
    </div>
  )
}
