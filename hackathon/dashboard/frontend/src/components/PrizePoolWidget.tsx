import { useState, useEffect } from 'react'
import { Card, CardContent } from './Card'
import { Button } from './Button'
import { Trophy, DollarSign, RefreshCw, TrendingUp, Clock } from 'lucide-react'
import { cn } from '../lib/utils'
import { hackathonApi } from '../lib/api'
import { PrizePoolData, TokenBreakdown } from '../types'

interface PrizePoolWidgetProps {
  className?: string
  showContributions?: boolean
}

export function PrizePoolWidget({ className, showContributions = true }: PrizePoolWidgetProps) {
  const [prizePoolData, setPrizePoolData] = useState<PrizePoolData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  useEffect(() => {
    loadPrizePool()
    // Refresh every 30 seconds
    const interval = setInterval(loadPrizePool, 30000)
    return () => clearInterval(interval)
  }, [])
  
  const loadPrizePool = async () => {
    try {
      setError(null)
      const data = await hackathonApi.getPrizePool()
      setPrizePoolData(data)
    } catch (err) {
      console.error('Failed to load prize pool:', err)
      setError('Failed to load prize pool data')
    } finally {
      setLoading(false)
    }
  }
  
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount)
  }
  
  const formatTokenAmount = (amount: number, decimals = 2) => {
    if (amount >= 1000000) {
      return `${(amount / 1000000).toFixed(1)}M`
    } else if (amount >= 1000) {
      return `${(amount / 1000).toFixed(1)}K`
    }
    return amount.toFixed(decimals)
  }
  
  const getTokenDisplayName = (mint: string) => {
    if (mint === 'HeLp6NuQkmYB4pYWo2zYs22mESHXPQYzXbB8n4V98jwC') return 'ai16z'
    if (mint === 'So11111111111111111111111111111111111111112') return 'SOL'
    return mint.substring(0, 8) + '...'
  }
  
  const formatTimeAgo = (timestamp: number) => {
    const now = Date.now() / 1000
    const diff = now - timestamp
    
    if (diff < 60) return 'just now'
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
    return `${Math.floor(diff / 86400)}d ago`
  }

  if (loading) {
    return (
      <Card className={cn("bg-white dark:bg-gray-900", className)}>
        <CardContent className="p-6">
          <div className="flex items-center justify-center h-32">
            <RefreshCw className="h-6 w-6 animate-spin text-indigo-600" />
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error || !prizePoolData) {
    return (
      <Card className={cn("bg-white dark:bg-gray-900", className)}>
        <CardContent className="p-6">
          <div className="text-center space-y-2">
            <div className="text-sm text-red-600 dark:text-red-400">{error || 'No prize pool data'}</div>
            <Button variant="ghost" size="sm" onClick={loadPrizePool}>
              <RefreshCw className="h-4 w-4 mr-1" />
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className={cn("bg-gradient-to-br from-purple-50 to-indigo-50 dark:from-gray-900 dark:to-gray-800", className)}>
      <CardContent className="p-6">
        <div className="space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-100 dark:bg-yellow-900/30 rounded-lg">
                <Trophy className="h-6 w-6 text-yellow-600 dark:text-yellow-400" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  Prize Pool
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Community contributions + vote overflow
                </p>
              </div>
            </div>
            <Button variant="ghost" size="sm" onClick={loadPrizePool}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
          
          {/* Current Total */}
          <div className="text-center space-y-2">
            <div className="text-4xl font-bold text-gray-900 dark:text-gray-100">
              {formatCurrency(prizePoolData.total_usd)}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              {prizePoolData.progress_percentage.toFixed(1)}% of {formatCurrency(prizePoolData.target_usd)} goal
            </div>
            
            {/* Progress Bar */}
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
              <div 
                className="bg-gradient-to-r from-green-500 to-blue-500 h-3 rounded-full transition-all duration-300"
                style={{ width: `${Math.min(prizePoolData.progress_percentage, 100)}%` }}
              />
            </div>
          </div>
          
          {/* Token Breakdown */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <DollarSign className="h-4 w-4 text-gray-500" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Token Breakdown
              </span>
            </div>
            
            <div className="grid gap-2">
              {Object.entries(prizePoolData.token_breakdown).map(([mint, breakdown]: [string, TokenBreakdown]) => (
                <div 
                  key={mint}
                  className="flex items-center justify-between p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full flex items-center justify-center">
                      <span className="text-xs font-bold text-white">
                        {getTokenDisplayName(mint).substring(0, 2).toUpperCase()}
                      </span>
                    </div>
                    <div>
                      <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {formatTokenAmount(breakdown.amount)} {getTokenDisplayName(mint)}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        ${breakdown.price_per_token.toFixed(4)} each
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                      {formatCurrency(breakdown.usd_value)}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      {((breakdown.usd_value / prizePoolData.total_usd) * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          {/* Recent Contributions */}
          {showContributions && prizePoolData.recent_contributions.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-gray-500" />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Recent Activity
                </span>
              </div>
              
              <div className="space-y-2 max-h-32 overflow-y-auto">
                {prizePoolData.recent_contributions.slice(0, 5).map((contribution, index) => (
                  <div 
                    key={index}
                    className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700 rounded text-xs"
                  >
                    <div className="flex items-center gap-2">
                      <Clock className="h-3 w-3 text-gray-400" />
                      <span className="text-gray-600 dark:text-gray-300">
                        {contribution.wallet.substring(0, 6)}...{contribution.wallet.slice(-4)}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-900 dark:text-gray-100">
                        +{formatTokenAmount(contribution.amount)} {getTokenDisplayName(contribution.token)}
                      </span>
                      <span className={cn(
                        "px-1.5 py-0.5 rounded text-xs font-medium",
                        contribution.source === 'vote_overflow' 
                          ? "bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300"
                          : "bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300"
                      )}>
                        {contribution.source === 'vote_overflow' ? 'Vote' : 'Direct'}
                      </span>
                      <span className="text-gray-500 dark:text-gray-400">
                        {formatTimeAgo(contribution.timestamp)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {/* Call to Action */}
          <div className="bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-800 rounded-lg p-3">
            <div className="text-center space-y-2">
              <div className="text-sm font-medium text-indigo-900 dark:text-indigo-100">
                Boost the Prize Pool!
              </div>
              <div className="text-xs text-indigo-700 dark:text-indigo-300">
                Vote with excess ai16z tokens or send direct contributions to grow the prize pool for winners
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}