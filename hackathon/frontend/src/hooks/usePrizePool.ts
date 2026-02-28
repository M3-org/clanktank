import { useState, useCallback, useEffect, useRef } from 'react'
import { toast } from 'react-hot-toast'
import { hackathonApi } from '../lib/api'
import type { PrizePoolContribution } from '../types'

const USE_STATIC = import.meta.env.VITE_USE_STATIC === 'true'

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
  const [recentContributions, setRecentContributions] = useState<PrizePoolContribution[]>([])
  const [loading, setLoading] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const [connected, setConnected] = useState(false)
  
  // WebSocket connection ref
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const isConnectingRef = useRef<boolean>(false)

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
      
      // Process recent contributions from backend
      const contributions = prizePoolData.recent_contributions || []
      setRecentContributions(contributions)
      
      setLastUpdated(new Date())
    } catch (error) {
      console.error('Error fetching prize pool data:', error)
      toast.error('Failed to fetch prize pool data')
      // Set safe defaults on error
      setTokenHoldings([])
      setTotalValue(0)
      setRecentContributions([])
    } finally {
      setLoading(false)
    }
  }, []) // Remove address dependency since we're using backend data

  // Process WebSocket data
  const processWebSocketData = useCallback((data: any) => {
    try {
      // Convert backend format to frontend format (same as fetchTokenHoldings)
      const processedTokens: TokenHolding[] = []
      const totalSol = data.total_sol || 0
      
      if (data.token_breakdown && typeof data.token_breakdown === 'object') {
        for (const [symbol, tokenData] of Object.entries(data.token_breakdown)) {
          if (tokenData && typeof tokenData === 'object') {
            const amount = (tokenData as any).amount || 0
            
            processedTokens.push({
              mint: (tokenData as any).mint || '',
              symbol: (tokenData as any).symbol || symbol,
              amount: amount.toString(),
              solValue: symbol === 'SOL' ? amount : 0,
              decimals: (tokenData as any).decimals || 6,
              logo: (tokenData as any).logo
            })
          }
        }
      }
      
      // Sort tokens same way as before
      const priorityTokens = ['SOL', 'ai16z', 'USDC']
      const sortedTokens = processedTokens
        .sort((a, b) => {
          const aPriority = priorityTokens.indexOf(a.symbol)
          const bPriority = priorityTokens.indexOf(b.symbol)
          
          if (aPriority !== -1 && bPriority !== -1) {
            return aPriority - bPriority
          }
          
          if (aPriority !== -1) return -1
          if (bPriority !== -1) return 1
          
          return parseFloat(b.amount) - parseFloat(a.amount)
        })
        .slice(0, 12)
      
      setTokenHoldings(sortedTokens)
      setTotalValue(totalSol)
      setRecentContributions(data.recent_contributions || [])
      setLastUpdated(new Date())
      
    } catch (error) {
      console.error('Error processing WebSocket data:', error)
    }
  }, [])

  // WebSocket connection management
  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return // Already connected
    }
    
    if (isConnectingRef.current) {
      return // Already connecting
    }

    isConnectingRef.current = true

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      // In development, connect to backend API port (8000)
      // In production, use the same host (backend serves both API and frontend)
      const isDev = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
      const wsHost = isDev ? `${window.location.hostname}:8000` : window.location.host
      const wsUrl = `${protocol}//${wsHost}/ws/prize-pool`
      
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        console.log('Prize pool WebSocket connected')
        setConnected(true)
        setLoading(false)
        isConnectingRef.current = false
        
        // Clear any reconnect timeout
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current)
          reconnectTimeoutRef.current = null
        }
      }

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          
          if (message.type === 'prize_pool_update' && message.data) {
            processWebSocketData(message.data)
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
          console.error('Raw message data:', event.data)
        }
      }

      ws.onclose = (event) => {
        console.log('Prize pool WebSocket disconnected', event.code, event.reason)
        setConnected(false)
        isConnectingRef.current = false
        
        // Only attempt to reconnect if it wasn't a clean close
        if (event.code !== 1000 && !reconnectTimeoutRef.current) {
          console.log('Attempting to reconnect in 5 seconds...')
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectTimeoutRef.current = null
            connectWebSocket()
          }, 5000)
        }
      }

      ws.onerror = (error) => {
        console.warn('Prize pool WebSocket error - will attempt reconnect:', error.type)
        setConnected(false)
        isConnectingRef.current = false
      }

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      isConnectingRef.current = false
      
      // Fallback to HTTP polling if WebSocket fails
      if (!reconnectTimeoutRef.current) {
        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectTimeoutRef.current = null
          fetchTokenHoldings() // Fallback to HTTP
        }, 5000)
      }
    }
  }, [processWebSocketData, fetchTokenHoldings])

  // Initialize connection on mount (skip in static mode — no backend)
  useEffect(() => {
    if (USE_STATIC) {
      setLoading(false)
      return
    }

    setLoading(true)

    // Try WebSocket first, fallback to HTTP if needed
    connectWebSocket()

    // Cleanup on unmount
    return () => {
      isConnectingRef.current = false

      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }

      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
        reconnectTimeoutRef.current = null
      }
    }
  }, [connectWebSocket])

  const totalTokenTypes = tokenHoldings.length

  return {
    tokenHoldings,
    totalValue,
    totalTokenTypes,
    recentContributions,
    loading,
    lastUpdated,
    connected,
    refetch: fetchTokenHoldings, // Keep as fallback
    reconnect: connectWebSocket
  }
}