import { useEffect, useState } from 'react'
import { hackathonApi } from '../lib/api'
import { LeaderboardEntry } from '../types'
import { Card, CardContent } from '../components/Card'
import { Badge } from '../components/Badge'
import { Button } from '../components/Button'
import { Trophy, ExternalLink, Share2, RefreshCw, Medal } from 'lucide-react'
import { cn } from '../lib/utils'

export default function Leaderboard() {
  const [entries, setEntries] = useState<LeaderboardEntry[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadLeaderboard()
  }, [])

  const loadLeaderboard = async () => {
    try {
      const data = await hackathonApi.getLeaderboard()
      setEntries(data)
    } catch (error) {
      console.error('Failed to load leaderboard:', error)
    } finally {
      setLoading(false)
    }
  }

  const shareLeaderboard = () => {
    const url = window.location.href
    const text = `Check out the Clank Tank Hackathon Leaderboard! 🚀`
    
    if (navigator.share) {
      navigator.share({ title: 'Clank Tank Hackathon Leaderboard', text, url })
    } else {
      // Fallback to Twitter
      window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`, '_blank')
    }
  }

  const getMedalIcon = (rank: number) => {
    if (rank === 1) return <Medal className="h-8 w-8 text-yellow-500" />
    if (rank === 2) return <Medal className="h-8 w-8 text-gray-400" />
    if (rank === 3) return <Medal className="h-8 w-8 text-orange-600" />
    return null
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-indigo-600" />
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
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
        <h1 className="text-4xl font-bold text-gray-900 mb-2">Hackathon Leaderboard</h1>
        <p className="text-lg text-gray-600">Top projects as judged by our AI panel</p>
        
        <Button
          onClick={shareLeaderboard}
          className="mt-6"
        >
          <Share2 className="h-4 w-4 mr-2" />
          Share Leaderboard
        </Button>
      </div>

      {/* Leaderboard */}
      <Card className="overflow-hidden">
        <div className="bg-gradient-to-r from-indigo-600 to-purple-600 px-6 py-4">
          <h2 className="text-xl font-semibold text-white">Final Rankings</h2>
        </div>
        
        <div className="divide-y divide-gray-200">
          {entries.map((entry, index) => (
            <div
              key={`${entry.rank}-${entry.project_name}`}
              className={cn(
                "px-6 py-6 hover:bg-gray-50 transition-colors",
                index === 0 && "bg-gradient-to-r from-yellow-50 to-amber-50",
                index === 1 && "bg-gradient-to-r from-gray-50 to-slate-50",
                index === 2 && "bg-gradient-to-r from-orange-50 to-amber-50"
              )}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  {/* Rank */}
                  <div className="flex-shrink-0 w-16 text-center">
                    {index < 3 ? (
                      getMedalIcon(entry.rank)
                    ) : (
                      <div className="h-12 w-12 mx-auto rounded-full bg-gray-100 flex items-center justify-center">
                        <span className="font-bold text-lg text-gray-700">{entry.rank}</span>
                      </div>
                    )}
                  </div>
                  
                  {/* Project Info */}
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900">
                      {entry.project_name}
                    </h3>
                    <div className="flex items-center gap-3 mt-1">
                      <span className="text-sm text-gray-600">
                        by <span className="font-medium">{entry.team_name}</span>
                      </span>
                      <Badge variant={
                        entry.category === 'DeFi' ? 'info' :
                        entry.category === 'Gaming' ? 'secondary' :
                        entry.category === 'AI/Agents' ? 'warning' :
                        'default'
                      }>
                        {entry.category}
                      </Badge>
                    </div>
                  </div>
                </div>
                
                {/* Score and Link */}
                <div className="flex items-center gap-6">
                  <div className="text-right">
                    <div className="text-3xl font-bold text-gray-900">
                      {entry.final_score.toFixed(2)}
                    </div>
                    <div className="text-xs text-gray-500 uppercase tracking-wide">Score</div>
                  </div>
                  
                  {entry.youtube_url && (
                    <Button
                      onClick={() => window.open(entry.youtube_url, '_blank')}
                      variant="secondary"
                      size="sm"
                    >
                      Watch
                      <ExternalLink className="h-3 w-3 ml-2" />
                    </Button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Footer */}
      <div className="mt-8 text-center">
        <Card>
          <CardContent className="py-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">About the Scoring</h3>
            <p className="text-sm text-gray-600 max-w-2xl mx-auto">
              Projects are evaluated by our panel of AI judges on four criteria: Innovation & Creativity, 
              Technical Execution, Market Potential, and User Experience. Each judge brings their unique 
              perspective and expertise to create a balanced assessment.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}