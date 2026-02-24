import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function getStatusColor(status: string) {
  switch (status) {
    case 'submitted':
      return 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-100'
    case 'researched':
      return 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-100'
    case 'scored':
      return 'bg-indigo-100 dark:bg-indigo-900 text-indigo-800 dark:text-indigo-100'
    case 'community-voting':
      return 'bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-100'
    case 'completed':
      return 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-100'
    case 'published':
      return 'bg-emerald-100 dark:bg-emerald-900 text-emerald-800 dark:text-emerald-100'
    default:
      return 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-100'
  }
}

export function getCategoryColor(category: string) {
  switch (category) {
    case 'DeFi':
      return 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-100'
    case 'Gaming':
      return 'bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-100'
    case 'Agents':
      return 'bg-indigo-100 dark:bg-indigo-900 text-indigo-800 dark:text-indigo-100'
    case 'Infrastructure':
      return 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-100'
    case 'Social':
      return 'bg-pink-100 dark:bg-pink-900 text-pink-800 dark:text-pink-100'
    default:
      return 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-100'
  }
}

export function formatDate(dateString: string) {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

export const pretty = (n: number) =>
  n.toLocaleString(undefined, { maximumFractionDigits: 2 })