import { cn } from '../lib/utils';

export function StatusBadge({ status }: { status?: string }) {
  const normalized = (status || 'unknown').toLowerCase();
  const color =
    normalized === 'scored' ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-100 border-blue-300 dark:border-blue-700' :
    normalized === 'completed' ? 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-100 border-yellow-300 dark:border-yellow-700' :
    normalized === 'published' ? 'bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-100 border-purple-300 dark:border-purple-700' :
    'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-100 border-gray-300 dark:border-gray-600';
  return (
    <span className={cn(
      'ml-2 px-2 py-0.5 rounded text-xs font-semibold border',
      color
    )}>
      {normalized.charAt(0).toUpperCase() + normalized.slice(1)}
    </span>
  );
} 