import { useEffect, useState } from 'react'
import { hackathonApi } from '../lib/api'
import { LeaderboardEntry, CommunityScore } from '../types'
import { Card, CardContent } from '../components/Card'
import { Button } from '../components/Button'
import { WalletVoting } from '../components/WalletVoting'
import { PrizePoolWidget } from '../components/PrizePoolWidget'
import { Trophy, RefreshCw, Medal, User, Vote } from 'lucide-react'
import { cn } from '../lib/utils'

export default function Leaderboard() {
  const [entries, setEntries] = useState<LeaderboardEntry[]>([])
  const [, setCommunityScores] = useState<CommunityScore[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedProject, setSelectedProject] = useState<string | null>(null)
  const [showVoting, setShowVoting] = useState(false)

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


  const getMedalIcon = (rank: number) => {
    if (rank === 1) return <Medal className="h-8 w-8 text-yellow-500" />
    if (rank === 2) return <Medal className="h-8 w-8 text-gray-400" />
    if (rank === 3) return <Medal className="h-8 w-8 text-orange-600" />
    return null
  }

  const statusColor = (status: string) => {
    switch (status) {
      case 'scored':
        return 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-100 border-blue-300 dark:border-blue-700';
      case 'completed':
        return 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-100 border-yellow-300 dark:border-yellow-700';
      case 'published':
        return 'bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-100 border-purple-300 dark:border-purple-700';
      default:
        return 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-100 border-gray-300 dark:border-gray-600';
    }
  };

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
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="flex justify-center mb-4">
          <div className="relative">
            <Trophy className="h-20 w-20 text-yellow-500" />
            <div className="absolute -top-2 -right-2 h-8 w-8 bg-yellow-500 rounded-full flex items-center justify-center">
              <span className="text-white font-bold text-sm">{entries.length}</span>
            </div>
          </div>
        </div>
        <h1 className="text-4xl font-bold text-gray-900 dark:text-gray-100 mb-2">Hackathon Leaderboard</h1>
        <p className="text-lg text-gray-600 dark:text-gray-300">Top projects as judged by our AI panel</p>
        
        <div className="flex justify-center mt-6">
          <Button
            onClick={() => setShowVoting(!showVoting)}
            variant="secondary"
          >
            <Vote className="h-4 w-4 mr-2" />
            {showVoting ? 'Hide Voting' : 'Community Voting'}
          </Button>
        </div>
      </div>

      {/* Community Voting Interface */}
      {showVoting && (
        <div className="grid md:grid-cols-2 gap-6 mb-8">
          {/* Prize Pool Widget */}
          <PrizePoolWidget />
          
          {/* Voting Interface */}
          {selectedProject ? (
            <WalletVoting
              submissionId={selectedProject}
              projectName={entries.find(e => e.submission_id === selectedProject)?.project_name || 'Unknown Project'}
            />
          ) : (
            <Card className="bg-white dark:bg-gray-900">
              <CardContent className="p-6">
                <div className="text-center space-y-4">
                  <div className="p-4 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg">
                    <Vote className="h-12 w-12 text-indigo-600 dark:text-indigo-400 mx-auto mb-3" />
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                      Select a Project to Vote
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Click the "Vote" button next to any project below to cast your community vote with ai16z tokens
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Leaderboard */}
      <Card className="overflow-hidden bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 mb-8">
        <div className="bg-gradient-to-r from-indigo-600 to-purple-600 px-6 py-4">
          <h2 className="text-xl font-semibold text-white">Final Rankings</h2>
        </div>
        
        <div className="divide-y divide-gray-200 dark:divide-gray-700">
          {entries.map((entry, index) => (
            <div
              key={`${entry.rank}-${entry.project_name}`}
              className={cn(
                "px-6 py-6 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors border-l-4",
                statusColor(entry.status || "unknown"),
                index === 0 && "bg-gradient-to-r from-yellow-50 to-amber-50 dark:from-gray-900 dark:to-gray-800",
                index === 1 && "bg-gradient-to-r from-gray-50 to-slate-50 dark:from-gray-800 dark:to-gray-700",
                index === 2 && "bg-gradient-to-r from-orange-50 to-amber-50 dark:from-gray-800 dark:to-gray-700"
              )}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  {/* Rank */}
                  <div className="flex-shrink-0 w-16 text-center">
                    {index < 3 ? (
                      getMedalIcon(entry.rank)
                    ) : (
                      <div className="h-12 w-12 mx-auto rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                        <span className="font-bold text-lg text-gray-700 dark:text-gray-200">{entry.rank}</span>
                      </div>
                    )}
                  </div>
                  
                  {/* Project Info */}
                  <div className="flex-1 flex items-center gap-3">
                    {entry.discord_avatar && entry.discord_id ? (
                      <img
                        src={`https://cdn.discordapp.com/avatars/${entry.discord_id}/${entry.discord_avatar}.png`}
                        alt="Discord avatar"
                        className="h-8 w-8 rounded-full object-cover border border-gray-300 dark:border-gray-700"
                      />
                    ) : (
                      <span className="h-8 w-8 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
                        <User className="h-5 w-5 text-gray-400" />
                      </span>
                    )}
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                      <a
                        // TODO: Use submission_id for deep linking if available in LeaderboardEntry
                        href={`/submission/${entry.project_name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9\-]/g, '')}`}
                        className="hover:underline text-cyan-600 dark:text-cyan-300 hover:text-cyan-800 dark:hover:text-cyan-200"
                      >
                        {entry.project_name}
                      </a>
                    </h3>
                  </div>
                </div>
                
                {/* Score and Actions */}
                <div className="flex items-center gap-6">
                  {/* AI Score */}
                  <div className="text-right">
                    <div className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                      {entry.final_score.toFixed(2)}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">AI Score</div>
                  </div>
                  
                  {/* Community Score */}
                  <div className="text-right">
                    <div className="text-2xl font-semibold text-blue-600 dark:text-blue-400">
                      {entry.community_score ? entry.community_score.toFixed(1) : "—"}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">Community</div>
                  </div>
                  
                  {/* Vote Button */}
                  {showVoting && (
                    <Button
                      variant={selectedProject === entry.submission_id ? "primary" : "secondary"}
                      size="sm"
                      onClick={() => {
                        setSelectedProject(entry.submission_id)
                        if (!showVoting) setShowVoting(true)
                      }}
                    >
                      <Vote className="h-4 w-4 mr-1" />
                      {selectedProject === entry.submission_id ? 'Selected' : 'Vote'}
                    </Button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Footer */}
      <Card className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
        <CardContent className="py-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">About the Scoring</h3>
          <p className="text-sm text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
            Projects are evaluated by our panel of AI judges on four criteria: Innovation & Creativity, 
            Technical Execution, Market Potential, and User Experience. Each judge brings their unique 
            perspective and expertise to create a balanced assessment.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}