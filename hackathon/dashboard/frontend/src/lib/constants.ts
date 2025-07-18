// Prize Pool Constants
export const PRIZE_WALLET = "2K1reedtyDUQigdaLoHLEyugkH88iVGNE2BQemiGx6xf"
export const AI16Z_MINT = "HeLp6NuQkmYB4pYWo2zYs22mESHXPQYzXbB8n4V98jwC"

// Default Settings
export const DEFAULT_GOAL_SOL = 10
export const PRIZE_POOL_REFRESH_INTERVAL = 2 * 60 * 1000 // 2 minutes

// API Endpoints
export const API_ENDPOINTS = {
  PRIZE_POOL: '/api/prize-pool',
  SUBMISSIONS: '/api/submissions',
  LEADERBOARD: '/api/leaderboard',
  STATS: '/api/stats'
} as const

// Responsive Breakpoints
export const BREAKPOINTS = {
  SM: '(max-width: 640px)',
  MD: '(max-width: 768px)',
  LG: '(max-width: 1024px)',
  XL: '(max-width: 1280px)'
} as const

// Toast Messages
export const TOAST_MESSAGES = {
  ADDRESS_COPIED: 'Address copied!',
  MEMO_COPIED: 'Memo copied!',
  COPY_FAILED: 'Copy failed',
  VOTE_SUCCESS: 'Vote submitted successfully!',
  VOTE_FAILED: 'Vote submission failed'
} as const