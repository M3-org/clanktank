# Backend Tasks (Well-Scoped for Community Event)

**Context**: Implementing token voting system based on decisions in `/home/jin/repo/clanktank/leaderboard-plans/question-audit.md`

**Scope**: 20-50 projects, 100-200 voters, 1-week timeline

## Key Decisions Referenced:
- **Database**: Using existing hackathon.db (Option 1 - simpler for community event)
- **Vote weight formula**: `weight = min(log10(totalTokensSent + 1) × 3, 10)` per wallet per submission (C8)
- **Community score**: Normalized to 0-10 scale like AI scores (A2) 
- **Empty states**: Show "—" when no community votes (A3)
- **Prize pool**: Static target, SOL only display (B5, B6)
- **Contribution feed**: Last 5 deposits with "View All" modal (B7)

## Database Tasks

### Task 1: Create `sol_votes` table
**Priority**: High | **Effort**: 1 day | **Dependencies**: None

**Acceptance Criteria**:
- [ ] `sol_votes` table created with schema from implementation-guide.md
- [ ] Indexes created for performance
- [ ] Migration script created
- [ ] Can insert/query test data

**SQL to implement**:
```sql
CREATE TABLE sol_votes (
    tx_sig TEXT PRIMARY KEY,
    submission_id TEXT NOT NULL,
    sender TEXT NOT NULL,
    amount REAL NOT NULL,
    timestamp INTEGER NOT NULL
);

CREATE INDEX idx_sol_votes_submission ON sol_votes(submission_id);
CREATE INDEX idx_sol_votes_sender ON sol_votes(sender);
CREATE INDEX idx_sol_votes_timestamp ON sol_votes(timestamp);
```

### Task 2: Vote weight calculation function  
**Priority**: High | **Effort**: 2 hours | **Dependencies**: Task 1

**Acceptance Criteria**:
- [ ] Implement exact formula: `weight = min(log10(totalTokensSent + 1) × 3, 10)`
- [ ] Use environment variables for constants (multiplier=3, cap=10, min=1)
- [ ] Handle edge cases: < 1 ai16z returns 0 weight

**Implementation**:
```python
import math
import os

def calculate_vote_weight(total_tokens_sent):
    min_vote = float(os.getenv('MIN_VOTE_AMOUNT', 1))
    if total_tokens_sent < min_vote:
        return 0
    
    multiplier = float(os.getenv('VOTE_WEIGHT_MULTIPLIER', 3))
    cap = float(os.getenv('VOTE_WEIGHT_CAP', 10))
    
    return min(math.log10(total_tokens_sent + 1) * multiplier, cap)
```

---

## API Endpoints (Day 2)

### Task 3: `/api/community-scores` endpoint
**Priority**: High | **Effort**: 4 hours | **Dependencies**: Task 2

**Acceptance Criteria**:
- [ ] GET endpoint returns community scores for all submissions
- [ ] Normalized to 0-10 scale (matches AI scores per decision A2)
- [ ] Shows "—" equivalent (null/empty) when no votes (per decision A3)
- [ ] Basic error handling, no complex optimization needed

**Query implementation**:
```sql
-- Aggregate votes per wallet per submission, then sum weights
SELECT 
  submission_id,
  SUM(vote_weight) as raw_community_score,
  COUNT(DISTINCT sender) as unique_voters,
  MAX(timestamp) as last_tx_time
FROM (
  SELECT 
    submission_id,
    sender,
    -- Apply vote weight formula per wallet per submission
    CASE 
      WHEN SUM(amount) < 1 THEN 0
      ELSE MIN(LOG10(SUM(amount) + 1) * 3, 10)
    END as vote_weight
  FROM sol_votes 
  GROUP BY submission_id, sender
) wallet_weights
GROUP BY submission_id;
```

### Task 4: Multi-token prize pool with Birdeye API
**Priority**: Medium | **Effort**: 4 hours | **Dependencies**: Task 1

**Acceptance Criteria**:
- [ ] GET endpoint returns prize pool data with USD conversion (updated decision B6)
- [ ] Support for SOL, ai16z, and whitelisted tokens
- [ ] Birdeye API integration for real-time prices
- [ ] Token breakdown display
- [ ] Last 5 contributions for feed

**Database Schema Updates**:
```sql
-- Multi-token prize pool contributions
CREATE TABLE prize_pool_contributions (
    id INTEGER PRIMARY KEY,
    tx_sig TEXT UNIQUE,
    token_mint TEXT NOT NULL,
    token_symbol TEXT NOT NULL,
    amount REAL NOT NULL,
    usd_value_at_time REAL,
    contributor_wallet TEXT,
    source TEXT,  -- 'vote_overflow', 'direct_donation'
    timestamp INTEGER NOT NULL
);

-- Whitelisted tokens for prize pool
CREATE TABLE whitelisted_tokens (
    mint_address TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    name TEXT NOT NULL,
    decimals INTEGER DEFAULT 9,
    active BOOLEAN DEFAULT TRUE
);

-- Default whitelist data
INSERT INTO whitelisted_tokens VALUES
('So11111111111111111111111111111111111111112', 'SOL', 'Solana', 9, TRUE),
('HeLp6NuQkmYB4pYWo2zYs22mESHXPQYzXbB8n4V98jwC', 'ai16z', 'ai16z', 6, TRUE);
```

**Birdeye Price Service**:
```python
import requests
import time
from typing import Dict

class BirdeyePriceService:
    def __init__(self):
        self.base_url = "https://public-api.birdeye.so/defi/multi_price"
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        
    def get_token_prices(self, mint_addresses: list) -> Dict[str, float]:
        """Get current USD prices for multiple tokens"""
        cache_key = ','.join(sorted(mint_addresses))
        now = time.time()
        
        # Check cache
        if (cache_key in self.cache and 
            now - self.cache[cache_key]['timestamp'] < self.cache_ttl):
            return self.cache[cache_key]['prices']
        
        # Fetch from Birdeye
        params = {
            'list_address': ','.join(mint_addresses),
            'ui_amount_mode': 'raw'
        }
        headers = {
            'accept': 'application/json',
            'x-chain': 'solana'
        }
        
        try:
            response = requests.get(self.base_url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            prices = {}
            if data.get('success') and 'data' in data:
                for mint, price_data in data['data'].items():
                    prices[mint] = price_data.get('value', 0)
            
            # Cache results
            self.cache[cache_key] = {
                'prices': prices,
                'timestamp': now
            }
            
            return prices
            
        except Exception as e:
            app.logger.error(f"Birdeye API error: {e}")
            return {mint: 0 for mint in mint_addresses}

# Global price service instance
price_service = BirdeyePriceService()
```

**Updated Prize Pool API**:
```python
@app.route('/api/prize-pool')
def get_prize_pool():
    target_usd = float(os.getenv('PRIZE_POOL_TARGET_USD', 1000))
    
    # Get all contributions grouped by token
    cursor.execute("""
        SELECT token_mint, token_symbol, SUM(amount) as total_amount
        FROM prize_pool_contributions
        WHERE source IN ('vote_overflow', 'direct_donation')
        GROUP BY token_mint, token_symbol
    """)
    contributions_by_token = cursor.fetchall()
    
    # Get current prices
    mint_addresses = [row[0] for row in contributions_by_token]
    if mint_addresses:
        prices = price_service.get_token_prices(mint_addresses)
    else:
        prices = {}
    
    # Calculate total USD value and breakdown
    total_usd = 0
    token_breakdown = {}
    
    for mint, symbol, amount in contributions_by_token:
        price = prices.get(mint, 0)
        usd_value = amount * price
        total_usd += usd_value
        
        token_breakdown[symbol] = {
            'mint': mint,
            'amount': amount,
            'usd_value': usd_value,
            'price_per_token': price
        }
    
    # Get recent 5 contributions
    cursor.execute("""
        SELECT contributor_wallet, token_symbol, amount, source, timestamp
        FROM prize_pool_contributions
        ORDER BY timestamp DESC
        LIMIT 5
    """)
    recent_contributions = cursor.fetchall()
    
    return {
        'total_usd': total_usd,
        'target_usd': target_usd,
        'progress_percentage': (total_usd / target_usd) * 100 if target_usd > 0 else 0,
        'token_breakdown': token_breakdown,
        'recent_contributions': [
            {
                'wallet': contrib[0][:4] + '...' + contrib[0][-4:] if contrib[0] else 'Unknown',
                'token': contrib[1],
                'amount': contrib[2],
                'source': contrib[3],
                'timestamp': contrib[4]
            }
            for contrib in recent_contributions
        ]
    }
```

---

## Webhook Integration (Day 3)

### Task 5: Helius webhook receiver
**Priority**: High | **Effort**: 4 hours | **Dependencies**: Task 1

**Acceptance Criteria**:
- [ ] POST endpoint accepts Helius webhook payload
- [ ] Validates ai16z token mint: `HeLp6NuQkmYB4pYWo2zYs22mESHXPQYzXbB8n4V98jwC`
- [ ] Extracts memo as submission_id (per decision C9: lowercase/hyphens allowed)
- [ ] Uses tx_sig as primary key (per decision I25: prevents replay attacks)
- [ ] Basic logging, no enterprise monitoring needed

**Implementation with Vote/Prize Pool Split**:
```python
AI16Z_MINT = "HeLp6NuQkmYB4pYWo2zYs22mESHXPQYzXbB8n4V98jwC"

def process_ai16z_transaction(tx_sig, submission_id, sender, amount):
    """Process ai16z token transaction for voting and prize pool"""
    
    # Calculate vote weight (capped)
    vote_weight = min(math.log10(amount + 1) * 3, 10)
    
    # Calculate tokens used for voting vs overflow
    # Tokens needed for max vote weight (configurable)
    max_vote_tokens = float(os.getenv('MAX_VOTE_TOKENS', 100))
    vote_tokens = min(amount, max_vote_tokens)
    overflow_tokens = max(0, amount - max_vote_tokens)
    
    try:
        # Record the vote in sol_votes table
        cursor.execute("""
            INSERT OR IGNORE INTO sol_votes 
            (tx_sig, submission_id, sender, amount, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (tx_sig, submission_id, sender, vote_tokens, int(time.time())))
        
        # Record overflow as prize pool contribution
        if overflow_tokens > 0:
            cursor.execute("""
                INSERT OR IGNORE INTO prize_pool_contributions
                (tx_sig, token_mint, token_symbol, amount, contributor_wallet, source, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                f"{tx_sig}_overflow",  # Unique ID for overflow portion
                AI16Z_MINT,
                'ai16z',
                overflow_tokens,
                sender,
                'vote_overflow',
                int(time.time())
            ))
        
        conn.commit()
        app.logger.info(f"Processed vote: {vote_tokens} ai16z vote, {overflow_tokens} ai16z to prize pool")
        return True
        
    except Exception as e:
        app.logger.error(f"Transaction processing error: {e}")
        conn.rollback()
        return False

@app.route('/webhook/helius', methods=['POST'])
def helius_webhook():
    data = request.json
    
    # Extract transaction details
    tx_sig = data.get('signature')
    transfers = data.get('tokenTransfers', [])
    
    processed_count = 0
    
    for transfer in transfers:
        mint = transfer.get('mint')
        
        # Handle ai16z voting transactions
        if mint == AI16Z_MINT:
            submission_id = transfer.get('memo', '').strip()
            sender = transfer.get('fromUserAccount')
            amount = float(transfer.get('tokenAmount', 0))
            
            if submission_id and sender and amount >= 1:  # Minimum 1 ai16z
                if process_ai16z_transaction(tx_sig, submission_id, sender, amount):
                    processed_count += 1
        
        # Handle direct SOL donations to prize pool (no memo needed)
        elif mint == "So11111111111111111111111111111111111111112":
            sender = transfer.get('fromUserAccount') 
            amount = float(transfer.get('tokenAmount', 0))
            
            if sender and amount > 0:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO prize_pool_contributions
                        (tx_sig, token_mint, token_symbol, amount, contributor_wallet, source, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (tx_sig, "So11111111111111111111111111111111111111112", 'SOL', 
                          amount, sender, 'direct_donation', int(time.time())))
                    conn.commit()
                    processed_count += 1
                except Exception as e:
                    app.logger.error(f"SOL donation processing error: {e}")
    
    return {"processed": processed_count}, 200
```

---

## Real-time Updates

### Task 8: WebSocket broadcasting
**Priority**: Medium | **Effort**: 1 day | **Dependencies**: Task 6

**Acceptance Criteria**:
- [ ] WebSocket server for real-time updates
- [ ] Broadcasts community score changes
- [ ] Broadcasts prize pool updates
- [ ] Handles connection management
- [ ] Graceful fallback to polling

### Task 9: Vote processing pipeline
**Priority**: Medium | **Effort**: 0.5 day | **Dependencies**: Task 7, Task 8

**Acceptance Criteria**:
- [ ] Webhook → Database → Score calculation → WS broadcast
- [ ] End-to-end latency < 15 seconds
- [ ] Error handling and retry logic
- [ ] Monitoring and alerting

---

## Environment Configuration

### Task 10: Environment variable setup
**Priority**: Medium | **Effort**: 0.5 day | **Dependencies**: None

**Acceptance Criteria**:
- [ ] All constants configurable via .env
- [ ] Documentation for each variable
- [ ] Validation on startup
- [ ] Default values for development

```bash
# Vote weight formula
VOTE_WEIGHT_MULTIPLIER=3
VOTE_WEIGHT_CAP=10

# Minimum vote threshold  
MIN_VOTE_AMOUNT=1

# Prize pool configuration (updated for multi-token)
PRIZE_POOL_TARGET_USD=1000
MAX_VOTE_TOKENS=100

# Token configuration
AI16Z_TOKEN_MINT=HeLp6NuQkmYB4pYWo2zYs22mESHXPQYzXbB8n4V98jwC
SOL_TOKEN_MINT=So11111111111111111111111111111111111111112

# External APIs
BIRDEYE_API_KEY=optional_for_rate_limits
HELIUS_WEBHOOK_SECRET=your_secret_here

# Voting window
VOTING_WINDOW_DURATION=48h

# Data refresh rate
UI_REFRESH_INTERVAL=15s
```

---

## Testing

### Task 11: Unit tests
**Priority**: Medium | **Effort**: 1 day | **Dependencies**: Tasks 1-7

**Acceptance Criteria**:
- [ ] Database query tests
- [ ] Vote weight calculation tests
- [ ] API endpoint tests
- [ ] Webhook processing tests
- [ ] 80%+ code coverage

### Task 12: Integration tests
**Priority**: Medium | **Effort**: 1 day | **Dependencies**: Task 11

**Acceptance Criteria**:
- [ ] End-to-end webhook → database → API flow
- [ ] Test with sample transaction data
- [ ] Performance tests with load
- [ ] Error scenario tests

---

## Deployment

### Task 13: Database migration
**Priority**: High | **Effort**: 0.5 day | **Dependencies**: Task 1

**Acceptance Criteria**:
- [ ] Migration script runs safely on production
- [ ] Rollback plan documented
- [ ] Data backup created
- [ ] Zero downtime deployment

### Task 14: Webhook endpoint deployment
**Priority**: High | **Effort**: 0.5 day | **Dependencies**: Task 6

**Acceptance Criteria**:
- [ ] Webhook endpoint deployed and accessible
- [ ] Helius webhook configured
- [ ] SSL certificate valid
- [ ] Monitoring and logging active