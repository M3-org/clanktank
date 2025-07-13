import { useState } from 'react'
import { X, Copy, Smartphone, Monitor, Check } from 'lucide-react'
import { Button } from './Button'
import { LeaderboardEntry, SubmissionSummary } from '../types'
import { buildVotingLink, generateCopyInstructions, isMobile, validateMemo } from '../utils/phantomLink'
import { toast } from 'react-hot-toast'

interface VoteModalProps {
  submission: SubmissionSummary | LeaderboardEntry
  onClose: () => void
}

export function VoteModal({ submission, onClose }: VoteModalProps) {
  const [amount, setAmount] = useState(1)
  const [customMemo, setCustomMemo] = useState('')
  const [copied, setCopied] = useState(false)
  const isOnMobile = isMobile()

  // Calculate vote weight using same formula as backend
  const voteWeight = Math.min(Math.log10(amount + 1) * 3, 10)
  const overflowTokens = Math.max(0, amount - 100)

  // Use custom memo if provided, otherwise fall back to submission ID
  const memoToUse = customMemo.trim() || submission.submission_id || submission.project_name.toLowerCase().replace(/\s+/g, '-')
  const phantomLink = buildVotingLink({ submissionId: memoToUse, amount })
  const copyInstructions = generateCopyInstructions({ submissionId: memoToUse, amount })

  const handleCopyInstructions = async () => {
    try {
      await navigator.clipboard.writeText(copyInstructions)
      setCopied(true)
      toast.success("Instructions copied!", { duration: 1500 })
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.log('Clipboard API failed:', copyInstructions)
      toast.error("Copy failed - please copy manually")
    }
  }

  const handlePhantomVote = () => {
    // Validate memo length
    const validation = validateMemo(memoToUse)
    if (!validation.valid) {
      toast.error(validation.error!)
      return
    }
    
    window.open(phantomLink, '_blank')
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto" aria-modal="true" role="dialog">
      <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
        {/* Backdrop */}
        <div 
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" 
          onClick={onClose}
          aria-hidden="true"
        />
        
        {/* Modal panel */}
        <div className="relative transform overflow-hidden rounded-lg bg-white dark:bg-gray-900 px-4 pb-4 pt-5 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg sm:p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Vote for {submission.project_name}
            </h3>
            <button
              onClick={onClose}
              className="rounded-md text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label="Close modal"
            >
              <X className="h-6 w-6" />
            </button>
          </div>

          {/* Current scores */}
          <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <div className="flex justify-between items-center">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">AI Score</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {('final_score' in submission ? submission.final_score : submission.avg_score)?.toFixed(1) || '—'}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Community Score</p>
                <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
                  {('community_score' in submission && submission.community_score) ? submission.community_score.toFixed(1) : "—"}
                </p>
              </div>
            </div>
          </div>

          {/* Amount slider */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Amount of ai16z to send
            </label>
            <input
              type="range"
              min="1"
              max="100"
              value={amount}
              onChange={(e) => setAmount(Number(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700 slider"
            />
            <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
              <span>1 ai16z</span>
              <span>{amount} ai16z</span>
              <span>100 ai16z</span>
            </div>
          </div>

          {/* Custom memo input */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Custom memo (optional, max 80 chars)
            </label>
            <input
              type="text"
              maxLength={80}
              value={customMemo}
              onChange={(e) => setCustomMemo(e.target.value)}
              placeholder={`Default: ${submission.submission_id || submission.project_name.toLowerCase().replace(/\s+/g, '-')}`}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
              <span>Leave empty to use project ID</span>
              <span>{customMemo.length}/80 characters</span>
            </div>
          </div>

          {/* Vote feedback */}
          <div className="mb-6 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <div className="text-sm">
              <p className="font-medium text-blue-900 dark:text-blue-100">
                You'll cast: {voteWeight.toFixed(1)} votes
              </p>
              {overflowTokens > 0 && (
                <p className="text-blue-700 dark:text-blue-300">
                  Extra {overflowTokens} ai16z goes to prize pool (+${(overflowTokens * 0.3).toFixed(2)} USD)
                </p>
              )}
              <p className="text-blue-600 dark:text-blue-400 mt-1">
                Memo: "{memoToUse}"
              </p>
            </div>
          </div>

          {/* Voting options */}
          <div className="space-y-4">
            {/* Mobile Phantom button */}
            {isOnMobile && (
              <Button
                onClick={handlePhantomVote}
                className="w-full flex items-center justify-center gap-2"
                size="lg"
              >
                <Smartphone className="h-5 w-5" />
                Send with Phantom
              </Button>
            )}

            {/* Copy instructions */}
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <Monitor className="h-4 w-4 text-gray-500 dark:text-gray-400" />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  {isOnMobile ? "Alternative: Manual transaction" : "Send transaction manually"}
                </span>
              </div>
              
              <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded text-sm font-mono text-gray-900 dark:text-gray-100 mb-3">
                {copyInstructions}
              </div>
              
              <Button
                onClick={handleCopyInstructions}
                variant="secondary"
                size="sm"
                className="w-full flex items-center justify-center gap-2"
              >
                {copied ? (
                  <>
                    <Check className="h-4 w-4 text-green-600" />
                    Copied!
                  </>
                ) : (
                  <>
                    <Copy className="h-4 w-4" />
                    Copy Instructions
                  </>
                )}
              </Button>
            </div>
          </div>

          {/* Help text */}
          <p className="mt-4 text-xs text-gray-500 dark:text-gray-400 text-center">
            Voting uses ai16z tokens. Higher amounts increase vote weight using logarithmic scaling.
            <br />
            Transactions over 100 ai16z contribute excess to the prize pool.
          </p>
        </div>
      </div>
    </div>
  )
}