# Instructions for AI Coder - Token Voting Implementation

You are implementing a token voting system for the Clank Tank hackathon leaderboard. This document provides step-by-step guidance on how to proceed.

## 🎯 **Your Mission**
Add ai16z token voting functionality to the existing hackathon dashboard, allowing community members to vote on projects using Solana tokens while maintaining AI judges as the primary ranking system.

## 📁 **File Structure Overview**

### Implementation Plans (Your Main Guide)
- **`README.md`** - Start here for navigation and context
- **`simple-tasks.md`** - Daily task breakdown (use for planning)
- **`backend-tasks.md`** - Detailed backend implementation with code examples
- **`frontend-tasks.md`** - Detailed frontend implementation with React components
- **`notes/`** - Reference materials with design decisions and rationale

### Existing Codebase (What You're Building On)
- **Backend**: `/home/jin/repo/clanktank/hackathon/backend/`
  - `app.py` - FastAPI application with existing endpoints
  - `data/hackathon.db` - SQLite database (may be empty initially)
  - `schema.py` - Database schema management
- **Frontend**: `/home/jin/repo/clanktank/hackathon/dashboard/frontend/`
  - `src/pages/Leaderboard.tsx` - Existing leaderboard page to enhance
  - `src/lib/api.ts` - API client functions
  - `package.json` - React + Vite + TypeScript setup
- **Discord Bot**: `/home/jin/repo/clanktank/hackathon/bots/discord_bot.py` - Existing community voting

## 🔍 **Pre-Implementation Assessment**

### Step 1: Understand the Existing System
Before writing any code, thoroughly examine:

1. **Read all planning documents**:
   ```bash
   # Read these in order:
   cat leaderboard-plans/README.md
   cat leaderboard-plans/simple-tasks.md
   cat leaderboard-plans/notes/question-audit.md  # Key design decisions
   ```

2. **Examine the existing codebase structure**:
   ```bash
   # Backend structure
   ls -la hackathon/backend/
   python hackathon/backend/app.py --help  # Check startup options
   
   # Frontend structure  
   ls -la hackathon/dashboard/frontend/src/
   cat hackathon/dashboard/frontend/package.json
   ```

3. **Check the current database state**:
   ```bash
   # See what tables exist
   sqlite3 hackathon/backend/data/hackathon.db ".tables"
   sqlite3 hackathon/backend/data/hackathon.db ".schema"
   
   # If empty, create test data first:
   # python -m hackathon.scripts.create_db
   ```

4. **Test the existing system**:
   ```bash
   # Start backend
   cd hackathon/backend && python app.py
   
   # Start frontend (separate terminal)
   cd hackathon/dashboard/frontend && npm run dev
   
   # Check existing endpoints
   curl http://localhost:8000/api/leaderboard
   ```

### Step 2: Create Your Progress Tracking Document
Create `leaderboard-plans/PROGRESS.md` to track your work:

```markdown
# Implementation Progress

**Started**: [DATE]
**Estimated Completion**: [DATE + 1 week]

## Daily Progress

### Day 1: [DATE]
**Target**: Backend database and basic API (from simple-tasks.md)

#### Tasks Completed:
- [ ] Assessed existing codebase
- [ ] Created test submissions for development
- [ ] Added sol_votes table to database
- [ ] Implemented /api/community-scores endpoint
- [ ] Created vote weight calculation function

#### Issues Encountered:
[Document any problems and solutions]

#### Next Day Priority:
[What to focus on tomorrow]

### Day 2: [DATE+1]
**Target**: Webhook processing

[Continue for each day...]

## Technical Decisions Made:
[Document any deviations from the plan or technical choices]

## Testing Completed:
[Keep track of what you've tested]
```

## 📋 **Implementation Workflow**

### Phase 1: Backend Implementation (Days 1-3)

#### Day 1: Database and Basic API
**Primary Reference**: `backend-tasks.md` Tasks 1-3

1. **Understand the current database**:
   - Read `hackathon/backend/schema.py` to understand the existing schema
   - Check if `community_feedback` table exists and its structure
   - Decide whether to extend existing table or create new `sol_votes` table

2. **Create test data** (if database is empty):
   ```bash
   # You may need to create test submissions first
   python -m hackathon.scripts.create_db
   # Add test submissions via the frontend or API
   ```

3. **Implement database changes**:
   - Follow the SQL schema in `backend-tasks.md` Task 1
   - Add the vote weight calculation function from Task 2
   - Test with sample data

4. **Create community scores API**:
   - Add `/api/community-scores` endpoint to `app.py`
   - Use the query examples from `backend-tasks.md` Task 3
   - Test endpoint returns proper JSON

5. **Update progress**:
   ```markdown
   #### Day 1 Completed:
   - [x] Added sol_votes table with schema: [SQL used]
   - [x] Implemented vote weight calculation: [formula confirmed]
   - [x] Created /api/community-scores endpoint: [test results]
   
   #### Issues:
   - Database schema needed modification because [reason]
   - Vote weight calculation edge case: [how handled]
   ```

#### Day 2: Webhook Processing
**Primary Reference**: `backend-tasks.md` Tasks 4-5

1. **Implement Helius webhook endpoint**:
   - Add webhook route to `app.py`
   - Follow the implementation example in Task 5
   - Test with sample webhook payloads

2. **Test webhook processing**:
   - Create sample Helius webhook JSON
   - Test memo parsing and database insertion
   - Verify duplicate transaction handling

#### Day 3: Prize Pool API
**Primary Reference**: `backend-tasks.md` Task 4

1. **Implement prize pool endpoint**:
   - Add `/api/prize-pool` route
   - Test with sample data

### Phase 2: Frontend Implementation (Days 4-6)

#### Day 4: Leaderboard Updates
**Primary Reference**: `frontend-tasks.md` Tasks 1-2

1. **Examine existing leaderboard**:
   ```bash
   cat hackathon/dashboard/frontend/src/pages/Leaderboard.tsx
   cat hackathon/dashboard/frontend/src/lib/api.ts
   ```

2. **Add community score column**:
   - Modify `Leaderboard.tsx` to display community scores
   - Update API client to fetch community scores
   - Test with sample data

#### Day 5: Voting Interface
**Primary Reference**: `frontend-tasks.md` Tasks 5-6

1. **Implement voting components**:
   - Add vote slider component
   - Implement mobile deep-links and desktop copy-paste
   - Test voting flow without actual transactions

#### Day 6: Prize Pool Widget
**Primary Reference**: `frontend-tasks.md` Task 3

1. **Add prize pool widget to leaderboard**
2. **Test responsive design**

### Phase 3: Integration and Testing (Day 7)

1. **End-to-end testing**:
   - Test complete voting flow
   - Verify webhook processing
   - Check leaderboard updates

2. **Documentation**:
   - Update README with setup instructions
   - Document any deviations from original plan

## ⚠️ **Important Guidelines**

### Code Quality Standards
- **Follow existing code patterns** in the codebase
- **Use existing utilities** (don't reinvent auth, database connections, etc.)
- **Match existing styling** (TailwindCSS classes, component patterns)
- **Add proper error handling** for all new endpoints

### Testing Approach
- **Test each component independently** before integration
- **Use manual testing** (create sample data, test API endpoints with curl)
- **Document test cases** in your progress file
- **Test edge cases** (empty data, malformed requests, etc.)

### Security Considerations
- **Keep financial data separate** - use dedicated `sol_votes` table as planned
- **Validate all inputs** - especially webhook payloads and transaction memos
- **Log important events** - use existing audit logging patterns
- **Never commit sensitive data** - wallet addresses, API keys, etc.

### When to Deviate from Plans
The implementation plans are detailed but you may need to adapt:

- **Document any changes** in your progress file with rationale
- **Prefer simpler solutions** that integrate with existing code
- **Ask for clarification** if plans conflict with codebase reality
- **Prioritize functionality** over perfect adherence to detailed specs

## 🚨 **Getting Unstuck**

### If Database Issues:
1. Check existing schema with `.schema` command
2. Look at existing API endpoints for patterns
3. Create minimal test data first

### If API Issues:
1. Test with curl commands
2. Check FastAPI docs at `/docs` endpoint
3. Follow existing endpoint patterns in `app.py`

### If Frontend Issues:
1. Check browser console for errors
2. Verify API calls in Network tab
3. Follow existing component patterns

### If Integration Issues:
1. Test each piece separately first
2. Use sample data instead of real transactions
3. Check logs for detailed error messages

## ✅ **Definition of Done**

Your implementation is complete when:

- [ ] Community scores appear in leaderboard
- [ ] Token voting works (copy-paste instructions + mobile deep-links)
- [ ] Prize pool widget shows current amount and progress
- [ ] Webhook processes sample Solana transactions
- [ ] All manual tests pass
- [ ] Progress document shows completed tasks
- [ ] Basic documentation updated

Remember: This is a **proof of concept for a community event**. Prioritize working functionality over perfect optimization. Good luck!