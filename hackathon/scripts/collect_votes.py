#!/usr/bin/env python3
"""
Community Vote Collection and Analysis Tool

This script handles:
1. Collecting votes from Solana blockchain via Helius API
2. Processing and storing votes in the database
3. Calculating community scores
4. Displaying voting statistics

Usage Examples:
  python collect_votes.py --test                    # Test Helius API connection
  python collect_votes.py --collect                 # Collect new votes from blockchain
  python collect_votes.py --scores                  # Show community scores
  python collect_votes.py --stats                   # Show voting statistics
  python collect_votes.py --collect --scores        # Collect votes and show scores
"""

import os
import time
import sqlite3
import logging
import asyncio
import aiohttp
import argparse
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import re
import math
import base58
from dotenv import load_dotenv

# Load environment variables from repo root
repo_root = Path(__file__).parent.parent.parent
load_dotenv(repo_root / ".env")

# Constants
PRIZE_WALLET = "2K1reedtyDUQigdaLoHLEyugkH88iVGNE2BQemiGx6xf"
AI16Z_MINT = "HeLp6NuQkmYB4pYWo2zYs22mESHXPQYzXbB8n4V98jwC"
HELIUS_BASE_URL = "https://api.helius.xyz/v0"
DEFAULT_DB_PATH = repo_root / "data" / "hackathon.db"
HOLDERS_CSV_PATH = repo_root / "data" / "holders.csv"
MEMO_PROGRAM_ID = "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"

# Setup logging
def setup_logging(verbose=False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()]
    )
    return logging.getLogger(__name__)

@dataclass
class CommunityVote:
    """Represents a community vote transaction."""
    submission_id: str
    transaction_signature: str
    sender_address: str
    memo: str
    amount: int  # in lamports
    timestamp: int

class TokenHolderRegistry:
    """Manages token holder data and quadratic funding weights."""
    
    def __init__(self, holders_csv_path: str = None):
        self.holders_csv_path = holders_csv_path or str(HOLDERS_CSV_PATH)
        self.holders = {}  # address -> balance
        self.quadratic_weights = {}  # address -> sqrt(balance) weight
        self.logger = logging.getLogger(__name__)
        self._load_holders()
    
    def _load_holders(self):
        """Load token holders from CSV file."""
        try:
            with open(self.holders_csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    address = row['owner']
                    amount = float(row['amount'])
                    self.holders[address] = amount
                    # Quadratic funding: weight = sqrt(amount)
                    self.quadratic_weights[address] = math.sqrt(amount)
            
            self.logger.info(f"Loaded {len(self.holders)} token holders from {self.holders_csv_path}")
        except Exception as e:
            self.logger.error(f"Failed to load holders data: {e}")
            self.holders = {}
            self.quadratic_weights = {}
    
    def is_token_holder(self, address: str) -> bool:
        """Check if address is a known token holder."""
        return address in self.holders
    
    def get_quadratic_weight(self, address: str) -> float:
        """Get quadratic funding weight for an address."""
        return self.quadratic_weights.get(address, 0.0)
    
    def get_balance(self, address: str) -> float:
        """Get token balance for an address."""
        return self.holders.get(address, 0.0)
    
    def get_voting_power_info(self, address: str) -> Dict[str, Any]:
        """Get comprehensive voting power info for an address."""
        balance = self.get_balance(address)
        weight = self.get_quadratic_weight(address)
        
        return {
            'is_holder': self.is_token_holder(address),
            'balance': balance,
            'quadratic_weight': weight,
            'voting_power_multiplier': weight / math.sqrt(1.0) if weight > 0 else 0.0  # relative to 1 token
        }

class HeliusClient:
    """Client for Helius Enhanced Transactions API."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('HELIUS_API_KEY')
        if not self.api_key:
            raise ValueError("HELIUS_API_KEY environment variable not set")
        
        self.base_url = HELIUS_BASE_URL
        self.prize_wallet = PRIZE_WALLET
        self.logger = logging.getLogger(__name__)
    
    async def get_enhanced_transactions(self, signatures: List[str]) -> List[Dict[str, Any]]:
        """Batch-decode raw transactions → enhanced form."""
        url = f"{self.base_url}/transactions?api-key={self.api_key}"
        
        payload = {
            "transactions": signatures  # ✅ Reverted to correct field name
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=25) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    error_text = await response.text()
                    self.logger.error(f"Helius API error {response.status}: {error_text}")
                    return []
    
    async def stream_wallet_transfers(self, since_unix: int = None, page_size: int = 100) -> List[Dict[str, Any]]:
        """Stream decoded transfers into the prize wallet with cursor pagination."""
        url_root = f"{self.base_url}/addresses/{self.prize_wallet}/transactions"
        params = f"limit={min(page_size, 100)}"  # Remove type=TRANSFER to get all transactions
        before = ""  # signature cursor
        all_txs = []

        while True:
            url = f"{url_root}?api-key={self.api_key}&{params}"
            if before:
                url += f"&before={before}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=25) as response:
                    if response.status != 200:
                        self.logger.error(f"Helius API {response.status}: {await response.text()}")
                        break
                    page = await response.json()

            if not page:
                break

            for tx in page:
                # Stop once we're past our time window
                if since_unix and tx.get("timestamp", 0) < since_unix:
                    return all_txs
                all_txs.append(tx)

            # Cursor for next page = last signature we just saw
            before = page[-1]["signature"]

            # Safety: don't fetch more than ~10k tx in one run
            if len(all_txs) > 10_000:
                break

        return all_txs

    async def get_enhanced_transactions_by_address(self, address: str, limit: int = 100, tx_type: str = None) -> List[Dict[str, Any]]:
        """Get enhanced transactions for an address using the direct API endpoint."""
        url = f"{self.base_url}/addresses/{address}/transactions?api-key={self.api_key}"
        
        params = {}
        if limit:
            params["limit"] = min(limit, 100)  # API max is 100
        if tx_type:
            params["type"] = tx_type
            
        # Add params to URL
        if params:
            param_str = "&".join([f"{k}={v}" for k, v in params.items()])
            url += f"&{param_str}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    error_text = await response.text()
                    self.logger.error(f"Helius enhanced transactions API error {response.status}: {error_text}")
                    return []

    async def get_signatures_for_address(self, address: str, limit: int = 100, before: str = None) -> List[Dict[str, Any]]:
        """Get transaction signatures for an address using Helius RPC."""
        url = f"https://mainnet.helius-rpc.com/?api-key={self.api_key}"
        
        params = {
            "commitment": "confirmed",
            "limit": limit
        }
        if before:
            params["before"] = before
            
        payload = {
            "jsonrpc": "2.0",
            "id": "get-signatures",
            "method": "getSignaturesForAddress",
            "params": [address, params]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'result' in data:
                        return data['result']
                    else:
                        self.logger.error(f"Helius RPC error: {data.get('error', 'Unknown error')}")
                        return []
                else:
                    error_text = await response.text()
                    self.logger.error(f"Helius RPC error {response.status}: {error_text}")
                    return []
    
    def extract_memo(self, tx: Dict[str, Any]) -> Optional[str]:
        """Extract memo from transaction (checks multiple possible formats)."""
        # Check various memo field formats
        
        # 1. Top-level memos array (new format)
        if (memos := tx.get("memos")):
            if isinstance(memos, list) and memos:
                return memos[0].strip()
        
        # 2. Top-level memo field (simple format)
        if memo := tx.get("memo"):
            return memo.strip()
            
        # 3. Check in description field (sometimes memos appear here)
        if desc := tx.get("description"):
            # Look for memo pattern in description
            import re
            memo_match = re.search(r'memo[:\s]+"([^"]+)"', desc, re.IGNORECASE)
            if memo_match:
                return memo_match.group(1).strip()
        
        # 4. Fallback: instruction scan for memo program
        return self.extract_memo_from_transaction(tx)
    
    def extract_memo_from_transaction(self, tx_data: Dict[str, Any]) -> Optional[str]:
        """Extract memo from enhanced transaction data."""
        # Check top-level memo field
        if 'memo' in tx_data and tx_data['memo']:
            return tx_data['memo']
        
        # Check instructions for memo program calls
        instructions = tx_data.get('instructions', [])
        for instruction in instructions:
            # Memo program ID: MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr
            if instruction.get('programId') == MEMO_PROGRAM_ID:
                self.logger.info(f"🎯 Found memo program instruction!")
                memo_data = instruction.get('data', '')
                self.logger.info(f"Memo data: '{memo_data}'")
                if memo_data:
                    try:
                        # Method 1: Try base58 decoding
                        decoded_bytes = base58.b58decode(memo_data)
                        memo_text = decoded_bytes.decode('utf-8')
                        self.logger.info(f"✅ Base58 decoded memo: '{memo_text}'")
                        return memo_text.strip()
                    except Exception as e:
                        self.logger.info(f"❌ Base58 decode failed: {e}")
                        try:
                            # Method 2: Try as plain text
                            memo_text = memo_data.strip()
                            self.logger.info(f"✅ Plain text memo: '{memo_text}'")
                            return memo_text
                        except Exception as e2:
                            self.logger.info(f"❌ Plain text also failed: {e2}")
                            pass
            
            # Also check for memo in parsed data field (sometimes Helius parses it)
            if 'parsed' in instruction:
                parsed = instruction['parsed']
                if isinstance(parsed, dict) and 'info' in parsed:
                    info = parsed['info']
                    if 'memo' in info:
                        return info['memo'].strip()
        
        return None
    
    def extract_token_transfer_amount(self, tx_data: Dict[str, Any]) -> int:
        """Extract ai16z token transfer amount from transaction."""
        ai16z_mint = AI16Z_MINT
        
        # Check token transfers
        token_transfers = tx_data.get('tokenTransfers', [])
        for transfer in token_transfers:
            if (transfer.get('mint') == ai16z_mint and 
                transfer.get('toUserAccount') == self.prize_wallet):
                return transfer.get('tokenAmount', 0)
        
        # Check native transfers (SOL)
        native_transfers = tx_data.get('nativeTransfers', [])
        for transfer in native_transfers:
            if transfer.get('toUserAccount') == self.prize_wallet:
                return transfer.get('amount', 0)
        
        return 0
    
    def is_voting_transaction(self, tx_data: Dict[str, Any]) -> bool:
        """Check if transaction is a voting transaction to prize wallet."""
        token_transfers = tx_data.get('tokenTransfers', [])
        native_transfers = tx_data.get('nativeTransfers', [])
        
        for transfer in token_transfers:
            if transfer.get('toUserAccount') == self.prize_wallet:
                return True
        
        for transfer in native_transfers:
            if transfer.get('toUserAccount') == self.prize_wallet:
                return True
        
        return False
    
    def extract_sender(self, tx: Dict[str, Any]) -> Optional[str]:
        """Extract sender address (transfers array is more reliable)."""
        # Check transfers first - more reliable
        for t in tx.get("tokenTransfers", []) + tx.get("nativeTransfers", []):
            if t.get("toUserAccount") == self.prize_wallet:
                return t.get("fromUserAccount")
        # Fallback to feePayer
        return tx.get("feePayer")

    
    def is_submission_id_memo(self, memo: str) -> bool:
        """Check if memo looks like a submission ID."""
        if not memo or len(memo) < 5 or len(memo) > 80:
            return False
        
        # Allow alphanumeric, dashes, underscores
        if re.match(r'^[a-zA-Z0-9_-]+$', memo.strip()):
            return True
        
        return False
    
    
    async def find_ata_address(self, wallet: str, mint: str) -> str:
        """Find Associated Token Account address using RPC"""
        rpc_url = f"https://mainnet.helius-rpc.com/?api-key={self.api_key}"
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenAccountsByOwner",
            "params": [
                wallet,
                {"mint": mint},
                {"encoding": "jsonParsed"}
            ]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(rpc_url, json=payload) as response:
                result = await response.json()
                accounts = result.get("result", {}).get("value", [])
                if accounts:
                    return accounts[0]["pubkey"]
        
        return None
    
    async def detect_voting_transactions(self, since_timestamp: int = None, holders_registry=None) -> List[CommunityVote]:
        """Detect voting transactions by scanning recent transactions."""
        votes = []
        ai16z_mint = AI16Z_MINT
        
        try:
            # First, try to find the ATA address
            ata_address = await self.find_ata_address(self.prize_wallet, ai16z_mint)
            
            if ata_address:
                self.logger.info(f"Found ATA address: {ata_address}")
                # Query the ATA address instead of wallet
                url = f"{self.base_url}/addresses/{ata_address}/transactions"
            else:
                # Fallback to wallet address
                self.logger.info(f"Could not find ATA, using wallet address")
                url = f"{self.base_url}/addresses/{self.prize_wallet}/transactions"
            params = {
                "api-key": self.api_key,
                "limit": 100
            }
            
            param_str = "&".join([f"{k}={v}" for k, v in params.items()])
            full_url = f"{url}?{param_str}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(full_url) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"Failed to fetch transactions: {response.status} - {error_text}")
                        return votes
                    
                    all_transactions = await response.json()
                    self.logger.info(f"Found {len(all_transactions)} total transactions")
                    
                    # Filter for ai16z transfers
                    ai16z_transfers = []
                    for tx in all_transactions:
                        token_transfers = tx.get('tokenTransfers', [])
                        for transfer in token_transfers:
                            if (transfer.get('mint') == ai16z_mint and 
                                transfer.get('toUserAccount') == self.prize_wallet):
                                ai16z_transfers.append(tx)
                                break
                    
                    self.logger.info(f"Found {len(ai16z_transfers)} ai16z transfers")
                    
                    # Process ai16z transfers
                    for tx in ai16z_transfers:
                        if not tx:
                            continue
                        
                        # Skip old transactions if since_timestamp provided
                        if since_timestamp and tx.get("timestamp", 0) < since_timestamp:
                            continue
                        
                        memo = self.extract_memo(tx)
                        
                        self.logger.info(f"Found memo: '{memo}' in transfer {tx.get('signature', 'unknown')[:20]}...")
                        if not (memo and self.is_submission_id_memo(memo)):
                            self.logger.info(f"Memo '{memo}' doesn't match submission ID pattern")
                            continue
                        
                        sender = self.extract_sender(tx)
                        amount = self.extract_token_transfer_amount(tx)
                        
                        if not (sender and amount):
                            self.logger.info(f"Skipping tx - no sender ({sender}) or amount ({amount})")
                            continue
                        
                        # Optional: Filter to token holders only
                        if holders_registry and not holders_registry.is_token_holder(sender):
                            self.logger.debug(f"Skip non-holder {sender[:8]}...")
                            continue
                        
                        vote = CommunityVote(
                            submission_id=memo,
                            transaction_signature=tx["signature"],
                            sender_address=sender,
                            memo=memo,
                            amount=amount,
                            timestamp=tx.get("timestamp", int(time.time()))
                        )
                        votes.append(vote)
                        self.logger.info(f"✓ vote {memo} {amount/1_000_000:.6f} → {sender[:8]}…")
            
        except Exception as e:
            self.logger.error(f"Error detecting voting transactions: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
        
        return votes
    
    async def detect_voting_transactions_fallback(self, since_timestamp: int = None, holders_registry=None) -> List[CommunityVote]:
        """Fallback method using the old approach if token transfer search fails."""
        self.logger.info("Using fallback method for transaction detection")
        votes = []
        
        try:
            # Get transaction signatures first
            signatures = await self.get_signatures_for_address(self.prize_wallet, limit=50)
            
            if not signatures:
                self.logger.warning("No transaction signatures found")
                return votes
                
            self.logger.info(f"Found {len(signatures)} transaction signatures")
            
            # Get enhanced transaction data for each signature
            sig_list = [sig['signature'] for sig in signatures]
            
            # Process in batches to avoid API limits
            batch_size = 10
            for i in range(0, len(sig_list), batch_size):
                batch = sig_list[i:i+batch_size]
                enhanced_txs = await self.get_enhanced_transactions(batch)
                
                if not enhanced_txs:
                    continue
                
                for tx in enhanced_txs:
                    if not tx or not self.is_voting_transaction(tx):
                        continue
                    
                    memo = self.extract_memo(tx)
                    if not (memo and self.is_submission_id_memo(memo)):
                        continue
                    
                    sender = self.extract_sender(tx)
                    amount = self.extract_token_transfer_amount(tx)
                    if not (sender and amount):
                        continue
                    
                    if holders_registry and not holders_registry.is_token_holder(sender):
                        continue
                    
                    vote = CommunityVote(
                        submission_id=memo.strip(),
                        transaction_signature=tx["signature"],
                        sender_address=sender,
                        memo=memo,
                        amount=amount,
                        timestamp=tx.get("timestamp", int(time.time()))
                    )
                    votes.append(vote)
                    self.logger.info(f"✓ vote {memo} {amount/1_000_000:.6f} → {sender[:8]}…")
            
        except Exception as e:
            self.logger.error(f"Error in fallback method: {e}")
        
        return votes

class VoteProcessor:
    """Processes and stores community votes."""
    
    def __init__(self, db_path: str = None, holders_registry: TokenHolderRegistry = None):
        self.db_path = db_path or os.getenv("HACKATHON_DB_PATH", str(DEFAULT_DB_PATH))
        self.holders_registry = holders_registry or TokenHolderRegistry()
        self.logger = logging.getLogger(__name__)
    
    def get_db_connection(self):
        """Get database connection."""
        return sqlite3.connect(self.db_path, timeout=30.0)
    
    def save_votes(self, votes: List[CommunityVote]) -> int:
        """Save votes to database, returns number of new votes saved."""
        if not votes:
            return 0
        
        saved_count = 0
        
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            
            for vote in votes:
                try:
                    # Check if submission exists
                    cursor.execute("""
                        SELECT submission_id FROM hackathon_submissions_v2 
                        WHERE submission_id = ?
                    """, (vote.submission_id,))
                    
                    if not cursor.fetchone():
                        self.logger.warning(f"Submission not found: {vote.submission_id}")
                        continue
                    
                    # Insert vote (ignore if duplicate signature)
                    cursor.execute("""
                        INSERT OR IGNORE INTO community_votes 
                        (submission_id, transaction_signature, sender_address, memo, amount, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        vote.submission_id,
                        vote.transaction_signature,
                        vote.sender_address,
                        vote.memo,
                        vote.amount,
                        vote.timestamp
                    ))
                    
                    if cursor.rowcount > 0:
                        saved_count += 1
                        self.logger.info(f"Saved vote: {vote.submission_id} from {vote.sender_address[:8]}...")
                
                except Exception as e:
                    self.logger.error(f"Error saving vote {vote.transaction_signature}: {e}")
            
            conn.commit()
        
        return saved_count
    
    def get_community_scores(self) -> dict:
        """Calculate community scores using quadratic funding weights."""
        scores = {}
        
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    submission_id,
                    sender_address,
                    amount,
                    timestamp
                FROM community_votes
                ORDER BY submission_id, timestamp
            """)
            
            # Group votes by submission
            submission_votes = {}
            for row in cursor.fetchall():
                submission_id, sender_address, amount, timestamp = row
                if submission_id not in submission_votes:
                    submission_votes[submission_id] = []
                submission_votes[submission_id].append({
                    'sender': sender_address,
                    'amount': amount,
                    'timestamp': timestamp
                })
            
            # Calculate quadratic funding scores for each submission
            for submission_id, votes in submission_votes.items():
                total_quadratic_weight = 0.0
                unique_holders = set()
                total_votes = len(votes)
                total_amount = 0
                last_vote_time = 0
                
                for vote in votes:
                    sender = vote['sender']
                    amount = vote['amount']
                    timestamp = vote['timestamp']
                    
                    total_amount += amount
                    last_vote_time = max(last_vote_time, timestamp)
                    
                    # Only count votes from token holders
                    if self.holders_registry.is_token_holder(sender):
                        unique_holders.add(sender)
                        # Get quadratic weight based on token holdings
                        quadratic_weight = self.holders_registry.get_quadratic_weight(sender)
                        total_quadratic_weight += quadratic_weight
                        
                        self.logger.debug(f"Vote from {sender[:8]}...: balance={self.holders_registry.get_balance(sender):.2f}, weight={quadratic_weight:.2f}")
                    else:
                        self.logger.debug(f"Vote from non-holder {sender[:8]}... ignored")
                
                # Calculate final community score
                # Base score is sum of quadratic weights from token holders
                quadratic_score = total_quadratic_weight
                
                # Apply scaling to keep scores reasonable (0-10 range)
                # Use log scaling to prevent extreme values
                if quadratic_score > 0:
                    community_score = min(math.log10(quadratic_score + 1) * 2, 10)
                else:
                    community_score = 0
                
                scores[submission_id] = {
                    'community_score': community_score,
                    'quadratic_weight': total_quadratic_weight,
                    'vote_count': total_votes,
                    'unique_voters': len(unique_holders),
                    'holder_voters': len(unique_holders),
                    'total_amount': total_amount,
                    'avg_amount': total_amount / total_votes if total_votes > 0 else 0,
                    'last_vote_time': last_vote_time
                }
        
        return scores
    
    def get_vote_stats(self) -> dict:
        """Get overall voting statistics."""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_votes,
                    COUNT(DISTINCT sender_address) as unique_voters,
                    COUNT(DISTINCT submission_id) as submissions_with_votes,
                    SUM(amount) as total_amount,
                    MIN(timestamp) as first_vote_time,
                    MAX(timestamp) as last_vote_time
                FROM community_votes
            """)
            
            row = cursor.fetchone()
            if row:
                return {
                    'total_votes': row[0],
                    'unique_voters': row[1],
                    'submissions_with_votes': row[2],
                    'total_amount': row[3] or 0,
                    'first_vote_time': row[4],
                    'last_vote_time': row[5]
                }
        
        return {}

async def main():
    """Main function to handle all vote collection and analysis."""
    parser = argparse.ArgumentParser(
        description="Community Vote Collection and Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python collect_votes.py --test                    # Test Helius API connection
  python collect_votes.py --collect                 # Collect new votes from blockchain
  python collect_votes.py --scores                  # Show community scores
  python collect_votes.py --stats                   # Show voting statistics
  python collect_votes.py --collect --scores        # Collect votes and show scores
  python collect_votes.py --debug-tx TX_SIGNATURE   # Debug specific transaction
  python collect_votes.py --process-tx TX_SIGNATURE # Process and save specific transaction
        """
    )
    
    parser.add_argument("--test", action="store_true", help="Test Helius API connection")
    parser.add_argument("--collect", action="store_true", help="Collect new votes from blockchain")
    parser.add_argument("--scores", action="store_true", help="Calculate and display community scores")
    parser.add_argument("--stats", action="store_true", help="Display voting statistics")
    parser.add_argument("--debug-tx", help="Debug specific transaction signature")
    parser.add_argument("--process-tx", help="Process and save specific transaction if valid")
    parser.add_argument("--since", type=int, help="Check for votes since timestamp (unix time)")
    parser.add_argument("--db-path", help="Path to database file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.verbose)
    
    if not any([args.test, args.collect, args.scores, args.stats, args.debug_tx, args.process_tx]):
        parser.print_help()
        return
    
    try:
        # Initialize processor (always needed)
        processor = VoteProcessor(db_path=args.db_path)
        
        # Initialize Helius client if needed
        helius_client = None
        if args.test or args.collect or args.debug_tx or args.process_tx:
            try:
                helius_client = HeliusClient()
                logger.info("✅ Helius client initialized")
            except ValueError as e:
                if "HELIUS_API_KEY" in str(e):
                    print("❌ HELIUS_API_KEY environment variable not set")
                    print("   Get your API key from https://helius.dev")
                    if not (args.scores or args.stats):
                        return
                else:
                    raise
        
        # Test Helius API connection
        if args.test and helius_client:
            print("🔍 Testing Helius API connection...")
            signatures = await helius_client.get_signatures_for_address(
                helius_client.prize_wallet, limit=5
            )
            print(f"✅ Successfully fetched {len(signatures)} recent signatures")
            
            if signatures:
                print("Recent transactions:")
                for i, sig in enumerate(signatures[:3]):
                    block_time = sig.get('blockTime')
                    time_str = datetime.fromtimestamp(block_time).strftime('%Y-%m-%d %H:%M:%S') if block_time else 'unknown'
                    print(f"  {i+1}. {sig['signature'][:20]}... ({time_str})")
        
        # Debug specific transaction
        if args.debug_tx and helius_client:
            print(f"🔍 Debugging transaction {args.debug_tx[:20]}...")
            try:
                # Get enhanced transaction data
                enhanced_txs = await helius_client.get_enhanced_transactions([args.debug_tx])
                
                if not enhanced_txs:
                    print(f"❌ No enhanced transaction data found for {args.debug_tx}")
                    return
                
                tx = enhanced_txs[0]
                print(f"✅ Transaction found!")
                print(f"   Description: {tx.get('description', 'No description')}")
                print(f"   Type: {tx.get('type', 'Unknown')}")
                print(f"   Fee Payer: {tx.get('feePayer', 'Unknown')}")
                print(f"   Instructions: {len(tx.get('instructions', []))}")
                
                # Check for memo
                memo = helius_client.extract_memo(tx)
                print(f"   Memo: '{memo}'")
                
                # Check if it's a voting transaction
                is_voting = helius_client.is_voting_transaction(tx)
                print(f"   Is voting transaction: {is_voting}")
                
                # Check sender and amount
                sender = helius_client.extract_sender(tx)
                amount = helius_client.extract_token_transfer_amount(tx)
                print(f"   Sender: {sender}")
                print(f"   Amount: {amount}")
                
                # Check if sender is token holder
                if sender and processor.holders_registry.is_token_holder(sender):
                    voting_info = processor.holders_registry.get_voting_power_info(sender)
                    print(f"   Token holder: ✅ Balance: {voting_info['balance']:.2f}, Weight: {voting_info['quadratic_weight']:.2f}")
                else:
                    print(f"   Token holder: ❌")
                
                # Show detailed instruction analysis
                print(f"\n📋 Instructions Analysis:")
                for i, instr in enumerate(tx.get('instructions', [])):
                    program_id = instr.get('programId', 'Unknown')
                    data = instr.get('data', 'No data')
                    print(f"   {i+1}. Program: {program_id}")
                    print(f"      Data: {data[:50]}{'...' if len(data) > 50 else ''}")
                    
                    # Special handling for memo program
                    if program_id == MEMO_PROGRAM_ID:
                        print(f"      🎯 MEMO PROGRAM FOUND!")
                        try:
                            decoded = base58.b58decode(data).decode('utf-8')
                            print(f"      💬 Decoded memo: '{decoded}'")
                        except:
                            print(f"      ❌ Failed to decode memo data")
                
            except Exception as e:
                print(f"❌ Error debugging transaction: {e}")
                import traceback
                traceback.print_exc()
        
        # Process and save specific transaction
        if args.process_tx and helius_client:
            print(f"🔄 Processing transaction {args.process_tx[:20]}...")
            try:
                # Get enhanced transaction data
                enhanced_txs = await helius_client.get_enhanced_transactions([args.process_tx])
                
                if not enhanced_txs:
                    print(f"❌ No enhanced transaction data found for {args.process_tx}")
                    return
                
                tx = enhanced_txs[0]
                print(f"✅ Transaction found: {tx.get('description', 'No description')}")
                
                # Extract transaction details
                memo = helius_client.extract_memo(tx)
                is_voting = helius_client.is_voting_transaction(tx)
                sender = helius_client.extract_sender(tx)
                amount = helius_client.extract_token_transfer_amount(tx)
                
                print(f"   Memo: '{memo}'")
                print(f"   Is voting: {is_voting}")
                print(f"   Sender: {sender}")
                print(f"   Amount: {amount}")
                
                # Validate transaction
                if not is_voting:
                    print("❌ Transaction is not a voting transaction (no transfer to prize wallet)")
                    return
                
                if not (memo and helius_client.is_submission_id_memo(memo)):
                    print(f"❌ Memo '{memo}' is not a valid submission ID")
                    return
                
                if not (sender and amount):
                    print("❌ Missing sender or amount data")
                    return
                
                # Check if sender is token holder
                if not processor.holders_registry.is_token_holder(sender):
                    print(f"❌ Sender {sender[:8]}... is not a token holder")
                    return
                
                # Create vote object
                vote = CommunityVote(
                    submission_id=memo.strip(),
                    transaction_signature=tx["signature"],
                    sender_address=sender,
                    memo=memo,
                    amount=amount,
                    timestamp=tx.get("timestamp", int(time.time()))
                )
                
                # Save to database
                saved_count = processor.save_votes([vote])
                
                if saved_count > 0:
                    voting_info = processor.holders_registry.get_voting_power_info(sender)
                    print(f"✅ Vote saved successfully!")
                    print(f"   Submission ID: {vote.submission_id}")
                    print(f"   Voter: {sender[:8]}... (Balance: {voting_info['balance']:.2f}, Weight: {voting_info['quadratic_weight']:.2f})")
                    print(f"   Amount: {amount/1_000_000:.6f} tokens")
                    print(f"   Transaction: {args.process_tx[:20]}...")
                else:
                    print(f"⚠️  Vote already exists in database")
                
            except Exception as e:
                print(f"❌ Error processing transaction: {e}")
                import traceback
                traceback.print_exc()
        
        # Collect new votes
        if args.collect and helius_client:
            print("🔍 Collecting votes from blockchain...")
            votes = await helius_client.detect_voting_transactions(
                since_timestamp=args.since, 
                holders_registry=processor.holders_registry
            )
            
            if votes:
                saved_count = processor.save_votes(votes)
                print(f"✅ Found {len(votes)} votes, saved {saved_count} new ones")
                
                if saved_count > 0:
                    print("New votes:")
                    for vote in votes:
                        voting_info = processor.holders_registry.get_voting_power_info(vote.sender_address)
                        weight = voting_info.get('quadratic_weight', 0)
                        print(f"  📝 {vote.submission_id}: {vote.amount/1_000_000:.6f} tokens from {vote.sender_address[:8]}... (weight: {weight:.2f})")
            else:
                print("No new votes found")
        
        # Show community scores
        if args.scores:
            print("\n📊 Community Scores:")
            scores = processor.get_community_scores()
            if scores:
                print(f"Found {len(scores)} submissions with votes:")
                for submission_id, data in sorted(scores.items(), key=lambda x: x[1]['community_score'], reverse=True):
                    print(f"  🏆 {submission_id}: {data['community_score']:.2f} points")
                    print(f"     👥 {data['unique_voters']} unique voters")
                    print(f"     🗳️  {data['vote_count']} total votes")
                    print(f"     💰 {data['total_amount']/1_000_000:.6f} tokens total")
                    print()
            else:
                print("  No votes found in database")
        
        # Show voting statistics
        if args.stats:
            print("\n📈 Voting Statistics:")
            stats = processor.get_vote_stats()
            if stats.get('total_votes', 0) > 0:
                print(f"  Total votes: {stats['total_votes']}")
                print(f"  Unique voters: {stats['unique_voters']}")
                print(f"  Submissions with votes: {stats['submissions_with_votes']}")
                print(f"  Total amount: {stats['total_amount']/1_000_000:.6f} tokens")
                if stats['first_vote_time']:
                    first_vote = datetime.fromtimestamp(stats['first_vote_time'])
                    last_vote = datetime.fromtimestamp(stats['last_vote_time'])
                    print(f"  First vote: {first_vote}")
                    print(f"  Last vote: {last_vote}")
            else:
                print("  No votes recorded yet")
                
    except Exception as e:
        logger.error(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())