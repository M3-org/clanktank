# Simple Implementation Tasks (MVP for Small Community Event)

## Reality Check
- **Event size**: 20-50 projects, maybe 100-200 community voters
- **Timeline**: Probably 1-2 weeks to build
- **Goal**: Proof of concept, not enterprise-scale system
- **Traffic**: Maybe 10-20 concurrent users max

---

## Backend (3-4 days total)

### Day 1: Basic Database & API
**Task**: Get data flowing
- [ ] Add `sol_votes` table to existing hackathon.db
- [ ] Simple `/api/community-scores` endpoint
- [ ] Basic vote weight calculation function
- [ ] Manual testing with SQLite browser

### Day 2: Webhook Processing  
**Task**: Receive and process votes
- [ ] Simple webhook endpoint that accepts Helius POST
- [ ] Parse memo, validate format, insert to database
- [ ] Handle duplicate transactions (just ignore them)
- [ ] Test with a few manual transactions

### Day 3: Multi-Token Prize Pool Endpoint
**Task**: Prize pool data with USD display
- [ ] `/api/prize-pool` endpoint with Birdeye price integration
- [ ] Multi-token support (SOL, ai16z, whitelisted tokens)
- [ ] USD conversion and token breakdown
- [ ] Recent contributions feed

---

## Frontend (3-4 days total)

### Day 1: Leaderboard Updates
**Task**: Add community scores to existing leaderboard
- [ ] Add "Community Score" column next to AI score
- [ ] Fetch from `/api/community-scores` endpoint
- [ ] Show "—" when no votes
- [ ] Keep AI ranking as primary

### Day 2: Basic Voting UI
**Task**: Let people vote
- [ ] Simple vote button on each project
- [ ] Amount slider (1-100 ai16z range is fine)
- [ ] Generate copy-paste instructions: "Send X ai16z to [address] with memo [id]"
- [ ] Mobile: Generate `solana:` deep link

### Day 3: Multi-Token Prize Pool Widget
**Task**: Show prize pool progress with USD display
- [ ] Progress bar widget with USD total vs USD target
- [ ] Token breakdown showing SOL, ai16z, and other contributions
- [ ] Real-time USD conversion display
- [ ] List of recent 5 contributions with token types
- [ ] Refresh button (no real-time needed for MVP)

---

## Integration (1 day)

### Day 1: Wire Everything Together
**Task**: Make it work end-to-end
- [ ] Test: vote → webhook → database → refresh page → see update
- [ ] Fix the inevitable bugs
- [ ] Deploy to staging
- [ ] Test with real Phantom wallet transactions

---

## What We're NOT Building (for MVP)
- ❌ Real-time WebSockets (just refresh button)
- ❌ Wallet connect (just copy-paste/deep-links)
- ❌ Multi-project cart (vote one at a time)
- ❌ Complex animations (maybe a simple CSS transition)
- ❌ Enterprise monitoring (just basic error logging)
- ❌ Load testing (it's 20 people)
- ❌ Advanced security (basic input validation is fine)

---

## Success Criteria (Realistic)
- [ ] **Community votes show up** in leaderboard
- [ ] **Prize pool updates** when people send SOL or ai16z tokens
- [ ] **USD conversion** displays correctly for multi-token prize pool
- [ ] **Mobile voting works** via Phantom deep-links
- [ ] **Desktop voting works** via copy-paste
- [ ] **No crashes** during the 2-day hackathon voting period

---

## If We Have Extra Time
- [ ] Auto-refresh every 30 seconds instead of manual refresh
- [ ] Basic wallet connect for easier voting
- [ ] Nicer CSS styling
- [ ] "View All" contributions modal

---

## Total Effort: ~1 week
- Backend: 3-4 days  
- Frontend: 3-4 days
- Integration: 1 day
- Buffer: 2-3 days for bugs and polish

This is much more realistic for a small community hackathon proof of concept!