import { pretty } from './utils'

export interface TokenHolding {
  mint: string
  symbol: string
  amount: string
  logo?: string
}

/**
 * Renders a token icon with fallback
 */
export function renderTokenIcon(token: TokenHolding, size: 'sm' | 'md' | 'lg' = 'md') {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-5 w-5', 
    lg: 'h-8 w-8'
  }
  
  if (token.logo) {
    return (
      <img 
        src={token.logo} 
        alt={token.symbol}
        className={`${sizeClasses[size]} rounded-full`}
        onError={(e) => {
          (e.target as HTMLImageElement).style.display = 'none'
        }}
      />
    )
  }
  
  return (
    <div className={`${sizeClasses[size]} rounded-full bg-gradient-to-br from-brand-accent to-cyan-500 flex items-center justify-center`}>
      <span className="text-white font-bold text-xs">
        {token.symbol ? token.symbol.slice(0, size === 'sm' ? 1 : 2) : '??'}
      </span>
    </div>
  )
}

/**
 * Formats token amount with proper notation
 */
export function formatTokenAmount(amount: string | number): string {
  const num = typeof amount === 'string' ? parseFloat(amount) : amount
  if (isNaN(num)) return '0'
  
  return pretty(num)
}

/**
 * Formats token amount with compact notation for large numbers
 */
export function formatTokenAmountCompact(amount: string | number): string {
  const num = typeof amount === 'string' ? parseFloat(amount) : amount
  if (isNaN(num)) return '0'
  
  return num.toLocaleString(undefined, { 
    maximumFractionDigits: 1,
    notation: num > 1000 ? 'compact' : 'standard'
  })
}