# Hackathon Dashboard Frontend

## Project Structure

### `/src/components/`
Reusable UI components following design system patterns:

- **`Button.tsx`** - Primary button component with variants (primary, secondary, ghost, discord, outline) and sizes (sm, md, lg)
- **`Card.tsx`** - Base card container component for consistent styling
- **`Badge.tsx`** - **CONSOLIDATED**: Unified badge system with specialized exports:
  - `Badge` - Generic badge with predefined variants (default, secondary, success, warning, error, info)
  - `StatusBadge` - Submission status indicators using `getStatusColor()` utility
  - `CategoryBadge` - Project category badges using `getCategoryColor()` utility
  - Single source of truth for all badge styling and logic
- **`VoteModal.tsx`** - Modal for community voting functionality with enhanced clipboard support
- **`PrizePool.tsx`** - **CONSOLIDATED**: Unified prize pool component with variant support ('card' | 'banner')
  - Replaces multiple prize pool components
  - Includes integrated token modal functionality
  - Supports responsive design with mobile-first approach
- **`LeaderboardCard.tsx`** - Individual submission card for leaderboard display
- **`Header.tsx`** - Application header with navigation
- **`ProtectedRoute.tsx`** - Route protection based on Discord authentication
- **`SolanaProvider.tsx`** - Solana wallet context provider
- **`WalletVoting.tsx`** - Wallet-based voting interface
- **`LikeDislike.tsx`** - Like/dislike button component
- **`DiscordAvatar.tsx`** - Discord user avatar display
- **`CountdownTimer.tsx`** - Timer component for deadlines
- **`SkeletonCard.tsx`** - Loading skeleton for cards

### `/src/utils/`
Utility functions and helpers:

- **`phantomLink.ts`** - Phantom wallet deep-link utilities:
  - `buildVotingLink()` - Creates Phantom deep-links for voting
  - `buildSponsorLink()` - Creates Phantom deep-links for sponsorship
  - `generateCopyInstructions()` - Generates copy-paste transaction instructions
  - `isMobile()` - Mobile device detection (standardized approach)
  - `validateMemo()` - Validates memo length (80 char limit)

### `/src/lib/`
Core library modules:

- **`api.ts`** - API client with axios configuration:
  - REST endpoints for submissions, leaderboard, stats
  - Discord OAuth integration
  - File upload handling
  - Static data fallback for production builds
- **`utils.ts`** - Common utilities:
  - `cn()` - Tailwind class merging with clsx
  - `getStatusColor()` - Status-based color mapping
  - `getCategoryColor()` - Category-based color mapping
  - `formatDate()` - Date formatting helper
  - `pretty()` - Number formatting utility
- **`constants.ts`** - **CONSOLIDATED**: Single source of truth for all constants:
  - `PRIZE_WALLET` - Prize pool wallet address
  - `API_ENDPOINTS` - API endpoint constants
  - `TOAST_MESSAGES` - Consistent toast notifications
  - Responsive breakpoints and configuration

### `/src/hooks/`
React hooks for state management:

- **`usePrizePool.ts`** - Prize pool data fetching and state management
  - Token holdings tracking
  - Total value calculations
  - Helius API integration for wallet balance
- **`useCopyToClipboard.ts`** - **ENHANCED**: Copy-to-clipboard functionality:
  - `useCopyToClipboard()` - Single copy state management
  - `useMultipleCopyStates()` - Multiple copy states support (key-based)
  - Consistent toast messaging with flexible parameters

### `/src/types/`
TypeScript type definitions:

- **`index.ts`** - Core types:
  - `SubmissionSummary` - Basic submission data (`submission_id: number`)
  - `SubmissionDetail` - Extended submission with scores/research
  - `LeaderboardEntry` - Leaderboard-specific data structure
  - `Score` - Judge scoring data with round information
  - `Research` - GitHub analysis and market research data
  - `Stats` - Dashboard statistics
  - `CommunityScore` - Community voting metrics
  - `PrizePoolData` - Prize pool balance and contribution data
- **`submission.ts`** - Submission form input types

## Code Quality Improvements

### Recent Consolidation (2025)
- **Eliminated 240+ lines of code** through strategic refactoring
- **Consolidated 6+ files into 2** (PrizePool and Badge ecosystems)
- **Removed duplicate constants** (shotgun surgery anti-pattern)
- **Enhanced hook usage** with proper multiple state management
- **Standardized mobile detection** with consistent `isMobile()` approach
- **Unified badge system** with utility-based color management

### Anti-patterns Eliminated
- ✅ **Shotgun Surgery**: PRIZE_WALLET in multiple files → single source in constants.ts
- ✅ **Cargo Cult Programming**: Removed duplicate utilities and components
- ✅ **Feature Creep**: Unnecessary abstractions consolidated into practical solutions
- ✅ **Dead Code**: Eliminated unused utilities and components
- ✅ **Inconsistent Interface**: Standardized clipboard, mobile detection, and badge patterns
- ✅ **Logic Duplication**: Badge color logic centralized in utility functions

## Reusable Patterns

### Enhanced Copy-to-Clipboard Pattern
Using `useMultipleCopyStates` for multiple copy states:
```typescript
const { copyToClipboard, isCopied } = useMultipleCopyStates()

const handleCopyAddress = () => copyToClipboard(PRIZE_WALLET, 'address')
const handleCopyMemo = () => copyToClipboard(submissionId.toString(), 'memo', TOAST_MESSAGES.MEMO_COPIED)

// Usage in JSX
{isCopied('address') ? <CheckIcon /> : <CopyIcon />}
```

### Consolidated Component Pattern
PrizePool component with variant support:
```typescript
// Card variant (feature-rich)
<PrizePool variant="card" goal={10} />

// Banner variant (compact)
<PrizePool variant="banner" goal={10} />

// Legacy compatibility maintained
<PrizePoolCard /> // → <PrizePool variant="card" />
<PrizePoolBanner /> // → <PrizePool variant="banner" />
```

### Mobile Detection Pattern
Standardized approach using `isMobile()` function:
```typescript
import { isMobile } from '../utils/phantomLink'

const isOnMobile = isMobile()
if (isOnMobile) {
  // Mobile-specific logic
}
```

### Constants Pattern
Single source of truth in `constants.ts`:
```typescript
import { PRIZE_WALLET, TOAST_MESSAGES } from '../lib/constants'

copyToClipboard(PRIZE_WALLET, 'address', TOAST_MESSAGES.ADDRESS_COPIED)
```

### Unified Badge Pattern
Consolidated badge system with utility-based styling:
```typescript
import { Badge, StatusBadge, CategoryBadge } from '../components/Badge'

// Generic badge with variants
<Badge variant="success">Active</Badge>

// Specialized badges using utility functions
<StatusBadge status="completed" />
<CategoryBadge category="DeFi" />

// All color logic centralized in utils.ts:
// - getStatusColor(status) 
// - getCategoryColor(category)
```

## Styling Conventions

- **Tailwind CSS** for all styling
- **Dark mode** support with `dark:` variants
- **Brand colors** - Steel blue theme: `brand-dark`, `brand-mid`, `brand-accent`
- **Gradient backgrounds** for visual appeal
- **Responsive design** with mobile-first approach
- **Color system** based on project categories and statuses
- **Icon library** using Lucide React
- **Consistent spacing** using Tailwind's spacing scale

## Development Commands

```bash
# Development
npm install          # Install dependencies
npm run dev         # Start development server
npm run build       # Build for production
npm run lint        # Run ESLint (TypeScript)
npm run preview     # Preview production build

# Testing
npm run test        # Run test suite (if configured)
```

## Development Notes

- **React 18** with functional components and TypeScript
- **Vite** for fast development and building
- **State management** using React hooks (useState, useEffect, custom hooks)
- **API integration** centralized in `/src/lib/api.ts`
- **Type safety** enforced throughout with TypeScript
- **Environment variables** supported via Vite (`VITE_` prefix)
- **Static data generation** for production deployments
- **Responsive design** with mobile-first approach
- **Accessibility** considerations with ARIA attributes

## Architecture Philosophy

### Minimal Viable Abstractions
- Only abstract when 3+ use cases exist
- Prefer consolidation over multiple files
- Question abstractions: "Does this serve a purpose?"
- Maintain backward compatibility during refactoring

### Safety-First Refactoring
- Use trashcan folder for safe refactoring
- Comprehensive build testing after changes
- Maintain todo.md for tracking complex changes
- Progressive enhancement over breaking changes

### Single Source of Truth
- All constants in `constants.ts`
- One component per logical UI pattern
- Centralized API client configuration
- Consistent type definitions across app

This architecture establishes solid development discipline for maintainable, scalable frontend development.