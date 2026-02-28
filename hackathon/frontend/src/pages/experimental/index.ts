// Experimental pages - DO NOT import to main application
// This folder contains UI prototypes, archived versions, and experimental features
// that should remain isolated from production code

// Export nothing to prevent accidental imports
export {}

/*
Available experimental pages (development only):
- LeaderboardV1.tsx - Archived original leaderboard (full voting interface)
- LeaderboardV2.tsx - Enhanced prototype with side-by-side tables (not used - dropped approach)
- VotingPrototypes.tsx - Voting UI experiments and wallet integration tests
- Templates.tsx - Real-time URL state management with form templates

Routing (see App.tsx):
- /experimental/leaderboard-v1
- /experimental/leaderboard-v2
- /experimental/voting-prototypes  
- /experimental/templates

Guidelines:
- Self-contained components (relative imports only: ../../lib, ../../hooks)
- No imports from experimental to production code
- Development environment access only (import.meta.env.DEV)
*/