import { useState, useEffect } from 'react'
import { Card, CardHeader, CardContent } from '../../components/Card'
import { Button } from '../../components/Button'
import { WalletVoting } from '../../components/WalletVoting'
import { DiscordAvatar } from '../../components/DiscordAvatar'
import { hackathonApi } from '../../lib/api'
import { LeaderboardEntry, CommunityScore, PrizePoolData, TokenBreakdown } from '../../types'
import { 
  Coins, 
  Zap, 
  MessageSquare, 
  Star, 
  Trophy,
  DollarSign,
  RefreshCw,
  TrendingUp,
  ArrowUp,
  Crown,
  Rocket,
  Flame,
  Gavel,
  Timer,
  Clock,
  Copy,
  Smartphone,
  Monitor,
  HelpCircle,
  Vote,
  Medal
} from 'lucide-react'
import { cn } from '../../lib/utils'

// Mock data for prototyping
const mockSubmission = {
  submission_id: 'test-123',
  project_name: 'AI Trading Bot',
  current_votes: 42,
  current_superchats: 7,
  vote_power: 156.5
}

// VotingSlider Component (merged from components)
interface VotingSliderProps {
  submissionId: string
  projectName: string
  className?: string
}

function VotingSlider({ submissionId, projectName, className }: VotingSliderProps) {
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
              <Button onClick={openPhantom} className="w-full" style={{ backgroundColor: '#AB9FF2', color: '#FFFDF8' }} onMouseEnter={(e: React.MouseEvent<HTMLButtonElement>) => e.currentTarget.style.backgroundColor = '#9A8FF0'} onMouseLeave={(e: React.MouseEvent<HTMLButtonElement>) => e.currentTarget.style.backgroundColor = '#AB9FF2'}>
                <PhantomLogo className="h-4 w-4 mr-2" />
                Vote with Phantom Mobile
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

// Prototype 1: Current PowerBar System
function PowerBarPrototype() {
  return (
    <Card className="bg-white dark:bg-gray-900">
      <CardHeader>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          PowerBar (Current)
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Interactive slider with logarithmic scaling
        </p>
      </CardHeader>
      <CardContent>
        <VotingSlider 
          submissionId={mockSubmission.submission_id}
          projectName={mockSubmission.project_name}
        />
      </CardContent>
    </Card>
  )
}

// Phantom Logo SVG Component for prototypes
const PhantomLogo = ({ className = "h-4 w-4" }: { className?: string }) => (
  <svg viewBox="0 0 128 128" className={className} fill="none">
    <rect width="128" height="128" fill="#AB9FF2"/>
    <path fillRule="evenodd" clipRule="evenodd" d="M55.6416 82.1477C50.8744 89.4525 42.8862 98.6966 32.2568 98.6966C27.232 98.6966 22.4004 96.628 22.4004 87.6424C22.4004 64.7584 53.6445 29.3335 82.6339 29.3335C99.1257 29.3335 105.697 40.7755 105.697 53.7689C105.697 70.4471 94.8739 89.5171 84.1156 89.5171C80.7013 89.5171 79.0264 87.6424 79.0264 84.6688C79.0264 83.8931 79.1552 83.0527 79.4129 82.1477C75.7409 88.4182 68.6546 94.2361 62.0192 94.2361C57.1877 94.2361 54.7397 91.1979 54.7397 86.9314C54.7397 85.3799 55.0618 83.7638 55.6416 82.1477ZM80.6133 53.3182C80.6133 57.1044 78.3795 58.9975 75.8806 58.9975C73.3438 58.9975 71.1479 57.1044 71.1479 53.3182C71.1479 49.532 73.3438 47.6389 75.8806 47.6389C78.3795 47.6389 80.6133 49.532 80.6133 53.3182ZM94.8102 53.3184C94.8102 57.1046 92.5763 58.9977 90.0775 58.9977C87.5407 58.9977 85.3447 57.1046 85.3447 53.3184C85.3447 49.5323 87.5407 47.6392 90.0775 47.6392C92.5763 47.6392 94.8102 49.5323 94.8102 53.3184Z" fill="#FFFDF8"/>
  </svg>
)

// Prototype 2: Action Buttons System
function ActionButtonsPrototype() {
  const [voteCount] = useState(mockSubmission.current_votes)
  const [superchatCount] = useState(mockSubmission.current_superchats)
  const [votePower] = useState(mockSubmission.vote_power)
  const [showVoteInstructions, setShowVoteInstructions] = useState(false)
  const [showSuperchatInstructions, setShowSuperchatInstructions] = useState(false)
  const [copied, setCopied] = useState('')

  const copyToClipboard = async (text: string, type: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(type)
      setTimeout(() => setCopied(''), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const handleVote = () => {
    setShowVoteInstructions(true)
  }

  const handleSuperchat = () => {
    if (superchatCount < 10) {
      setShowSuperchatInstructions(true)
    }
  }

  return (
    <Card className="bg-white dark:bg-gray-900">
      <CardHeader>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Action Buttons
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Simple actions with clear outcomes
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Visual Power Bar */}
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Community Power
            </span>
            <span className="text-lg font-bold text-indigo-600 dark:text-indigo-400">
              {votePower.toFixed(1)}
            </span>
          </div>
          <div className="w-full h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-500"
              style={{ width: `${Math.min((votePower / 500) * 100, 100)}%` }}
            />
          </div>
        </div>

        {/* Action Buttons */}
        <div className="grid grid-cols-2 gap-3">
          <Button
            onClick={handleVote}
            variant="outline"
            className="flex flex-col items-center gap-2 h-20 border-blue-200 hover:border-blue-400 hover:bg-blue-50 dark:border-blue-800 dark:hover:border-blue-600"
          >
            <ArrowUp className="h-5 w-5 text-blue-600" />
            <div className="text-center">
              <div className="text-sm font-medium text-blue-600">Vote</div>
              <div className="text-xs text-gray-500">1 ai16z</div>
            </div>
          </Button>

          <Button
            onClick={handleSuperchat}
            disabled={superchatCount >= 10}
            variant="outline"
            className="flex flex-col items-center gap-2 h-20 border-purple-200 hover:border-purple-400 hover:bg-purple-50 dark:border-purple-800 dark:hover:border-purple-600 disabled:opacity-50"
          >
            <MessageSquare className="h-5 w-5 text-purple-600" />
            <div className="text-center">
              <div className="text-sm font-medium text-purple-600">Superchat</div>
              <div className="text-xs text-gray-500">10 ai16z</div>
            </div>
          </Button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-4 pt-2">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{voteCount}</div>
            <div className="text-xs text-gray-500">Votes</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">{superchatCount}/10</div>
            <div className="text-xs text-gray-500">Superchats</div>
          </div>
        </div>

        {/* Vote Instructions Modal */}
        {showVoteInstructions && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-gray-900 rounded-lg p-6 max-w-md w-full space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold">Cast Your Vote</h3>
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={() => setShowVoteInstructions(false)}
                >
                  ✕
                </Button>
              </div>
              
              {/* Mobile */}
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Smartphone className="h-4 w-4" />
                  <span className="font-medium">Mobile (Recommended)</span>
                </div>
                <Button 
                  className="w-full"
                  style={{ backgroundColor: '#AB9FF2', color: '#FFFDF8' }}
                  onMouseEnter={(e: React.MouseEvent<HTMLButtonElement>) => e.currentTarget.style.backgroundColor = '#9A8FF0'}
                  onMouseLeave={(e: React.MouseEvent<HTMLButtonElement>) => e.currentTarget.style.backgroundColor = '#AB9FF2'}
                  onClick={() => window.open(`phantom://transfer?mint=HeLp6NuQkmYB4pYWo2zYs22mESHXPQYzXbB8n4V98jwC&amount=1&recipient=AiMarcWallet123&memo=${encodeURIComponent(`vote:${mockSubmission.submission_id}`)}`)}
                >
                  <PhantomLogo className="h-4 w-4 mr-2" />
                  Vote with Phantom Mobile
                </Button>
              </div>

              {/* Desktop */}
              <div className="space-y-3 border-t pt-4">
                <div className="flex items-center gap-2">
                  <Monitor className="h-4 w-4" />
                  <span className="font-medium">Desktop Instructions</span>
                </div>
                
                <div className="space-y-2 text-sm">
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500 min-w-[80px]">Recipient:</span>
                    <code className="flex-1 bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded font-mono text-xs">
                      AiMarcWallet123...
                    </code>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyToClipboard('AiMarcWallet123...', 'recipient')}
                    >
                      <Copy className="h-3 w-3" />
                    </Button>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500 min-w-[80px]">Amount:</span>
                    <code className="flex-1 bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded font-mono text-xs">
                      1 ai16z
                    </code>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyToClipboard('1', 'amount')}
                    >
                      <Copy className="h-3 w-3" />
                    </Button>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500 min-w-[80px]">Memo:</span>
                    <code className="flex-1 bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded font-mono text-xs">
                      vote:{mockSubmission.submission_id}
                    </code>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyToClipboard(`vote:${mockSubmission.submission_id}`, 'memo')}
                    >
                      <Copy className="h-3 w-3" />
                    </Button>
                  </div>
                </div>

                {copied && (
                  <div className="text-center text-xs text-green-600">
                    ✓ {copied} copied to clipboard!
                  </div>
                )}
              </div>

              <div className="text-xs text-gray-500 text-center border-t pt-4">
                One vote per wallet. Send exactly 1 ai16z with the memo to cast your vote.
              </div>
            </div>
          </div>
        )}

        {/* Superchat Instructions Modal */}
        {showSuperchatInstructions && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-gray-900 rounded-lg p-6 max-w-md w-full space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold">Send a Superchat</h3>
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={() => setShowSuperchatInstructions(false)}
                >
                  ✕
                </Button>
              </div>
              
              {/* Mobile */}
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Smartphone className="h-4 w-4" />
                  <span className="font-medium">Mobile (Recommended)</span>
                </div>
                <Button 
                  className="w-full"
                  style={{ backgroundColor: '#AB9FF2', color: '#FFFDF8' }}
                  onMouseEnter={(e: React.MouseEvent<HTMLButtonElement>) => e.currentTarget.style.backgroundColor = '#9A8FF0'}
                  onMouseLeave={(e: React.MouseEvent<HTMLButtonElement>) => e.currentTarget.style.backgroundColor = '#AB9FF2'}
                  onClick={() => window.open(`phantom://transfer?mint=HeLp6NuQkmYB4pYWo2zYs22mESHXPQYzXbB8n4V98jwC&amount=10&recipient=AiMarcWallet123&memo=${encodeURIComponent(`superchat:${mockSubmission.submission_id}`)}`)}
                >
                  <PhantomLogo className="h-4 w-4 mr-2" />
                  Superchat with Phantom Mobile
                </Button>
              </div>

              {/* Desktop */}
              <div className="space-y-3 border-t pt-4">
                <div className="flex items-center gap-2">
                  <Monitor className="h-4 w-4" />
                  <span className="font-medium">Desktop Instructions</span>
                </div>
                
                <div className="space-y-2 text-sm">
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500 min-w-[80px]">Recipient:</span>
                    <code className="flex-1 bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded font-mono text-xs">
                      AiMarcWallet123...
                    </code>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyToClipboard('AiMarcWallet123...', 'recipient')}
                    >
                      <Copy className="h-3 w-3" />
                    </Button>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500 min-w-[80px]">Amount:</span>
                    <code className="flex-1 bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded font-mono text-xs">
                      10 ai16z
                    </code>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyToClipboard('10', 'amount')}
                    >
                      <Copy className="h-3 w-3" />
                    </Button>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500 min-w-[80px]">Memo:</span>
                    <code className="flex-1 bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded font-mono text-xs">
                      superchat:{mockSubmission.submission_id}
                    </code>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyToClipboard(`superchat:${mockSubmission.submission_id}`, 'memo')}
                    >
                      <Copy className="h-3 w-3" />
                    </Button>
                  </div>
                </div>

                {copied && (
                  <div className="text-center text-xs text-green-600">
                    ✓ {copied} copied to clipboard!
                  </div>
                )}
              </div>

              <div className="text-xs text-gray-500 text-center border-t pt-4">
                One superchat per wallet. Max 10 superchats per project. Send exactly 10 ai16z with the memo.
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// Prototype 3: Gaming Credits System
function CreditsPrototype() {
  const [credits, setCredits] = useState(0)
  const [spent, setSpent] = useState({ boost: 0, highlight: 0, premium: 0 })

  const actions = [
    { name: 'Boost', cost: 5, icon: Zap, color: 'yellow', description: '+5 vote power' },
    { name: 'Highlight', cost: 15, icon: Star, color: 'blue', description: 'Feature project' },
    { name: 'Premium', cost: 25, icon: Crown, color: 'purple', description: 'VIP treatment' }
  ]

  return (
    <Card className="bg-white dark:bg-gray-900">
      <CardHeader>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Gaming Credits
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Buy credits, spend on power-ups
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Credits Balance */}
        <div className="text-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <div className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-1">
            {credits} Credits
          </div>
          <Button 
            onClick={() => setCredits(prev => prev + 10)}
            size="sm"
            className="bg-green-600 hover:bg-green-700"
          >
            Buy 10 Credits (10 ai16z)
          </Button>
        </div>

        {/* Power-ups */}
        <div className="space-y-3">
          {actions.map((action) => {
            const Icon = action.icon
            const canAfford = credits >= action.cost
            const colorClasses = {
              yellow: 'text-yellow-600 border-yellow-200 hover:border-yellow-400',
              blue: 'text-blue-600 border-blue-200 hover:border-blue-400',
              purple: 'text-purple-600 border-purple-200 hover:border-purple-400'
            }

            return (
              <div key={action.name} className="flex items-center gap-3 p-3 border rounded-lg">
                <Icon className={`h-6 w-6 ${colorClasses[action.color as keyof typeof colorClasses]}`} />
                <div className="flex-1">
                  <div className="font-medium text-gray-900 dark:text-gray-100">{action.name}</div>
                  <div className="text-sm text-gray-500">{action.description}</div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium text-gray-900 dark:text-gray-100">{action.cost} credits</div>
                  <Button
                    size="sm"
                    disabled={!canAfford}
                    onClick={() => {
                      if (canAfford) {
                        setCredits(prev => prev - action.cost)
                        setSpent(prev => ({ ...prev, [action.name.toLowerCase()]: prev[action.name.toLowerCase() as keyof typeof prev] + 1 }))
                      }
                    }}
                    className="mt-1"
                  >
                    Use ({spent[action.name.toLowerCase() as keyof typeof spent]})
                  </Button>
                </div>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}

// Prototype 4: Reaction System
function ReactionsPrototype() {
  const [reactions, setReactions] = useState({ fire: 0, love: 0, rocket: 0, gem: 0 })

  const reactionTypes = [
    { emoji: '🔥', name: 'fire', cost: 1, label: 'Fire' },
    { emoji: '❤️', name: 'love', cost: 2, label: 'Love' },
    { emoji: '🚀', name: 'rocket', cost: 5, label: 'Rocket' },
    { emoji: '💎', name: 'gem', cost: 10, label: 'Diamond' }
  ]

  return (
    <Card className="bg-white dark:bg-gray-900">
      <CardHeader>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Reactions
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Express support with token-powered reactions
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Reaction Grid */}
        <div className="grid grid-cols-2 gap-3">
          {reactionTypes.map((reaction) => (
            <Button
              key={reaction.name}
              onClick={() => setReactions(prev => ({ ...prev, [reaction.name]: prev[reaction.name as keyof typeof prev] + 1 }))}
              variant="outline"
              className="flex flex-col items-center gap-2 h-20 hover:scale-105 transition-transform"
            >
              <div className="text-2xl">{reaction.emoji}</div>
              <div className="text-center">
                <div className="text-sm font-medium">{reaction.label}</div>
                <div className="text-xs text-gray-500">{reaction.cost} ai16z</div>
              </div>
            </Button>
          ))}
        </div>

        {/* Reaction Count */}
        <div className="flex justify-between items-center pt-2 border-t">
          {reactionTypes.map((reaction) => (
            <div key={reaction.name} className="flex items-center gap-1">
              <span className="text-lg">{reaction.emoji}</span>
              <span className="text-sm font-medium">{reactions[reaction.name as keyof typeof reactions]}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

// Prototype 5: Rocket Fuel Tank (Episode Integration)
function FuelTankPrototype() {
  const [fuelLevel, setFuelLevel] = useState(25)
  const [, setFuelType] = useState('regular')
  
  const fuelTypes = [
    { name: 'regular', cost: 1, boost: 1, color: 'blue', icon: Coins },
    { name: 'premium', cost: 5, boost: 3, color: 'purple', icon: Zap },
    { name: 'rocket', cost: 15, boost: 10, color: 'orange', icon: Rocket }
  ]

  const handleFuel = (type: string) => {
    const fuelInfo = fuelTypes.find(f => f.name === type)
    if (fuelInfo) {
      setFuelLevel(prev => Math.min(prev + fuelInfo.boost, 100))
      setFuelType(type)
    }
  }

  return (
    <Card className="bg-white dark:bg-gray-900">
      <CardHeader>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Rocket Fuel Tank
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Fuel your project's rocket for episode takeoff! 🚀 Higher fuel = bigger episode moments
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Rocket Visual */}
        <div className="relative h-32 bg-gradient-to-b from-blue-100 to-blue-200 dark:from-blue-900 dark:to-blue-800 rounded-lg overflow-hidden">
          <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2">
            <Rocket className="h-16 w-16 text-gray-600 dark:text-gray-400" />
          </div>
          {/* Fuel bar */}
          <div className="absolute bottom-0 left-0 w-full">
            <div 
              className="bg-gradient-to-t from-orange-500 to-yellow-400 transition-all duration-1000"
              style={{ height: `${fuelLevel}%` }}
            />
          </div>
          {/* Fuel level indicator */}
          <div className="absolute top-2 right-2 bg-black/50 text-white px-2 py-1 rounded text-sm">
            {fuelLevel}% Fuel
          </div>
        </div>

        {/* Fuel Types */}
        <div className="grid grid-cols-3 gap-2">
          {fuelTypes.map((fuel) => {
            const Icon = fuel.icon
            return (
              <Button
                key={fuel.name}
                onClick={() => handleFuel(fuel.name)}
                variant="outline"
                className="flex flex-col items-center gap-1 h-16 text-xs"
                disabled={fuelLevel >= 100}
              >
                <Icon className="h-4 w-4" />
                <div>{fuel.name}</div>
                <div className="text-xs text-gray-500">{fuel.cost} ai16z</div>
              </Button>
            )
          })}
        </div>

        <div className="text-xs text-gray-500 text-center">
          💡 Episode Feature: Highly fueled projects get dramatic camera zooms and victory music!
        </div>
      </CardContent>
    </Card>
  )
}

// Prototype 6: Live Bidding War (Real-time Episode Drama)
function BiddingWarPrototype() {
  const [currentBid, setCurrentBid] = useState(42)
  const [timeLeft] = useState(30)
  const [myBid, setMyBid] = useState('')
  const [recentBids] = useState([
    { user: 'crypto_whale', amount: 42, time: '2s ago' },
    { user: 'dev_master', amount: 38, time: '8s ago' },
    { user: 'ai16z_fan', amount: 35, time: '12s ago' }
  ])

  const handleBid = () => {
    const bidAmount = parseInt(myBid)
    if (bidAmount > currentBid) {
      setCurrentBid(bidAmount)
      setMyBid('')
    }
  }

  return (
    <Card className="bg-white dark:bg-gray-900">
      <CardHeader>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Live Bidding War
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          ⚡ Real-time auction creates episode tension! Highest bidder gets judge spotlight
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Current High Bid */}
        <div className="text-center p-4 bg-gradient-to-r from-red-50 to-orange-50 dark:from-red-900 dark:to-orange-900 rounded-lg">
          <div className="text-3xl font-bold text-red-600 dark:text-red-400">
            {currentBid} ai16z
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Current High Bid</div>
        </div>

        {/* Timer */}
        <div className="flex items-center justify-center gap-2 text-orange-600">
          <Timer className="h-4 w-4" />
          <span className="font-mono text-lg">{timeLeft}s left</span>
        </div>

        {/* Bid Input */}
        <div className="flex gap-2">
          <input
            type="number"
            value={myBid}
            onChange={(e) => setMyBid(e.target.value)}
            placeholder={`Min: ${currentBid + 1}`}
            className="flex-1 px-3 py-2 border rounded dark:bg-gray-800 dark:border-gray-700"
          />
          <Button 
            onClick={handleBid}
            disabled={!myBid || parseInt(myBid) <= currentBid}
            className="bg-red-600 hover:bg-red-700"
          >
            <Gavel className="h-4 w-4 mr-1" />
            Bid!
          </Button>
        </div>

        {/* Recent Bids */}
        <div className="space-y-1">
          <h4 className="text-sm font-medium">Recent Bids:</h4>
          {recentBids.map((bid, i) => (
            <div key={i} className="flex justify-between text-sm bg-gray-50 dark:bg-gray-800 p-2 rounded">
              <span>{bid.user}</span>
              <span className="font-medium">{bid.amount} ai16z</span>
              <span className="text-gray-500">{bid.time}</span>
            </div>
          ))}
        </div>

        <div className="text-xs text-gray-500 text-center">
          🎬 Episode Feature: Bidding wars trigger dramatic "GOING ONCE!" moments from judges
        </div>
      </CardContent>
    </Card>
  )
}

// Prototype 7: Building Blocks Stack (Visual Progress for Episodes)
function StackingBlocksPrototype() {
  const [blocks, setBlocks] = useState([1, 1, 1]) // Small, medium, large
  const [totalHeight, setTotalHeight] = useState(3)

  const blockTypes = [
    { name: 'Small', cost: 1, height: 1, color: 'bg-blue-400' },
    { name: 'Medium', cost: 5, height: 2, color: 'bg-purple-500' },
    { name: 'Large', cost: 10, height: 3, color: 'bg-orange-500' }
  ]

  const addBlock = (typeIndex: number) => {
    const newBlocks = [...blocks]
    newBlocks[typeIndex]++
    setBlocks(newBlocks)
    setTotalHeight(prev => prev + blockTypes[typeIndex].height)
  }

  return (
    <Card className="bg-white dark:bg-gray-900">
      <CardHeader>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Building Blocks Stack
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          🏗️ Build your project's tower! Height determines episode screen time and camera angles
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Tower Visualization */}
        <div className="h-40 bg-gray-100 dark:bg-gray-800 rounded-lg p-4 flex items-end justify-center">
          <div className="flex flex-col items-center space-y-1">
            {/* Show stacked blocks */}
            {blocks.map((count, typeIndex) => 
              Array.from({ length: count }, (_, i) => (
                <div
                  key={`${typeIndex}-${i}`}
                  className={`w-12 rounded ${blockTypes[typeIndex].color}`}
                  style={{ height: `${blockTypes[typeIndex].height * 8}px` }}
                />
              ))
            ).flat()}
          </div>
        </div>

        {/* Building Actions */}
        <div className="grid grid-cols-3 gap-2">
          {blockTypes.map((block, i) => (
            <Button
              key={i}
              onClick={() => addBlock(i)}
              variant="outline"
              className="flex flex-col items-center gap-1 h-20"
            >
              <div className={`w-8 h-4 rounded ${block.color}`} />
              <div className="text-xs">{block.name}</div>
              <div className="text-xs text-gray-500">{block.cost} ai16z</div>
            </Button>
          ))}
        </div>

        {/* Stats */}
        <div className="text-center">
          <div className="text-2xl font-bold text-purple-600">Height: {totalHeight}</div>
          <div className="text-sm text-gray-500">
            Blocks: {blocks.map((count, i) => `${count} ${blockTypes[i].name}`).join(', ')}
          </div>
        </div>

        <div className="text-xs text-gray-500 text-center">
          📺 Episode Feature: Taller projects get panoramic "tower shots" and building sound effects
        </div>
      </CardContent>
    </Card>
  )
}

// Prototype 8: Social Proof Feed (Community Hype for Episodes)
function SocialProofPrototype() {
  const [recentVotes] = useState([
    { user: 'eliza_ai', action: 'PUMPED', amount: 25, avatar: '🤖', time: '30s' },
    { user: 'crypto_dev', action: 'supported', amount: 10, avatar: '👨‍💻', time: '1m' },
    { user: 'dao_whale', action: 'MEGA PUMPED', amount: 50, avatar: '🐋', time: '2m' },
    { user: 'anon_builder', action: 'voted', amount: 5, avatar: '🛠️', time: '3m' }
  ])

  const [communityTemp] = useState(87) // Temperature gauge
  const [viewers] = useState(234)

  return (
    <Card className="bg-white dark:bg-gray-900">
      <CardHeader>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Social Proof Feed
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          👥 Live community hype! Feeds into episode excitement and judge reactions
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Community Temperature */}
        <div className="flex items-center justify-between p-3 bg-gradient-to-r from-orange-50 to-red-50 dark:from-orange-900 dark:to-red-900 rounded-lg">
          <div className="flex items-center gap-2">
            <Flame className="h-5 w-5 text-orange-500" />
            <span className="font-medium">Community Heat</span>
          </div>
          <div className="text-2xl font-bold text-orange-600">{communityTemp}°</div>
        </div>

        {/* Live Stats */}
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center p-2 bg-gray-50 dark:bg-gray-800 rounded">
            <div className="text-xl font-bold text-green-600">{viewers}</div>
            <div className="text-xs text-gray-500">Watching Live</div>
          </div>
          <div className="text-center p-2 bg-gray-50 dark:bg-gray-800 rounded">
            <div className="text-xl font-bold text-blue-600">{recentVotes.length}</div>
            <div className="text-xs text-gray-500">Recent Votes</div>
          </div>
        </div>

        {/* Live Feed */}
        <div className="space-y-2 max-h-32 overflow-y-auto">
          {recentVotes.map((vote, i) => (
            <div key={i} className="flex items-center gap-3 p-2 bg-gray-50 dark:bg-gray-800 rounded text-sm">
              <span className="text-lg">{vote.avatar}</span>
              <div className="flex-1">
                <span className="font-medium">{vote.user}</span>
                <span className="text-gray-600 dark:text-gray-400"> {vote.action} with </span>
                <span className="font-medium text-purple-600">{vote.amount} ai16z</span>
              </div>
              <span className="text-xs text-gray-500">{vote.time}</span>
            </div>
          ))}
        </div>

        <div className="text-xs text-gray-500 text-center">
          🎭 Episode Feature: High community heat triggers judge comments like "The crowd loves this!"
        </div>
      </CardContent>
    </Card>
  )
}

// Inline Prize Pool Widget (moved from separate component file)
function PrizePoolWidgetInline({ className, showContributions = true }: { className?: string; showContributions?: boolean }) {
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
      <Card className={`bg-white dark:bg-gray-900 ${className || ''}`}>
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
      <Card className={`bg-white dark:bg-gray-900 ${className || ''}`}>
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
    <Card className={`bg-gradient-to-br from-purple-50 to-indigo-50 dark:from-gray-900 dark:to-gray-800 ${className || ''}`}>
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
              {prizePoolData.total_sol.toFixed(2)} SOL
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              {prizePoolData.progress_percentage.toFixed(1)}% of {prizePoolData.target_sol} SOL goal
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
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                      {formatTokenAmount(breakdown.amount)}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      {mint === 'SOL' ? 
                        ((breakdown.amount / prizePoolData.total_sol) * 100).toFixed(1)
                        : '—'
                      }%
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
                {prizePoolData.recent_contributions.slice(0, 5).map((contribution: any, index: number) => (
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
                      <span className="px-1.5 py-0.5 rounded text-xs font-medium bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300">
                        {contribution.description || 'Transfer'}
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

// Community Voting from Leaderboard (for posterity)
function CommunityVotingFromLeaderboard() {
  const [entries, setEntries] = useState<LeaderboardEntry[]>([])
  const [, setCommunityScores] = useState<CommunityScore[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedProject, setSelectedProject] = useState<number | null>(null)
  useState(true) // Always show for demo - showVoting unused

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
      communityData.forEach((score: any) => {
        communityScoreMap.set(score.submission_id, score.community_score)
      })
      
      // Merge community scores into leaderboard entries using submission_id
      const entriesWithCommunity = leaderboardData.map((entry: any) => ({
        ...entry,
        community_score: communityScoreMap.get(entry.submission_id) || undefined
      }))
      
      setEntries(entriesWithCommunity.slice(0, 3)) // Only show top 3 for demo
      setCommunityScores(communityData)
    } catch (error) {
      console.error('Failed to load leaderboard:', error)
    } finally {
      setLoading(false)
    }
  }

  const getMedalIcon = (rank: number) => {
    if (rank === 1) return <Medal className="h-6 w-6 text-yellow-500" />
    if (rank === 2) return <Medal className="h-6 w-6 text-gray-400" />
    if (rank === 3) return <Medal className="h-6 w-6 text-orange-600" />
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
      <Card className="bg-white dark:bg-gray-900">
        <CardHeader>
          <h3 className="text-xl font-semibold">Community Voting Interface (from Leaderboard)</h3>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="bg-white dark:bg-gray-900">
      <CardHeader>
        <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
          Community Voting Interface (from Leaderboard)
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          This is the voting UI that was integrated into the leaderboard page - preserved here for posterity
        </p>
      </CardHeader>
      <CardContent>
        {/* Community Voting Interface */}
        <div className="grid md:grid-cols-2 gap-6 mb-6">
          {/* Prize Pool Widget */}
          <PrizePoolWidgetInline />
          
          {/* Voting Interface */}
          {selectedProject ? (
            <WalletVoting
              submissionId={selectedProject.toString()}
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

        {/* Mini Leaderboard for Demo */}
        <Card className="overflow-hidden bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
          <div className="bg-gradient-to-r from-indigo-600 to-purple-600 px-4 py-3">
            <h4 className="text-lg font-semibold text-white">Top Projects (Demo)</h4>
          </div>
          
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {entries.map((entry, index) => (
              <div
                key={`${entry.rank}-${entry.project_name}`}
                className={cn(
                  "px-4 py-4 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors border-l-4",
                  statusColor(entry.status || "unknown"),
                  index === 0 && "bg-gradient-to-r from-yellow-50 to-amber-50 dark:from-gray-900 dark:to-gray-800"
                )}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {/* Rank */}
                    <div className="flex-shrink-0 w-10 text-center">
                      {index < 3 ? (
                        getMedalIcon(entry.rank)
                      ) : (
                        <div className="h-8 w-8 mx-auto rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                          <span className="font-bold text-sm text-gray-700 dark:text-gray-200">{entry.rank}</span>
                        </div>
                      )}
                    </div>
                    
                    {/* Project Info */}
                    <div className="flex-1 flex items-center gap-2">
                      <DiscordAvatar
                        discord_id={entry.discord_id}
                        discord_avatar={entry.discord_avatar}
                        discord_handle={entry.discord_handle}
                        size="sm"
                        className="border border-gray-300 dark:border-gray-700"
                      />
                      <h5 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                        {entry.project_name}
                      </h5>
                    </div>
                  </div>
                  
                  {/* Score and Actions */}
                  <div className="flex items-center gap-4">
                    {/* AI Score */}
                    <div className="text-right">
                      <div className="text-lg font-bold text-gray-900 dark:text-gray-100">
                        {entry.final_score.toFixed(2)}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">AI Score</div>
                    </div>
                    
                    {/* Community Score */}
                    <div className="text-right">
                      <div className="text-lg font-semibold text-blue-600 dark:text-blue-400">
                        {entry.community_score ? entry.community_score.toFixed(1) : "—"}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">Community</div>
                    </div>
                    
                    {/* Vote Button */}
                    <Button
                      variant={selectedProject === entry.submission_id ? "primary" : "secondary"}
                      size="sm"
                      onClick={() => {
                        setSelectedProject(entry.submission_id)
                      }}
                    >
                      <Vote className="h-3 w-3 mr-1" />
                      {selectedProject === entry.submission_id ? 'Selected' : 'Vote'}
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <p className="text-xs text-gray-600 dark:text-gray-400">
            💡 <strong>Note:</strong> This voting interface was originally part of the leaderboard page. 
            It includes real-time wallet voting with ai16z tokens, prize pool tracking, and community score integration.
          </p>
        </div>
      </CardContent>
    </Card>
  )
}

export default function VotingPrototypes() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
          Voting Prototypes
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Rapid prototyping different community voting mechanisms for episode integration
        </p>
      </div>

      <div className="space-y-6">
        {/* Community Voting from Leaderboard */}
        <div className="col-span-full">
          <CommunityVotingFromLeaderboard />
        </div>
        
        {/* Original Prototypes */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <PowerBarPrototype />
          <ActionButtonsPrototype />
          <CreditsPrototype />
          <ReactionsPrototype />
          <FuelTankPrototype />
          <BiddingWarPrototype />
          <StackingBlocksPrototype />
          <SocialProofPrototype />
        </div>
      </div>
    </div>
  )
}