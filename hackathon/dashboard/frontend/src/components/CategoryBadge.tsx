import { cn } from '../lib/utils';

export function CategoryBadge({ category }: { category?: string }) {
  const normalized = (category || 'Unknown').toLowerCase();
  let color = 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-100 border-gray-300 dark:border-gray-600';
  if (normalized === 'defi') color = 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-100 border-blue-300 dark:border-blue-700';
  else if (normalized === 'gaming') color = 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-100 border-green-300 dark:border-green-700';
  else if (normalized === 'ai/agents' || normalized === 'ai' || normalized === 'agents') color = 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-100 border-yellow-300 dark:border-yellow-700';
  return (
    <span className={cn(
      'ml-2 px-2 py-0.5 rounded text-xs font-semibold border',
      color
    )}>
      {category || 'Unknown'}
    </span>
  );
} 