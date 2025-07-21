import { useEffect, useState } from 'react'
import { hackathonApi } from '../lib/api'
import { LeaderboardEntry } from '../types'
import { Copy, Check } from 'lucide-react'
import { VoteModal } from '../components/VoteModal'
import { SubmissionModal } from '../components/SubmissionModal'
import { PrizePool } from '../components/PrizePool'
import { useCopyToClipboard } from '../hooks/useCopyToClipboard'
import { TOAST_MESSAGES } from '../lib/constants'

const VOTING_WALLET = '7ErPek9uyReCBwiLkTi3DbqNDRf2Kmz4BShGhXmWLebx'

export default function Leaderboard() {
  const [entries, setEntries] = useState<LeaderboardEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedSubmission, setSelectedSubmission] = useState<LeaderboardEntry | null>(null)
  const [votingSubmission, setVotingSubmission] = useState<LeaderboardEntry | null>(null)
  const { copied, copyToClipboard } = useCopyToClipboard()

  const loadLeaderboard = async () => {
    try {
      const leaderboardData = await hackathonApi.getLeaderboard()
      setEntries(leaderboardData || [])
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

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 text-gray-100 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-900 text-gray-100">
      {/* Hero Video Section */}
      <section className="w-full relative bg-black overflow-hidden">
        {/* Responsive aspect ratio container */}
        <div className="relative w-full" style={{ paddingBottom: '56.25%' /* 16:9 aspect ratio */ }}>
          <div className="absolute inset-0">
            <video
              src="/loop.mp4"
              autoPlay
              loop
              muted
              playsInline
              className="w-full h-full object-cover"
              style={{ 
                width: '100%', 
                height: '100%',
                maxWidth: '100vw',
                maxHeight: '100vh'
              }}
            />
            {/* 
            Future YouTube embed structure (commented for reference):
            <iframe
              src="https://www.youtube.com/embed/VIDEO_ID?autoplay=1&mute=1&loop=1&playlist=VIDEO_ID&controls=0&showinfo=0&rel=0&iv_load_policy=3&modestbranding=1"
              title="Hero Video"
              frameBorder="0"
              allow="autoplay; encrypted-media"
              allowFullScreen
              className="w-full h-full"
              style={{ 
                width: '100%', 
                height: '100%',
                aspectRatio: '16/9'
              }}
            />
            */}
          </div>
          
          {/* Overlay content */}
          <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
            <div className="text-center px-4 max-w-4xl mx-auto">
              <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-4 leading-tight">
                Watch & Vote
              </h1>
              <p className="text-lg sm:text-xl text-white/90 max-w-2xl mx-auto leading-relaxed">
                AI judges have scored the submissions. Now it's your turn to vote!
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Leaderboard Table */}
      <section className="max-w-7xl mx-auto px-4 pt-8 pb-28">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3 lg:gap-4 mb-6 border-b border-slate-800 pb-4">
          <h2 className="text-2xl font-bold">Leaderboard</h2>
          
          {/* Voting Instructions - Same Row on Desktop */}
          <div className="bg-slate-800/30 rounded-lg p-2.5 border border-slate-700 lg:bg-transparent lg:border-0 lg:p-0">
            <div className="flex flex-col sm:flex-row sm:items-center lg:flex-row lg:items-center gap-2 text-sm lg:flex-wrap lg:justify-end">
              <div className="flex items-center gap-1 flex-wrap lg:whitespace-nowrap">
                <span className="font-semibold text-indigo-400">Vote:</span>
                <span>Send <span className="font-semibold">1 ai16z</span> to</span>
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
          <div className="bg-slate-800/30 rounded-lg border border-slate-700 overflow-hidden">
            {/* Table Header - Hidden on mobile */}
            <div className="hidden md:grid grid-cols-[64px_1fr_100px_100px_280px] gap-4 px-4 py-3 text-xs font-semibold text-gray-400 bg-slate-800/50 border-b border-slate-700">
              <span className="text-center">#</span>
              <span>Project</span>
              <span className="text-center">AI Score</span>
              <span className="text-center">Human Score</span>
              <span className="text-center">Vote Instructions</span>
            </div>

            {/* Table Rows */}
            <div className="divide-y divide-slate-700">
              {entries.map((entry, index) => {
                const rank = index + 1
                return (
                  <div
                    key={entry.submission_id}
                    className="grid grid-cols-1 md:grid-cols-[64px_1fr_100px_100px_280px] gap-4 hover:bg-slate-700/30 transition-colors cursor-pointer"
                    onClick={() => setSelectedSubmission(entry)}
                  >
                    {/* Mobile: All info stacked */}
                    <div className="md:hidden space-y-3">
                      <div className="flex items-center gap-3">
                        {getRankBadge(rank)}
                        <img 
                          src={entry.discord_avatar || `https://ui-avatars.com/api/?name=${encodeURIComponent(entry.discord_username || 'User')}&size=40&background=6366f1&color=ffffff`}
                          className="h-10 w-10 rounded-full object-cover"
                          alt="Profile"
                        />
                        <div className="flex-1 min-w-0">
                          <h3 className="font-medium truncate text-white">{entry.project_name}</h3>
                          <p className="text-sm text-gray-400 truncate">{entry.category}</p>
                        </div>
                        <div className="text-right">
                          <div className="grid grid-cols-2 gap-3 text-center">
                            <div>
                              <div className="text-lg font-semibold text-white">
                                {entry.final_score?.toFixed(1) || '—'}
                              </div>
                              <div className="text-xs text-gray-400">AI Score</div>
                            </div>
                            <div>
                              <div className="text-lg font-semibold text-white">
                                {entry.community_score?.toFixed(1) || '—'}
                              </div>
                              <div className="text-xs text-gray-400">Human Score</div>
                            </div>
                          </div>
                        </div>
                      </div>
                      <div 
                        className="text-xs text-center bg-slate-800/50 rounded-lg p-3 border border-slate-700 cursor-pointer hover:bg-slate-700/50 transition-colors w-full"
                        onClick={(e) => {
                          e.stopPropagation()
                          setVotingSubmission(entry)
                        }}
                      >
                        <span>Send </span><span className="font-semibold text-indigo-400">ai16z</span>{' '}→{' '}
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleCopyVotingWallet()
                          }}
                          className="font-mono text-indigo-400 hover:text-indigo-300"
                        >
                          {VOTING_WALLET.slice(0, 6)}…{VOTING_WALLET.slice(-6)}
                        </button>
                        {' '}Memo <kbd className="px-1.5 py-0.5 bg-slate-700 rounded text-xs font-mono">{entry.submission_id}</kbd>
                      </div>
                    </div>

                    {/* Desktop: Table layout */}
                    <div className="hidden md:flex items-center justify-center px-4 py-4">
                      {getRankBadge(rank)}
                    </div>

                    <div className="hidden md:flex items-center gap-3 min-w-0 px-4 py-4">
                      <img 
                        src={entry.discord_avatar || `https://ui-avatars.com/api/?name=${encodeURIComponent(entry.discord_username || 'User')}&size=40&background=6366f1&color=ffffff`}
                        className="h-10 w-10 rounded-full object-cover flex-shrink-0"
                        alt="Profile"
                      />
                      <div className="min-w-0">
                        <h3 className="font-medium truncate text-white">{entry.project_name}</h3>
                        <p className="text-sm text-gray-400 truncate">{entry.category}</p>
                      </div>
                    </div>

                    <div className="hidden md:flex items-center justify-center px-4 py-4">
                      <div className="text-center">
                        <div className="text-lg font-semibold text-white">
                          {entry.final_score?.toFixed(1) || '—'}
                        </div>
                      </div>
                    </div>

                    <div className="hidden md:flex items-center justify-center px-4 py-4">
                      <div className="text-center">
                        <div className="text-lg font-semibold text-white">
                          {entry.community_score?.toFixed(1) || '—'}
                        </div>
                      </div>
                    </div>

                    <div 
                      className="hidden md:flex items-center justify-center cursor-pointer hover:bg-slate-700/20 transition-colors"
                      onClick={(e) => {
                        e.stopPropagation()
                        setVotingSubmission(entry)
                      }}
                    >
                      <div className="text-xs bg-slate-800/50 hover:bg-slate-700/50 transition-colors w-full h-full flex items-center justify-center border-l border-slate-700">
                        <div className="flex items-center gap-1 flex-wrap justify-center">
                          <span>Send</span>
                          <span className="font-semibold text-indigo-400">ai16z</span>
                          <span>→</span>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              handleCopyVotingWallet()
                            }}
                            className="font-mono text-indigo-400 hover:text-indigo-300 underline decoration-dotted"
                          >
                            {VOTING_WALLET.slice(0, 6)}…{VOTING_WALLET.slice(-6)}
                          </button>
                          <span>with Memo</span>
                          <kbd className="bg-slate-700 rounded font-mono px-1 py-0.5">{entry.submission_id}</kbd>
                        </div>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </section>

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

      {/* Music Player Style Prize Pool - Fixed at Bottom */}
      <PrizePool goal={10} variant="marquee" />
    </div>
  )
}