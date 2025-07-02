import { cn } from '../lib/utils';

export function CategoryBadge({ category }: { category?: string }) {
  const normalized = (category || 'Unknown').toLowerCase();
  let color = 'bg-gray-100 text-gray-700 border-gray-300';
  if (normalized === 'defi') color = 'bg-blue-100 text-blue-700 border-blue-300';
  else if (normalized === 'gaming') color = 'bg-green-100 text-green-800 border-green-300';
  else if (normalized === 'ai/agents' || normalized === 'ai' || normalized === 'agents') color = 'bg-yellow-100 text-yellow-800 border-yellow-300';
  return (
    <span className={cn(
      'ml-2 px-2 py-0.5 rounded text-xs font-semibold border',
      color
    )}>
      {category || 'Unknown'}
    </span>
  );
} 