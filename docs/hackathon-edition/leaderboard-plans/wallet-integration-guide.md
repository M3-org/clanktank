# Wallet Integration Implementation Guide

## Overview
This document outlines the requirements for implementing proper Solana wallet integration for the token voting system. The current implementation has placeholder components that need to be replaced with secure, production-ready wallet functionality.

## Current Status
- ✅ **Placeholder Components Created**: WalletVoting component with disabled UI
- ✅ **Backend Infrastructure Ready**: Webhook processing, vote aggregation, prize pool
- ✅ **API Endpoints Working**: Community scores, prize pool data
- 🔄 **Wallet Integration Needed**: Proper Solana transaction handling

## Implementation Requirements

### 1. Wallet-Adapter Setup

**Dependencies to Install:**
```bash
npm install @solana/web3.js \
    @solana/wallet-adapter-base \
    @solana/wallet-adapter-react \
    @solana/wallet-adapter-react-ui \
    @solana/wallet-adapter-wallets \
    @solana/spl-token
```

**Supported Wallets (Top 3):**
- PhantomWalletAdapter (most popular)
- SolflareWalletAdapter (desktop focus)
- BackpackWalletAdapter (growing ecosystem)

**Network Configuration:**
- Use Mainnet for ai16z tokens (HeLp6NuQkmYB4pYWo2zYs22mESHXPQYzXbB8n4V98jwC)
- Custom RPC endpoint recommended for better reliability
- Auto-connect enabled for better UX

### 2. Transaction Implementation

**Token Transfer Requirements:**
- ai16z token mint: `HeLp6NuQkmYB4pYWo2zYs22mESHXPQYzXbB8n4V98jwC`
- ai16z decimals: 5 (need to convert UI amount to smallest units)
- Voting wallet address: Environment variable `VITE_VOTING_WALLET_ADDRESS`
- Associated Token Account creation if needed

**Memo Program Integration:**
- Include submission ID in transaction memo for backend tracking
- Format: `vote:{submission_id}` (e.g., "vote:test-submission-1")
- Use SPL Memo Program for proper on-chain memo storage
- Required for Helius webhook to parse voting transactions

**Transaction Structure:**
```typescript
// 1. Create transfer instruction (ai16z tokens)
createTransferInstruction(
  userTokenAccount,     // From: User's ai16z ATA
  votingTokenAccount,   // To: Voting wallet's ai16z ATA  
  userPublicKey,        // Authority: User's wallet
  tokenAmountInSmallestUnits, // Amount: tokens * 10^5
  [],                   // Multisig signers (none)
  TOKEN_PROGRAM_ID      // Program ID
)

// 2. Add memo instruction for tracking
memoInstruction(
  `vote:${submissionId}`,  // Memo text
  [userPublicKey]          // Signers
)
```

### 3. Error Handling & UX

**Transaction States:**
- `idle` - Ready to vote
- `connecting` - Wallet connection in progress
- `preparing` - Building transaction
- `signing` - Waiting for user signature
- `confirming` - Transaction submitted, waiting for confirmation
- `success` - Vote recorded successfully
- `error` - Transaction failed

**Error Scenarios to Handle:**
- Wallet not connected
- Insufficient ai16z tokens
- Network/RPC errors
- Transaction timeout
- User rejection of signature
- Associated Token Account not found (create if needed)
- Slippage/fee estimation issues

**User Feedback:**
- Clear loading states with progress indicators
- Estimated transaction fees displayed
- Success confirmation with transaction signature link
- Error messages with actionable next steps
- Token balance validation before transaction

### 4. Security Best Practices

**Input Validation:**
- Validate token amounts (1-250 range)
- Sanitize submission IDs
- Verify wallet addresses format
- Check minimum SOL balance for transaction fees

**Transaction Safety:**
- Never store private keys
- Always verify transaction before signing
- Use recent blockhash for transaction freshness
- Implement proper timeout handling
- Validate recipient addresses

**Rate Limiting:**
- Frontend: Prevent multiple simultaneous transactions
- Backend: Webhook deduplication via transaction signature
- User feedback: Show cooldown periods if needed

### 5. Integration Points

**Backend Webhook Processing:**
The existing Helius webhook at `/webhook/helius` expects:
```json
{
  "signature": "transaction_signature",
  "tokenTransfers": [{
    "mint": "HeLp6NuQkmYB4pYWo2zYs22mESHXPQYzXbB8n4V98jwC",
    "memo": "vote:submission-id-here", 
    "fromUserAccount": "voter_wallet_address",
    "tokenAmount": 25.0
  }]
}
```

**Vote Weight Calculation:**
Frontend should show real-time preview but backend does final calculation:
```python
def calculate_vote_weight(token_amount):
    max_vote_tokens = 100
    voting_tokens = min(token_amount, max_vote_tokens)
    return min(math.log10(voting_tokens + 1) * 3, 10)
```

**Prize Pool Overflow:**
- Tokens > 100 automatically go to prize pool
- Frontend should preview this split
- Backend processes overflow in webhook handler

### 6. Testing Strategy

**Development Testing:**
- Use devnet for initial testing
- Test with small token amounts first
- Verify memo parsing in backend logs
- Test wallet connection/disconnection flows

**Production Validation:**
- Test with real ai16z tokens on mainnet
- Verify Helius webhook receives transactions
- Confirm vote weight calculations match
- Test overflow mechanism with 100+ token amounts
- Validate leaderboard updates after voting

**Cross-Wallet Testing:**
- Test on Phantom mobile and desktop
- Verify Solflare compatibility
- Check Backpack integration
- Test wallet switching scenarios

### 7. Environment Configuration

**Required Environment Variables:**
```env
# Frontend (.env)
VITE_VOTING_WALLET_ADDRESS=<voting_wallet_public_key>
VITE_SOLANA_RPC_URL=<custom_rpc_endpoint> # Optional
VITE_SOLANA_NETWORK=mainnet-beta

# Backend (if needed)
VOTING_WALLET_PRIVATE_KEY=<for_transaction_processing> # If backend signs
HELIUS_API_KEY=<for_webhook_processing>
```

**Security Notes:**
- Never expose private keys in frontend code
- Use environment variables for all addresses
- Consider using read-only wallet for voting address display

### 8. Implementation Checklist

**Phase 1: Basic Wallet Connection**
- [ ] Install wallet-adapter dependencies
- [ ] Configure SolanaProvider with top 3 wallets
- [ ] Add WalletMultiButton to voting interface
- [ ] Test wallet connection/disconnection

**Phase 2: Token Transfer Implementation**
- [ ] Implement ai16z token transfer logic
- [ ] Add SPL memo program for submission tracking
- [ ] Handle Associated Token Account creation
- [ ] Add transaction fee estimation

**Phase 3: Error Handling & UX**
- [ ] Implement all transaction states
- [ ] Add loading indicators and error messages
- [ ] Validate user token balances
- [ ] Add transaction confirmation links

**Phase 4: Integration Testing**
- [ ] Test with backend webhook processing
- [ ] Verify vote weight calculations
- [ ] Test overflow mechanism
- [ ] Validate leaderboard updates

**Phase 5: Production Deployment**
- [ ] Switch to mainnet configuration
- [ ] Test with real ai16z tokens
- [ ] Monitor Helius webhook logs
- [ ] Verify end-to-end voting flow

## Implementation Timeline

**Estimated Development Time: 2-3 days**

**Day 1: Wallet Setup & Basic Transactions**
- Wallet-adapter configuration
- Basic token transfer implementation
- Local testing with devnet

**Day 2: Error Handling & UX Polish**
- Comprehensive error handling
- Transaction state management  
- User feedback improvements

**Day 3: Integration & Testing**
- Backend webhook integration
- Cross-wallet testing
- Production deployment preparation

## Resources & References

**Documentation:**
- [Solana Wallet-Adapter Docs](https://github.com/anza-xyz/wallet-adapter)
- [SPL Token Program](https://spl.solana.com/token)
- [Solana Web3.js Guide](https://docs.solana.com/developing/clients/javascript-api)

**Example Implementations:**
- [Solana Cookbook - Wallet Integration](https://solanacookbook.com/guides/get-started.html#connecting-to-wallets)
- [SPL Token Transfer Example](https://github.com/solana-labs/solana-program-library/tree/master/token/js/examples)

**Testing Tools:**
- [Solana Explorer](https://explorer.solana.com/) - Transaction verification
- [Sol-faucet](https://solfaucet.com/) - Devnet SOL for testing
- [Phantom Developer Tools](https://docs.phantom.app/developer-powertools/developer-tools)

## Success Criteria

- ✅ Users can connect Phantom, Solflare, or Backpack wallets
- ✅ Token transfers work with proper memo tracking
- ✅ Vote weights calculate correctly with overflow to prize pool
- ✅ Transactions appear in backend within 10 seconds
- ✅ Leaderboard updates show new community scores
- ✅ Error handling provides clear user guidance
- ✅ Mobile and desktop voting flows work smoothly