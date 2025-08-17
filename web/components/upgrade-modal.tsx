'use client'

import { useState } from 'react'
import { X, Crown, Check, Zap, Globe, Download } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { upgradeToPro } from '@/lib/credits'

interface UpgradeModalProps {
  isOpen: boolean
  onClose: () => void
  onUpgrade?: () => void
}

export function UpgradeModal({
  isOpen,
  onClose,
  onUpgrade,
}: UpgradeModalProps) {
  const [isUpgrading, setIsUpgrading] = useState(false)

  if (!isOpen) return null

  const handleUpgrade = async () => {
    setIsUpgrading(true)
    try {
      // Simulate upgrade process
      await new Promise((resolve) => setTimeout(resolve, 1000))
      upgradeToPro()
      onUpgrade?.()
      onClose()
    } catch (error) {
      console.error('Upgrade failed:', error)
    } finally {
      setIsUpgrading(false)
    }
  }

  const handleSignup = () => {
    // For demo purposes, just upgrade to pro
    handleUpgrade()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <Card className="relative w-full max-w-2xl">
        <Button
          variant="ghost"
          size="sm"
          onClick={onClose}
          className="absolute right-4 top-4 z-10"
        >
          <X className="h-4 w-4" />
        </Button>

        <CardHeader className="pb-6">
          <div className="flex items-center gap-3">
            <div className="rounded-full bg-gradient-to-r from-blue-600 to-purple-600 p-2">
              <Crown className="h-5 w-5 text-white" />
            </div>
            <div>
              <CardTitle className="text-xl">Upgrade to Pro</CardTitle>
              <CardDescription>
                Unlock unlimited generations and premium features
              </CardDescription>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Features */}
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="flex items-start gap-3">
              <div className="rounded-full bg-green-100 p-1">
                <Check className="h-3 w-3 text-green-600" />
              </div>
              <div>
                <h4 className="font-medium">Unlimited Generations</h4>
                <p className="text-sm text-muted-foreground">
                  Generate as many llm.txt files as you need
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="rounded-full bg-green-100 p-1">
                <Check className="h-3 w-3 text-green-600" />
              </div>
              <div>
                <h4 className="font-medium">Priority Processing</h4>
                <p className="text-sm text-muted-foreground">
                  Faster generation times and priority queue access
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="rounded-full bg-green-100 p-1">
                <Check className="h-3 w-3 text-green-600" />
              </div>
              <div>
                <h4 className="font-medium">Larger Sites</h4>
                <p className="text-sm text-muted-foreground">
                  Process documentation sites up to 10,000 pages
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="rounded-full bg-green-100 p-1">
                <Check className="h-3 w-3 text-green-600" />
              </div>
              <div>
                <h4 className="font-medium">API Access</h4>
                <p className="text-sm text-muted-foreground">
                  Integrate llm.txt generation into your workflow
                </p>
              </div>
            </div>
          </div>

          {/* Pricing */}
          <div className="rounded-lg border bg-gradient-to-r from-blue-50 to-purple-50 p-4">
            <div className="text-center">
              <div className="mb-2">
                <span className="text-3xl font-bold">$9</span>
                <span className="text-muted-foreground">/month</span>
              </div>
              <p className="text-sm text-muted-foreground">
                Cancel anytime • 7-day free trial
              </p>
            </div>
          </div>

          {/* CTA Buttons */}
          <div className="space-y-3">
            <Button
              onClick={handleSignup}
              disabled={isUpgrading}
              className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:from-blue-700 hover:to-purple-700"
            >
              {isUpgrading ? (
                <>
                  <Zap className="mr-2 h-4 w-4 animate-spin" />
                  Upgrading...
                </>
              ) : (
                <>
                  <Crown className="mr-2 h-4 w-4" />
                  Start Free Trial
                </>
              )}
            </Button>

            <div className="text-center">
              <Button
                variant="ghost"
                onClick={onClose}
                className="text-muted-foreground"
              >
                Maybe later
              </Button>
            </div>
          </div>

          {/* Demo Notice */}
          <div className="rounded-lg bg-amber-50 p-3 text-center">
            <p className="text-sm text-amber-800">
              <strong>Demo Mode:</strong> This will instantly upgrade you to Pro
              for demonstration purposes
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
