"use client"
import { useState, useCallback } from 'react'

/**
 * Hook to manage email modal state and localStorage
 */
export function useEmailModal() {
  const [isOpen, setIsOpen] = useState(false)
  const [resolveCallback, setResolveCallback] = useState<((email: string | null) => void) | null>(null)

  const getEmail = useCallback((): Promise<string | null> => {
    // Check if email already stored
    try {
      const stored = localStorage.getItem('llmxt_email')
      if (stored && validateEmail(stored)) {
        return Promise.resolve(stored)
      }
    } catch {}

    // Return promise that resolves when modal submits
    return new Promise((resolve) => {
      setResolveCallback(() => resolve)
      setIsOpen(true)
    })
  }, [])

  const handleSubmit = useCallback((email: string) => {
    // Store for future use
    try {
      localStorage.setItem('llmxt_email', email)
    } catch {}

    setIsOpen(false)
    if (resolveCallback) {
      resolveCallback(email)
      setResolveCallback(null)
    }
  }, [resolveCallback])

  const handleClose = useCallback(() => {
    setIsOpen(false)
    if (resolveCallback) {
      resolveCallback(null)
      setResolveCallback(null)
    }
  }, [resolveCallback])

  return {
    isOpen,
    getEmail,
    handleSubmit,
    handleClose,
  }
}

function validateEmail(email: string): boolean {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return re.test(email)
}
