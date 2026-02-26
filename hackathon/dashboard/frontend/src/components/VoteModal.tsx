import { X, Copy, Smartphone, Check, Info } from 'lucide-react'
import { Button } from './Button'
import { LeaderboardEntry, SubmissionSummary } from '../types'
import { buildVotingLink, isMobile } from '../utils/phantomLink'
import { useMultipleCopyStates } from '../hooks/useCopyToClipboard'
import { TOAST_MESSAGES, PRIZE_WALLET } from '../lib/constants'
import { useState } from 'react'

interface VoteModalProps {
  submission: SubmissionSummary | LeaderboardEntry
  onClose: () => void
}

export function VoteModal({ submission, onClose }: VoteModalProps) {
  const isOnMobile = isMobile()
  const { copyToClipboard, isCopied } = useMultipleCopyStates()
  const [showTooltip, setShowTooltip] = useState(false)

  // Use submission ID as transaction memo
  const submissionId = submission.submission_id || 0
  const phantomLink = buildVotingLink({ submissionId, amount: 1 })

  const handleCopyAddress = () => copyToClipboard(PRIZE_WALLET, 'address')
  const handleCopyMemo = () => copyToClipboard(submissionId.toString(), 'memo', TOAST_MESSAGES.MEMO_COPIED)
  const handlePhantomVote = () => window.open(phantomLink, '_blank')

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
        <div className="relative transform overflow-hidden rounded-lg bg-white dark:bg-gray-900 px-4 pb-4 pt-5 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-2xl sm:p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Vote for {submission.project_name}
              </h3>
              {/* Voting guide tooltip */}
              <div className="relative">
                <button
                  onMouseEnter={() => setShowTooltip(true)}
                  onMouseLeave={() => setShowTooltip(false)}
                  onClick={() => setShowTooltip(!showTooltip)}
                  className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                  aria-label="Show voting guide"
                >
                  <Info className="h-4 w-4" />
                </button>
                
                {showTooltip && (
                  <div className="absolute top-6 left-0 z-50 w-60 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-3">
                    <img 
                      src={`${import.meta.env.BASE_URL}voting-guide.jpg`}
                      alt="Voting Guide" 
                      className="w-full h-auto rounded"
                    />
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-2 text-center">
                      Visual guide for voting process
                    </p>
                  </div>
                )}
              </div>
            </div>
            <button
              onClick={onClose}
              className="rounded-md text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label="Close modal"
            >
              <X className="h-6 w-6" />
            </button>
          </div>


          {/* Mobile Phantom button */}
          {isOnMobile && (
            <div className="mb-6">
              <Button
                onClick={handlePhantomVote}
                className="w-full flex items-center justify-center gap-3"
                size="lg"
              >
                <Smartphone className="h-5 w-5" />
                Vote with Phantom
              </Button>
            </div>
          )}

          {/* Voting instructions */}
          <div className="space-y-4">
            <div className="text-center">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Send ai16z tokens to vote for this project
              </p>
            </div>

              {/* Address section */}
              <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Step 1: Copy recipient address
                </h4>
                <div className="flex flex-col sm:flex-row gap-2">
                  <div className="flex-1 bg-gray-50 dark:bg-gray-800 p-3 rounded text-sm font-mono text-gray-900 dark:text-gray-100 break-all">
                    {PRIZE_WALLET}
                  </div>
                  <Button
                    onClick={handleCopyAddress}
                    variant="secondary"
                    size="sm"
                    className="flex items-center justify-center gap-2 sm:flex-shrink-0 w-full sm:w-auto"
                  >
                    {isCopied('address') ? (
                      <>
                        <Check className="h-4 w-4 text-green-600" />
                        Copied!
                      </>
                    ) : (
                      <>
                        <Copy className="h-4 w-4" />
                        Copy
                      </>
                    )}
                  </Button>
                </div>
              </div>

              {/* Amount section */}
              <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Step 2: Send any amount of ai16z
                </h4>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Voting power is measured by your holding amount. Any amount counts as a vote!
                </p>
              </div>

              {/* Memo section */}
              <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Step 3: Copy this memo with transaction
                </h4>
                <div className="flex flex-col sm:flex-row gap-2">
                  <div className="flex-1 bg-gray-50 dark:bg-gray-800 p-3 rounded text-sm font-mono text-gray-900 dark:text-gray-100 break-all">
                    {submissionId}
                  </div>
                  <Button
                    onClick={handleCopyMemo}
                    variant="secondary"
                    size="sm"
                    className="flex items-center justify-center gap-2 sm:flex-shrink-0 w-full sm:w-auto"
                  >
                    {isCopied('memo') ? (
                      <>
                        <Check className="h-4 w-4 text-green-600" />
                        Copied!
                      </>
                    ) : (
                      <>
                        <Copy className="h-4 w-4" />
                        Copy
                      </>
                    )}
                  </Button>
                </div>
                
                {/* Phantom wallet tip */}
                <div className="mt-3 p-2 bg-blue-50 dark:bg-blue-900/20 rounded text-xs text-blue-600 dark:text-blue-400">
                  💡 Use Phantom wallet for best memo support
                </div>
              </div>
          </div>

          {/* Help text - mobile only */}
          {isOnMobile && (
            <p className="mt-4 text-xs text-gray-500 dark:text-gray-400 text-center">
              Got the Phantom Wallet app? Use the "Vote with Phantom" button above for one-click deep-link voting, or copy the address and memo manually.
            </p>
          )}
        </div>
      </div>
    </div>
  )
}