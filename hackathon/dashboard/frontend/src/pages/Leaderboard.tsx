import { useEffect, useState } from 'react'
import { hackathonApi } from '../lib/api'
import { LeaderboardEntry, CommunityScore } from '../types'
import { Trophy, RefreshCw } from 'lucide-react'
import PrizePoolBanner from '../components/PrizePoolBanner'
import { LeaderboardCard } from '../components/LeaderboardCard'

export default function Leaderboard() {
  const [entries, setEntries] = useState<LeaderboardEntry[]>([])
  const [, setCommunityScores] = useState<CommunityScore[]>([])
  const [loading, setLoading] = useState(true)
  
  // Prize pool data - could be fetched from API
  const prizeTotalEth = 16.42
  const prizeAddress = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM" // Prize pool address

  useEffect(() => {
    loadLeaderboard()
  }, [])

  const loadLeaderboard = async () => {
    try {
      const [leaderboardData, communityData] = await Promise.all([
        hackathonApi.getLeaderboard(),
        hackathonApi.getCommunityScores().catch(() => []) // Gracefully handle if voting not available
      ])
      
      // Create a map of community scores by submission_id
      const communityScoreMap = new Map()
      communityData.forEach(score => {
        communityScoreMap.set(score.submission_id, score.community_score)
      })
      
      // Merge community scores into leaderboard entries using submission_id
      const entriesWithCommunity = leaderboardData.map(entry => ({
        ...entry,
        community_score: communityScoreMap.get(entry.submission_id) || undefined
      }))
      
      setEntries(entriesWithCommunity)
      setCommunityScores(communityData)
    } catch (error) {
      console.error('Failed to load leaderboard:', error)
    } finally {
      setLoading(false)
    }
  }



  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="h-8 w-8 animate-spin text-indigo-600" />
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <PrizePoolBanner total={prizeTotalEth} goal={25} address={prizeAddress} />

      {/* Header */}
      <div className="text-center mb-12">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-100 dark:bg-gray-800 mb-6">
          <Trophy className="h-8 w-8 text-gray-600 dark:text-gray-400" />
        </div>
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-3">Leaderboard</h1>
        <p className="text-gray-600 dark:text-gray-400">AI-judged rankings from our expert panel</p>
      </div>

      {/* Leaderboard */}
      <div className="space-y-2">
        {entries.map(entry => <LeaderboardCard key={entry.submission_id} entry={entry} />)}
      </div>

      {/* Footer */}
      <div className="mt-16 text-center">
        <p className="text-sm text-gray-500 dark:text-gray-400 max-w-2xl mx-auto leading-relaxed">
          Projects are evaluated on Innovation, Technical Execution, Market Potential, and User Experience 
          by our panel of specialized AI judges.
        </p>
      </div>
    </div>
  )
}