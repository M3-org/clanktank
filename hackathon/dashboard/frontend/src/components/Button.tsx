import { cn } from '../lib/utils'
import { ButtonHTMLAttributes, forwardRef } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'discord' | 'outline'
  size?: 'sm' | 'md' | 'lg'
}

const variantStyles = {
  primary: 'bg-indigo-600 dark:bg-indigo-500 text-white hover:bg-indigo-700 dark:hover:bg-indigo-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600',
  secondary: 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-100 hover:bg-gray-200 dark:hover:bg-gray-700',
  ghost: 'bg-transparent text-gray-800 dark:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-800',
  discord: 'bg-[#5865F2] text-white hover:bg-[#4752C4] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#5865F2]',
  outline: 'border border-gray-300 dark:border-gray-600 bg-transparent text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800'
}

const sizeStyles = {
  sm: 'px-2.5 py-1.5 text-sm',
  md: 'px-3 py-2 text-sm',
  lg: 'px-4 py-2 text-base'
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          'inline-flex items-center justify-center rounded-md font-semibold shadow-sm transition-colors',
          variantStyles[variant],
          sizeStyles[size],
          className
        )}
        {...props}
      />
    )
  }
)

Button.displayName = 'Button'