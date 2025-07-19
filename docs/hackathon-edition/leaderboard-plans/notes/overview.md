# Leaderboard Enhancement Plans

## Current State Analysis

### Leaderboard.tsx Current Features
- **AI-only scoring**: Shows final scores from AI judges (aimarc, aishaw, spartan, peepo)
- **Visual hierarchy**: Medal icons for top 3, gradient backgrounds, status indicators
- **Discord integration**: Avatar display, handles
- **Status tracking**: Color-coded status (scored, completed, published)
- **Basic sharing**: Native share API with Twitter fallback
- **Project linking**: Deep links to submission detail pages

### Discord Bot Current Features
- **Community voting**: React-based voting system (🔥 hype, 💡 innovation, 💻 technical, 📈 market, 😍 UX)
- **Automatic posting**: Posts scored submissions to Discord channel
- **Vote tracking**: Records votes in `community_feedback` table
- **Status management**: Updates submission status to `community-voting`

---

## 🎯 Quick Wins for Current Leaderboard

### 1. **Rotten Tomatoes-Style Dual Score Display**
- **Current**: Single AI score display
- **Enhancement**: Show AI score (canonical ranking) + Community score (info only)
- **Implementation**: 
  - **AI Score**: Determines leaderboard ranking (Critics Score)
  - **Community Score**: Token voting display (Audience Score)
  - **No weighted combination**: Keep rankings pure AI-based
  - Optional filter toggle to re-rank by Community score

### 2. **Real-time Updates**
- **Current**: Static data on page load
- **Enhancement**: Live updating scores during voting period
- **Implementation**: WebSocket connection or polling for live score updates

### 3. **Score Breakdown Tooltips**
- **Current**: Only shows final score
- **Enhancement**: Hover tooltips showing detailed scoring breakdown
- **Implementation**: Display individual criteria scores (Innovation, Technical, Market, UX)

### 4. **Prize Pool Progress Bar**
- **Current**: No prize pool visibility
- **Enhancement**: Progress bar showing journey toward prize pool goal
- **Implementation**: 
  - Set target amount (e.g., 100 SOL)
  - Animated progress bar with current/target
  - "X% funded" indicator
  - Recent contributions ticker

### 5. **Discord Hype Bar**
- **Current**: Discord reactions hidden from leaderboard
- **Enhancement**: Show Discord engagement as "Social Hype" metric
- **Implementation**: 
  - Separate visual indicator for Discord reactions
  - Not affecting leaderboard ranking
  - Shows community engagement without token requirement

---

## 💰 Solana Integration Roadmap

### Phase 1: Prize Pool Visualization

#### **Easy-to-Copy Solana Address**
```tsx
const PRIZE_POOL_ADDRESS = "YOUR_PRIZE_POOL_WALLET_ADDRESS";

// Component with copy functionality
<div className="prize-pool-widget">
  <h3>Prize Pool</h3>
  <div className="address-display">
    <code>{PRIZE_POOL_ADDRESS}</code>
    <button onClick={() => navigator.clipboard.writeText(PRIZE_POOL_ADDRESS)}>
      Copy
    </button>
  </div>
</div>
```

#### **Real-time Balance Tracker**
- **Data source**: Solana RPC calls to get wallet balance
- **Visualization**: 
  - Animated counter showing current prize pool
  - Progress bar or thermometer visual
  - Historical growth chart
  - Contribution leaderboard

#### **Implementation Stack**
```javascript
// Real-time balance fetching
const fetchPrizePool = async () => {
  const connection = new Connection(clusterApiUrl('mainnet-beta'));
  const balance = await connection.getBalance(new PublicKey(PRIZE_POOL_ADDRESS));
  return balance / LAMPORTS_PER_SOL;
};

// Helius webhook integration for real-time updates
const setupWebhook = () => {
  // Listen for transactions to prize pool address
  // Update UI in real-time when donations received
};
```

### Phase 2: Token-Based Voting System

#### **ai16z Token Voting Mechanism**
- **Token**: ai16z (HeLp6NuQkmYB4pYWo2zYs22mESHXPQYzXbB8n4V98jwC)
- **Voting method**: Send tokens with memo containing submission ID
- **Minimum vote**: 1 ai16z token per vote
- **Logarithmic weighting**: Prevents whale domination
- **Overflow to prize pool**: Excess tokens beyond voting cap

#### **Vote Weight Formula**
```javascript
const calculateVoteWeight = (tokensSent) => {
  const minVote = 1; // 1 ai16z minimum
  if (tokensSent < minVote) return 0;
  
  // Logarithmic scaling with cap
  const maxWeight = 10; // Maximum vote weight
  const weight = Math.min(Math.log10(tokensSent + 1) * 3, maxWeight);
  
  return weight;
};
```

#### **Voting UX Considerations**
- **Slider/Input**: UI shows vote weight for different amounts
- **Cap notification**: "Sending more than X tokens goes to prize pool"
- **Confirmation**: Clear feedback on vote weight vs donation split

#### **Helius Integration**
```javascript
// Monitor ai16z token transfers with memos
const monitorVotes = async () => {
  const webhook = await helius.createWebhook({
    webhookURL: "https://your-api.com/webhook/votes",
    transactionTypes: ["TOKEN_TRANSFER"],
    tokenTransfers: [{
      mint: "HeLp6NuQkmYB4pYWo2zYs22mESHXPQYzXbB8n4V98jwC",
      // Monitor transfers with memos
    }]
  });
};
```

### Phase 3: Mobile Voting Experience

#### **Solana URI Deep Links**
```javascript
// Generate voting links for mobile
const generateVoteLink = (submissionId, amount = 1) => {
  const params = new URLSearchParams({
    amount: amount.toString(),
    'spl-token': 'HeLp6NuQkmYB4pYWo2zYs22mESHXPQYzXbB8n4V98jwC',
    label: 'ai16z transfer',
    memo: submissionId
  });
  
  return `solana:${VOTING_WALLET_ADDRESS}?${params}`;
};

// Mobile-optimized voting buttons
<div className="mobile-voting">
  {isMobile && (
    <a href={generateVoteLink(submission.id)} className="vote-button">
      Send vote to {submission.project_name}
    </a>
  )}
</div>
```

#### **User Experience Flow**
1. **Desktop**: Copy address + manual transaction
2. **Mobile**: Tap link → Phantom opens → Pre-filled transaction → Send
3. **Fallback**: QR code for wallet scanning

---

## 🤖 Discord Bot Enhanced Voting

### Current Discord Integration
- **Strengths**: 
  - Simple reaction-based voting
  - Automatic posting of scored submissions
  - Vote tracking in database
  - Multiple voting categories

### Enhancement Ideas

#### **Token-Gated Channels**
```python
# Add token verification to Discord bot
async def verify_ai16z_holdings(discord_user_id, wallet_address):
    # Check if user holds minimum ai16z tokens
    # Grant access to token-gated voting channels
    pass

# Weighted Discord votes based on token holdings
async def calculate_discord_vote_weight(discord_user_id):
    wallet = await get_verified_wallet(discord_user_id)
    if wallet:
        holdings = await get_ai16z_balance(wallet)
        return calculate_vote_multiplier(holdings)
    return 1.0  # Base weight for non-verified users
```

#### **Multi-Channel Strategy**
- **Public channel**: General community voting (current system)
- **Token-gated channel**: Weighted voting for ai16z holders
- **Contributor channel**: Special voting for top contributors

#### **Enhanced Voting Commands**
```python
# New Discord commands
@bot.command(name='vote')
async def vote_command(ctx, submission_id: str, category: str, amount: int = 1):
    """Enhanced voting with amounts and categories"""
    pass

@bot.command(name='leaderboard')
async def show_leaderboard(ctx):
    """Display current leaderboard in Discord"""
    pass

@bot.command(name='verify')
async def verify_wallet(ctx, wallet_address: str):
    """Verify wallet ownership for weighted voting"""
    pass
```

---

## 📊 Advanced Scoring & Analytics

### Dual Scoring System

#### **AI Judge Scores** (Current)
- **Innovation & Creativity**: 0-10
- **Technical Execution**: 0-10  
- **Market Potential**: 0-10
- **User Experience**: 0-10
- **Weighted by judge expertise**

#### **Community Scores** (New)
- **Solana token voting**: Weighted by holdings and contribution
- **Discord reaction voting**: Weighted by verified status
- **Combined community score**: Normalized to 0-10 scale

#### **Dual Score Display (No Combination)**
```javascript
const LeaderboardEntry = ({ submission }) => {
  return (
    <div className="submission-row">
      <div className="ranking-score">
        <span className="label">AI Score</span>
        <span className="primary-score">{submission.ai_score}</span>
      </div>
      <div className="community-score">
        <span className="label">Community</span>
        <span className="secondary-score">{submission.community_score}</span>
      </div>
      <div className="hype-bar">
        <span className="label">Social Hype</span>
        <span className="hype-level">{submission.discord_reactions}</span>
      </div>
    </div>
  );
};
```

### Analytics Dashboard

#### **Voting Analytics**
- **Total votes**: Across all platforms
- **Vote distribution**: By category and platform
- **Engagement metrics**: Time spent voting, return visitors
- **Token flow**: Prize pool contributions and voting spend

#### **Community Insights**
- **Top contributors**: By tokens sent and voting activity
- **Voting patterns**: Which projects get what type of votes
- **Platform preference**: Discord vs Solana voting breakdown

---

## 🎨 UI/UX Enhancements

### Enhanced Leaderboard Design

#### **Score Visualization**
```tsx
// Dual score display component
<div className="score-display">
  <div className="ai-score">
    <span className="label">AI Judges</span>
    <span className="score">{aiScore.toFixed(1)}</span>
  </div>
  <div className="community-score">
    <span className="label">Community</span>
    <span className="score">{communityScore.toFixed(1)}</span>
  </div>
  <div className="final-score">
    <span className="label">Final</span>
    <span className="score">{finalScore.toFixed(1)}</span>
  </div>
</div>
```

#### **Interactive Elements**
- **Hover effects**: Show detailed breakdowns
- **Filtering**: By category, status, score range
- **Sorting**: Multiple sort options
- **Search**: Find specific projects

#### **Prize Pool Widget**
```tsx
const PrizePoolWidget = () => {
  const [balance, setBalance] = useState(0);
  const [contributions, setContributions] = useState([]);
  
  return (
    <div className="prize-pool-widget">
      <h3>Prize Pool</h3>
      <div className="balance-display">
        <span className="amount">◎ {balance.toFixed(2)}</span>
        <span className="usd">≈ ${(balance * solPrice).toFixed(2)}</span>
      </div>
      <div className="contributions">
        {contributions.map(c => (
          <div key={c.id} className="contribution">
            {c.amount} SOL from {c.contributor}
          </div>
        ))}
      </div>
    </div>
  );
};
```

### Mobile Optimization

#### **Responsive Voting**
- **Desktop**: Full interface with all options
- **Mobile**: Streamlined voting via Solana URIs
- **Progressive enhancement**: Works without JavaScript

#### **Touch-Friendly Interface**
- **Larger touch targets** for mobile voting
- **Swipe gestures** for navigation
- **Haptic feedback** for successful votes

---

## 🔧 Actionable Implementation Roadmap

### Phase 1: UI Polish & Structure (Week 1)
**Definition of Done**: Leaderboard shows dual-score display, dark indigo theme, mobile-responsive
- [ ] **Rotten Tomatoes UI**: AI score (primary) + Community score (secondary) columns
- [ ] **Prize pool progress bar**: Current balance / target with percentage
- [ ] **Discord hype bar**: Social engagement indicator (doesn't affect ranking)
- [ ] **Dark indigo theme**: Apply consistent color scheme, Roboto font
- [ ] **Mobile-first responsive**: Touch-friendly interface, proper breakpoints

### Phase 2: On-Chain Data Ingestion (Week 2)
**Definition of Done**: System tracks incoming ai16z transactions and updates community scores
- [ ] **Transaction monitoring**: Poll/webhook for ai16z transfers to prize wallet
- [ ] **Memo validation**: Extract submission_id from transaction memos
- [ ] **Vote weight calculation**: Logarithmic formula with 1 ai16z minimum
- [ ] **Database schema**: `sol_votes` table (tx_sig, submission_id, sender, amount, timestamp)
- [ ] **API endpoint**: `/api/community-scores` returns aggregated scores per submission

### Phase 3: Mobile Voting Experience (Week 3)
**Definition of Done**: Mobile users can vote via Phantom deep-links, desktop users via copy-paste
- [ ] **Mobile deep-links**: Generate `solana:` URIs with pre-filled memo
- [ ] **Desktop fallback**: Copy-to-clipboard with instructions
- [ ] **Vote confirmation**: Transaction success/failure feedback
- [ ] **Voting UI**: Amount slider showing vote weight preview
- [ ] **Mobile detection**: Serve appropriate voting interface

### Phase 4: Contributors & Analytics (Week 4)
**Definition of Done**: Top contributors tab, basic analytics for engagement
- [ ] **Contributors leaderboard**: Top donors by amount and frequency
- [ ] **Prize pool analytics**: Historical growth, recent contributions
- [ ] **Vote analytics**: Submission vote counts, engagement metrics
- [ ] **Simple filtering**: Toggle between AI-ranked and Community-ranked views

---

## 🤔 Voting UX Deep Dive & Brainstorming

### Core Voting Flow Analysis

#### **Current State**: 
- Discord reactions (working, but limited reach)
- No token voting mechanism
- No mobile-optimized voting experience

#### **Desired State**:
- Token holders can vote using ai16z tokens
- Mobile-first voting experience
- Desktop fallback that works
- Clear incentive for prize pool contributions

### Two Parallel Voting Approaches

#### **Path A: Wallet-First Multi-Project Voting**
```
User Flow:
1. Connect wallet once → Unlock personalized features
2. Browse leaderboard with checkboxes on each project
3. Select multiple projects → Add to "voting cart"
4. Adjust amounts per project with sliders
5. Single checkout → One transaction with multiple memos
6. Real-time updates across all voted projects
```

**Advantages:**
- **Lower fees**: Single transaction for multiple votes
- **Better UX**: Shopping cart metaphor, familiar flow
- **Wallet analytics**: See holdings, voting history, personalized recommendations
- **Batch efficiency**: Vote on 5-10 projects at once
- **Conversion optimization**: Committed users vote more

**Considerations:**
- **Wallet connection friction**: Some users hesitate to connect
- **Mobile complexity**: Wallet adapters can be finicky on mobile
- **Technical complexity**: Multi-memo transaction construction

#### **Path B: Anonymous Transaction-Based Voting**
```
User Flow:
1. Browse leaderboard → Click "Vote" on any project
2. Select amount (slider shows vote weight split)
3. Mobile: Deep-link to Phantom | Desktop: Copy address + memo
4. Send transaction → System detects → Updates score
5. Repeat for each project individually
```

**Advantages:**
- **Privacy-first**: No wallet connection required
- **Mobile-optimized**: Deep-links work reliably on mobile
- **Paranoid-friendly**: Appeals to privacy-conscious users
- **Simple implementation**: Standard transaction monitoring
- **Lower barrier**: No signup/connection friction

**Considerations:**
- **Higher fees**: Multiple transactions for multiple votes
- **Manual process**: Users must vote project by project
- **Limited analytics**: Can't track voting patterns easily
- **Memo dependency**: Relies on correct memo formatting

#### **Hybrid Implementation Strategy**
```
Primary UI: 
- "Connect Wallet to Vote" (prominent)
- "Vote Anonymously" (secondary button)

Connected Experience:
- Multi-project cart voting
- Voting history and analytics
- Personalized recommendations

Anonymous Experience:
- Single-project voting
- Deep-link or copy-paste options
- Still contributes to community scores
```

### Mobile Deep-Link Mechanics

#### **Phantom URI Structure**:
```
solana:PRIZE_WALLET_ADDRESS?amount=X&spl-token=ai16z_MINT&memo=SUBMISSION_ID&label=ClankTank%20Vote
```

#### **Implementation Considerations**:
- **Memo validation**: Must match submission ID exactly
- **Amount parsing**: Handle decimals correctly
- **Return handling**: Detect when user returns from Phantom
- **Error cases**: Invalid memo, insufficient funds, etc.

### Prize Pool Integration Strategy

#### **Dual-Purpose Voting**:
- **Vote portion**: Up to logarithmic cap (e.g., 10 ai16z max effective)
- **Donation portion**: Everything above cap goes to prize pool
- **Clear communication**: "5 ai16z for max vote weight + 15 ai16z to prize pool"

#### **Progress Gamification**:
- **Prize pool thermometer**: Visual progress toward goal
- **Contributor recognition**: Top donors leaderboard
- **Milestone celebrations**: Special recognition at funding levels

### User Mental Models

#### **The "Speculation" Angle**:
- "I think this project will win" → Vote with ai16z
- "I want to support the prize pool" → Donate extra
- "I want to be recognized as a contributor" → Larger amounts

#### **The "Participation" Angle**:
- "I have ai16z tokens, might as well use them"
- "I want to influence the community score"
- "I want to be part of the ecosystem"

### Edge Cases & Error Handling

#### **Transaction Failures**:
- **Insufficient funds**: Clear error message with suggested alternatives
- **Wrong memo**: Auto-refund or manual contact flow
- **Network issues**: Retry mechanism and status updates

#### **Duplicate Voting**:
- **Same wallet multiple votes**: Allow but cap total weight
- **Sybil resistance**: Consider wallet history/activity (future)

### Analytics & Feedback Loops

#### **Voting Analytics**:
- **Conversion rates**: Views → Votes → Donations
- **Drop-off points**: Where users abandon the flow
- **Platform preference**: Mobile vs desktop usage
- **Amount distribution**: Voting vs donation splits

#### **User Feedback**:
- **Success confirmations**: "Your vote is counted!"
- **Impact visibility**: "Your vote contributed X weight to Project Y"
- **Leaderboard updates**: Real-time score changes

### Vote-Weight Slider & Clear Messaging

#### **Mental Model Goal**
> "Move the slider → see exactly **how many votes** you'll cast and **how much** goes to the prize pool."

#### **UI Design Specification**
```
┌───────────────────────────────────────────────┐
│  🗳️  Vote for 〈Project Name〉                 │
│                                               │
│  Amount of ai16z to send                      │
│  ╭──────────┬───────┬───────┬──────────╮      │
│  1          10      100     1,000       │ slider
│  ╰──────────●───────────────╯           │
│                                               │
│  You'll cast:      3 votes (cap reached)      │
│  Goes to pool:     47 ai16z                   │
│                                               │
│  [ Send Vote ]                                │
│  <small>* votes cap at 100 ai16z (3 votes).   │
│  • Extra tokens fund the prize pool           │
└───────────────────────────────────────────────┘
```

#### **Interactive Feedback**
| User Action | Instant Feedback |
|-------------|------------------|
| Drag ≤ 1 ai16z | "You'll cast: **1 vote** – no donation." |
| Drag 10 ai16z | "You'll cast: **2 votes** – 6 ai16z to pool" |
| Drag 100+ ai16z | "Max votes reached (3) – everything else becomes donation." |

#### **Copy Guidelines**
- **Primary button**: "Send Vote" (mobile) / "Copy Tx Details" (desktop)
- **Explanatory text**: "Votes use log scale to keep things fair"
- **Error state**: "Amount too low (<1 ai16z). Try Discord reactions!"

---

## 💬 "Superchat SOL" Concept

### **Core Mechanism**
Pay SOL during live deliberation → short message piped into AI judge context and read aloud via TTS

#### **How It Works**
1. **Separate SOL address** (dedicated superchat wallet)
2. **Memo structure**: `SUBMISSION_ID | message up to 80 chars`
3. **Pricing tiers**:
   - 0.1 SOL = Basic message (30 chars)
   - 0.5 SOL = Highlighted + TTS emphasis
   - 1.0 SOL = Pinned message + emoji effects

#### **Guard Rails**
| Risk | Mitigation |
|------|------------|
| Spam/inappropriate content | Profanity filter + optional human approval |
| Judge manipulation | LLM instruction: "Consider input but maintain independence" |
| Dust transactions | 0.05 SOL minimum to appear |

#### **Engagement Features**
- **Leaderboard sidebar**: "Most influential voices" (top superchat contributors)
- **Live ticker**: "🚀 0.5 SOL from 7gx... 'Ship it!'"
- **Prize pool destination**: Superchat SOL goes to main prize pool

### Alternative/Supplemental Voting Ideas

| Concept | UX Flow | Pros | Cons |
|---------|---------|------|------|
| **NFT Badge Mint** | Vote > X ai16z → auto-mint dynamic badge | Collectible clout, tradeable | Extra tx fees, image hosting |
| **Batch Vote Cart** | Add projects to cart → single transaction | Lower fees, broad participation | Complex memo packing |
| **Off-chain Signing** | Sign message (no tx) → vote stored | Zero fees, instant | Less transparent, sybil risk |
| **Airdrop Vote Credits** | Burn voting NFT → cast vote | Inclusive for non-holders | Distribution complexity |

### Open Questions for Further Discussion

1. **Vote Privacy**: Should votes be anonymous or public?
2. **Voting Windows**: Time-limited voting periods or always open?
3. **Multiple Projects**: Can users vote for multiple projects?
4. **Vote Changes**: Can users change their vote or is it final?
5. **Minimum Thresholds**: Should projects need minimum votes to be eligible?
6. **Superchat Integration**: Should superchats influence AI scores or just engagement?

---

## 🚀 Future Expansion Ideas

### **NFT Integration**
- **Voting NFTs**: Special edition NFTs for top voters
- **Project NFTs**: Mint NFTs for winning projects
- **Collectible badges**: Achievement system

### **Cross-Platform Voting**
- **Twitter integration**: Vote via Twitter mentions
- **Telegram bot**: Voting in Telegram groups
- **Email voting**: For broader reach

### **Advanced Analytics**
- **ML-powered insights**: Predict winning projects
- **Sentiment analysis**: Social media sentiment tracking
- **Market correlation**: Compare votes to market performance

### **Gamification**
- **Voting streaks**: Bonus multipliers for consistent voters
- **Achievement system**: Badges for different voting milestones
- **Leaderboard for voters**: Top contributors recognition

---

## 📋 Technical Considerations

### **Security**
- **Wallet verification**: Prevent multi-account abuse
- **Rate limiting**: Prevent spam voting
- **Memo validation**: Ensure proper submission ID format
- **Token verification**: Confirm ai16z token authenticity

### **Performance**
- **Real-time updates**: WebSocket vs polling optimization
- **Database optimization**: Efficient queries for large datasets
- **Caching strategy**: Redis for frequently accessed data
- **CDN integration**: Fast global content delivery

### **Scalability**
- **Horizontal scaling**: Multiple server instances
- **Database sharding**: Handle large voting datasets
- **Queue systems**: Process votes asynchronously
- **Monitoring**: Comprehensive logging and alerting

---

## 🎯 Success Metrics

### **Engagement Metrics**
- **Unique voters**: Total number of unique participants
- **Vote volume**: Total votes cast across all platforms
- **Time on site**: Engagement duration
- **Return visitors**: Repeat voting behavior

### **Financial Metrics**
- **Prize pool growth**: Total contributions
- **Token circulation**: ai16z tokens used for voting
- **Average contribution**: Per-user contribution amounts
- **Conversion rate**: Viewers to voters

### **Technical Metrics**
- **System uptime**: 99.9% availability target
- **Response time**: Sub-second API responses
- **Error rate**: <0.1% error rate
- **Mobile adoption**: Mobile vs desktop usage

---

*This document serves as a comprehensive roadmap for enhancing the Clank Tank hackathon leaderboard with innovative Solana-based voting mechanisms and improved user experience.*