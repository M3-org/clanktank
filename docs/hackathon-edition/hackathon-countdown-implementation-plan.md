# Submission Deadline Countdown Implementation Plan

## Overview
This plan outlines the implementation of a submission deadline countdown component for the Clank Tank hackathon dashboard, to be displayed on both the Dashboard and Frontpage.

## Current Infrastructure

### Backend Support
- **Environment Variable**: `SUBMISSION_DEADLINE` (ISO format datetime string)
- **API Function**: `is_submission_window_open()` in `app.py`
- **API Endpoint**: `/api/config` returns:
  ```json
  {
    "submission_window_open": true,
    "submission_deadline": "2024-01-31T23:59:59",
    "current_time": "2024-01-25T10:30:00"
  }
  ```

### Frontend Structure
- **Dashboard**: `/hackathon/dashboard/frontend/src/pages/Dashboard.tsx`
- **Frontpage**: `/hackathon/dashboard/frontend/src/pages/Frontpage.tsx`
- **Components**: `/hackathon/dashboard/frontend/src/components/`
- **API Library**: Already integrated with `hackathonApi` for data fetching

## Implementation Plan

### Phase 1: Create Countdown Component

#### 1.1 Create `CountdownTimer.tsx` Component
**Location**: `/hackathon/dashboard/frontend/src/components/CountdownTimer.tsx`

**Features**:
- Real-time countdown display (days, hours, minutes, seconds)
- Auto-refresh every second
- Visual states:
  - **Active**: Colorful countdown with time remaining
  - **Expired**: Red warning message
  - **No Deadline**: Subtle "No deadline set" message
- Responsive design for mobile/desktop
- Dark mode support

**Props Interface**:
```typescript
interface CountdownTimerProps {
  deadline: string | null;
  variant?: 'banner' | 'compact' | 'card';
  className?: string;
  showLabel?: boolean;
}
```

#### 1.2 Component Architecture (Streamlined)
```typescript
// Minimal state - just total seconds remaining
const [totalSeconds, setTotalSeconds] = useState<number | null>(null);
const epochRef = useRef<number>(0); // Server epoch for monotonic time

// Monotonic ticker (handles sleep/wake gracefully)
function useTicker(callback: () => void) {
  useEffect(() => {
    let timeoutId: number;
    
    const step = () => {
      callback();
      timeoutId = window.setTimeout(step, 1000 - (performance.now() % 1000));
    };
    
    step();
    return () => clearTimeout(timeoutId);
  }, [callback]);
}

// Simple countdown calculation
const calculateTime = useCallback(() => {
  if (!deadline) return;
  
  const now = epochRef.current + performance.now();
  const target = new Date(deadline).getTime();
  const diff = Math.floor((target - now) / 1000);
  
  setTotalSeconds(diff > 0 ? diff : null);
}, [deadline]);

// Derive display values in render (no extra state)
const days = totalSeconds ? Math.floor(totalSeconds / 86400) : 0;
const hours = totalSeconds ? Math.floor(totalSeconds / 3600) % 24 : 0;
const minutes = totalSeconds ? Math.floor(totalSeconds / 60) % 60 : 0;
const seconds = totalSeconds ? totalSeconds % 60 : 0;

useTicker(calculateTime);
```

#### 1.3 Visual Design Variants (Optimized)

**Banner Variant** (for hero sections):
```tsx
// Memoized to avoid re-renders when only numbers change
const TimeUnit = React.memo(({ value, label }: { value: number; label: string }) => (
  <div className="text-center">
    <div className="text-3xl font-bold">{value}</div>
    <div className="text-sm opacity-75">{label}</div>
  </div>
));

<div 
  className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white p-6 rounded-lg shadow-lg"
  style={{ '--remaining-seconds': timeRemaining?.totalSeconds }}
  data-remaining-s
  aria-live="polite"
>
  <div className="text-center">
    <h3 className="text-lg font-semibold mb-2">Submissions Close In</h3>
    <div className="flex justify-center gap-4">
      <TimeUnit value={timeRemaining.days} label="Days" />
      <TimeUnit value={timeRemaining.hours} label="Hours" />
      <TimeUnit value={timeRemaining.minutes} label="Minutes" />
      <TimeUnit value={timeRemaining.seconds} label="Seconds" />
    </div>
  </div>
</div>
```

**Compact Variant** (using Intl.RelativeTimeFormat):
```tsx
const compactFormat = useMemo(() => {
  if (!timeRemaining) return 'Expired';
  
  const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' });
  const { totalSeconds } = timeRemaining;
  
  if (totalSeconds > 86400) return rtf.format(Math.ceil(totalSeconds / 86400), 'day');
  if (totalSeconds > 3600) return rtf.format(Math.ceil(totalSeconds / 3600), 'hour');
  return rtf.format(Math.ceil(totalSeconds / 60), 'minute');
}, [timeRemaining]);

<div className="inline-flex items-center gap-2 text-sm">
  <Clock className="h-4 w-4" />
  <span>{compactFormat}</span>
</div>
```

**Urgency States** (clean conditional classes):
```tsx
<div 
  data-s={totalSeconds}
  className={clsx('countdown-timer', {
    'text-green-600': totalSeconds > 86400,
    'text-orange-600': totalSeconds <= 86400 && totalSeconds > 3600,
    'text-red-600': totalSeconds <= 3600,
  })}
  aria-live="polite"
>
  {/* countdown content */}
</div>
```

### Phase 2: API Integration

#### 2.1 Create Backend Endpoint
**Location**: `/hackathon/backend/app.py`

**REQUIRED**: Add the missing `/api/config` endpoint with grace period logic:
```python
@app.get("/api/config", tags=["latest"])
async def get_config():
    """Get configuration including submission deadline information."""
    info = get_submission_window_info()
    
    # Add grace period logic here (not in frontend)
    grace_period = 60 * 60  # 60 minutes grace (feeling generous!)
    if info["submission_deadline"]:
        deadline = datetime.fromisoformat(info["submission_deadline"])
        now = datetime.now(timezone.utc)
        info["can_submit"] = now < (deadline + timedelta(seconds=grace_period))
    else:
        info["can_submit"] = True
        
    return info
```

Centralizes grace period logic in one place instead of sprinkling it across frontend/backend.

#### 2.2 Update API Client
**Location**: `/hackathon/dashboard/frontend/src/lib/api.ts`

Add method to fetch deadline info:
```typescript
async getConfig(): Promise<{
  submission_window_open: boolean;
  submission_deadline: string | null;
  current_time: string;
}> {
  const response = await fetch(`${this.baseUrl}/api/config`);
  return response.json();
}
```

#### 2.3 Simple Config Cache (No Context)
**Location**: `/hackathon/dashboard/frontend/src/lib/config.ts`

```typescript
// Dead-simple singleton cache
export const configPromise = fetch('/api/config').then(r => r.json());

// Use anywhere without providers
export async function useDeadline() {
  try {
    const config = await configPromise;
    
    // Calculate server epoch once for monotonic time
    const serverTime = new Date(config.current_time).getTime();
    const epoch = serverTime - performance.now();
    
    return {
      deadline: config.submission_deadline,
      epoch,
      canSubmit: config.can_submit // Let backend handle grace periods
    };
  } catch (err) {
    console.error('Failed to fetch deadline:', err);
    return { deadline: null, epoch: Date.now(), canSubmit: false };
  }
}
```

### Phase 3: Integration with Pages

#### 3.1 Dashboard Integration
**Location**: `/hackathon/dashboard/frontend/src/pages/Dashboard.tsx`

Add countdown to the stats section:
```tsx
// Add to imports
import { CountdownTimer } from '../components/CountdownTimer';
import { useDeadline } from '../hooks/useDeadline';

// In component
const { deadline, isOpen, loading: deadlineLoading } = useDeadline();

// Add to stats grid (after existing stats)
{deadline && (
  <CountdownTimer 
    deadline={deadline}
    variant="card"
    className="col-span-1"
  />
)}
```

#### 3.2 Frontpage Integration
**Location**: `/hackathon/dashboard/frontend/src/pages/Frontpage.tsx`

Add countdown to hero section:
```tsx
// Add to hero section, after the logo and description
{deadline && (
  <div className="mt-8 max-w-md mx-auto">
    <CountdownTimer 
      deadline={deadline}
      variant="banner"
      showLabel={true}
    />
  </div>
)}
```

### Phase 4: Additional Features

#### 4.1 Deadline Status Indicators
Add visual indicators throughout the app:
- **Header**: Compact countdown in navigation
- **Submission Page**: Warning banner when deadline is near
- **Form Validation**: Block submissions when deadline passed

#### 4.2 Simple Urgency States
Different visual states based on time remaining:
- **> 1 day**: Green, calm
- **< 1 day**: Orange, urgent  
- **Expired**: Red, blocked

### Phase 5: Testing & Deployment

#### 5.1 Component Testing
- Test with various deadline formats
- Test timezone handling
- Test countdown accuracy
- Test visual states and transitions

#### 5.2 Integration Testing
- Test API integration
- Test with real deadline data
- Test error handling
- Test mobile responsiveness

#### 5.3 Environment Testing
- Test with `SUBMISSION_DEADLINE` set
- Test with no deadline (always open)
- Test with invalid deadline format
- Test with expired deadline

## Implementation Timeline

### Day 1: Backend & Component
- [ ] Add `/api/config` endpoint to backend
- [ ] Create `CountdownTimer.tsx` component
- [ ] Implement simple countdown logic
- [ ] Create `useDeadline` hook

### Day 2: Integration & Polish
- [ ] Integrate with Dashboard page
- [ ] Integrate with Frontpage  
- [ ] Add simple urgency states (green/orange/red)
- [ ] Test and deploy

## Technical Optimizations

### 1. Performance (Expert-Level)
- **Server as time source**: Calculate drift once, use `Date.now() - drift` for accuracy
- **Drift-free ticking**: `setTimeout` aligned to next full second (no cumulative drift)
- **Memoized rendering**: `React.memo` on TimeUnit, `useMemo` for formatting
- **Shared context**: Both pages fetch config only once, subsequent mounts read from cache
- **CSS urgency states**: Use CSS custom properties instead of JS conditionals

### 2. Simplicity
- **Single API call**: Fetch deadline once, calculate countdown locally
- **No timezone complexity**: Native Date objects handle it automatically  
- **Single source of truth**: Backend provides deadline via `/api/config`
- **Clean intervals**: Proper `setTimeout` cleanup on unmount

### 3. Built-in APIs (Zero Dependencies)
- **Intl.RelativeTimeFormat**: "in 5 hours", "in 4 minutes" with auto-pluralization
- **aria-live="polite"**: Accessibility announcements for unit rollovers
- **CSS custom properties**: Dynamic urgency styling without re-renders

## Dependencies Required

### No New Dependencies
All functionality uses native JavaScript Date objects and existing dependencies:
- `lucide-react` - Icons (Clock, AlertCircle, etc.)
- `tailwindcss` - Styling
- React hooks - State management
- Existing API client - Data fetching

## Configuration

### Environment Variables
```bash
# Backend (.env)
SUBMISSION_DEADLINE=2024-01-31T23:59:59-05:00
```

### API Response Format
```json
{
  "submission_window_open": true,
  "submission_deadline": "2024-01-31T23:59:59-05:00",
  "current_time": "2024-01-25T10:30:00-05:00"
}
```

## Success Metrics
- [ ] Countdown displays accurate time remaining
- [ ] Visual states change appropriately (green → orange → red)
- [ ] Mobile responsive design
- [ ] Single API call on mount (no repeated requests)
- [ ] Proper interval cleanup
- [ ] Integrates seamlessly with existing UI

---

*Implementation Plan Created: 2025-01-09*