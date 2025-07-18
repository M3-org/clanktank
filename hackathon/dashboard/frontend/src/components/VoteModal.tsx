import { X, Copy, Smartphone, Check } from 'lucide-react'
import { Button } from './Button'
import { LeaderboardEntry, SubmissionSummary } from '../types'
import { buildVotingLink, isMobile } from '../utils/phantomLink'
import { useMultipleCopyStates } from '../hooks/useCopyToClipboard'
import { TOAST_MESSAGES, PRIZE_WALLET } from '../lib/constants'

interface VoteModalProps {
  submission: SubmissionSummary | LeaderboardEntry
  onClose: () => void
}

export function VoteModal({ submission, onClose }: VoteModalProps) {
  const isOnMobile = isMobile()
  const { copyToClipboard, isCopied } = useMultipleCopyStates()

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
                Send any amount of ai16z to vote for this project
              </p>
            </div>

            {/* Address section */}
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                1. Copy recipient address
              </h4>
              <div className="flex gap-2">
                <div className="flex-1 bg-gray-50 dark:bg-gray-800 p-3 rounded text-sm font-mono text-gray-900 dark:text-gray-100 break-all">
                  {PRIZE_WALLET}
                </div>
                <Button
                  onClick={handleCopyAddress}
                  variant="secondary"
                  size="sm"
                  className="flex items-center gap-2 flex-shrink-0"
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

            {/* Memo section */}
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                2. Copy memo
              </h4>
              <div className="flex gap-2">
                <div className="flex-1 bg-gray-50 dark:bg-gray-800 p-3 rounded text-sm font-mono text-gray-900 dark:text-gray-100">
                  {submissionId}
                </div>
                <Button
                  onClick={handleCopyMemo}
                  variant="secondary"
                  size="sm"
                  className="flex items-center gap-2 flex-shrink-0"
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
            </div>

            {/* Explanation image placeholder */}
            <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-8 text-center">
              <div className="text-gray-500 dark:text-gray-400">
                <p className="text-sm mb-2">📱 Voting Guide Image</p>
                <p className="text-xs">Visual explanation of the voting process will go here</p>
              </div>
            </div>
          </div>

          {/* Help text */}
          <p className="mt-4 text-xs text-gray-500 dark:text-gray-400 text-center">
            Votes are automatically detected and counted. Any amount counts as a vote!
          </p>
        </div>
      </div>
    </div>
  )
}