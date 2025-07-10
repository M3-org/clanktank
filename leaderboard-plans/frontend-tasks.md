# Frontend Tasks (Well-Scoped for Community Event)

**Context**: Implementing UI based on decisions in `/home/jin/repo/clanktank/leaderboard-plans/question-audit.md`

**Tech Stack**: React + Vite + TypeScript + TailwindCSS (existing hackathon dashboard)

**Scope**: 20-50 projects, 100-200 voters, 1-week timeline

## Key Decisions Referenced:
- **Rotten Tomatoes style**: AI score (primary ranking) + Community score (secondary display) (A1, A4)
- **Score display**: Community score normalized to 0-10, show "—" when no votes (A2, A3)
- **Voting flows**: Both wallet-connect and anonymous copy-paste options (D12)
- **Vote slider**: Shows vote weight + overflow to prize pool with clear messaging
- **Prize pool**: Progress bar, SOL only, last 5 contributions (B5, B6, B7)
- **Mobile deep-links**: Phantom URI generation for mobile voting

---

## Leaderboard Updates (Day 1)

### Task 1: Add Community Score column to existing Leaderboard.tsx
**Priority**: High | **Effort**: 4 hours | **Dependencies**: Backend `/api/community-scores`

**File**: `/home/jin/repo/clanktank/hackathon/dashboard/frontend/src/pages/Leaderboard.tsx`

**Acceptance Criteria**:
- [ ] Add Community Score column next to existing AI score
- [ ] AI Score determines ranking (keep existing sort logic)
- [ ] Show "—" when no community votes (per decision A3)
- [ ] Community score normalized to 0-10 display (per decision A2)
- [ ] Tie-breaker: higher community score wins AI ties (per decision A4)

**Implementation example**:
```tsx
// Add to existing leaderboard entry display
<div className="score-display">
  <div className="ai-score">
    <span className="label">AI</span>
    <span className="primary-score">{entry.final_score.toFixed(1)}</span>
  </div>
  <div className="community-score">
    <span className="label">Community</span>
    <span className="secondary-score">
      {entry.community_score ? entry.community_score.toFixed(1) : "—"}
    </span>
  </div>
</div>
```

### Task 2: Simple refresh mechanism
**Priority**: Medium | **Effort**: 1 hour | **Dependencies**: Task 1

**Acceptance Criteria**:
- [ ] Refresh button to reload community scores (no real-time needed for MVP)
- [ ] Auto-refresh every 30 seconds during voting period
- [ ] Loading indicator during refresh
- [ ] Error handling if API fails

**Implementation**:
```tsx
const [refreshing, setRefreshing] = useState(false);

const refreshScores = async () => {
  setRefreshing(true);
  try {
    const scores = await hackathonApi.getCommunityScores();
    // Update leaderboard with new scores
  } catch (error) {
    console.error('Refresh failed:', error);
  } finally {
    setRefreshing(false);
  }
};

// Auto-refresh every 30 seconds
useEffect(() => {
  const interval = setInterval(refreshScores, 30000);
  return () => clearInterval(interval);
}, []);
```

---

## Prize Pool Widget (Day 2)

### Task 3: Multi-token prize pool widget with USD display
**Priority**: High | **Effort**: 4 hours | **Dependencies**: Backend `/api/prize-pool`

**Acceptance Criteria**:
- [ ] Progress bar with USD total vs USD target (updated decision B6)
- [ ] Token breakdown showing SOL, ai16z, and other contributions
- [ ] Real-time USD conversion using Birdeye prices
- [ ] Last 5 contributions feed with token types
- [ ] Add to existing leaderboard page

**Implementation**:
```tsx
interface PrizePoolData {
  total_usd: number;
  target_usd: number;
  progress_percentage: number;
  token_breakdown: {
    [symbol: string]: {
      mint: string;
      amount: number;
      usd_value: number;
      price_per_token: number;
    };
  };
  recent_contributions: Array<{
    wallet: string;
    token: string;
    amount: number;
    source: string;
    timestamp: number;
  }>;
}

const PrizePoolWidget: React.FC = () => {
  const [poolData, setPoolData] = useState<PrizePoolData | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  
  const fetchPrizePool = async () => {
    setRefreshing(true);
    try {
      const response = await fetch('/api/prize-pool');
      const data = await response.json();
      setPoolData(data);
    } catch (error) {
      console.error('Failed to fetch prize pool:', error);
    } finally {
      setRefreshing(false);
    }
  };
  
  useEffect(() => {
    fetchPrizePool();
    // Refresh every 30 seconds
    const interval = setInterval(fetchPrizePool, 30000);
    return () => clearInterval(interval);
  }, []);
  
  if (!poolData) return <div>Loading prize pool...</div>;
  
  return (
    <div className="prize-pool-widget bg-white dark:bg-gray-900 rounded-lg p-6 mb-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-xl font-semibold">Prize Pool</h3>
        <button 
          onClick={fetchPrizePool}
          disabled={refreshing}
          className="text-sm text-gray-500 hover:text-gray-700"
        >
          {refreshing ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>
      
      {/* Main USD display */}
      <div className="text-center mb-4">
        <div className="text-3xl font-bold text-green-600">
          ${poolData.total_usd.toFixed(2)} USD
        </div>
        <div className="text-gray-500">
          / ${poolData.target_usd.toFixed(2)} USD target ({poolData.progress_percentage.toFixed(1)}%)
        </div>
      </div>
      
      {/* Progress bar */}
      <div className="w-full bg-gray-200 rounded-full h-4 mb-6">
        <div 
          className="bg-green-500 h-4 rounded-full transition-all duration-500"
          style={{ width: `${Math.min(poolData.progress_percentage, 100)}%` }}
        />
      </div>
      
      {/* Token breakdown */}
      {Object.keys(poolData.token_breakdown).length > 0 && (
        <div className="mb-6">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Token Breakdown</h4>
          <div className="space-y-2">
            {Object.entries(poolData.token_breakdown).map(([symbol, data]) => (
              <div key={symbol} className="flex justify-between items-center text-sm">
                <span className="font-medium">{symbol}</span>
                <div className="text-right">
                  <div>{data.amount.toFixed(2)} tokens</div>
                  <div className="text-gray-500">${data.usd_value.toFixed(2)}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Recent contributions */}
      <div>
        <h4 className="text-sm font-medium text-gray-700 mb-2">Recent Contributions</h4>
        <div className="space-y-1">
          {poolData.recent_contributions.map((contrib, index) => (
            <div key={index} className="text-xs text-gray-600 flex justify-between">
              <span>
                {contrib.wallet} sent {contrib.amount.toFixed(2)} {contrib.token}
              </span>
              <span className="text-gray-400">
                {contrib.source === 'vote_overflow' ? 'Vote overflow' : 'Direct donation'}
              </span>
            </div>
          ))}
          {poolData.recent_contributions.length === 0 && (
            <div className="text-xs text-gray-400">No contributions yet</div>
          )}
        </div>
      </div>
    </div>
  );
};
```

### Task 4: "View All" contributions modal (if time allows)
**Priority**: Low | **Effort**: 2 hours | **Dependencies**: Task 3

**Acceptance Criteria**:
- [ ] Simple modal with all contributions
- [ ] No pagination needed for community event scale
- [ ] Basic mobile-friendly design

---

## Voting Interface (Day 3)

### Task 5: Vote amount slider with clear messaging
**Priority**: High | **Effort**: 3 hours | **Dependencies**: None

**Acceptance Criteria**:
- [ ] Slider for amount selection (1-100 ai16z range is fine for community event)
- [ ] Real-time vote weight calculation using formula: `min(log10(amount + 1) × 3, 10)`
- [ ] Clear messaging per vote-weight slider design from overview.md
- [ ] "You'll cast: X votes" feedback
- [ ] "Goes to pool: X ai16z" overflow feedback

**Implementation**:
```tsx
const VoteSlider: React.FC<{ onAmountChange: (amount: number) => void }> = ({ onAmountChange }) => {
  const [amount, setAmount] = useState(1);
  
  // Vote weight formula from decisions C8
  const voteWeight = Math.min(Math.log10(amount + 1) * 3, 10);
  
  return (
    <div className="vote-slider">
      <label>Amount of ai16z to send</label>
      <input
        type="range"
        min="1"
        max="100"
        value={amount}
        onChange={(e) => {
          const newAmount = Number(e.target.value);
          setAmount(newAmount);
          onAmountChange(newAmount);
        }}
      />
      
      <div className="feedback">
        <div>You'll cast: {voteWeight.toFixed(1)} votes</div>
        {amount > 10 && (
          <div>Extra tokens grow the prize pool</div>
        )}
      </div>
    </div>
  );
};
```

### Task 6: Anonymous voting (copy-paste method)  
**Priority**: High | **Effort**: 2 hours | **Dependencies**: Task 5

**Acceptance Criteria**:
- [ ] Generate copy-paste instructions for desktop users
- [ ] Generate Phantom deep-links for mobile (per decision D12)
- [ ] Clear voting instructions
- [ ] Works without wallet connection

**Implementation**:
```tsx
const generateVoteInstructions = (submissionId: string, amount: number) => {
  const address = import.meta.env.VITE_VOTE_WALLET;
  const memo = submissionId;
  const AI16Z_MINT = import.meta.env.VITE_AI16Z_MINT;
  
  // Mobile deep link
  const deepLink = `solana:${address}?amount=${amount}&spl-token=${AI16Z_MINT}&memo=${memo}`;
  
  return {
    deepLink,
    instructions: `Send ${amount} ai16z to ${address} with memo: ${memo}`
  };
};

const VoteButton: React.FC<{ submissionId: string }> = ({ submissionId }) => {
  const [amount, setAmount] = useState(1);
  const isMobile = /Mobile|Android|iPhone/.test(navigator.userAgent);
  
  const { deepLink, instructions } = generateVoteInstructions(submissionId, amount);
  
  return (
    <div className="vote-section">
      <VoteSlider onAmountChange={setAmount} />
      
      {isMobile ? (
        <a href={deepLink} className="vote-button">
          Vote with Phantom
        </a>
      ) : (
        <div className="copy-instructions">
          <p>{instructions}</p>
          <button onClick={() => navigator.clipboard.writeText(instructions)}>
            Copy Instructions
          </button>
        </div>
      )}
    </div>
  );
};
```

### Task 7: Basic wallet connection (if time allows)
**Priority**: Low | **Effort**: 4 hours | **Dependencies**: Task 6

**Acceptance Criteria**:
- [ ] Simple wallet adapter for Phantom
- [ ] One project at a time voting (no cart needed for MVP)
- [ ] Transaction confirmation handling
- [ ] Fallback to copy-paste if connection fails

---

## Polish & Testing (Day 4)

### Task 8: Basic responsive design  
**Priority**: Medium | **Effort**: 2 hours | **Dependencies**: Tasks 1, 3, 5

**Acceptance Criteria**:
- [ ] Mobile-friendly voting slider and buttons
- [ ] Prize pool widget responsive on mobile
- [ ] Community score column readable on mobile
- [ ] No horizontal scrolling

### Task 9: Simple animations (if time allows)
**Priority**: Low | **Effort**: 2 hours | **Dependencies**: Task 2

**Acceptance Criteria**:
- [ ] Subtle glow/pulse on community score when it updates (per decision D14)
- [ ] Smooth progress bar animation for prize pool
- [ ] Basic CSS transitions (no complex animation library)

### Task 10: Manual testing
**Priority**: High | **Effort**: 2 hours | **Dependencies**: All tasks

**Acceptance Criteria**:
- [ ] Test voting flow on mobile (Phantom deep-link)
- [ ] Test voting flow on desktop (copy-paste)
- [ ] Test community score display with and without votes
- [ ] Test prize pool widget with contributions
- [ ] Test responsive design on different screen sizes

---

## Environment Setup

### Task 11: Frontend environment variables
**Priority**: Medium | **Effort**: 30 minutes | **Dependencies**: None

**Required variables**:
```bash
# Vite environment variables (note: VITE_ prefix, not NEXT_PUBLIC_)
VITE_API_BASE_URL=http://localhost:8000
VITE_AI16Z_MINT=HeLp6NuQkmYB4pYWo2zYs22mESHXPQYzXbB8n4V98jwC  
VITE_VOTE_WALLET=your_vote_wallet_address_here
```

---

## Success Criteria (Community Event Scale)
- [ ] **Community scores**: Display properly in leaderboard
- [ ] **Prize pool**: Shows current amount and progress  
- [ ] **Mobile voting**: Phantom deep-links work on iOS/Android
- [ ] **Desktop voting**: Copy-paste instructions clear and functional
- [ ] **Responsive**: No broken layouts on mobile devices
- [ ] **Performance**: Page loads in < 3 seconds on mobile
- [ ] **Error handling**: Graceful fallbacks when APIs fail