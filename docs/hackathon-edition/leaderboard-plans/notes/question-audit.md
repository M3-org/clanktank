# Question Audit - Design Decisions

This document captures the answers to all key design questions that will drive implementation.

## A. Dual-Score Display & Ranking

### 1. Default sort
**Question**: When the page first loads, should it always be AI-ranked, or remember the user's last choice (AI vs Community) in localStorage?

**Decision**: **Default sort = AI-ranked**

**Rationale**: Keeps the canonical ranking (AI judges) as the primary experience while allowing users to toggle to Community view if interested.

---

### 2. Community score precision
**Question**: Do we show raw vote weight (e.g. 237.4) or normalize to a 0-10 scale like the AI score?

**Decision**: **Community score normalized to same 0-10 range**

**Rationale**: Creates visual consistency with AI scores and makes comparison easier for users.

---

### 3. Empty state
**Question**: Until a project gets the minimum X votes, do we hide the Community score cell, show "—", or show "0.0"?

**Decision**: **If no community votes ⇒ show "—"**

**Rationale**: Distinguishes between "no votes yet" and "scored zero" states, avoiding confusion.

---

### 4. Tie-breakers
**Question**: If two projects share the exact AI score, do we fall back to Community score, submission timestamp, or random shuffle?

**Decision**: **AI tie-break → higher community score wins**

**Rationale**: Uses community engagement as the secondary ranking factor, keeping it meaningful while preserving AI primacy.

---

## B. Prize Pool Widget & Progress Bar

### 5. Target amount semantics
**Question**: Is the goal static (set at hackathon start) or dynamic (ratchets up once the pool is > 90%)?

**Decision**: **Prize-pool target = static (set once)**

**Rationale**: Simpler to implement and understand; provides clear goal for participants.

---

### 6. Currency display
**Question**: SOL only, or should we always show an ≈USD value fetched from a price oracle?

**Decision**: **Display USD equivalent with token breakdown using Birdeye API**

**Rationale**: Since voting uses ai16z tokens and overflow goes to prize pool, we need multi-token support. USD display provides clarity across different tokens.

---

### 7. Contribution feed length
**Question**: How many recent contributions should we surface before collapsing into "View all"?

**Decision**: **Contribution feed: directly under the progress bar → scrollable list of the last 5 deposits with "View All" modal**

**Rationale**: Provides recent activity visibility without overwhelming the UI; modal allows deeper engagement for interested users.

---

## C. Token Voting Mechanics

### 8. Formula constants
**Question**: What's the exact cap in the log curve (you floated 3 votes @ ≈100 ai16z) — should we bake that in or keep it env-configurable?

**Decision**: **Log-curve constants pulled from env vars**

**Rationale**: Allows for easy adjustment and A/B testing without code changes.

---

### 9. Memo grammar
**Question**: Submission IDs can contain hyphens or uppercase? Any risk of ambiguous IDs colliding?

**Decision**: **Memo format handled (unique IDs, lowercase/hyphens)**

**Rationale**: Existing system already handles ID uniqueness and format validation.

---

### 10. Refund / error path
**Question**: If someone sends a malformed memo, do we auto-refund less a fee, or send a DM with manual instructions?

**Decision**: **Collect all bad memos, treat feature as "experimental – low fee, use at own risk"**

**Rationale**: Avoids complex refund logic while setting appropriate expectations for users.

---

### 11. Whale transparency
**Question**: Do we publicly surface the top N voter wallets for each project, or keep individual weights hidden?

**Decision**: **Whale transparency postponed. For v1 we omit the per-wallet leaderboard and just show the aggregate Community score + prize-pool total**

**Rationale**: Simplifies v1 implementation and avoids privacy concerns; can be added later if community requests it.

---

## D. Wallet-Connection vs Anonymous Voting

### 12. Default CTA hierarchy
**Question**: Which button is more prominent on mobile: "Connect wallet" or "Vote anonymously"?

**Decision**: **Show both "Connect Wallet" & "Vote Anonymously" CTAs equally**

**Rationale**: Gives users choice without biasing toward one approach; lets usage patterns emerge naturally.

---

### 13. Batch-vote cart complexity
**Question**: Do we allow unequal amounts per project in a single transaction, or force one uniform amount?

**Decision**: **Wallet-cart lets user set different amounts per project**

**Rationale**: Maximizes flexibility for users who want to weight their votes differently across projects.

---

### 14. Post-vote state
**Question**: For anonymous voters we can't reliably show "You voted"; any concern about confusing repeats?

**Decision**: **Feedback animation: subtle glow / pulse on the Community-score cell and prize-pool bar—no toast**

**Rationale**: Provides visual confirmation of vote processing without intrusive UI elements; works for both connected and anonymous users.

---

## E. Superchat SOL

### 15. Time window
**Question**: Exactly when does superchat open and close relative to the AI deliberation stream?

**Decision**: **Superchat SOL delivered via queue for deliberation segment**

**Rationale**: Allows for controlled integration into episode production workflow.

---

### 16. LLM context size
**Question**: How many superchat messages per submission are we comfortable injecting before we risk prompt-stuffing?

**Decision**: **Spoken time budget ~ <3 min per submission, messages ≤80 chars, log-scale cost**

**Rationale**: Balances engagement with content quality and technical constraints.

---

### 17. Moderation latency
**Question**: Do we need a real-time human approve button, or is automated profanity + blocklist enough?

**Decision**: **Automated moderation (blocklist/profanity)**

**Rationale**: Reduces operational overhead while maintaining content quality.

---

## F. Discord Integration

### 18. Token-gated weighting
**Question**: If a user has 100 ai16z they get extra weight on Discord reactions — does that stack with on-chain votes or remain siloed?

**Decision**: **Discord reaction weight silo'd from on-chain votes**

**Rationale**: Keeps the scoring systems separate and prevents double-counting or complex interaction effects.

---

### 19. Role gating vs channel gating
**Question**: Do we create special channels, or assign a "Verified Holder" role that just multiplies emoji counts anywhere?

**Decision**: **Existing token-gated roles/channels stay as-is**

**Rationale**: Avoids disrupting existing Discord community structure and workflows.

---

## G. Voting Windows & Eligibility

### 20. Opening trigger
**Question**: Does community voting open the moment AI scores post, or at a scheduled "Community Voting Kickoff" time?

**Decision**: **Community voting opens when you run the bot (manual start)**

**Rationale**: Provides operational control over timing and allows for coordination with other activities.

---

### 21. Closing/freeze mechanics
**Question**: Do we hard-close at T-0 or implement a rolling "10 min extension if vote comes in during last 5 min" anti-sniping rule?

**Decision**: **Voting hard stops at deadline (no extensions)**

**Rationale**: Simple, predictable, and prevents gaming the system with last-minute activity.

---

### 22. Minimum-vote eligibility
**Question**: What is the floor for a Community score to show (≥ 5 unique wallets? ≥ 25 total weight?) — needs to be codified.

**Decision**: **Community score shown once > 1 unique vote**

**Rationale**: Low barrier for engagement while preventing completely empty states.

---

## H. Analytics & Privacy

### 23. Anonymous analytics
**Question**: Are we comfortable logging IP addresses / browser fingerprints for conversion funnels, or keep purely on-chain analytics?

**Decision**: **No off-chain PII analytics; rely on on-chain only**

**Rationale**: Maintains privacy focus and avoids compliance complexity while still providing useful data.

---

### 24. Public data export
**Question**: Will we expose a JSON/CSV dump of all votes for transparency, or keep that internal?

**Decision**: **Vote data internal for now**

**Rationale**: Keeps options open for future transparency while maintaining operational flexibility.

---

## I. Edge Cases & Security

### 25. Replay attacks
**Question**: If someone re-uses an old transaction signature in a webhook replay, do we de-dupe by sig or by sender+memo?

**Decision**: **Secure plan: Use the transaction signature (tx sig) as the primary key in the `sol_votes` table (UNIQUE). Store `sender`, `memo`, `amount`, `timestamp` alongside. Each unique signature counts once, so no timing window is needed—Solana will never repeat a sig. If the same wallet wants to add more votes later they simply broadcast a new tx (new sig). Log-weight cap is enforced per wallet ▸ per submission, so spamming many micro-txs doesn't bypass the cap.**

**Rationale**: Leverages Solana's cryptographic guarantees for foolproof deduplication while allowing legitimate repeat voting through new transactions.

---

### 26. Dust spam
**Question**: Do we ignore token transfers < 1 ai16z outright, or accept but give 0 weight?

**Decision**: **Dust < 1 ai16z gets 0 weight / not displayed**

**Rationale**: Maintains minimum vote threshold while avoiding database bloat from spam.

---

### 27. Program-derived addresses
**Question**: Any plan to support votes coming from multisig or DAO treasuries controlled by PDAs?

**Decision**: **PDA / multisig support out of scope v1**

**Rationale**: Focuses on individual user experience for initial launch; can be added later if needed.

---

## Decision Summary

Once all questions are answered, provide a summary of the key decisions that will drive implementation:

### Core Mechanics
- [ ] Voting formula: _[constants and caps]_
- [ ] Score display: _[format and precision]_
- [ ] Ranking logic: _[primary sort and tie-breakers]_

### User Experience
- [ ] Voting flow: _[wallet-first vs anonymous priority]_
- [ ] UI hierarchy: _[button prominence and messaging]_
- [ ] Error handling: _[refund policy and user feedback]_

### Technical Implementation
- [ ] Database schema: _[tables and relationships]_
- [ ] API endpoints: _[data flow and caching]_
- [ ] Security measures: _[validation and attack prevention]_

### Timeline Impact
- [ ] Must-have for MVP: _[core features]_
- [ ] Nice-to-have for v1: _[enhanced features]_
- [ ] Future consideration: _[advanced features]_