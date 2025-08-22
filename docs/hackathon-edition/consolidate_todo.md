# Clank Tank Hackathon Code Audit TODO

## Code Audit Scope
**Focus:** Recent updates in the `consolidate` branch over the last 2 weeks, primarily in `/hackathon` directory
**Goal:** Surface quick-win clean-ups and identify non-DRY or hard-to-maintain patterns
**Strategy:** Move unused files to `/trashcan` instead of deletion

## Recent Git History Analysis (2 Weeks)
Based on recent commits, here's the comprehensive picture of recent activity:

### Major Consolidation & Refactoring Efforts (Last 2 Weeks)
1. **1496b9f** - "refactor: consolidate PrizePool components into single variant-based component"
   - Merged PrizePoolCard.tsx, PrizePoolBanner.tsx, usePrizePoolUI.ts into PrizePool.tsx
   - Reduced from 297 lines across 3 files to 295 lines in 1 file
   - **This explains why PrizePool.tsx is well-consolidated!**

2. **f6b464d** - "refactor: eliminate dead code and cargo cult programming"
   - Removed tokenUtils.tsx (62 lines of unused code)
   - Eliminated cargo cult programming anti-pattern

3. **9dc6fd3** - "refactor(frontend): unify all card components to use shared Card base with variants"
   - LeaderboardCard, PrizePoolCard, SkeletonCard now use Card.tsx
   - Removes container duplication, improves maintainability

4. **d1e6538** - "consolidate components, do some cleanup"
   - Multiple component consolidations
   - Badge, CategoryBadge, LikeDislike, StatusBadge components

### Recent Frontend Activity (Last Week)
1. **b2f7319** - "add some docs notes" (Jul 21)
2. **aea8692** - "bump" (Jul 21) - Footer.tsx
3. **be3a8b6** - "add mobile/desktop control for lightbox video watch mode" (Jul 20) - Frontpage.tsx
4. **8f6e628** - "consolidate prize pool banner + add footer" (Jul 20)
5. **66139c4** - "Major frontend UX consolidation and mobile optimizations" (Jul 20)
6. **52071d7** - "Implement comprehensive Frontpage redesign" (Jul 20)

### Backend & Infrastructure Changes
1. **de310c7** - "Fix research pipeline 413 errors"
2. **e243dc8** - "backend: update database and API configuration"
3. **8710f3a** - "cleanup media folder, add gallery"
4. **fd8282a** - "cleanup submission backups folder (deprecated)"

## 0. Documentation Audit (NEW SECTION)

### README Files Review Summary

#### ✅ **Excellent Documentation Found**
1. **`hackathon/README.md`** - **COMPREHENSIVE & UP-TO-DATE**
   - 878 lines of detailed documentation
   - Complete workflow from DB setup to episode generation
   - GitIngest integration documentation
   - Schema management and versioning
   - Security & audit logging features
   - **Status:** ✅ Excellent - reflects recent consolidation work

2. **`hackathon/dashboard/frontend/README.md`** - **EXCELLENT & CURRENT**
   - 225 lines of frontend-specific documentation
   - Documents recent consolidation work (PrizePool, Badge components)
   - Code quality improvements section
   - Reusable patterns and anti-patterns eliminated
   - **Status:** ✅ Excellent - reflects recent refactoring

3. **`hackathon/tests/README.md`** - **COMPREHENSIVE & ACCURATE**
   - 449 lines of detailed test documentation
   - Documents recent test cleanup (4 files moved to trashcan)
   - Full pipeline testing guide
   - V2 schema compliance updates
   - **Status:** ✅ Excellent - reflects recent test consolidation

#### ⚠️ **Documentation Issues Found**

4. **`hackathon/dashboard/README.md`** - **OUTDATED PATHS**
   - **Issue:** References old paths like `scripts/hackathon/dashboard` instead of `hackathon/dashboard`
   - **Issue:** Mentions `scripts/hackathon/schema.py` instead of `hackathon/backend/schema.py`
   - **Issue:** Outdated setup instructions
   - **Status:** ⚠️ Needs path updates

5. **`hackathon/scripts/README.md`** - **MINIMAL BUT ACCURATE**
   - Only 52 lines, correctly notes DB scripts moved to backend
   - **Status:** ✅ Accurate but could be expanded

### Documentation Audit Findings

#### **Positive Patterns** ✅
1. **Comprehensive Coverage** - Main README covers entire pipeline
2. **Recent Updates** - Documentation reflects recent consolidation work
3. **Code Examples** - Good command examples throughout
4. **Architecture Documentation** - Clear system overview
5. **Troubleshooting Guides** - Practical problem-solving sections

#### **Issues to Fix** ⚠️
1. **Path Inconsistencies** - Dashboard README has outdated paths
2. **Missing Experimental Framework Docs** - New experimental UI framework not documented
3. **Schema Sync Documentation** - Could be clearer about frontend/backend sync process

#### **Documentation Gaps** 📝
1. **Experimental Framework** - No documentation for new experimental UI components
2. **Video Integration** - Recent video features not well documented
3. **Mobile Controls** - New mobile/desktop controls not documented

## 1. Initial Discovery & File Triage

### FILE LIST (Actually Modified Recently)
| File | Why Flagged | Immediate-Fix? (y/n) | Notes |
|------|-------------|---------------------|-------|
| hackathon/dashboard/frontend/src/pages/Frontpage.tsx | Modified 4 times recently | y | High activity, needs review |
| hackathon/dashboard/frontend/src/pages/experimental/ | Created/moved in recent commit | y | New experimental framework |
| hackathon/dashboard/frontend/src/pages/Leaderboard.tsx | Modified recently | y | Video integration needs review |
| hackathon/dashboard/frontend/src/components/Footer.tsx | Modified recently | y | Prize pool integration |
| hackathon/dashboard/frontend/src/App.tsx | Modified recently | y | Experimental routing added |
| hackathon/backend/app.py | Modified in consolidation | n | Part of ongoing consolidation |
| hackathon/dashboard/frontend/src/components/Badge.tsx | Modified in consolidation | n | Part of ongoing consolidation |

## 2. Deep Dive Analysis Tasks

### High-Priority Files (Start Here)

#### A. hackathon/dashboard/frontend/src/pages/Frontpage.tsx
**Context:** Most frequently modified file (4 recent commits)
**Key Issues:**
- High modification frequency suggests potential instability
- Video integration and mobile controls added recently
- Hero section and marquee prize pool logic

**Refactor Suggestions:**
1. **Extract Video Component** - Separate video player logic
2. **Extract Hero Section** - Create reusable hero component
3. **Review Mobile Controls** - Ensure they're properly implemented

**Effort vs Impact:** Medium impact, Low effort (1 hour)

#### B. hackathon/dashboard/frontend/src/pages/experimental/
**Context:** Newly created experimental framework
**Key Issues:**
- Large files (VotingPrototypes.tsx is 1564 lines)
- New framework needs documentation
- Potential dead code

**Refactor Suggestions:**
1. **Audit Usage** - Check if any experimental code is actually used
2. **Document Framework** - Better documentation of experimental patterns
3. **Archive Unused** - Move truly experimental code to trashcan

**Effort vs Impact:** Medium impact, Low effort (30 minutes)

#### C. hackathon/dashboard/frontend/src/pages/Leaderboard.tsx
**Context:** Modified recently with video integration
**Key Issues:**
- Video handling logic mixed with leaderboard logic
- Hardcoded wallet addresses
- Complex rank badge logic

**Refactor Suggestions:**
1. **Extract Video Component** - Separate video player logic
2. **Extract Rank Badge** - Create reusable rank badge component
3. **Move Constants** - Extract wallet addresses to constants

**Effort vs Impact:** Low impact, Low effort (30 minutes)

### Medium-Priority Files

#### D. hackathon/dashboard/frontend/src/App.tsx
**Context:** Modified to add experimental routing
**Key Issues:**
- Experimental routes added recently
- Need to ensure proper isolation

**Refactor Suggestions:**
1. **Review Experimental Routing** - Ensure proper DEV-only gating
2. **Document Routing Patterns** - Clear separation of concerns

**Effort vs Impact:** Low impact, Low effort (15 minutes)

## 3. Global Findings & Systemic Issues

### Architecture Issues
1. **Frontpage Instability** - Most frequently modified file suggests design instability
2. **Experimental Code Pollution** - New experimental framework needs boundaries
3. **Video Integration** - Video logic appearing in multiple components

### Positive Patterns Found ✅
1. **Active Consolidation** - Team is actively consolidating components (PrizePool, Card components)
2. **Dead Code Elimination** - Removing unused code (tokenUtils.tsx)
3. **Cargo Cult Prevention** - Eliminating unnecessary abstractions
4. **Component Unification** - Card components unified under shared base

### Naming Issues
1. **Experimental Framework** - New framework needs better documentation
2. **Component Boundaries** - Video logic should be isolated

### Build/Config Issues
1. **Experimental Isolation** - New experimental framework needs proper isolation
2. **Mobile Controls** - Recent mobile/desktop controls need review

## 4. Top 3 Refactors (Ordered by Impact/Effort)

### 1. ✅ Fix Documentation Paths - **COMPLETED**
**Impact:** High - Improve developer experience
**Effort:** Low - 15 minutes
**Approach:** Update dashboard README with correct paths
**Status:** ✅ **DONE** - Fixed all outdated paths in `hackathon/dashboard/README.md` and `hackathon/README.md`

### 2. ✅ Document Experimental Framework - **COMPLETED**
**Impact:** Medium - Improve developer experience
**Effort:** Low - 30 minutes
**Approach:** Better documentation and usage guidelines
**Status:** ✅ **DONE** - Added comprehensive experimental framework documentation to frontend README

### 3. Extract Video Components
**Impact:** Medium - Improve reusability
**Effort:** Low - 30 minutes
**Approach:** Separate video logic from business logic

## 5. Questions & Blockers

### Questions for Clarification
1. **Frontpage Stability** - Why is Frontpage.tsx modified so frequently?
2. **Experimental Usage** - Are any experimental components actually used in production?
3. **Video Integration** - Is video logic duplicated across components?

### Potential Blockers
1. **Design Iteration** - Frontpage changes might be intentional design iterations
2. **Experimental Framework** - New framework might need time to stabilize

## 6. Next Steps

1. **Review and approve this audit plan**
2. ✅ **Documentation Paths Fixed** - Dashboard README paths updated
3. ✅ **Experimental Framework Documented** - Added comprehensive documentation
4. **Extract Video Components** - Separate video logic from business logic

## Implementation Notes
- Always move files to `/trashcan`