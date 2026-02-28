# Voting System Context & UX/UI Decisions

## 🎯 Project Overview

**Clank Tank** is an AI-powered game show platform where entrepreneurs pitch to simulated AI judges. We have two main deployments:

1. **Main Platform**: Full production pipeline for creating episodes from pitch submissions
2. **Hackathon Edition**: Specialized judging system for hackathon competitions with AI judges and community voting

**Current Focus**: The hackathon edition needs a community voting system to complement AI judge scores.

## 📊 Current State Analysis

### What's Already Built (Backend - FULLY FUNCTIONAL)

**Database Tables:**
```sql
-- Vote tracking
CREATE TABLE sol_votes (
    tx_sig TEXT PRIMARY KEY,
    submission_id TEXT NOT NULL, 
    sender TEXT NOT NULL,
    amount REAL NOT NULL,
    timestamp INTEGER NOT NULL
);

-- Prize pool contributions  
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
```

**Live API Endpoints:**
- `/api/community-scores` → Returns voting scores per submission
- `/api/prize-pool` → Returns $480 USD current total with token breakdown
- `/webhook/helius` → Processes real Solana transactions for voting

**Current Live Data:**
- **Prize Pool**: $480 USD (2.5 SOL + 100 ai16z tokens)
- **Votes**: 3 active votes in database
- **Community Score**: 20.19 points for test-submission-1

**Voting Logic (Working):**
- Users send ai16z tokens with submission ID as memo
- Vote weight = `min(log10(amount + 1) × 3, 10)`
- Tokens over 100 ai16z go to prize pool as "overflow"
- Real-time USD conversion via Birdeye API

### Frontend State (Partially Built)

**What Exists:**
- `/home/jin/repo/clanktank/hackathon/frontend/src/pages/Leaderboard.tsx` → Modern leaderboard with medal rankings
- `/home/jin/repo/clanktank/hackathon/frontend/src/components/PrizePoolBanner.tsx` → Prize pool display (just connected to real API)
- `/home/jin/repo/clanktank/hackathon/frontend/src/pages/VotingPrototypes.tsx` → 8 different voting UI prototypes

**What's Connected:**
- ✅ Prize pool banner shows real $480 USD
- ✅ Community scores API integration ready
- ✅ Leaderboard displays AI scores with medal colors (gold/silver/bronze)

**What's Missing:**
- Voting interface on submission detail pages
- Community score display in leaderboard
- Mobile voting workflow (Phantom deep-links)

## 🎨 UX/UI Design Considerations

### Core Design Philosophy

**"Rotten Tomatoes Style"** - Established in planning docs:
- **AI Score**: Primary ranking mechanism (like critic score)
- **Community Score**: Secondary social proof (like audience score)
- **Prize Pool**: Gamification element showing community investment

### Current Leaderboard Design

**File**: `/home/jin/repo/clanktank/hackathon/frontend/src/pages/Leaderboard.tsx`

**Visual Hierarchy:**
```
🏆 Prize Pool Banner: $480 USD [Progress Bar] [Copy Address]
    ↓
📋 Leaderboard Header: "AI-judged rankings from our expert panel"
    ↓
🥇 Rank Cards: [Medal Badge] [Project] [AI Score: 8.7] [Community: —]
```

**Current Medal System:**
- 🥇 Gold (#f5c000) - 1st place
- 🥈 Silver (#c0c0c0) - 2nd place  
- 🥉 Bronze (#cd7f32) - 3rd place

### Existing Voting Prototypes

**File**: `/home/jin/repo/clanktank/hackathon/frontend/src/pages/VotingPrototypes.tsx`

**8 Different Concepts Built:**
1. **PowerBar**: Slider with visual power levels
2. **Action Buttons**: Simple thumbs up/down with token amounts
3. **Credits**: Allocate limited credits across projects
4. **Reactions**: Emoji-based voting (🔥🚀💎)
5. **Fuel Tank**: Gaming metaphor for vote power
6. **Bidding**: Auction-style competitive voting
7. **Blocks**: Blockchain-themed stacking interface
8. **Social Proof**: Community sentiment display

## 🤔 The UX/UI Problem

### Current User Journey Gap

**What works:**
1. User visits leaderboard → sees AI rankings + prize pool
2. Backend processes ai16z transactions → updates scores

**What's broken:**
3. 🚫 **No clear voting interface** → Users don't know how to vote
4. 🚫 **No mobile workflow** → Difficult on phones (primary crypto usage)
5. 🚫 **Community scores hidden** → Social proof not visible
6. 🚫 **Voting feels disconnected** → Prize pool and voting not linked visually

### Technical Constraints

**Solana Voting Requirements:**
- Must send ai16z tokens to specific wallet
- Must include submission ID in transaction memo
- Mobile users need Phantom wallet deep-links
- Desktop users need copy-paste instructions

**Social Dynamics:**
- Hackathon audience (20-50 projects, 100-200 voters)
- 1-week competition timeline
- Discord community integration exists
- Need balance between voting and prize pool contribution

## 💡 Potential Solutions

### Option 1: Minimal Integration (Quick Win)
**Add community scores to existing leaderboard**
- Show community score next to AI score in rank cards
- Add simple "Vote" button that opens voting modal
- Mobile: Generate Phantom deep-link
- Desktop: Show copy-paste instructions

**Pros:** Fast implementation, minimal design changes
**Cons:** Voting feels separate from main experience

### Option 2: Dedicated Voting Page (Medium Effort)
**Create `/submission/:id` pages with integrated voting**
- Full submission details + voting interface
- Real-time vote count updates
- Progress toward personal vote weight cap
- Visual connection between voting and prize pool

**Pros:** Focused voting experience, better conversion
**Cons:** More development time, navigation complexity

### Option 3: Gamified Leaderboard (High Impact)
**Transform leaderboard into interactive voting dashboard**
- Inline voting on each rank card
- Real-time score updates with animations
- Vote weight visualization
- Prize pool grows visibly with each vote

**Pros:** Engaging, high conversion, social proof
**Cons:** Complex interactions, performance considerations

### Option 4: Hybrid Approach (Recommended?)
**Enhance existing leaderboard + dedicated voting flows**
- Community scores visible on leaderboard (social proof)
- "Vote" buttons lead to focused voting modals/pages
- Prize pool banner shows recent contributions feed
- Mobile-optimized Phantom integration

## 🎯 Key UX Questions Needing Decisions

### 1. Where should voting happen?
- **A)** Directly on leaderboard (inline)
- **B)** Dedicated submission detail pages
- **C)** Modal overlays from leaderboard
- **D)** Separate voting dashboard

### 2. How to handle mobile vs desktop?
- **A)** Phantom deep-links for all users
- **B)** Desktop copy-paste + mobile deep-links
- **C)** Web3 wallet connection for desktop
- **D)** QR codes for mobile scanning

### 3. Community score visibility?
- **A)** Always visible next to AI scores
- **B)** Toggle between AI and community views
- **C)** Combined weighted score display
- **D)** Separate community leaderboard

### 4. Prize pool integration?
- **A)** Static banner showing current total
- **B)** Live feed of recent contributions
- **C)** Visual connection between votes and pool growth
- **D)** Gamified progress toward goals

### 5. Real-time updates?
- **A)** Manual refresh button
- **B)** Auto-refresh every 30 seconds
- **C)** WebSocket real-time updates
- **D)** Optimistic UI updates

## 📁 Relevant Files for Implementation

### Backend (Already Complete)
```
/hackathon/backend/app.py (lines 1533-1665)
├── /api/community-scores
├── /api/prize-pool  
└── /webhook/helius
```

### Frontend (Needs Work)
```
/hackathon/frontend/src/
├── pages/Leaderboard.tsx (main leaderboard)
├── pages/VotingPrototypes.tsx (8 voting concepts)
├── components/PrizePoolBanner.tsx (prize pool display)
├── components/LeaderboardCard.tsx (rank cards)
└── lib/api.ts (API client with voting methods)
```

### Planning Documents
```
/leaderboard-plans/
├── frontend-tasks.md (detailed implementation guide)
├── backend-tasks.md (voting system architecture)
├── PROGRESS.md (current implementation status)
└── AI-CODER-INSTRUCTIONS.md (step-by-step guide)
```

## 🚀 Next Steps

**For UX/UI Decision Making:**
1. **Review voting prototypes** at `/voting-prototypes` page
2. **Consider user flow** from discovery → voting → social proof
3. **Balance simplicity vs engagement** for 1-week hackathon timeline
4. **Mobile-first design** since crypto users primarily on mobile
5. **Social proof prioritization** to drive voting momentum

The technical foundation is solid. The question is how to present this powerful voting system in a way that feels natural, engaging, and drives community participation.

---

*This context document provides the full picture for UX/UI decision making. The backend is production-ready with real money flowing through it ($480 USD prize pool). The frontend needs thoughtful voting interface design to complete the experience.*