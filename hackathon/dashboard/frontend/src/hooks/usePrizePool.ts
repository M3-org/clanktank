import { useState, useCallback, useEffect } from 'react'
import { toast } from 'react-hot-toast'
import { hackathonApi } from '../lib/api'

interface TokenHolding {
  mint: string
  symbol: string
  amount: string
  solValue: number
  decimals: number
  logo?: string
}

export function usePrizePool() {
  const [tokenHoldings, setTokenHoldings] = useState<TokenHolding[]>([])
  const [totalValue, setTotalValue] = useState(0)
  const [loading, setLoading] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  const fetchTokenHoldings = useCallback(async () => {
    try {
      setLoading(true)
      
      // Use existing backend API instead of Helius
      const prizePoolData = await hackathonApi.getPrizePool()
      
      // Convert backend format to frontend format
      const processedTokens: TokenHolding[] = []
      const totalSol = prizePoolData.total_sol || 0
      
      // Process token breakdown from backend (now includes full Helius metadata)
      if (prizePoolData.token_breakdown && typeof prizePoolData.token_breakdown === 'object') {
        for (const [symbol, tokenData] of Object.entries(prizePoolData.token_breakdown)) {
          if (tokenData && typeof tokenData === 'object') {
            const amount = tokenData.amount || 0
            
            processedTokens.push({
              mint: tokenData.mint || '',
              symbol: tokenData.symbol || symbol,
              amount: amount.toString(),
              solValue: symbol === 'SOL' ? amount : 0, // Only count SOL for total
              decimals: tokenData.decimals || 6,
              logo: tokenData.logo
            })
          }
        }
      }
      
      // Sort: Priority tokens first (SOL, ai16z, USDC), then by balance amount
      const priorityTokens = ['SOL', 'ai16z', 'USDC']
      const sortedTokens = processedTokens
        .sort((a, b) => {
          const aPriority = priorityTokens.indexOf(a.symbol)
          const bPriority = priorityTokens.indexOf(b.symbol)
          
          // If both are priority tokens, sort by priority order
          if (aPriority !== -1 && bPriority !== -1) {
            return aPriority - bPriority
          }
          
          // Priority tokens come first
          if (aPriority !== -1) return -1
          if (bPriority !== -1) return 1
          
          // For non-priority tokens, sort by balance
          return parseFloat(b.amount) - parseFloat(a.amount)
        })
        .slice(0, 12) // Show more tokens in grid format
      
      setTokenHoldings(sortedTokens)
      setTotalValue(totalSol) // Use SOL from prize pool
      setLastUpdated(new Date())
    } catch (error) {
      console.error('Error fetching prize pool data:', error)
      toast.error('Failed to fetch prize pool data')
      // Set safe defaults on error
      setTokenHoldings([])
      setTotalValue(0)
    } finally {
      setLoading(false)
    }
  }, []) // Remove address dependency since we're using backend data

  // Auto-fetch on mount and refresh every 2 minutes
  useEffect(() => {
    fetchTokenHoldings()
    const interval = setInterval(fetchTokenHoldings, 120000) // 2 minutes
    return () => clearInterval(interval)
  }, [fetchTokenHoldings])

  const totalTokenTypes = tokenHoldings.length

  return {
    tokenHoldings,
    totalValue,
    totalTokenTypes,
    loading,
    lastUpdated,
    refetch: fetchTokenHoldings
  }
}