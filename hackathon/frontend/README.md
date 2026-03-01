# Hackathon Dashboard Frontend

React + TypeScript + Vite. See [hackathon/README.md](../../../hackathon/README.md) for setup and run commands.

## Components (`/src/components/`)

- **`Button.tsx`** — variants: primary, secondary, ghost, discord, outline; sizes: sm, md, lg
- **`Badge.tsx`** — unified badge system: `Badge`, `StatusBadge`, `CategoryBadge`; color logic in `utils.ts`
- **`Card.tsx`** — base card container
- **`PrizePool.tsx`** — prize pool display; variants: `'card'` | `'banner'`
- **`LeaderboardCard.tsx`** — submission card for leaderboard
- **`VoteModal.tsx`** — community voting modal with clipboard support
- **`Header.tsx`** — app header + navigation
- **`ProtectedRoute.tsx`** — Discord auth gate
- **`SolanaProvider.tsx`** — Solana wallet context
- **`WalletVoting.tsx`** — wallet-based voting UI
- **`LikeDislike.tsx`** — like/dislike buttons
- **`DiscordAvatar.tsx`** — Discord user avatar
- **`CountdownTimer.tsx`** — deadline countdown
- **`SkeletonCard.tsx`** — loading skeleton

## Utilities (`/src/utils/`, `/src/lib/`, `/src/hooks/`)

- **`lib/api.ts`** — API client; REST endpoints, Discord OAuth, file upload, static data fallback
- **`lib/constants.ts`** — single source of truth: `PRIZE_WALLET`, `API_ENDPOINTS`, `TOAST_MESSAGES`
- **`lib/utils.ts`** — `cn()`, `getStatusColor()`, `getCategoryColor()`, `formatDate()`, `pretty()`
- **`utils/phantomLink.ts`** — Phantom wallet deep-links: `buildVotingLink()`, `isMobile()`, `validateMemo()`
- **`hooks/usePrizePool.ts`** — prize pool state + Helius API integration
- **`hooks/useCopyToClipboard.ts`** — `useCopyToClipboard()` / `useMultipleCopyStates()`

## Types (`/src/types/`)

- **`index.ts`** — `SubmissionSummary`, `SubmissionDetail`, `LeaderboardEntry`, `Score`, `Research`, `Stats`, `CommunityScore`, `PrizePoolData`
- **`submission.ts`** — form input types (auto-generated from backend schema via `npm run sync-schema`)

## Experimental pages (`/src/pages/experimental/`)

Dev-only (`import.meta.env.DEV`), self-contained, no production impact.

| Route | File | Status |
|---|---|---|
| `/experimental/leaderboard-v1` | `LeaderboardV1.tsx` | Archived |
| `/experimental/leaderboard-v2` | `LeaderboardV2.tsx` | Archived |
| `/experimental/voting-prototypes` | `VotingPrototypes.tsx` | Active |
| `/experimental/templates` | `Templates.tsx` | Active |

## Styling

Tailwind CSS, dark mode, brand colors (`brand-dark`, `brand-mid`, `brand-accent`), Lucide React icons.
