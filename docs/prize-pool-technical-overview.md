# Prize Pool Component Technical Overview

The prize pool component provides **real-time blockchain tracking** of deposits to the hackathon prize wallet with an animated progress bar showing progress toward the funding goal.

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Solana        │    │   Backend API    │    │   Frontend      │
│   Blockchain    │───▶│   (FastAPI)      │───▶│   React Hook    │
│                 │    │                  │    │                 │
│ Prize Wallet    │    │ Helius DAS API   │    │ Progress Bar    │
│ Deposits        │    │ Token Metadata   │    │ Components      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Backend Data Source

**File**: `hackathon/backend/app.py:1778`

The backend uses the Helius DAS (Digital Asset Standard) API to fetch real-time token holdings:

```python
@app.get("/api/prize-pool")
async def get_prize_pool():
    """Get crypto-native prize pool data using Helius DAS API."""
    
    # Environment configuration
    helius_api_key = os.getenv('HELIUS_API_KEY')
    prize_wallet = os.getenv('PRIZE_WALLET_ADDRESS')
    target_sol = float(os.getenv('PRIZE_POOL_TARGET_SOL', 10))
    
    # Fetch real-time token holdings from Helius DAS API
    payload = {
        "jsonrpc": "2.0",
        "id": "prize-pool-live",
        "method": "getAssetsByOwner",
        "params": {
            "ownerAddress": prize_wallet,
            "page": 1,
            "limit": 100,
            "options": {
                "showFungible": True,
                "showNativeBalance": True,
                "showZeroBalance": False
            }
        }
    }
```

### Token Metadata Caching

To avoid API rate limits, the system implements 24-hour caching:

```python
def get_token_metadata_from_helius(mint_address):
    """Fetch token metadata from Helius DAS API and cache it"""
    
    # Check 24-hour cache first
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM token_metadata WHERE token_mint = :token_mint AND last_updated > :min_time"),
            {'token_mint': mint_address, 'min_time': int(time.time()) - 86400}
        )
        cached = result.fetchone()
        if cached:
            return {
                'symbol': cached[2],
                'decimals': cached[4],
                'logo': cached[6] or cached[5]  # prefer cdn_uri over logo_uri
            }
```

### SOL Balance Conversion

Native SOL balance is converted from lamports:

```python
# Process native SOL balance
native_balance = data['result'].get('nativeBalance', {})
if native_balance and native_balance.get('lamports', 0) > 0:
    sol_amount = native_balance['lamports'] / 1_000_000_000  # Convert lamports to SOL
    total_sol = sol_amount
    token_breakdown['SOL'] = {
        'mint': 'So11111111111111111111111111111111111111112',
        'symbol': 'SOL',
        'amount': sol_amount
    }
```

## Frontend Data Hook

**File**: `hackathon/frontend/src/hooks/usePrizePool.ts`

The React hook manages data fetching and processing:

```typescript
export function usePrizePool() {
  const [tokenHoldings, setTokenHoldings] = useState<TokenHolding[]>([])
  const [totalValue, setTotalValue] = useState(0)
  const [loading, setLoading] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  const fetchTokenHoldings = useCallback(async () => {
    // Use existing backend API instead of direct Helius calls
    const prizePoolData = await hackathonApi.getPrizePool()
    
    // Convert backend format to frontend format
    const processedTokens: TokenHolding[] = []
    const totalSol = prizePoolData.total_sol || 0
    
    // Process token breakdown with full Helius metadata
    if (prizePoolData.token_breakdown) {
      for (const [symbol, tokenData] of Object.entries(prizePoolData.token_breakdown)) {
        processedTokens.push({
          mint: tokenData.mint || '',
          symbol: tokenData.symbol || symbol,
          amount: tokenData.amount.toString(),
          solValue: symbol === 'SOL' ? tokenData.amount : 0,
          logo: tokenData.logo
        })
      }
    }
    
    setTokenHoldings(sortedTokens)
    setTotalValue(totalSol)
    setLastUpdated(new Date())
  }, [])

  // Auto-fetch every 2 minutes
  useEffect(() => {
    fetchTokenHoldings()
    const interval = setInterval(fetchTokenHoldings, 120000) // 2 minutes
    return () => clearInterval(interval)
  }, [fetchTokenHoldings])
}
```

### Token Prioritization

The hook sorts tokens by priority and balance:

```typescript
// Sort: Priority tokens first (SOL, ai16z, USDC), then by balance amount
const priorityTokens = ['SOL', 'ai16z', 'USDC']
const sortedTokens = processedTokens
  .sort((a, b) => {
    const aPriority = priorityTokens.indexOf(a.symbol)
    const bPriority = priorityTokens.indexOf(b.symbol)
    
    // Priority tokens come first
    if (aPriority !== -1 && bPriority !== -1) {
      return aPriority - bPriority
    }
    if (aPriority !== -1) return -1
    if (bPriority !== -1) return 1
    
    // Non-priority tokens sorted by balance
    return parseFloat(b.amount) - parseFloat(a.amount)
  })
  .slice(0, 12) // Show up to 12 tokens
```

## Progress Bar Component

**File**: `hackathon/frontend/src/components/PrizePool.tsx`

The component calculates and renders the progress bar:

```typescript
export function PrizePool({ goal = 10, variant = 'card' }: PrizePoolProps) {
  const prizePoolData = usePrizePool()
  
  // Progress calculation
  const progress = Math.min((prizePoolData.totalValue / goal) * 100, 100)
  
  // Card variant progress bar
  if (variant === 'card') {
    return (
      <div 
        role="progressbar"
        aria-valuenow={progress}
        aria-valuemax={100}
        className="relative h-2 bg-brand-mid/40 rounded-full overflow-hidden"
      >
        <div 
          className="absolute inset-0 bg-brand-accent transition-[width] duration-700"
          style={{ width: `${progress}%` }}
        />
      </div>
    )
  }
  
  // Marquee variant (bottom sticky bar)
  if (variant === 'marquee') {
    return (
      <div className="fixed bottom-0 left-0 right-0 z-50">
        {/* Animated progress bar at top */}
        <div className="relative h-1 bg-slate-700/50">
          <div 
            className="absolute inset-y-0 left-0 bg-gradient-to-r from-cyan-400 to-blue-500 transition-all duration-1000 ease-out"
            style={{ width: `${Math.min(progress, 100)}%` }}
          />
        </div>
        
        {/* Prize pool display */}
        <div className="h-16 px-4 flex items-center">
          <div className="text-white font-semibold">
            Prize Pool • {pretty(totalValue)} SOL
          </div>
          <div className="text-slate-400 text-xs">
            {progress.toFixed(1)}% of {goal} SOL goal
          </div>
        </div>
      </div>
    )
  }
}
```

### Token Display Modal

For detailed token breakdown:

```typescript
// Token breakdown with logos
{tokenHoldings.slice(0, 3).map((token) => (
  <div key={token.mint} className="flex items-center justify-between">
    <div className="flex items-center gap-2">
      <div className="w-2 h-2 rounded-full bg-brand-accent"></div>
      <span>{token.symbol}</span>
    </div>
    <span>{pretty(parseFloat(token.amount))}</span>
  </div>
))}

{tokenHoldings.length > 3 && (
  <button onClick={() => setShowTokenModal(true)}>
    View all {tokenHoldings.length} tokens
  </button>
)}
```

## Environment Configuration

**File**: `.env` (project root)

Required environment variables:

```bash
# Required: Prize wallet address for tracking deposits
PRIZE_WALLET_ADDRESS=2K1reedtyDUQigdaLoHLEyugkH88iVGNE2BQemiGx6xf

# Required: Helius API key for blockchain data
HELIUS_API_KEY=your_helius_api_key_here

# Optional: Prize pool target (default: 10 SOL)
PRIZE_POOL_TARGET_SOL=10

# Frontend environment variables (Vite prefix required)
VITE_PRIZE_WALLET_ADDRESS=2K1reedtyDUQigdaLoHLEyugkH88iVGNE2BQemiGx6xf
```

## Data Flow Timeline

1. **Deposit Detection** (Real-time)
   - User sends SOL/tokens to prize wallet
   - Transaction confirms on Solana blockchain

2. **Backend Polling** (Every API call)
   - FastAPI endpoint calls Helius DAS API
   - Fetches current wallet token holdings
   - Caches token metadata for 24 hours

3. **Frontend Updates** (Every 2 minutes)
   - React hook polls backend API
   - Calculates new progress percentage
   - Updates component state

4. **Visual Animation** (Immediate)
   - Progress bar width animates to new percentage
   - Token breakdown updates with new holdings
   - Last updated timestamp refreshes

## Database Schema

**Token Metadata Cache Table**:
```sql
CREATE TABLE token_metadata (
    token_mint TEXT PRIMARY KEY,
    symbol TEXT,
    name TEXT,
    decimals INTEGER,
    logo_uri TEXT,
    cdn_uri TEXT,
    json_uri TEXT,
    interface_type TEXT,
    content_metadata TEXT,
    last_updated INTEGER
);
```

## Key Features

- **Real-time tracking**: Deposits appear within 2 minutes of blockchain confirmation
- **Multi-token support**: Tracks SOL, SPL tokens, and provides token metadata
- **Progress visualization**: Animated progress bar with percentage display  
- **Caching optimization**: 24-hour metadata cache reduces API calls
- **Responsive design**: Card, banner, and marquee variants for different layouts
- **Error handling**: Graceful fallbacks when APIs are unavailable

## Files Used

### Backend
- `hackathon/backend/app.py:1778` - Prize pool API endpoint
- `hackathon/backend/app.py:1841` - Token metadata caching system

### Frontend  
- `hackathon/frontend/src/hooks/usePrizePool.ts` - Data fetching hook
- `hackathon/frontend/src/components/PrizePool.tsx` - UI components
- `hackathon/frontend/src/lib/api.ts` - API client with caching

### Configuration
- `.env` - Environment variables for wallet address and API keys
- `hackathon/frontend/src/lib/constants.ts` - Frontend constants

The system provides **autonomous prize pool tracking** without requiring manual intervention - deposits automatically appear in the progress bar as they're confirmed on the Solana blockchain.