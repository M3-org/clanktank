import { useState } from 'react'
import { Copy, Check, ExternalLink, TrendingUp, Gift } from 'lucide-react'
import { Card } from './Card'
import { usePrizePool } from '../hooks/usePrizePool'
import { toast } from 'react-hot-toast'

interface PrizePoolCardProps {
  goal?: number // goal in SOL
}

export function PrizePoolCard({ goal = 10 }: PrizePoolCardProps) {
  const [copied, setCopied] = useState(false)
  const { tokenHoldings, totalValue, loading, lastUpdated } = usePrizePool()
  
  // Hardcoded prize wallet address (same as backend)
  const address = "2K1reedtyDUQigdaLoHLEyugkH88iVGNE2BQemiGx6xf"
  const progress = Math.min((totalValue / goal) * 100, 100)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(address)
      setCopied(true)
      toast.success('Address copied!', { duration: 1500 })
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      toast.error('Copy failed')
    }
  }

  return (
    <Card 
      variant="highlight" 
      className="group mb-8 overflow-hidden transition-all duration-300 hover:shadow-xl hover:shadow-amber-500/20"
    >
      <div className="relative p-6">
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Left Side - Prize Pool Info */}
          <div className="flex-1">
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center shadow-lg">
                  <Gift className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-amber-900 dark:text-amber-100">Prize Pool</h2>
                  <p className="text-sm text-amber-700 dark:text-amber-300">Community Contributions</p>
                </div>
              </div>
              
            </div>

            {/* Value Display */}
            <div className="mb-6">
              <div className="mb-2">
                <div className="text-4xl font-black text-amber-900 dark:text-amber-100 tracking-tight">
                  {totalValue.toLocaleString(undefined, { 
                    maximumFractionDigits: 3
                  })} SOL
                </div>
              </div>
              <div className="flex items-center gap-2 text-amber-700 dark:text-amber-300">
                <TrendingUp className="h-4 w-4" />
                <span className="text-sm font-medium">
                  {totalValue.toLocaleString(undefined, { maximumFractionDigits: 3 })} / {goal.toLocaleString()} SOL ({progress.toFixed(0)}%)
                </span>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="mb-6">
              <div className="h-3 bg-slate-700/40 dark:bg-slate-600/40 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-amber-400 via-orange-500 to-red-500 rounded-full transition-all duration-1000 ease-out"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>

            {/* Wallet Address */}
            <div className="flex gap-2">
              <button
                onClick={handleCopy}
                className="flex-1 flex items-center justify-center gap-1 px-1 py-2 bg-white/60 dark:bg-gray-900/60 hover:bg-white/80 dark:hover:bg-gray-900/80 rounded-xl border border-amber-200 dark:border-amber-800 transition-all duration-200 group/copy"
              >
                {/* Full address on larger screens, truncated on smaller */}
                <span className="font-mono text-xs text-amber-900 dark:text-amber-100 hidden lg:block">
                  {address}
                </span>
                <span className="font-mono text-xs text-amber-900 dark:text-amber-100 hidden md:block lg:hidden">
                  {address.slice(0, 20)}...{address.slice(-12)}
                </span>
                <span className="font-mono text-xs text-amber-900 dark:text-amber-100 hidden sm:block md:hidden">
                  {address.slice(0, 16)}...{address.slice(-10)}
                </span>
                <span className="font-mono text-xs text-amber-900 dark:text-amber-100 block sm:hidden">
                  {address.slice(0, 12)}...{address.slice(-8)}
                </span>
                {copied ? (
                  <Check className="h-4 w-4 text-green-600" />
                ) : (
                  <Copy className="h-4 w-4 text-amber-600 dark:text-amber-400 group-hover/copy:text-amber-700 dark:group-hover/copy:text-amber-300" />
                )}
              </button>
              
              <a
                href={`https://solscan.io/account/${address}`}
                target="_blank"
                rel="noopener noreferrer"
                className="p-2 rounded-lg text-amber-600 dark:text-amber-400 bg-white/60 dark:bg-gray-900/60 hover:bg-white/80 dark:hover:bg-gray-900/80 border border-amber-200 dark:border-amber-800 transition-all duration-200"
                title="View on Solscan"
              >
                <ExternalLink className="h-4 w-4" />
              </a>
            </div>
          </div>

          {/* Right Side - Token Holdings */}
          <div className="w-full lg:w-96 bg-white/30 dark:bg-gray-900/30 rounded-xl p-4 backdrop-blur-sm">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-amber-900 dark:text-amber-100">
                Holdings
              </h3>
              {lastUpdated && (
                <span className="text-xs text-amber-600 dark:text-amber-400">
                  {lastUpdated.toLocaleTimeString()}
                </span>
              )}
            </div>
            
            {loading ? (
              <div className="flex items-center justify-center py-12 text-amber-600 dark:text-amber-400">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-amber-600 dark:border-amber-400 mr-2"></div>
                Loading...
              </div>
            ) : tokenHoldings.length === 0 ? (
              <div className="text-center py-12 text-amber-600 dark:text-amber-400">
                No tokens found
              </div>
            ) : (
              <div className="grid grid-cols-4 md:grid-cols-6 lg:grid-cols-3 gap-2 max-h-64 overflow-y-auto">
                {tokenHoldings && tokenHoldings.length > 0 ? tokenHoldings.map((token, index) => (
                  <div 
                    key={token.mint || index} 
                    className="flex flex-col items-center justify-center p-2 rounded-lg bg-white/30 dark:bg-gray-900/30 hover:bg-white/50 dark:hover:bg-gray-900/50 transition-colors duration-200"
                    style={{ animationDelay: `${index * 50}ms` }}
                  >
                    {/* Token Icon */}
                    <div className="mb-1">
                      {token.logo ? (
                        <img 
                          src={token.logo} 
                          alt={token.symbol}
                          className="h-6 w-6 rounded-full"
                          onError={(e) => {
                            (e.target as HTMLImageElement).style.display = 'none'
                          }}
                        />
                      ) : (
                        <div className="h-6 w-6 rounded-full bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center">
                          <span className="text-white font-bold text-xs">
                            {token.symbol ? token.symbol.slice(0, 2) : '??'}
                          </span>
                        </div>
                      )}
                    </div>
                    
                    {/* Token Symbol */}
                    <div className="font-medium text-amber-900 dark:text-amber-100 text-xs text-center mb-1">
                      {token.symbol || 'Unknown'}
                    </div>
                    
                    {/* Token Amount */}
                    <div className="text-xs font-medium text-gray-600 dark:text-gray-400 text-center">
                      {parseFloat(token.amount || '0').toLocaleString(undefined, { 
                        maximumFractionDigits: 3
                      })}
                    </div>
                  </div>
                )) : (
                  <div className="col-span-full text-center py-12 text-amber-600 dark:text-amber-400">
                    No tokens found
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </Card>
  )
}