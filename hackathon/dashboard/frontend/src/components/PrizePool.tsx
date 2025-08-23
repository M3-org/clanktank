import { useState, useEffect } from 'react'
import { Copy, Check, ExternalLink, TrendingUp, Eye, X } from 'lucide-react'
import { Card } from './Card'
import { usePrizePool } from '../hooks/usePrizePool'
import { useCopyToClipboard } from '../hooks/useCopyToClipboard'
import { buildSponsorLink, isMobile as isMobileDevice } from '../utils/phantomLink'
import { PRIZE_WALLET, TOAST_MESSAGES } from '../lib/constants'
import { pretty } from '../lib/utils'

interface PrizePoolProps {
  goal?: number
  variant?: 'card' | 'banner' | 'marquee'
}

export function PrizePool({ goal = 10, variant = 'card' }: PrizePoolProps) {
  const [showTokenModal, setShowTokenModal] = useState(false)
  const [isVisible, setIsVisible] = useState(false)
  const [isHovering, setIsHovering] = useState(false)
  
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
  const { tokenHoldings, totalValue, loading, lastUpdated, connected } = prizePoolData

  // Auto-hide/show logic for marquee
  useEffect(() => {
    if (variant !== 'marquee') return

    const handleScroll = () => {
      const scrollY = window.scrollY
      const windowHeight = window.innerHeight
      const documentHeight = document.documentElement.scrollHeight
      
      // Show if scrolled down at least 200px or near bottom of page
      const shouldShow = scrollY > 200 || (scrollY + windowHeight > documentHeight - 100)
      setIsVisible(shouldShow)
    }

    const handleMouseMove = (e: MouseEvent) => {
      // Show if mouse is near bottom 100px of screen
      const nearBottom = e.clientY > window.innerHeight - 100
      setIsHovering(nearBottom)
    }

    window.addEventListener('scroll', handleScroll)
    window.addEventListener('mousemove', handleMouseMove)
    
    // Initial check
    handleScroll()

    return () => {
      window.removeEventListener('scroll', handleScroll)
      window.removeEventListener('mousemove', handleMouseMove)
    }
  }, [variant])

  if (variant === 'marquee') {
    if (loading) {
      return (
        <div className="fixed bottom-0 left-0 right-0 z-50 bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 border-t border-slate-700 backdrop-blur-sm">
          <div className="flex items-center justify-center h-16 px-4">
            <div className="animate-spin rounded-full h-4 w-4 border-2 border-cyan-400 border-t-transparent mr-2"></div>
            <span className="text-sm text-cyan-400">
              {connected ? 'Loading prize pool...' : 'Connecting to live updates...'}
            </span>
          </div>
        </div>
      )
    }

    return (
      <div className={`fixed bottom-0 left-0 right-0 z-50 bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 border-t border-slate-700 shadow-2xl backdrop-blur-sm transition-transform duration-300 ${
        isVisible || isHovering ? 'translate-y-0' : 'translate-y-full'
      }`}>
        {/* Progress Bar at Top */}
        <div className="relative h-1 bg-slate-700/50">
          <div 
            className="absolute inset-y-0 left-0 bg-gradient-to-r from-cyan-400 to-blue-500 transition-all duration-1000 ease-out"
            style={{ width: `${Math.min(progress, 100)}%` }}
          />
        </div>
        
        {/* Music Player UI */}
        <div className="h-16 px-4 flex items-center justify-between">
          {/* Left: Album Art + Track Info */}
          <div className="flex items-center gap-3 min-w-0 flex-1">
            <div className="w-10 h-10 rounded bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-white font-bold shadow-lg flex-shrink-0">
              💎
            </div>
            
            <div className="min-w-0 flex-1">
              <div className="text-white font-semibold text-sm truncate">
                Prize Pool • {pretty(totalValue)} SOL
              </div>
              <div className="text-slate-400 text-xs truncate">
                {progress.toFixed(1)}% of {goal} SOL goal • 
                {tokenHoldings.length > 0 && (
                  <span className="ml-1">
                    {tokenHoldings.slice(0, 3).map((token, i) => (
                      <span key={token.mint}>
                        {i > 0 && ' • '}
                        {token.symbol}: {pretty(parseFloat(token.amount))}
                      </span>
                    ))}
                    {tokenHoldings.length > 3 && ` • +${tokenHoldings.length - 3} more`}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Center: Transport Controls */}
          <div className="flex items-center gap-2 mx-4">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-white shadow-lg">
              <TrendingUp className="w-4 h-4" />
            </div>
            
            <a
              href={solscanUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="w-8 h-8 rounded-full bg-slate-700 hover:bg-slate-600 flex items-center justify-center text-cyan-400 hover:text-cyan-300 transition-all duration-200"
              title="View on Solscan"
            >
              <ExternalLink className="w-4 h-4" />
            </a>
          </div>

          {/* Right: Volume/Wallet Controls */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <button
              onClick={handleCopy}
              className="flex items-center gap-2 px-3 py-1.5 bg-slate-700/80 hover:bg-slate-600/80 rounded-full border border-slate-600 hover:border-cyan-400 transition-all duration-200 group"
              title="Copy wallet address"
            >
              <span className="text-slate-300 font-mono text-xs hidden lg:block">
                {PRIZE_WALLET}
              </span>
              <span className="text-slate-300 font-mono text-xs hidden md:block lg:hidden">
                {PRIZE_WALLET.slice(0, 16)}...{PRIZE_WALLET.slice(-8)}
              </span>
              <span className="text-slate-300 font-mono text-xs hidden sm:block md:hidden">
                {PRIZE_WALLET.slice(0, 8)}...{PRIZE_WALLET.slice(-6)}
              </span>
              <span className="text-slate-300 font-mono text-xs sm:hidden">
                {PRIZE_WALLET.slice(0, 4)}...{PRIZE_WALLET.slice(-4)}
              </span>
              {copied ? (
                <Check className="w-3 h-3 text-green-400" />
              ) : (
                <Copy className="w-3 h-3 text-cyan-400 group-hover:text-cyan-300" />
              )}
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (variant === 'banner') {
    if (loading) {
      return (
        <div className="flex items-center gap-2">
          <div className="animate-spin rounded-full h-3 w-3 border-2 border-gray-400 border-t-transparent"></div>
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {connected ? 'Loading prize pool...' : 'Connecting to live updates...'}
          </span>
        </div>
      )
    }

    return (
      <div className="flex items-center gap-2 sm:gap-3 lg:gap-4">
        {/* Prize Pool Info - Inline with footer links */}
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Prize Pool:
          </span>
          <span className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            {pretty(totalValue)} SOL
          </span>
        </div>
        
        {/* Progress Indicator - Simple text */}
        <div className="hidden sm:flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
          <span>({progress.toFixed(0)}% of {goal})</span>
        </div>

        {/* Actions - With address preview */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleCopy}
            className="flex items-center gap-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors font-mono text-xs"
            title="Copy wallet address"
          >
            <span className="hidden 2xl:inline">
              {PRIZE_WALLET}
            </span>
            <span className="hidden xl:inline 2xl:hidden">
              {PRIZE_WALLET.slice(0, 12)}...{PRIZE_WALLET.slice(-8)}
            </span>
            <span className="hidden lg:inline xl:hidden">
              {PRIZE_WALLET.slice(0, 8)}...{PRIZE_WALLET.slice(-6)}
            </span>
            <span className="hidden md:inline lg:hidden">
              {PRIZE_WALLET.slice(0, 6)}...{PRIZE_WALLET.slice(-4)}
            </span>
            {copied ? (
              <Check className="h-3 w-3 text-green-500" />
            ) : (
              <Copy className="h-3 w-3" />
            )}
          </button>
          
          <a
            href={solscanUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 transition-colors"
            title="View on Solscan"
          >
            <ExternalLink className="h-3 w-3" />
          </a>
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
                  {connected ? (
                    <>Live • Updated {new Date(lastUpdated).toLocaleTimeString()}</>
                  ) : (
                    <>Offline • Updated {new Date(lastUpdated).toLocaleTimeString()}</>
                  )}
                </span>
              )}
              {!lastUpdated && (
                <span className="text-xs text-brand-accent/50">
                  {connected ? 'Live updates connected' : 'Connecting...'}
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
export const PrizePoolMarquee = (props: PrizePoolProps) => <PrizePool {...props} variant="marquee" />