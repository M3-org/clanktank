import { useState, useEffect } from 'react'
import { Button } from './Button'
import { Card, CardContent } from './Card'
import { Coins, ExternalLink, Copy, Smartphone, Monitor, HelpCircle } from 'lucide-react'
import { cn } from '../lib/utils'

interface VotingSliderProps {
  submissionId: string
  projectName: string
  className?: string
}

export function VotingSlider({ submissionId, projectName, className }: VotingSliderProps) {
  const [tokenAmount, setTokenAmount] = useState(25)
  const [voteWeight, setVoteWeight] = useState(0)
  const [overflowTokens, setOverflowTokens] = useState(0)
  const [deepLink, setDeepLink] = useState('')
  const [copied, setCopied] = useState(false)
  const [showTooltip, setShowTooltip] = useState(false)
  
  // Vote weight calculation: min(log10(tokens + 1) * 3, 10)
  useEffect(() => {
    const maxVoteTokens = 100
    const votingTokens = Math.min(tokenAmount, maxVoteTokens)
    const calculatedWeight = Math.min(Math.log10(votingTokens + 1) * 3, 10)
    const overflow = Math.max(0, tokenAmount - maxVoteTokens)
    
    setVoteWeight(calculatedWeight)
    setOverflowTokens(overflow)
    
    // Generate Phantom deep-link
    const ai16zMint = 'HeLp6NuQkmYB4pYWo2zYs22mESHXPQYzXbB8n4V98jwC'
    const receiverWallet = import.meta.env.VITE_VOTING_WALLET_ADDRESS || 'AiMarcWallet123...' // TODO: Get from env
    const memoText = `vote:${submissionId}`
    
    const phantomLink = `phantom://transfer?mint=${ai16zMint}&amount=${tokenAmount}&recipient=${receiverWallet}&memo=${encodeURIComponent(memoText)}`
    setDeepLink(phantomLink)
  }, [tokenAmount, submissionId])
  
  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }
  
  const openPhantom = () => {
    window.open(deepLink, '_blank')
  }
  
  // Power bar color coding - reversed progression with dopamine-inducing overflow
  const getSliderColor = () => {
    if (tokenAmount <= 10) return 'from-blue-400 to-blue-600' // Starting tier
    if (tokenAmount <= 50) return 'from-indigo-400 to-purple-500' // Building tier
    if (tokenAmount <= 100) return 'from-purple-500 to-pink-500' // Strong tier
    return 'from-pink-500 via-rose-400 to-yellow-400' // Overflow - rainbow dopamine hit!
  }

  const getVotePowerTier = () => {
    if (tokenAmount <= 10) return { color: 'text-blue-600 dark:text-blue-400' }
    if (tokenAmount <= 50) return { color: 'text-indigo-600 dark:text-indigo-400' }
    if (tokenAmount <= 100) return { color: 'text-purple-600 dark:text-purple-400' }
    return { color: 'text-pink-600 dark:text-pink-400' }
  }

  return (
    <Card className={cn("bg-white dark:bg-gray-900", className)}>
      <CardContent className="p-6">
        <div className="space-y-6">
          {/* Header */}
          <div className="text-center">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
              Vote for "{projectName}"
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Send ai16z tokens to cast your community vote
            </p>
          </div>
          
          {/* Token Amount Slider */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Token Amount
              </label>
              <div className="flex items-center gap-2">
                <Coins className="h-4 w-4 text-yellow-500" />
                <span className="text-lg font-bold text-gray-900 dark:text-gray-100">
                  {tokenAmount} ai16z
                </span>
              </div>
            </div>
            
            <div className="relative">
              {/* Power Bar Background with Tier Sections */}
              <div className="w-full h-6 bg-gray-200 dark:bg-gray-700 rounded-lg overflow-hidden relative">
                {/* Tier indicators */}
                <div className="absolute inset-0 flex">
                  <div className="w-[4%] bg-blue-100 dark:bg-blue-900 opacity-50"></div>
                  <div className="w-[16%] bg-indigo-100 dark:bg-indigo-900 opacity-50"></div>
                  <div className="w-[20%] bg-purple-100 dark:bg-purple-900 opacity-50"></div>
                  <div className="w-[60%] bg-gradient-to-r from-pink-100 to-yellow-100 dark:from-pink-900 dark:to-yellow-900 opacity-50"></div>
                </div>
                
                {/* Active power bar */}
                <div 
                  className={`h-full bg-gradient-to-r ${getSliderColor()} transition-all duration-300 ease-out shadow-lg relative overflow-hidden`}
                  style={{ width: `${(tokenAmount / 250) * 100}%` }}
                >
                  {/* Glow effect */}
                  <div className="w-full h-full bg-gradient-to-r from-transparent via-white/20 to-transparent"></div>
                  {/* Shimmer effect for overflow */}
                  {overflowTokens > 0 && (
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent animate-ping"></div>
                  )}
                </div>
                
                {/* Vote cap marker */}
                <div className="absolute top-0 h-full w-0.5 bg-white dark:bg-gray-300 shadow-md" style={{ left: '40%' }}>
                  <div className="absolute -top-1 left-1/2 transform -translate-x-1/2 w-2 h-2 bg-white dark:bg-gray-300 rounded-full shadow-md"></div>
                </div>
              </div>
              
              {/* Invisible slider for interaction */}
              <input
                type="range"
                min="1"
                max="250"
                value={tokenAmount}
                onChange={(e) => setTokenAmount(Number(e.target.value))}
                className="absolute inset-0 w-full h-6 opacity-0 cursor-pointer"
              />
              
              {/* Token ranges */}
              <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-2">
                <span className="text-blue-600 dark:text-blue-400">1-10</span>
                <span className="text-indigo-600 dark:text-indigo-400">11-50</span>
                <span className="text-purple-600 dark:text-purple-400">51-100</span>
                <span className="text-pink-600 dark:text-pink-400">101-250</span>
              </div>
            </div>
            
            {/* Quick Amount Buttons */}
            <div className="flex gap-2 justify-center">
              {[10, 25, 50, 100, 150].map((amount) => {
                const tierColor = amount <= 10 ? 'text-blue-600 dark:text-blue-400' : 
                                amount <= 50 ? 'text-indigo-600 dark:text-indigo-400' : 
                                amount <= 100 ? 'text-purple-600 dark:text-purple-400' : 
                                'text-pink-600 dark:text-pink-400'
                return (
                  <Button
                    key={amount}
                    variant="ghost"
                    size="sm"
                    onClick={() => setTokenAmount(amount)}
                    className={cn(
                      "px-3 py-1 text-xs border transition-all duration-200",
                      tokenAmount === amount 
                        ? `bg-opacity-20 border-current ${tierColor} font-semibold` 
                        : `${tierColor} border-transparent hover:border-current hover:bg-opacity-10`
                    )}
                  >
                    {amount}
                  </Button>
                )
              })}
            </div>
          </div>
          
          {/* Vote Impact Display */}
          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 space-y-3">
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600 dark:text-gray-400">Vote Weight:</span>
                <div className="relative">
                  <button
                    onMouseEnter={() => setShowTooltip(true)}
                    onMouseLeave={() => setShowTooltip(false)}
                    className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                  >
                    <HelpCircle className="h-3 w-3" />
                  </button>
                  {showTooltip && (
                    <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 w-72 p-3 bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 text-xs rounded-lg shadow-lg z-10">
                      <div className="text-center">
                        <strong>Secure Voting:</strong> Votes are processed via Helius webhooks. 
                        Transaction signatures are recorded to prevent double-voting. 
                        Your wallet address remains visible on-chain.
                      </div>
                      <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-900 dark:border-t-gray-100"></div>
                    </div>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-lg font-bold ${getVotePowerTier().color}`}>
                  {tokenAmount <= 100 ? voteWeight.toFixed(1) : '10.0'} / 10
                </span>
                {/* Vote power bar */}
                <div className="w-16 h-2 bg-gray-300 dark:bg-gray-600 rounded-full overflow-hidden">
                  <div 
                    className={`h-full bg-gradient-to-r ${getSliderColor()} transition-all duration-300`}
                    style={{ width: `${tokenAmount <= 100 ? (voteWeight / 10) * 100 : 100}%` }}
                  ></div>
                </div>
              </div>
            </div>
            
            {overflowTokens > 0 && (
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 dark:text-gray-400">Overflow to Prize Pool:</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-pink-600 dark:text-pink-400">
                    +{overflowTokens} ai16z
                  </span>
                  <div className="flex items-center">
                    <span className="text-lg animate-pulse">🎁</span>
                  </div>
                </div>
              </div>
            )}
            
          </div>
          
          {/* Voting Actions */}
          <div className="space-y-4">
            {/* Mobile Voting */}
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Smartphone className="h-4 w-4 text-gray-500" />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Mobile Voting (Recommended)
                </span>
              </div>
              <Button onClick={openPhantom} className="w-full">
                <ExternalLink className="h-4 w-4 mr-2" />
                Vote with Phantom Wallet
              </Button>
            </div>
            
            {/* Desktop Voting */}
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Monitor className="h-4 w-4 text-gray-500" />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Desktop Instructions
                </span>
              </div>
              
              <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 space-y-2">
                <div className="text-xs text-gray-600 dark:text-gray-400">
                  1. Copy recipient address and memo
                  2. Open your Solana wallet
                  3. Send {tokenAmount} ai16z tokens with the memo
                </div>
                
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-500">Recipient:</span>
                    <code className="flex-1 text-xs bg-white dark:bg-gray-900 px-2 py-1 rounded border font-mono">
                      {import.meta.env.VITE_VOTING_WALLET_ADDRESS || 'AiMarcWallet123...'}
                    </code>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyToClipboard(import.meta.env.VITE_VOTING_WALLET_ADDRESS || 'AiMarcWallet123...')}
                    >
                      <Copy className="h-3 w-3" />
                    </Button>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-500">Memo:</span>
                    <code className="flex-1 text-xs bg-white dark:bg-gray-900 px-2 py-1 rounded border font-mono">
                      vote:{submissionId}
                    </code>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyToClipboard(`vote:${submissionId}`)}
                    >
                      <Copy className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              </div>
            </div>
            
            {copied && (
              <div className="text-center text-xs text-green-600 dark:text-green-400">
                ✓ Copied to clipboard!
              </div>
            )}
          </div>
          
        </div>
      </CardContent>
    </Card>
  )
}