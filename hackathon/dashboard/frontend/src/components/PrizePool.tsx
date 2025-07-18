import { useState } from 'react'
import { Copy, Check, ExternalLink, TrendingUp, Eye, X } from 'lucide-react'
import { Card } from './Card'
import { usePrizePool } from '../hooks/usePrizePool'
import { useCopyToClipboard } from '../hooks/useCopyToClipboard'
import { buildSponsorLink, isMobile as isMobileDevice } from '../utils/phantomLink'
import { PRIZE_WALLET, TOAST_MESSAGES } from '../lib/constants'
import { pretty } from '../lib/utils'

interface PrizePoolProps {
  goal?: number
  variant?: 'card' | 'banner'
}

export function PrizePool({ goal = 10, variant = 'card' }: PrizePoolProps) {
  const [showTokenModal, setShowTokenModal] = useState(false)
  
  // Prize pool data
  const prizePoolData = usePrizePool()
  const { copied, copyToClipboard } = useCopyToClipboard()
  
  // Derived values
  const progress = Math.min((prizePoolData.totalValue / goal) * 100, 100)
  const solscanUrl = `https://solscan.io/account/${PRIZE_WALLET}`
  
  // Handlers
  const handleCopy = () => {
    copyToClipboard(PRIZE_WALLET, TOAST_MESSAGES.ADDRESS_COPIED)
  }

  const handleDonate = () => {
    if (isMobileDevice()) {
      const donateLink = buildSponsorLink({ amount: 1, memo: 'prize-pool-donation' })
      window.open(donateLink, '_blank')
    } else {
      handleCopy()
    }
  }
  
  // Destructure for easier access
  const { tokenHoldings, totalValue, loading, lastUpdated } = prizePoolData

  if (variant === 'banner') {
    if (loading) {
      return (
        <div className="bg-gradient-to-br from-brand-dark via-brand-mid to-brand-dark border border-brand-accent/20 rounded-lg p-3 mb-6">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-4 w-4 border-2 border-brand-accent border-t-transparent mr-2"></div>
            <span className="text-sm text-brand-accent/80">Loading prize pool...</span>
          </div>
        </div>
      )
    }

    return (
      <div className="bg-gradient-to-br from-brand-dark via-brand-mid to-brand-dark border border-brand-accent/20 rounded-lg p-3 mb-6">
        <div className="flex items-center justify-between">
          {/* Left: Prize Pool Info */}
          <div className="flex items-center gap-3">
            <div className="h-6 w-6 rounded bg-gradient-to-br from-brand-accent to-cyan-500 flex items-center justify-center text-sm">
              💎
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-brand-accent/80">
                  PRIZE POOL
                </span>
                <span className="text-lg font-black text-white">
                  {pretty(totalValue)} SOL
                </span>
              </div>
              <div className="flex items-center gap-2 text-xs text-brand-accent/70">
                <TrendingUp className="h-3 w-3" />
                <span>{progress.toFixed(0)}% of {goal} SOL goal</span>
              </div>
            </div>
          </div>

          {/* Right: Contribute Button */}
          <div className="flex items-center gap-2">
            <button
              onClick={handleCopy}
              className="flex items-center gap-1 px-3 py-1.5 bg-brand-mid/60 hover:bg-brand-mid/80 rounded border border-brand-accent/20 hover:border-brand-accent/40 transition-all duration-200 group text-xs"
            >
              <span className="text-slate-300 font-mono hidden sm:block">
                {PRIZE_WALLET.slice(0, 8)}...{PRIZE_WALLET.slice(-6)}
              </span>
              <span className="text-slate-300 font-mono sm:hidden">
                {PRIZE_WALLET.slice(0, 6)}...{PRIZE_WALLET.slice(-4)}
              </span>
              {copied ? (
                <Check className="h-3 w-3 text-green-400" />
              ) : (
                <Copy className="h-3 w-3 text-brand-accent group-hover:text-cyan-300" />
              )}
            </button>
            
            <a
              href={solscanUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="p-1.5 rounded text-brand-accent hover:text-cyan-300 bg-brand-mid/60 hover:bg-brand-mid/80 border border-brand-accent/20 hover:border-brand-accent/40 transition-all duration-200"
              title="View on Solscan"
            >
              <ExternalLink className="h-3 w-3" />
            </a>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mt-2">
          <div className="relative h-1.5 bg-brand-mid/40 rounded-full overflow-hidden">
            <div 
              className="h-full bg-brand-accent rounded-full transition-all duration-1000 ease-out"
              style={{ width: `${Math.min(progress, 100)}%` }}
            />
          </div>
        </div>
      </div>
    )
  }

  // Card variant (original PrizePoolCard)
  return (
    <>
      <Card className="overflow-hidden bg-gradient-to-br from-brand-dark via-brand-mid to-brand-dark border border-brand-accent/20 hover:shadow-lg hover:shadow-brand-accent/10 transition-shadow duration-300">
        <section className="grid gap-6 lg:grid-cols-[1fr_auto] p-6">
          {/* Header */}
          <header>
            <h2 className="text-sm font-semibold text-brand-accent/80 mb-2">HACKATHON PRIZE POOL</h2>
            <span className="text-4xl font-black text-white leading-none">{pretty(totalValue)}</span>
            <span className="text-sm text-brand-accent/70 ml-2">SOL</span>
          </header>

          {/* Progress */}
          <div className="lg:self-center">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-brand-accent/70">{progress.toFixed(0)}% of {goal} SOL</span>
              {lastUpdated && (
                <span className="text-xs text-brand-accent/50">
                  Updated {new Date(lastUpdated).toLocaleTimeString()}
                </span>
              )}
            </div>
            <div 
              role="progressbar"
              aria-valuenow={progress}
              aria-valuemax={100}
              className="relative h-2 bg-brand-mid/40 rounded-full overflow-hidden"
            >
              <div 
                className="absolute inset-0 bg-brand-accent transition-[width] duration-700"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>

          {/* Address + CTA */}
          <div className="lg:col-span-2">
            <h3 className="text-xs font-semibold text-brand-accent/80 mb-2">Wallet Address</h3>
            <div className="flex gap-2 mb-3">
              <button
                onClick={handleCopy}
                className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-brand-mid/60 hover:bg-brand-mid/80 rounded-lg border border-brand-accent/20 hover:border-brand-accent/40 transition-all duration-200 group"
              >
                <span className="font-mono text-xs text-slate-300 truncate">
                  <span className="hidden md:inline">{PRIZE_WALLET}</span>
                  <span className="hidden sm:inline md:hidden">{PRIZE_WALLET.slice(0, 16)}...{PRIZE_WALLET.slice(-8)}</span>
                  <span className="inline sm:hidden">{PRIZE_WALLET.slice(0, 12)}...{PRIZE_WALLET.slice(-6)}</span>
                </span>
                {copied ? (
                  <Check className="h-3 w-3 text-green-400 flex-shrink-0" />
                ) : (
                  <Copy className="h-3 w-3 text-brand-accent group-hover:text-cyan-300 flex-shrink-0" />
                )}
              </button>
              
              <a
                href={solscanUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="p-2 rounded-lg text-brand-accent hover:text-cyan-300 bg-brand-mid/60 hover:bg-brand-mid/80 border border-brand-accent/20 hover:border-brand-accent/40 transition-all duration-200"
                title="View on Solscan"
              >
                <ExternalLink className="h-3 w-3" />
              </a>
              
              <button
                onClick={handleDonate}
                className="px-4 py-2 bg-brand-accent hover:bg-cyan-300 text-white rounded-lg font-medium text-sm transition-colors duration-200"
              >
                Donate →
              </button>
            </div>

            {/* Token breakdown */}
            <div className="space-y-2">
              {tokenHoldings.slice(0, 3).map((token) => (
                <div key={token.mint} className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-brand-accent"></div>
                    <span className="text-slate-300">{token.symbol}</span>
                  </div>
                  <span className="text-brand-accent/80">{pretty(parseFloat(token.amount))}</span>
                </div>
              ))}
              
              {tokenHoldings.length > 3 && (
                <button
                  onClick={() => setShowTokenModal(true)}
                  className="flex items-center gap-1 text-xs text-brand-accent hover:text-cyan-300 transition-colors"
                >
                  <Eye className="h-3 w-3" />
                  View all {tokenHoldings.length} tokens
                </button>
              )}
            </div>
          </div>
        </section>
      </Card>

      {/* Token Modal */}
      {showTokenModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto" aria-modal="true" role="dialog">
          <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
            {/* Backdrop */}
            <div 
              className="fixed inset-0 bg-black/50 transition-opacity" 
              onClick={() => setShowTokenModal(false)}
              aria-hidden="true"
            />
            
            {/* Modal panel */}
            <div className="relative transform overflow-hidden rounded-lg bg-gradient-to-br from-brand-dark via-brand-mid to-brand-dark border border-brand-accent/20 px-4 pb-4 pt-5 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-2xl sm:p-6">
              {/* Header */}
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-brand-accent">
                  All Token Holdings
                </h3>
                <button
                  onClick={() => setShowTokenModal(false)}
                  className="rounded-md text-slate-400 hover:text-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-accent"
                  aria-label="Close modal"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>

              {/* Token grid */}
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 max-h-96 overflow-y-auto">
                {tokenHoldings.map((token) => (
                  <div 
                    key={token.mint}
                    className="flex flex-col items-center p-3 rounded-lg bg-brand-mid/60 border border-brand-accent/20 hover:border-brand-accent/40 transition-all duration-200"
                  >
                    <div className="mb-2">
                      {token.logo ? (
                        <img 
                          src={token.logo} 
                          alt={token.symbol}
                          className="h-8 w-8 rounded-full"
                          onError={(e) => {
                            (e.target as HTMLImageElement).style.display = 'none'
                          }}
                        />
                      ) : (
                        <div className="h-8 w-8 rounded-full bg-gradient-to-br from-brand-accent to-cyan-500 flex items-center justify-center">
                          <span className="text-white font-bold text-sm">
                            {token.symbol ? token.symbol.slice(0, 2) : '??'}
                          </span>
                        </div>
                      )}
                    </div>
                    
                    <div className="text-sm font-medium text-white text-center truncate w-full">
                      {token.symbol || 'Unknown'}
                    </div>
                    
                    <div className="text-sm text-brand-accent text-center mt-1">
                      {pretty(parseFloat(token.amount || '0'))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

// Legacy exports for backward compatibility
export const PrizePoolCard = (props: PrizePoolProps) => <PrizePool {...props} variant="card" />
export const PrizePoolBanner = (props: PrizePoolProps) => <PrizePool {...props} variant="banner" />