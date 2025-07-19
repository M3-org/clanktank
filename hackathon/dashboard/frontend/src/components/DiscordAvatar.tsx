import { cn } from '../lib/utils'

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
  const sizeClasses = {
    sm: 'w-6 h-6 text-xs',
    md: 'w-8 h-8 text-sm', 
    lg: 'w-12 h-12 text-base'
  }

  // Handle both full URL and hash formats
  let avatarUrl = null
  if (discord_avatar) {
    if (discord_avatar.startsWith('https://')) {
      // Already a full URL
      avatarUrl = discord_avatar
    } else if (discord_id) {
      // Just a hash, construct the URL
      avatarUrl = `https://cdn.discordapp.com/avatars/${discord_id}/${discord_avatar}.png`
    }
  }

  if (avatarUrl) {
    return (
      <img
        src={avatarUrl}
        alt={`${discord_handle} avatar`}
        className={cn(
          'rounded-full border-2 border-white/20 bg-white/10 object-cover',
          sizeClasses[size],
          className
        )}
      />
    )
  }

  // Fallback avatar with initial
  const initial = discord_handle?.charAt(0)?.toUpperCase() || '?'
  
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