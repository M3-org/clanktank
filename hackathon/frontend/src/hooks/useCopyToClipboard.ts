import { useState } from 'react'
import { toast } from 'react-hot-toast'
import { TOAST_MESSAGES } from '../lib/constants'

export const useCopyToClipboard = () => {
  const [copied, setCopied] = useState(false)
  
  const copyToClipboard = async (text: string, successMessage = TOAST_MESSAGES.ADDRESS_COPIED) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      toast.success(successMessage, { duration: 1500 })
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      toast.error(TOAST_MESSAGES.COPY_FAILED)
    }
  }
  
  return { copied, copyToClipboard }
}

/**
 * Enhanced version that supports multiple copy states
 */
export function useMultipleCopyStates() {
  const [copiedStates, setCopiedStates] = useState<Record<string, boolean>>({})

  const copyToClipboard = async (text: string, key: string, successMessage: string = TOAST_MESSAGES.ADDRESS_COPIED) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedStates(prev => ({ ...prev, [key]: true }))
      toast.success(successMessage, { duration: 1500 })
      setTimeout(() => {
        setCopiedStates(prev => ({ ...prev, [key]: false }))
      }, 2000)
    } catch (err) {
      toast.error(TOAST_MESSAGES.COPY_FAILED)
    }
  }

  const isCopied = (key: string) => copiedStates[key] || false

  return { copyToClipboard, isCopied }
}