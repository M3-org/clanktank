import { useState, useEffect } from 'react'
// TODO: Implement proper wallet-adapter integration
// import { useConnection, useWallet } from '@solana/wallet-adapter-react'
// import { WalletMultiButton } from '@solana/wallet-adapter-react-ui'
import { Button } from './Button'
import { Card, CardContent } from './Card'
import { Coins, Loader2, CheckCircle, AlertCircle } from 'lucide-react'
import { cn } from '../lib/utils'

interface WalletVotingProps {
  submissionId: string
  projectName: string
  className?: string
}

export function WalletVoting({ submissionId, projectName, className }: WalletVotingProps) {
  // TODO: Implement proper wallet connection hooks
  // const { connection } = useConnection()
  // const { publicKey, sendTransaction, connected } = useWallet()
  const connected = false // Placeholder
  
  const [tokenAmount, setTokenAmount] = useState(25)
  const [voteWeight, setVoteWeight] = useState(0)
  const [overflowTokens, setOverflowTokens] = useState(0)
  const [isVoting] = useState(false)
  const [voteStatus, setVoteStatus] = useState<'idle' | 'success' | 'error'>('idle')
  const [errorMessage, setErrorMessage] = useState('')
  
  // TODO: Define proper constants when implementing wallet integration
  // const AI16Z_MINT = new PublicKey('HeLp6NuQkmYB4pYWo2zYs22mESHXPQYzXbB8n4V98jwC')
  // const VOTING_WALLET = new PublicKey(import.meta.env.VITE_VOTING_WALLET_ADDRESS)
  
  // Vote weight calculation: min(log10(tokens + 1) * 3, 10)
  useEffect(() => {
    const maxVoteTokens = 100
    const votingTokens = Math.min(tokenAmount, maxVoteTokens)
    const calculatedWeight = Math.min(Math.log10(votingTokens + 1) * 3, 10)
    const overflow = Math.max(0, tokenAmount - maxVoteTokens)
    
    setVoteWeight(calculatedWeight)
    setOverflowTokens(overflow)
  }, [tokenAmount])
  
  const handleVote = async () => {
    // TODO: Implement proper Solana transaction handling
    console.log(`Voting for ${submissionId} with ${tokenAmount} ai16z tokens`)
    setErrorMessage('Wallet integration not yet implemented - placeholder functionality')
    setVoteStatus('error')
  }
  
  // TODO: Implement slider color logic when needed
  // const getSliderColor = () => {
  //   if (tokenAmount <= 25) return 'from-green-400 to-green-600'
  //   if (tokenAmount <= 100) return 'from-yellow-400 to-orange-500'
  //   return 'from-orange-500 to-red-600'
  // }

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
              Connect your wallet and send ai16z tokens to cast your community vote
            </p>
          </div>
          
          {/* Wallet Connection - PLACEHOLDER */}
          <div className="flex justify-center">
            <Button className="bg-gray-400 cursor-not-allowed" disabled>
              Connect Wallet (Not Implemented)
            </Button>
          </div>
          
          {connected && (
            <>
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
                  <input
                    type="range"
                    min="1"
                    max="250"
                    value={tokenAmount}
                    onChange={(e) => setTokenAmount(Number(e.target.value))}
                    className="w-full h-3 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
                    disabled={isVoting}
                  />
                  <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
                    <span>1</span>
                    <span className="text-orange-600 dark:text-orange-400">100 (vote cap)</span>
                    <span>250</span>
                  </div>
                </div>
                
                {/* Quick Amount Buttons */}
                <div className="flex gap-2 justify-center">
                  {[10, 25, 50, 100, 150].map((amount) => (
                    <Button
                      key={amount}
                      variant="ghost"
                      size="sm"
                      onClick={() => setTokenAmount(amount)}
                      disabled={isVoting}
                      className={cn(
                        "px-3 py-1 text-xs",
                        tokenAmount === amount && "bg-indigo-100 dark:bg-indigo-900 text-indigo-700 dark:text-indigo-300"
                      )}
                    >
                      {amount}
                    </Button>
                  ))}
                </div>
              </div>
              
              {/* Vote Impact Display */}
              <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Vote Weight:</span>
                  <span className="text-lg font-bold text-blue-600 dark:text-blue-400">
                    {voteWeight.toFixed(1)} / 10
                  </span>
                </div>
                
                {overflowTokens > 0 && (
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Overflow to Prize Pool:</span>
                    <span className="text-sm font-semibold text-green-600 dark:text-green-400">
                      +{overflowTokens} ai16z
                    </span>
                  </div>
                )}
                
                <div className="text-xs text-gray-500 dark:text-gray-400 text-center">
                  Formula: min(log₁₀(tokens + 1) × 3, 10)
                  {overflowTokens > 0 && " • Excess tokens boost the prize pool!"}
                </div>
              </div>
              
              {/* Vote Button */}
              <Button
                onClick={handleVote}
                disabled={isVoting || !connected}
                className="w-full"
                size="lg"
              >
                {isVoting ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Sending Vote...
                  </>
                ) : (
                  <>
                    <Coins className="h-4 w-4 mr-2" />
                    Vote with {tokenAmount} ai16z
                  </>
                )}
              </Button>
              
              {/* Status Messages */}
              {voteStatus === 'success' && (
                <div className="flex items-center gap-2 text-green-600 dark:text-green-400 text-sm">
                  <CheckCircle className="h-4 w-4" />
                  Vote submitted successfully! It may take a moment to appear in the leaderboard.
                </div>
              )}
              
              {voteStatus === 'error' && (
                <div className="flex items-center gap-2 text-red-600 dark:text-red-400 text-sm">
                  <AlertCircle className="h-4 w-4" />
                  {errorMessage || 'Vote failed. Please try again.'}
                </div>
              )}
            </>
          )}
          
          {/* Security Notice */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
            <div className="text-xs text-blue-800 dark:text-blue-200">
              <strong>Secure Voting:</strong> Votes are processed via on-chain transactions. 
              Transaction signatures are recorded to prevent double-voting. 
              Your wallet address will be visible on the blockchain.
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}