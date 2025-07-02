import { cn } from '../lib/utils';

export function StatusBadge({ status }: { status?: string }) {
  const normalized = (status || 'unknown').toLowerCase();
  const color =
    normalized === 'scored' ? 'bg-blue-100 text-blue-700 border-blue-300' :
    normalized === 'completed' ? 'bg-yellow-100 text-yellow-800 border-yellow-300' :
    normalized === 'published' ? 'bg-purple-100 text-purple-800 border-purple-300' :
    'bg-gray-100 text-gray-700 border-gray-300';
  return (
    <span className={cn(
      'ml-2 px-2 py-0.5 rounded text-xs font-semibold border',
      color
    )}>
      {normalized.charAt(0).toUpperCase() + normalized.slice(1)}
    </span>
  );
} 