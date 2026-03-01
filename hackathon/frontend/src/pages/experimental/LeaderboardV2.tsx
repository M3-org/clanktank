import { useState, useEffect } from 'react'
import { Copy, Check } from 'lucide-react'
import { VoteModal } from '../../components/VoteModal'
import { SubmissionModal } from '../../components/SubmissionModal'
import { hackathonApi } from '../../lib/api'
import { LeaderboardEntry } from '../../types'
import { useCopyToClipboard } from '../../hooks/useCopyToClipboard'
import { TOAST_MESSAGES } from '../../lib/constants'

const VOTING_WALLET = '7ErPek9uyReCBwiLkTi3DbqNDRf2Kmz4BShGhXmWLebx'

/**
 * Experimental LeaderboardV2 - Testing enhanced frontpage leaderboard
 * Features:
 * - Top 10 entries
 * - Side-by-side tables (Top 5 | Next 5)
 * - Voting modal functionality
 * - Full interactivity like main Leaderboard page
 */
export default function LeaderboardV2() {
  const [entries, setEntries] = useState<LeaderboardEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedSubmission, setSelectedSubmission] = useState<LeaderboardEntry | null>(null)
  const [votingSubmission, setVotingSubmission] = useState<LeaderboardEntry | null>(null)
  const { copied, copyToClipboard } = useCopyToClipboard()

  const loadLeaderboard = async () => {
    try {
      const leaderboardData = await hackathonApi.getLeaderboard()
      setEntries(leaderboardData?.slice(0, 10) || []) // Top 10
    } catch (error) {
      console.error('Failed to load leaderboard:', error)
      setEntries([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadLeaderboard()
  }, [])

  const handleCopyVotingWallet = () => {
    copyToClipboard(VOTING_WALLET, TOAST_MESSAGES.ADDRESS_COPIED)
  }

  const getRankBadge = (rank: number) => {
    if (rank === 1) {
      return <div className="h-8 w-8 rounded-full bg-yellow-400 text-slate-900 font-bold flex items-center justify-center text-sm">1</div>
    } else if (rank === 2) {
      return <div className="h-8 w-8 rounded-full bg-gray-400 text-slate-900 font-bold flex items-center justify-center text-sm">2</div>
    } else if (rank === 3) {
      return <div className="h-8 w-8 rounded-full bg-amber-600 text-white font-bold flex items-center justify-center text-sm">3</div>
    } else {
      return <div className="h-8 w-8 rounded-full bg-slate-600 text-slate-300 font-bold flex items-center justify-center text-sm">{rank}</div>
    }
  }

  const renderLeaderboardTable = (tableEntries: LeaderboardEntry[], startRank: number, title: string) => (
    <div className="bg-slate-800/30 rounded-lg border border-slate-700 overflow-hidden">
      <div className="bg-slate-800/70 px-4 py-2 border-b border-slate-700">
        <h3 className="text-sm font-semibold text-slate-300">{title}</h3>
      </div>
      
      {/* Table Header - Hidden on mobile */}
      <div className="hidden lg:grid grid-cols-[48px_1fr_80px_80px_200px] gap-2 px-3 py-2 text-xs font-semibold text-gray-400 bg-slate-800/50 border-b border-slate-700">
        <span className="text-center">#</span>
        <span>Project</span>
        <span className="text-center">AI</span>
        <span className="text-center">Human</span>
        <span className="text-center">Vote</span>
      </div>

      {/* Table Rows */}
      <div className="divide-y divide-slate-700">
        {tableEntries.map((entry, index) => {
          const rank = startRank + index
          return (
            <div
              key={entry.submission_id}
              className="hover:bg-slate-700/30 transition-colors cursor-pointer"
              onClick={() => setSelectedSubmission(entry)}
            >
              {/* Mobile: Compact stacked layout */}
              <div className="lg:hidden p-3 space-y-2">
                <div className="flex items-center gap-2">
                  {getRankBadge(rank)}
                  <img 
                    src={entry.discord_avatar || `https://ui-avatars.com/api/?name=${encodeURIComponent(entry.discord_username || 'User')}&size=32&background=6366f1&color=ffffff`}
                    className="h-6 w-6 rounded-full object-cover"
                    alt="Profile"
                  />
                  <div className="flex-1 min-w-0">
                    <h4 className="font-medium truncate text-white text-sm">{entry.project_name}</h4>
                    <p className="text-xs text-gray-400 truncate">{entry.category}</p>
                  </div>
                  <div className="flex gap-3 text-xs">
                    <div className="text-center">
                      <div className="font-semibold text-white">{entry.final_score?.toFixed(1) || '—'}</div>
                      <div className="text-gray-400">AI</div>
                    </div>
                    <div className="text-center">
                      <div className="font-semibold text-white">{entry.community_score?.toFixed(1) || '—'}</div>
                      <div className="text-gray-400">Human</div>
                    </div>
                  </div>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    setVotingSubmission(entry)
                  }}
                  className="w-full text-xs text-center bg-slate-800/50 hover:bg-slate-700/50 rounded p-2 border border-slate-700 transition-colors"
                >
                  <span>Vote: Send </span>
                  <span className="font-semibold text-indigo-400">ai16z</span>
                  <span> → </span>
                  <span className="font-mono text-xs">{VOTING_WALLET.slice(0, 6)}…{VOTING_WALLET.slice(-6)}</span>
                  <span> Memo: </span>
                  <kbd className="bg-slate-700 rounded px-1">{entry.submission_id}</kbd>
                </button>
              </div>

              {/* Desktop: Table layout */}
              <div className="hidden lg:grid grid-cols-[48px_1fr_80px_80px_200px] gap-2 items-center px-3 py-3">
                <div className="flex justify-center">
                  {getRankBadge(rank)}
                </div>

                <div className="flex items-center gap-2 min-w-0">
                  <img 
                    src={entry.discord_avatar || `https://ui-avatars.com/api/?name=${encodeURIComponent(entry.discord_username || 'User')}&size=32&background=6366f1&color=ffffff`}
                    className="h-6 w-6 rounded-full object-cover flex-shrink-0"
                    alt="Profile"
                  />
                  <div className="min-w-0">
                    <h4 className="font-medium truncate text-white text-sm">{entry.project_name}</h4>
                    <p className="text-xs text-gray-400 truncate">{entry.category}</p>
                  </div>
                </div>

                <div className="text-center">
                  <div className="font-semibold text-white text-sm">
                    {entry.final_score?.toFixed(1) || '—'}
                  </div>
                </div>

                <div className="text-center">
                  <div className="font-semibold text-white text-sm">
                    {entry.community_score?.toFixed(1) || '—'}
                  </div>
                </div>

                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    setVotingSubmission(entry)
                  }}
                  className="text-xs bg-slate-800/50 hover:bg-slate-700/50 transition-colors px-2 py-1 rounded border border-slate-700"
                >
                  <span>Send </span>
                  <span className="font-semibold text-indigo-400">ai16z</span>
                  <span> Memo </span>
                  <kbd className="bg-slate-700 rounded px-1">{entry.submission_id}</kbd>
                </button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )

  if (loading) {
    return (
      <div className="bg-slate-900 text-gray-100 py-12">
        <div className="max-w-6xl mx-auto px-4">
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500 mx-auto"></div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-slate-900 text-gray-100 py-12">
      <div className="max-w-7xl mx-auto px-4">
        {/* Header with voting instructions */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3 lg:gap-4 mb-6 border-b border-slate-800 pb-4">
          <h2 className="text-2xl md:text-3xl font-bold text-white">Top 10 Leaderboard</h2>
          
          <div className="bg-slate-800/30 rounded-lg p-2.5 border border-slate-700 lg:bg-transparent lg:border-0 lg:p-0">
            <div className="flex flex-col sm:flex-row sm:items-center lg:flex-row lg:items-center gap-2 text-sm lg:flex-wrap lg:justify-end">
              <div className="flex items-center gap-1 flex-wrap lg:whitespace-nowrap">
                <span className="font-semibold text-indigo-400">Vote:</span>
                <span>Send</span>
                <span className="font-semibold text-indigo-400">ai16z</span>
                <span>to</span>
              </div>
              
              <div className="flex items-center gap-2 flex-wrap">
                <button
                  onClick={handleCopyVotingWallet}
                  className="flex items-center gap-1 px-2 py-1 bg-slate-700/80 hover:bg-slate-600/80 rounded border border-slate-600 hover:border-indigo-400 transition-all duration-200 group"
                  title="Copy wallet address"
                >
                  <span className="text-slate-300 font-mono text-xs">
                    <span className="hidden md:inline">{VOTING_WALLET.slice(0, 8)}…{VOTING_WALLET.slice(-8)}</span>
                    <span className="md:hidden">{VOTING_WALLET.slice(0, 6)}…{VOTING_WALLET.slice(-6)}</span>
                  </span>
                  {copied ? (
                    <Check className="w-3 h-3 text-green-400" />
                  ) : (
                    <Copy className="w-3 h-3 text-indigo-400 group-hover:text-indigo-300" />
                  )}
                </button>
                <span className="whitespace-nowrap">with Memo <kbd className="px-1.5 py-0.5 bg-slate-700 rounded text-xs font-mono">ID</kbd></span>
              </div>
            </div>
          </div>
        </div>

        {entries.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            No submissions found
          </div>
        ) : (
          /* Side-by-side tables */
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            {/* Top 5 */}
            {renderLeaderboardTable(entries.slice(0, 5), 1, "🏆 Top 5")}
            
            {/* Next 5 (if available) */}
            {entries.length > 5 && renderLeaderboardTable(entries.slice(5, 10), 6, "🔥 Rising Stars")}
          </div>
        )}
      </div>

      {/* Submission Detail Modal */}
      {selectedSubmission && (
        <SubmissionModal
          submissionId={selectedSubmission.submission_id}
          onClose={() => setSelectedSubmission(null)}
          allSubmissionIds={entries.map(e => e.submission_id)}
        />
      )}

      {/* Vote Modal */}
      {votingSubmission && (
        <VoteModal
          submission={votingSubmission}
          onClose={() => setVotingSubmission(null)}
        />
      )}
    </div>
  )
}