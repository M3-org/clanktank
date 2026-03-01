import { cn } from '../lib/utils'

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
  className?: string
  variant?: 'default' | 'ghost' | 'highlight' | 'skeleton'
  interactive?: boolean
}

const variantStyles = {
  default: 'rounded-xl border border-gray-200/60 dark:border-gray-700/60 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 shadow-sm',
  ghost: 'border-0 bg-transparent shadow-none text-gray-900 dark:text-gray-100',
  highlight: 'rounded-2xl border border-amber-200/60 dark:border-amber-800/60 bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-950/20 dark:to-orange-950/20 shadow-lg shadow-amber-500/10 dark:shadow-amber-500/5',
  skeleton: 'rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 animate-pulse'
}

const interactiveStyles = 'transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg cursor-pointer'

export function Card({ children, className, variant = 'default', interactive = false, ...props }: CardProps) {
  return (
    <div 
      className={cn(
        variantStyles[variant], 
        interactive && interactiveStyles,
        className
      )} 
      {...props}
    >
      {children}
    </div>
  )
}

export function CardHeader({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn('px-6 py-4 border-b border-gray-100 dark:border-gray-700', className)}>
      {children}
    </div>
  )
}

export function CardContent({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn('px-6 py-4', className)}>
      {children}
    </div>
  )
}