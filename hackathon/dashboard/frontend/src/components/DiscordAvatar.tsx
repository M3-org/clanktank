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
  const [imageError, setImageError] = useState(false)
  
  const sizeClasses = {
    sm: 'w-6 h-6 text-xs',
    md: 'w-8 h-8 text-sm', 
    lg: 'w-12 h-12 text-base'
  }

  // Handle both full URL and hash formats
  let avatarUrl = null
  let fallbackUrl = null
  let generatedUrl = null
  
  if (discord_avatar && !imageError) {
    if (discord_avatar.startsWith('https://')) {
      // Already a full URL
      avatarUrl = discord_avatar
      
      // Try to construct fallback local cache URL
      if (discord_id) {
        const urlParts = discord_avatar.split('/')
        const avatarFilename = urlParts[urlParts.length - 1]
        const avatarHash = avatarFilename.split('.')[0]
        fallbackUrl = `/discord/${discord_id}_${avatarHash}.png`
      }
    } else if (discord_id) {
      // Just a hash, construct the URL
      avatarUrl = `https://cdn.discordapp.com/avatars/${discord_id}/${discord_avatar}.png`
      fallbackUrl = `/discord/${discord_id}_${discord_avatar}.png`
    }
  }
  
  // Always have generated avatar as final fallback for users with discord_id
  if (discord_id) {
    generatedUrl = `/discord/${discord_id}_generated.png`
  }

  // If we have an avatar URL to try OR if we should try generated avatar directly
  if ((avatarUrl && !imageError) || (!avatarUrl && generatedUrl && !imageError)) {
    const srcUrl = avatarUrl || generatedUrl!
    return (
      <img
        src={srcUrl}
        alt={`${discord_handle || 'user'} avatar`}
        className={cn(
          'rounded-full border-2 border-white/20 bg-white/10 object-cover',
          sizeClasses[size],
          className
        )}
        loading="lazy"
        onError={() => {
          // Try fallback to local cache if available
          if (fallbackUrl) {
            const img = new Image()
            img.onload = () => {
              // Fallback image exists, use it
              const currentImg = document.querySelector(`img[alt="${discord_handle || 'user'} avatar"]`) as HTMLImageElement
              if (currentImg) {
                currentImg.src = fallbackUrl!
              }
            }
            img.onerror = () => {
              // Try generated avatar if both Discord CDN and local cache failed
              if (generatedUrl) {
                const genImg = new Image()
                genImg.onload = () => {
                  const currentImg = document.querySelector(`img[alt="${discord_handle || 'user'} avatar"]`) as HTMLImageElement
                  if (currentImg) {
                    currentImg.src = generatedUrl!
                  }
                }
                genImg.onerror = () => {
                  setImageError(true)
                }
                genImg.src = generatedUrl
              } else {
                setImageError(true)
              }
            }
            img.src = fallbackUrl
          } else if (generatedUrl) {
            // No custom avatar, try generated avatar directly
            const genImg = new Image()
            genImg.onload = () => {
              const currentImg = document.querySelector(`img[alt="${discord_handle || 'user'} avatar"]`) as HTMLImageElement
              if (currentImg) {
                currentImg.src = generatedUrl!
              }
            }
            genImg.onerror = () => {
              setImageError(true)
            }
            genImg.src = generatedUrl
          } else {
            setImageError(true)
          }
        }}
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