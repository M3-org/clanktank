import { useState, useEffect } from 'react'
import { ThumbsUp, ThumbsDown } from 'lucide-react'
import { Button } from './Button'
import { hackathonApi } from '../lib/api'
import { LikeDislikeResponse } from '../types'
import { cn } from '../lib/utils'
import { useAuth } from '../contexts/AuthContext'
import toast from 'react-hot-toast'

interface LikeDislikeProps {
  submissionId: string
  className?: string
}

export function LikeDislike({ submissionId, className }: LikeDislikeProps) {
  const [data, setData] = useState<LikeDislikeResponse>({ likes: 0, dislikes: 0, user_action: null })
  const [loading, setLoading] = useState(false)
  const { authState } = useAuth()
  
  // Check if user is authenticated
  const isAuthenticated = authState.authMethod === 'discord' || authState.authMethod === 'invite'

  useEffect(() => {
    // Debounce loading to prevent rapid calls during navigation
    const timeoutId = setTimeout(() => {
      loadCounts()
    }, 100)
    
    return () => clearTimeout(timeoutId)
  }, [submissionId])

  const loadCounts = async () => {
    try {
      const response = await hackathonApi.getLikeDislikeCounts(submissionId)
      setData(response)
    } catch (error) {
      console.error('Failed to load like/dislike counts:', error)
    }
  }

  const handleAction = async (action: 'like' | 'dislike') => {
    if (loading) return
    
    // Check authentication first
    if (!isAuthenticated) {
      toast.error('Please sign in to vote on submissions')
      return
    }
    
    setLoading(true)
    try {
      // If user clicks the same action they already took, remove it
      const actionToSend = data.user_action === action ? 'remove' : action
      
      const response = await hackathonApi.toggleLikeDislike(submissionId, actionToSend)
      setData(response)
    } catch (error) {
      console.error('Failed to toggle like/dislike:', error)
    } finally {
      setLoading(false)
    }
  }

  const total = data.likes + data.dislikes

  return (
    <div className={cn("", className)}>
      {/* Simple Vote Buttons */}
      <div className="flex gap-3 justify-center">
        <Button
          variant="ghost"
          onClick={() => handleAction('like')}
          disabled={loading}
          className={cn(
            "flex items-center gap-2 px-4 py-3 h-auto transition-all duration-200 rounded-lg border",
            data.user_action === 'like' 
              ? "bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300 border-green-300 shadow-sm" 
              : "hover:bg-green-50 dark:hover:bg-green-900/20 border-transparent hover:border-green-200"
          )}
        >
          <ThumbsUp className={cn(
            "h-5 w-5 transition-colors",
            data.user_action === 'like' ? "fill-current" : "",
            loading ? "animate-pulse" : ""
          )} />
          <span className="text-lg font-semibold">{data.likes}</span>
        </Button>

        <Button
          variant="ghost"
          onClick={() => handleAction('dislike')}
          disabled={loading}
          className={cn(
            "flex items-center gap-2 px-4 py-3 h-auto transition-all duration-200 rounded-lg border",
            data.user_action === 'dislike' 
              ? "bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 border-red-300 shadow-sm" 
              : "hover:bg-red-50 dark:hover:bg-red-900/20 border-transparent hover:border-red-200"
          )}
        >
          <ThumbsDown className={cn(
            "h-5 w-5 transition-colors",
            data.user_action === 'dislike' ? "fill-current" : "",
            loading ? "animate-pulse" : ""
          )} />
          <span className="text-lg font-semibold">{data.dislikes}</span>
        </Button>
      </div>

      {total === 0 && (
        <div className="text-center py-4">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Be the first to vote!
          </p>
        </div>
      )}
    </div>
  )
}