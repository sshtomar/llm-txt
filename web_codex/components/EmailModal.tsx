"use client"
import { useState, useEffect, useRef } from 'react'

type Props = {
  isOpen: boolean
  onClose: () => void
  onSubmit: (email: string) => void
}

export default function EmailModal({ isOpen, onClose, onSubmit }: Props) {
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (isOpen) {
      // Focus input when modal opens
      setTimeout(() => inputRef.current?.focus(), 100)
      // Clear previous state
      setEmail('')
      setError('')
    }
  }, [isOpen])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = email.trim()

    if (!trimmed) {
      setError('Email is required')
      return
    }

    if (!validateEmail(trimmed)) {
      setError('Please enter a valid email address')
      return
    }

    onSubmit(trimmed)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose()
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/80"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative z-10 w-full max-w-md mx-4">
        <div className="border-2 border-terminal-border bg-[var(--bg)] p-6">
          {/* Header */}
          <div className="mb-4">
            <div className="flex items-center gap-2 mb-2">
              <div className="h-3 w-3 bg-terminal-teal" />
              <h2 className="text-lg font-mono">Enter your email</h2>
            </div>
            <p className="text-sm opacity-70">
              You'll receive receipts and access at this address
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} onKeyDown={handleKeyDown}>
            <div className="mb-4">
              <input
                ref={inputRef}
                type="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value)
                  setError('')
                }}
                placeholder="user@example.com"
                className="w-full px-4 py-3 border border-terminal-border bg-[var(--bg)] focus:outline-none focus:border-terminal-teal font-mono"
                autoComplete="email"
              />
              {error && (
                <div className="mt-2 text-sm text-terminal-red">
                  {error}
                </div>
              )}
            </div>

            {/* Buttons */}
            <div className="flex gap-3">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 px-4 py-2 border border-terminal-border hover:border-terminal-teal transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="flex-1 px-4 py-2 bg-terminal-teal text-black border border-terminal-teal hover:bg-terminal-teal/90 transition-colors"
              >
                Continue
              </button>
            </div>
          </form>

          {/* Keyboard hint */}
          <div className="mt-4 text-xs opacity-50 text-center">
            Press <kbd className="px-1 border border-terminal-border">ESC</kbd> to cancel
          </div>
        </div>
      </div>
    </div>
  )
}

function validateEmail(email: string): boolean {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return re.test(email)
}
