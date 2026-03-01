// Phantom wallet deep-link utilities for Solana transactions

import { PRIZE_WALLET } from '../lib/constants'

export const AI16Z_MINT = "HeLp6NuQkmYB4pYWo2zYs22mESHXPQYzXbB8n4V98jwC"

export interface VotingParams {
  submissionId: number
  amount: number // in ai16z tokens (not lamports)
}

export interface SponsorParams {
  amount: number // in SOL or ai16z
  memo?: string
  token?: 'SOL' | 'ai16z'
}

/**
 * Build Phantom deep-link for voting
 */
export const buildVotingLink = ({ submissionId, amount }: VotingParams): string => {
  return `https://phantom.app/ul/v1/transaction` +
    `?recipient=${PRIZE_WALLET}` +
    `&amount=${amount}` +
    `&spl-token=${AI16Z_MINT}` +
    `&memo=${submissionId}` +
    `&label=${encodeURIComponent('Clank Tank Vote')}`
}

/**
 * Build Phantom deep-link for sponsorship
 */
export const buildSponsorLink = ({ amount, memo = '', token = 'SOL' }: SponsorParams): string => {
  const sponsorMemo = memo.slice(0, 80) // Ensure memo stays under 80 chars
  const label = encodeURIComponent('Clank Tank Sponsor')
  
  if (token === 'SOL') {
    return `https://phantom.app/ul/v1/transaction` +
      `?recipient=${PRIZE_WALLET}` +
      `&amount=${amount}` +
      `&reference=${encodeURIComponent(sponsorMemo)}` +
      `&label=${label}`
  } else {
    return `https://phantom.app/ul/v1/transaction` +
      `?recipient=${PRIZE_WALLET}` +
      `&amount=${amount}` +
      `&spl-token=${AI16Z_MINT}` +
      `&reference=${encodeURIComponent(sponsorMemo)}` +
      `&label=${label}`
  }
}

/**
 * Generate copy-paste instructions
 */
export const generateCopyInstructions = ({ submissionId, amount }: VotingParams): string => {
  return `Send ${amount} ai16z to ${PRIZE_WALLET} with memo: ${submissionId}`
}

/**
 * Detect if user is on mobile device
 */
export const isMobile = (): boolean => {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
}

/**
 * Validate memo length (Phantom rejects > 80 chars)
 */
export const validateMemo = (memo: string): { valid: boolean; error?: string } => {
  if (memo.length > 80) {
    return { valid: false, error: `Memo too long (${memo.length}/80 characters)` }
  }
  return { valid: true }
}