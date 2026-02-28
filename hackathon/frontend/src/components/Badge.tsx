import { cn, getStatusColor, getCategoryColor } from '../lib/utils'

interface BadgeProps {
  children: React.ReactNode
  variant?: 'default' | 'secondary' | 'success' | 'warning' | 'error' | 'info'
  className?: string
}

interface StatusBadgeProps {
  status?: string
  className?: string
}

interface CategoryBadgeProps {
  category?: string
  className?: string
}

const variantStyles = {
  default: 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-100 ring-1 ring-inset ring-gray-500/10',
  secondary: 'bg-blue-50 dark:bg-blue-900 text-blue-700 dark:text-blue-100 ring-1 ring-inset ring-blue-700/10',
  success: 'bg-green-50 dark:bg-green-900 text-green-700 dark:text-green-100 ring-1 ring-inset ring-green-600/20',
  warning: 'bg-yellow-50 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-100 ring-1 ring-inset ring-yellow-600/20',
  error: 'bg-red-50 dark:bg-red-900 text-red-700 dark:text-red-100 ring-1 ring-inset ring-red-600/10',
  info: 'bg-indigo-50 dark:bg-indigo-900 text-indigo-700 dark:text-indigo-100 ring-1 ring-inset ring-indigo-700/10',
}

export function Badge({ children, variant = 'default', className }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2 py-1 text-xs font-medium',
        variantStyles[variant],
        className
      )}
    >
      {children}
    </span>
  )
}

// Specialized badge components using the utility functions
export function StatusBadge({ status, className }: StatusBadgeProps) {
  const normalizedStatus = (status || 'unknown').toLowerCase()
  return (
    <span
      className={cn(
        'ml-2 px-2 py-0.5 rounded text-xs font-semibold border border-opacity-30',
        getStatusColor(normalizedStatus),
        className
      )}
    >
      {normalizedStatus.charAt(0).toUpperCase() + normalizedStatus.slice(1)}
    </span>
  )
}

export function CategoryBadge({ category, className }: CategoryBadgeProps) {
  const displayCategory = category || 'Unknown'
  return (
    <span
      className={cn(
        'ml-2 px-2 py-0.5 rounded text-xs font-semibold border border-opacity-30',
        getCategoryColor(displayCategory),
        className
      )}
    >
      {displayCategory}
    </span>
  )
}