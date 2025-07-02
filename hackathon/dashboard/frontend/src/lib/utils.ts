import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function getStatusColor(status: string) {
  switch (status) {
    case 'submitted':
      return 'bg-yellow-100 text-yellow-800'
    case 'researched':
      return 'bg-blue-100 text-blue-800'
    case 'scored':
      return 'bg-indigo-100 text-indigo-800'
    case 'community-voting':
      return 'bg-purple-100 text-purple-800'
    case 'completed':
      return 'bg-green-100 text-green-800'
    case 'published':
      return 'bg-emerald-100 text-emerald-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

export function getCategoryColor(category: string) {
  switch (category) {
    case 'DeFi':
      return 'bg-blue-100 text-blue-800'
    case 'Gaming':
      return 'bg-purple-100 text-purple-800'
    case 'AI/Agents':
      return 'bg-indigo-100 text-indigo-800'
    case 'Infrastructure':
      return 'bg-gray-100 text-gray-800'
    case 'Social':
      return 'bg-pink-100 text-pink-800'
    default:
      return 'bg-gray-100 text-gray-800'
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