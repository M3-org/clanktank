import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { Clock, AlertCircle } from 'lucide-react';
import clsx from 'clsx';
import { useDeadline } from '../lib/config';

interface CountdownTimerProps {
  variant?: 'banner' | 'compact' | 'card';
  className?: string;
  showLabel?: boolean;
}

// Memoized time unit component to avoid re-renders when only numbers change
const TimeUnit = React.memo(({ value, label }: { value: number; label: string }) => (
  <div className="text-center">
    <div className="text-3xl font-bold">{value}</div>
    <div className="text-sm opacity-75">{label}</div>
  </div>
));

TimeUnit.displayName = 'TimeUnit';

// Time constants for readability
const SECONDS_PER_MINUTE = 60;
const SECONDS_PER_HOUR = 3600;
const SECONDS_PER_DAY = 86400;

// Monotonic ticker (handles sleep/wake gracefully)
function useTicker(callback: () => void) {
  useEffect(() => {
    let timeoutId: number;
    
    const step = () => {
      callback();
      // Align with next full second to avoid drift
      timeoutId = window.setTimeout(step, 1000 - (performance.now() % 1000));
    };
    
    step();
    return () => clearTimeout(timeoutId);
  }, [callback]);
}

export function CountdownTimer({ 
  variant = 'banner', 
  className = '', 
  showLabel = true 
}: CountdownTimerProps) {
  // Minimal state - just total seconds remaining
  const [totalSeconds, setTotalSeconds] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const epochRef = useRef<number>(0); // Server epoch for monotonic time
  const deadlineRef = useRef<string | null>(null);

  // Load config once on mount
  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const config = await useDeadline();
        deadlineRef.current = config.deadline;
        epochRef.current = config.epoch;
        
        if (config.deadline) {
          // Calculate initial time
          const now = epochRef.current + performance.now();
          const target = new Date(config.deadline).getTime();
          const diff = Math.floor((target - now) / 1000);
          setTotalSeconds(diff > 0 ? diff : null);
        }
      } catch (err) {
        console.error('Failed to load deadline config:', err);
        setTotalSeconds(null);
      } finally {
        setLoading(false);
      }
    };

    fetchConfig();
  }, []);

  // Simple countdown calculation
  const calculateTime = useCallback(() => {
    const deadline = deadlineRef.current;
    if (!deadline) return;
    
    const now = epochRef.current + performance.now();
    const target = new Date(deadline).getTime();
    const diff = Math.floor((target - now) / 1000);
    
    setTotalSeconds(diff > 0 ? diff : null);
  }, []);

  // Derive display values in render (no extra state)
  const days = totalSeconds ? Math.floor(totalSeconds / SECONDS_PER_DAY) : 0;
  const hours = totalSeconds ? Math.floor(totalSeconds / SECONDS_PER_HOUR) % 24 : 0;
  const minutes = totalSeconds ? Math.floor(totalSeconds / SECONDS_PER_MINUTE) % 60 : 0;
  const seconds = totalSeconds ? totalSeconds % 60 : 0;

  // Compact format using Intl.RelativeTimeFormat (must be before early returns)
  const compactFormat = useMemo(() => {
    if (!totalSeconds) return 'Expired';
    
    const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' });
    
    if (totalSeconds > SECONDS_PER_DAY) return rtf.format(Math.ceil(totalSeconds / SECONDS_PER_DAY), 'day');
    if (totalSeconds > SECONDS_PER_HOUR) return rtf.format(Math.ceil(totalSeconds / SECONDS_PER_HOUR), 'hour');
    return rtf.format(Math.ceil(totalSeconds / SECONDS_PER_MINUTE), 'minute');
  }, [totalSeconds]);

  useTicker(calculateTime);

  // Don't render while loading or if no deadline
  if (loading || !deadlineRef.current) return null;


  // Handle expired deadline
  if (totalSeconds === null) {
    if (variant === 'compact') {
      return (
        <div className={clsx('inline-flex items-center gap-2 text-sm text-red-600', className)}>
          <AlertCircle className="h-4 w-4" />
          <span>Submissions Closed</span>
        </div>
      );
    }
    
    return (
      <div className={clsx('bg-red-100 border-red-200 text-red-800 p-6 rounded-lg text-center', className)}>
        <AlertCircle className="h-8 w-8 mx-auto mb-2" />
        <h3 className="text-lg font-semibold">Submission Window Closed</h3>
      </div>
    );
  }

  // Banner variant (for hero sections)
  if (variant === 'banner') {
    return (
      <div 
        className={clsx(
          'bg-gradient-to-r from-indigo-600 to-purple-600 text-white p-6 rounded-lg shadow-lg',
          {
            'text-green-100': totalSeconds > SECONDS_PER_DAY,
            'text-orange-100': totalSeconds <= SECONDS_PER_DAY && totalSeconds > SECONDS_PER_HOUR,
            'text-red-100': totalSeconds <= SECONDS_PER_HOUR,
          },
          className
        )}
        data-s={totalSeconds}
        aria-live="polite"
      >
        <div className="text-center">
          {showLabel && <h3 className="text-lg font-semibold mb-2">Submissions Close In</h3>}
          <div className="flex justify-center gap-4">
            <TimeUnit value={days} label="Days" />
            <TimeUnit value={hours} label="Hours" />
            <TimeUnit value={minutes} label="Minutes" />
            <TimeUnit value={seconds} label="Seconds" />
          </div>
        </div>
      </div>
    );
  }

  // Compact variant (using Intl.RelativeTimeFormat)
  if (variant === 'compact') {
    return (
      <div className={clsx(
        'inline-flex items-center gap-2 text-sm',
        {
          'text-green-600': totalSeconds > SECONDS_PER_DAY,
          'text-orange-600': totalSeconds <= SECONDS_PER_DAY && totalSeconds > SECONDS_PER_HOUR,
          'text-red-600': totalSeconds <= SECONDS_PER_HOUR,
        },
        className
      )}>
        <Clock className="h-4 w-4" />
        <span>{compactFormat}</span>
      </div>
    );
  }

  // Card variant (for dashboard stats)
  return (
    <div className={clsx(
      'bg-white dark:bg-gray-800 border rounded-lg p-6',
      {
        'border-green-200 bg-green-50 dark:bg-green-900': totalSeconds > SECONDS_PER_DAY,
        'border-orange-200 bg-orange-50 dark:bg-orange-900': totalSeconds <= SECONDS_PER_DAY && totalSeconds > SECONDS_PER_HOUR,
        'border-red-200 bg-red-50 dark:bg-red-900': totalSeconds <= SECONDS_PER_HOUR,
      },
      className
    )}>
      <div className="flex items-center">
        <Clock className={clsx(
          'h-6 w-6',
          {
            'text-green-600 dark:text-green-400': totalSeconds > SECONDS_PER_DAY,
            'text-orange-600 dark:text-orange-400': totalSeconds <= SECONDS_PER_DAY && totalSeconds > SECONDS_PER_HOUR,
            'text-red-600 dark:text-red-400': totalSeconds <= SECONDS_PER_HOUR,
          }
        )} />
        <div className="ml-4">
          <h3 className={clsx(
            'font-semibold',
            {
              'text-green-800 dark:text-green-200': totalSeconds > SECONDS_PER_DAY,
              'text-orange-800 dark:text-orange-200': totalSeconds <= SECONDS_PER_DAY && totalSeconds > SECONDS_PER_HOUR,
              'text-red-800 dark:text-red-200': totalSeconds <= SECONDS_PER_HOUR,
            }
          )}>
            Submission Deadline
          </h3>
          <p className={clsx(
            {
              'text-green-600 dark:text-green-300': totalSeconds > SECONDS_PER_DAY,
              'text-orange-600 dark:text-orange-300': totalSeconds <= SECONDS_PER_DAY && totalSeconds > SECONDS_PER_HOUR,
              'text-red-600 dark:text-red-300': totalSeconds <= SECONDS_PER_HOUR,
            }
          )}>
            {compactFormat}
          </p>
        </div>
      </div>
    </div>
  );
}