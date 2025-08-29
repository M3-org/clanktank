import { cn } from '../lib/utils'
import { useState } from 'react'

interface DiscordAvatarProps {
  discord_id?: string
  discord_avatar?: string
  discord_handle?: string
  size?: 'sm' | 'md' | 'lg'
  className?: string
  variant?: 'light' | 'dark' | 'auto'
}

export function DiscordAvatar({ 
  discord_id, 
  discord_avatar, 
  discord_handle, 
  size = 'md',
  className,
  variant = 'auto'
}: DiscordAvatarProps) {
  const [currentSrc, setCurrentSrc] = useState<string | null>(null)
  const [hasError, setHasError] = useState(false)
  
  const sizeClasses = {
    sm: 'w-6 h-6 text-xs',
    md: 'w-8 h-8 text-sm', 
    lg: 'w-12 h-12 text-base'
  }

  // Build fallback chain based on available data
  const fallbackChain: string[] = []
  
  if (discord_avatar && discord_id) {
    if (discord_avatar.startsWith('https://')) {
      // Discord CDN URL - extract hash for local cache
      const urlParts = discord_avatar.split('/')
      const avatarFilename = urlParts[urlParts.length - 1]
      const avatarHash = avatarFilename.split('.')[0]
      
      // Add local cache as primary, skip Discord CDN (404s)
      fallbackChain.push(`/discord/${discord_id}_${avatarHash}.png`)
    } else {
      // Just a hash - add local cache
      fallbackChain.push(`/discord/${discord_id}_${discord_avatar}.png`)
    }
  }
  
  // Always add generated avatar as fallback
  if (discord_id) {
    fallbackChain.push(`/discord/${discord_id}_generated.png`)
  }

  // Initialize current source on first render
  if (currentSrc === null && fallbackChain.length > 0) {
    setCurrentSrc(fallbackChain[0])
  }

  const handleImageError = () => {
    if (!currentSrc || hasError) return
    
    const currentIndex = fallbackChain.indexOf(currentSrc)
    const nextIndex = currentIndex + 1
    
    if (nextIndex < fallbackChain.length) {
      // Try next fallback
      setCurrentSrc(fallbackChain[nextIndex])
    } else {
      // All fallbacks failed, show text avatar
      setHasError(true)
    }
  }

  // Show image if we have a valid source and haven't exhausted all fallbacks
  if (currentSrc && !hasError) {
    return (
      <img
        src={currentSrc}
        alt={`${discord_handle || 'user'} avatar`}
        className={cn(
          'rounded-full border-2 border-white/20 bg-white/10 object-cover',
          sizeClasses[size],
          className
        )}
        loading="lazy"
        onError={handleImageError}
      />
    )
  }

  // Fallback avatar with initial
  const initial = (discord_handle || 'U').charAt(0)?.toUpperCase()
  
  // Choose appropriate styling based on variant
  const getFallbackStyles = () => {
    if (variant === 'dark') {
      return {
        bg: 'border-2 border-white/20 bg-white/10',
        text: 'text-white'
      }
    } else if (variant === 'light') {
      return {
        bg: 'border-2 border-gray-300 dark:border-gray-700 bg-gray-200 dark:bg-gray-700',
        text: 'text-gray-600 dark:text-gray-300'
      }
    } else {
      // Auto: detect based on className or use default light
      const isDarkContext = className?.includes('border-white') || className?.includes('bg-white')
      return isDarkContext ? {
        bg: 'border-2 border-white/20 bg-white/10',
        text: 'text-white'
      } : {
        bg: 'border-2 border-gray-300 dark:border-gray-700 bg-gray-200 dark:bg-gray-700',
        text: 'text-gray-600 dark:text-gray-300'
      }
    }
  }
  
  const fallbackStyles = getFallbackStyles()
  
  return (
    <div className={cn(
      'rounded-full flex items-center justify-center',
      fallbackStyles.bg,
      sizeClasses[size],
      className
    )}>
      <span className={cn('font-semibold', fallbackStyles.text)}>
        {initial}
      </span>
    </div>
  )
}