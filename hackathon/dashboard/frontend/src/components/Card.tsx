import { cn } from '../lib/utils'

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
  className?: string
  variant?: 'default' | 'ghost'
}

const variantStyles = {
  default: 'rounded-lg shadow-md bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100',
  ghost: 'border-0 bg-transparent shadow-none text-gray-900 dark:text-gray-100'
}

export function Card({ children, className, variant = 'default', ...props }: CardProps) {
  return (
    <div className={cn(variantStyles[variant], className)} {...props}>
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