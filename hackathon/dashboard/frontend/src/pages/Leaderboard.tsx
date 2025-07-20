import { useEffect, useState } from 'react'
import { hackathonApi } from '../lib/api'
import { LeaderboardEntry } from '../types'
import { Trophy, RefreshCw } from 'lucide-react'
import { LeaderboardCard } from '../components/LeaderboardCard'
import { VoteModal } from '../components/VoteModal'
import { PrizePool } from '../components/PrizePool'


export default function Leaderboard() {
  const [entries, setEntries] = useState<LeaderboardEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedSubmission, setSelectedSubmission] = useState<LeaderboardEntry | null>(null)
  const [refreshing, setRefreshing] = useState(false)
  const [currentPage, setCurrentPage] = useState(0)
  
  const ENTRIES_PER_PAGE = 8
  const totalPages = Math.ceil(entries.length / ENTRIES_PER_PAGE)
  const startIndex = currentPage * ENTRIES_PER_PAGE
  const currentEntries = entries.slice(startIndex, startIndex + ENTRIES_PER_PAGE)

  const loadLeaderboard = async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true)
    
    try {
      const leaderboardData = await hackathonApi.getLeaderboard()
      setEntries(leaderboardData || [])
    } catch (error) {
      console.error('Failed to load leaderboard:', error)
      setEntries([])
    } finally {
      setLoading(false)
      if (isRefresh) setRefreshing(false)
    }
  }

  useEffect(() => {
    loadLeaderboard()
  }, [])

  const handleRefresh = () => {
    loadLeaderboard(true)
  }



  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-gray-950 dark:via-blue-950/20 dark:to-indigo-950/20">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="text-center">
            <Trophy className="h-16 w-16 mx-auto mb-4 text-blue-600" />
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">Leaderboard</h1>
            <p className="text-gray-600 dark:text-gray-400">Loading submissions...</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-gray-950 dark:via-blue-950/20 dark:to-indigo-950/20">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 mb-4 shadow-lg">
            <Trophy className="h-8 w-8 text-white" />
          </div>
          <div className="flex items-center justify-center gap-3 mb-2">
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white">
              Leaderboard
            </h1>
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="p-2 rounded-lg bg-white dark:bg-gray-800 shadow text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
              aria-label="Refresh leaderboard"
            >
              <RefreshCw className={`h-5 w-5 ${refreshing ? 'animate-spin' : ''}`} />
            </button>
          </div>
          <p className="text-lg text-gray-600 dark:text-gray-400">
            Ranked by AI judges · Powered by your votes
          </p>
        </div>

        {/* Prize Pool */}
        <div className="mb-8">
          <PrizePool goal={10} variant="banner" />
        </div>

        {/* Leaderboard */}
        {entries.length === 0 ? (
          <div className="text-center py-12 text-gray-500 dark:text-gray-400">
            No submissions found
          </div>
        ) : (
          <>
            <div className="space-y-4">
              {currentEntries.map((entry) => (
                <LeaderboardCard 
                  key={entry.submission_id}
                  entry={entry} 
                  onVoteClick={() => setSelectedSubmission(entry)}
                />
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2 mt-8">
                <button
                  onClick={() => setCurrentPage(prev => Math.max(0, prev - 1))}
                  disabled={currentPage === 0}
                  className="px-3 py-1 rounded bg-white dark:bg-gray-800 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                
                {Array.from({ length: totalPages }, (_, i) => (
                  <button
                    key={i}
                    onClick={() => setCurrentPage(i)}
                    className={`px-3 py-1 rounded text-sm ${
                      currentPage === i 
                        ? 'bg-blue-600 text-white' 
                        : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300'
                    }`}
                  >
                    {i + 1}
                  </button>
                ))}
                
                <button
                  onClick={() => setCurrentPage(prev => Math.min(totalPages - 1, prev + 1))}
                  disabled={currentPage === totalPages - 1}
                  className="px-3 py-1 rounded bg-white dark:bg-gray-800 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}

        {/* Vote Modal */}
        {selectedSubmission && (
          <VoteModal
            submission={selectedSubmission}
            onClose={() => setSelectedSubmission(null)}
          />
        )}
      </div>
    </div>
  )
}