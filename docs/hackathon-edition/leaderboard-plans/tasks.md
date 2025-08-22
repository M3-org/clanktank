# Hackathon Dashboard UX Consolidation Tasks

## 🎯 Strategic Context & Goals

### **Problem Statement**
Currently have 3 redundant pages (Frontpage, Dashboard, Leaderboard) causing user confusion about where to go and what to do. Users don't know whether to use Dashboard vs Leaderboard, and there's significant code duplication.

### **Solution Approach**
1. **Single Source of Truth**: Frontpage becomes primary interface for all users
2. **Phase-Based UX**: Interface automatically adapts based on `SUBMISSION_DEADLINE` env var
3. **Simplified User Journey**: Dashboard (build) → Frontpage (vote) → Archive (results)
4. **Community-Driven Templates**: URL-based sharing with transparent preview, no infrastructure overhead

### **Key Design Principles**
- **DRY (Don't Repeat Yourself)**: Reuse components, eliminate redundancy
- **Trust Through Transparency**: Users can see/preview data before using it
- **Environment-Driven**: Use existing env vars (`SUBMISSION_DEADLINE`) to control UX phases
- **Minimal New Infrastructure**: Prefer URL params and conditional rendering over new systems
- **Self-Contained Experiments**: Keep experimental code in isolated folder to prevent production impact

### **Codebase Context**
- **Frontend**: React + TypeScript + Vite in `hackathon/dashboard/frontend/`
- **State Management**: useState hooks, no complex state management library
- **Styling**: Tailwind CSS with dark mode support
- **Components**: Already have toast notifications, copy-to-clipboard hooks, form validation
- **API**: `hackathonApi` for leaderboard data, existing submission form handling
- **Build Commands**: `npm run build` (TypeScript + Vite), `npm run lint` for ESLint

## 🎯 Core UX Simplification

### 1. Archive Current Leaderboard Page ✅ COMPLETED
- [x] Create `/hackathon/dashboard/frontend/src/pages/experimental/` folder
- [x] Move current `Leaderboard.tsx` to `experimental/LeaderboardV1.tsx`
- [x] Move `VotingPrototypes.tsx` to experimental folder
- [x] Ensure experimental components are self-contained (no imports to main app)
- [x] Update experimental folder with index.ts that exports nothing to prevent import leaks
- [x] **CREATED**: LeaderboardV2.tsx with voting modal + side-by-side tables + top 10
- [x] **ADDED**: Routing for experimental pages accessible during development

### 2. Consolidate Dashboard Views (Simplified) ✅ COMPLETED
- [x] Add URL param support to Dashboard page for view switching
  - `/dashboard` (default: my projects)
  - `/dashboard?view=all` (all submissions)
  - **REMOVED**: rankings view (avoid voting confusion, direct to frontpage/leaderboard instead)
- [x] Unified component for submission display (reuse between views)
- [x] Add view toggle UI (My Projects / All Projects only)
- [x] Remove redundant leaderboard page from main routing during voting phases

### 3. Phase-Based Frontpage (Using SUBMISSION_DEADLINE) ✅ COMPLETED
- [x] Add conditional leaderboard rendering based on SUBMISSION_DEADLINE env variable
- [x] **Before deadline**: Remove leaderboard section entirely (Hero → Episodes → How it Works → Judges → FAQ)
- [x] **After deadline**: Show full leaderboard with voting (Hero → Leaderboard → Episodes → How it Works → Judges → FAQ)
- [x] Apply LeaderboardV1 + V2 patterns to the single leaderboard component (responsive design)
- [x] Add voting modal functionality and interactive voting cells
- [x] Implement top 10 display with single table layout (optimized for all screen sizes)
- [x] **ADDED**: Phase-based hero overlay messaging (Watch & Vote when deadline passes)
- [x] **ADDED**: "View All" link from leaderboard to dashboard
- [ ] Switch hero from static video to YouTube livestream embed when voting begins (FUTURE)

### 5. URL-Based Template System (REVISED APPROACH) ✅ COMPLETED
**Note**: Abandoned base64 URLs due to trust/UX issues (too long, look sketchy, not transparent)

**New Approach - Real-time URL State Management:**
- [x] Create templates page in experimental folder showcasing starter project ideas  
- [x] Add template preview modal with "Preview Full Data" before applying
- [x] Implement real-time URL updates with form state (`draft` parameter) for transparency
- [x] Add form state recovery from URL on page load/refresh
- [x] Add "Share as Template" functionality (copy clean URLs to clipboard)
- [x] Generate starter template data using existing test submission structure (DeFi, AI, Gaming)
- [x] Add visual feedback when state is saved to URL
- [x] Add toast feedback when template is applied to form (working with JSON upload)
- [x] **COMPLETED**: Integration with main submission forms (SubmissionPage.tsx + SubmissionEdit.tsx)
- [x] **COMPLETED**: Real-time URL state management in both submission forms
- [x] **COMPLETED**: Form state recovery from URL parameters with security protection
- [x] **COMPLETED**: Download JSON functionality updated to export current form state
- [x] **COMPLETED**: Upload JSON functionality integrated with URL state management

**Trust Building Features:**
- Users can see exactly what data they're using (no hidden base64)
- Real-time URL updates show form state transparently as they type
- Clean, shareable URLs for templates page rather than cryptic encoded data

## 🧪 Development Infrastructure

### 6. Template Generation Script (UPDATED)
- [ ] Create script to generate starter template data from existing test submissions
- [ ] Generate variety of templates (DeFi, NFT, AI, Gaming, Social, etc.)
- [ ] Structure: JSON files with project_name, description, category, github_url, etc.
- [ ] Output for templates page/section display (not URLs)
- [ ] Document template data structure and usage examples

**Context**: Changed from URL generation to template data generation for UI display

### 7. Experimental Page Organization ✅ COMPLETED
- [x] Ensure VotingPrototypes.tsx is properly isolated in experimental folder
- [x] Add experimental page index/navigation with documentation
- [x] Document experimental page guidelines for future development  
- [x] Clean up any remaining import artifacts from previous optimization
- [x] **COMPLETED**: LeaderboardV2.tsx experimental version with enhanced features
- [x] **COMPLETED**: Templates.tsx with real-time URL state management
- [x] Test LeaderboardV2 features (voting modal, side-by-side tables, top 10) - NOTE: Dropped side-by-side approach
- [x] Apply successful LeaderboardV2 patterns to Frontpage (see task #3) - Used single table approach instead

**NOTE**: Side-by-side tables approach was dropped in favor of single responsive table that works better across all screen sizes.

## 🎨 UX Polish

### 8. Navigation & Flow Cleanup ✅ STARTED
- [x] **COMPLETED**: Remove redundant "View Full Leaderboard" links from Header navigation (desktop + mobile)
- [x] **COMPLETED**: Remove count display from Dashboard filter bar to save space
- [x] **COMPLETED**: Update routing to handle consolidated dashboard views (mine/all only) - Done in Task 2
- [x] **COMPLETED**: Update main navigation for simplified user journey (Header cleanup)
- [ ] Phase-based navigation: automatic transition at SUBMISSION_DEADLINE (future enhancement)
- [x] **COMPLETED**: Ensure consistent user journey - Dashboard (mine/all) → Frontpage (leaderboard when voting active)

---

## 🚀 Implementation Priority

### **Phase 1: Core Consolidation** ✅ COMPLETED
1. ✅ Archive current leaderboard → experimental folder
2. ✅ Consolidate Dashboard views (mine/all only)
3. ✅ Implement phase-based Frontpage using SUBMISSION_DEADLINE

### **Phase 2: Template System** ✅ COMPLETED
4. ✅ URL-based form state management with transparent JSON encoding
5. ✅ Real-time form state in URL with debounced updates
6. ✅ Integration with submission forms (SubmissionPage + SubmissionEdit)
7. ✅ Security protection for Discord handle manipulation
8. ✅ Enhanced JSON download/upload functionality

### **Phase 3: Voting Phase Auto-Activation** (At Deadline)
7. SUBMISSION_DEADLINE triggers leaderboard section appearance
8. Hero video automatically switches to livestream embed
9. Section reordering happens automatically (engagement flow)
10. Navigation cleanup for voting phase

---

## 🎯 Success Metrics ✅ ACHIEVED
- ✅ **Single source of truth**: Frontpage becomes primary hackathon interface (phase-based)
- ✅ **Reduced confusion**: Clear user journey (Dashboard mine/all → Frontpage voting)
- ✅ **Simplified codebase**: Less redundancy, consolidated leaderboard, reusable components
- ✅ **Real-time collaboration**: URL-based form state sharing with transparent, secure UX
- ✅ **Enhanced workflows**: JSON download/upload + URL state management
- ✅ **Automatic phase transitions**: SUBMISSION_DEADLINE drives leaderboard appearance
- ✅ **Clean navigation**: Removed redundancy, focused user flow

## 📋 Key Decision History

### **Template System Evolution**
- **Initial idea**: Base64 encoded URLs for templates
- **Problem identified**: URLs too long, look sketchy, users can't verify content
- **Final implementation**: Real-time URL state management in submission forms with:
  - Transparent JSON encoding (users can see exactly what data is shared)
  - Security protection (Discord handle manipulation blocked)
  - React Hook Form integration with `mode: 'onChange'` and proper `reset()`
  - Debounced updates to prevent excessive URL changes
  - Enhanced JSON download/upload workflows

### **Leaderboard Consolidation Evolution**  
- **Initial idea**: Two different leaderboard components (preview vs full)
- **Problem identified**: Too much complexity, duplicate maintenance
- **Revised approach**: Single leaderboard component that appears after SUBMISSION_DEADLINE

### **Dashboard Ranking Views**
- **Initial idea**: Dashboard with "mine/all/rankings" views including voting
- **Problem identified**: Rankings without voting functionality confuses users
- **Final decision**: Dashboard just has "mine/all" views, voting happens on Frontpage/Leaderboard

### **Section Ordering Strategy**
- **Before deadline**: Educational flow (Hero → Episodes → How it Works → Judges → FAQ)
- **After deadline**: Engagement flow (Hero Livestream → Leaderboard → How it Works → Judges → Episodes → FAQ)
- **Trigger**: SUBMISSION_DEADLINE environment variable

## 🧠 Future Considerations (Post-Launch)

### **Phase-Based Access Evolution**
- [ ] Dynamic routing based on hackathon lifecycle phases
- [ ] Archive page structure for post-competition results
- [ ] Social media screenshot generation for leaderboard sharing

### **Community Features**
- [ ] Template sharing and discovery mechanisms  
- [ ] Winner template promotion and curation
- [ ] Community voting analytics and insights

### **Experimental Development**
- [ ] Maintain experimental folder for rapid UI prototyping
- [ ] Version control for major UX iterations
- [ ] A/B testing infrastructure for future hackathons