# Implementation Guide - Voting & Prize Pool (v1)

This document provides the final locked-in specification for implementing the token voting system.

## Voting & Prize-Pool Logic (v1)

| Item                         | Decision                                                                                                        |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------- |
| **Canonical ranking**        | AI Score only                                                                                                   |
| **Displayed scores**         | AI Score (primary), Community Score (secondary)                                                                 |
| **Community votes**          | On-chain ai16z transfers with `memo = submission_id`                                                            |
| **Vote weight**              | `weight = min(log10(totalTokensSent + 1) × 3, 10)` (evaluated *per wallet per submission*)                      |
| **Min vote**                 | 1 ai16z token                                                                                                   |
| **Overflow**                 | Tokens beyond vote-cap still transfer; count 0 additional weight; enlarge prize pool                            |
| **Replay protection**        | `tx_sig` is UNIQUE key in `sol_votes` table. Duplicate sigs rejected server-side.                               |
| **Sybil cap**                | Log formula inherently dampens whales; additional per-wallet cap enforced by weight rule                        |
| **Contribution feed**        | Show latest 5 deposits (address-truncated, amount, time) under progress bar → "View All" modal for full history |
| **Feedback animation**       | Subtle glow on Community score cell **and** progress bar when a new tx for that submission is detected          |
| **Data latency goal**        | ≤ 15 s from confirmed block to UI update (Helius webhook → backend → WS broadcast)                              |
| **Voting window**            | Opens when you (admin) trigger community voting; closes at hard stop datetime (config in `.env`)                |
| **Duplicate-memo allowance** | Different wallets can reuse the same memo; each counts separately                                               |

## API / DB Tasks

### 1. `sol_votes` table

```sql
CREATE TABLE sol_votes (
    tx_sig TEXT PRIMARY KEY,
    submission_id TEXT NOT NULL,
    sender TEXT NOT NULL,
    amount REAL NOT NULL,
    timestamp INTEGER NOT NULL
);

-- Indexes for performance
CREATE INDEX idx_sol_votes_submission ON sol_votes(submission_id);
CREATE INDEX idx_sol_votes_sender ON sol_votes(sender);
CREATE INDEX idx_sol_votes_timestamp ON sol_votes(timestamp);
```

### 2. Ingest service

* **Helius webhook** → verify mint & memo → `INSERT … ON CONFLICT IGNORE`
* **Aggregate view** per (wallet, submission) to compute `totalTokensSent`
* **Weight calculation**: Apply log formula per wallet per submission

### 3. `/api/community-scores`

Returns `{ submission_id, community_score, last_tx_time }` for front-end polling/WS.

**Example response:**
```json
{
  "community_scores": [
    {
      "submission_id": "project-alpha",
      "community_score": 7.2,
      "total_votes": 127.5,
      "unique_voters": 23,
      "last_tx_time": 1704067200
    }
  ]
}
```

## Front-End Tasks (Phase 1)

### Leaderboard Updates
* **Dual-score columns** added to `<Leaderboard />`
* **AI Score** (primary ranking column)
* **Community Score** (secondary display column)
* **Tie-breaker**: Higher community score wins AI ties

### Prize Pool Widget
* **Progress bar** toward static target amount
* **Live balance** display (SOL only)
* **Contribution feed**: Latest 5 deposits with "View All" modal
* **Animation**: Subtle glow when new contributions detected

### Voting Interface
* **Connected wallet flow (primary)**
  - *Add to cart* functionality
  - Amount slider showing vote weight
  - Single transaction with multiple memos
* **Anonymous flow (secondary)**
  - Deep-link generation for mobile
  - Copy address + memo for desktop
* **Post-vote feedback**: Animate Community cell + progress bar

## Technical Constants

All configurable via environment variables:

```bash
# Vote weight formula
VOTE_WEIGHT_MULTIPLIER=3
VOTE_WEIGHT_CAP=10

# Minimum vote threshold
MIN_VOTE_AMOUNT=1

# Prize pool target
PRIZE_POOL_TARGET=100

# Voting window
VOTING_WINDOW_DURATION=48h

# Data refresh rate
UI_REFRESH_INTERVAL=15s
```

## Vote Weight Calculation

```javascript
function calculateVoteWeight(totalTokensSent) {
  const minVote = process.env.MIN_VOTE_AMOUNT || 1;
  if (totalTokensSent < minVote) return 0;
  
  const multiplier = process.env.VOTE_WEIGHT_MULTIPLIER || 3;
  const cap = process.env.VOTE_WEIGHT_CAP || 10;
  
  return Math.min(Math.log10(totalTokensSent + 1) * multiplier, cap);
}
```

## Community Score Normalization

```javascript
function normalizeCommunityScore(rawWeight, maxWeight) {
  // Normalize to 0-10 scale to match AI scores
  return (rawWeight / maxWeight) * 10;
}
```

## Database Queries

### Get community scores for all submissions
```sql
SELECT 
  submission_id,
  SUM(
    CASE 
      WHEN per_wallet_total < 1 THEN 0
      ELSE LEAST(LOG10(per_wallet_total + 1) * 3, 10)
    END
  ) as total_weight,
  COUNT(DISTINCT sender) as unique_voters,
  MAX(timestamp) as last_tx_time
FROM (
  SELECT 
    submission_id,
    sender,
    SUM(amount) as per_wallet_total
  FROM sol_votes
  GROUP BY submission_id, sender
) wallet_totals
GROUP BY submission_id;
```

### Get recent contributions for feed
```sql
SELECT 
  sender,
  amount,
  timestamp,
  submission_id
FROM sol_votes
ORDER BY timestamp DESC
LIMIT 5;
```

## Success Metrics

### Phase 1 KPIs
- [ ] **Voting participation**: > 50 unique voters
- [ ] **Prize pool growth**: > 50 SOL contributed
- [ ] **UI responsiveness**: < 15s vote reflection
- [ ] **Error rate**: < 1% failed transactions

### Technical Milestones
- [ ] **Database schema**: `sol_votes` table created
- [ ] **Webhook integration**: Helius → backend working
- [ ] **API endpoints**: Community scores endpoint live
- [ ] **Frontend integration**: Dual scores displayed
- [ ] **Voting flows**: Both wallet-connect and anonymous working

---

**MVP Scope Locked**: This specification covers the complete v1 implementation. Additional features (sponsor perks, NFT rewards, etc.) can be layered on without breaking these core primitives.

**Next Steps**: 
1. Create database schema
2. Set up Helius webhook
3. Implement voting API endpoints
4. Build frontend components
5. Test end-to-end flow