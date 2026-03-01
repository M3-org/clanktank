"""Voting-related routes: token voting, prize pool, community scores, webhooks."""

import hmac
import logging
import os
import time

import aiohttp
import requests
from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from sqlalchemy import create_engine, text

from hackathon.backend.config import (
    HACKATHON_DB_PATH,
    calculate_vote_weight,
)
from hackathon.backend.websocket_service import prize_pool_service

router = APIRouter(tags=["voting"])

# Database engine (local to this module)
engine = create_engine(f"sqlite:///{HACKATHON_DB_PATH}")


def _is_production() -> bool:
    return os.getenv("ENVIRONMENT", "development").lower() == "production"


def _verify_webhook_auth(request: Request):
    """Verify shared-secret auth for webhook endpoints.

    Supported headers:
    - X-Helius-Webhook-Secret
    - X-Webhook-Secret
    - Authorization: Bearer <secret>
    """
    expected = os.getenv("HELIUS_WEBHOOK_SECRET", "").strip()

    if not expected:
        if _is_production():
            logging.error("HELIUS_WEBHOOK_SECRET is missing in production")
            raise HTTPException(status_code=500, detail="Webhook authentication is not configured")
        # In non-production, allow local testing without a shared secret.
        return

    provided = request.headers.get("X-Helius-Webhook-Secret") or request.headers.get("X-Webhook-Secret")
    if not provided:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            provided = auth.split(" ", 1)[1]

    if not provided or not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="Unauthorized webhook")


def _require_non_production_test_webhook():
    """Disable test webhook endpoint in production deployments."""
    if _is_production():
        raise HTTPException(status_code=404, detail="Not found")


class BirdeyePriceService:
    """Service for fetching token prices from Birdeye API."""

    def __init__(self):
        self.base_url = "https://public-api.birdeye.so/defi/multi_price"
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes

    def get_token_prices(self, mint_addresses: list) -> dict[str, float]:
        """Get current USD prices for multiple tokens"""
        cache_key = ",".join(sorted(mint_addresses))
        now = time.time()

        # Check cache
        if cache_key in self.cache and now - self.cache[cache_key]["timestamp"] < self.cache_ttl:
            return self.cache[cache_key]["prices"]

        # Fetch from Birdeye
        params = {"list_address": ",".join(mint_addresses), "ui_amount_mode": "raw"}
        headers = {"accept": "application/json", "x-chain": "solana"}

        try:
            response = requests.get(self.base_url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            prices = {}
            if data.get("success") and "data" in data:
                for mint, price_data in data["data"].items():
                    prices[mint] = price_data.get("value", 0)

            # Cache results
            self.cache[cache_key] = {"prices": prices, "timestamp": now}

            return prices

        except Exception as e:
            logging.error(f"Birdeye API error: {e}")
            return {mint: 0 for mint in mint_addresses}


# Global price service instance
price_service = BirdeyePriceService()


def get_db_connection():
    """Get database connection."""
    import sqlite3

    return sqlite3.connect(HACKATHON_DB_PATH)


async def get_recent_transactions_helius(wallet_address: str, helius_api_key: str, limit: int = 5):
    """Get recent transactions for wallet using Helius Enhanced Transactions API.

    NOTE: Helius RPC requires API key in URL (Solana RPC standard). This is server-side
    only and keys are never exposed to clients. Ensure access logs are secured.
    """
    import time

    try:
        # First get recent transaction signatures
        # SECURITY: API key in URL is required by Helius RPC - ensure logs don't expose keys
        helius_rpc_url = f"https://mainnet.helius-rpc.com/?api-key={helius_api_key}"

        async with aiohttp.ClientSession() as session:
            # Get recent transaction signatures
            rpc_payload = {
                "jsonrpc": "2.0",
                "id": "get-signatures",
                "method": "getSignaturesForAddress",
                "params": [
                    wallet_address,
                    {"limit": limit * 2},  # Get more to filter for incoming transfers
                ],
            }

            async with session.post(helius_rpc_url, json=rpc_payload) as resp:
                rpc_data = await resp.json()

            if "result" not in rpc_data or not rpc_data["result"]:
                return []

            # Extract transaction signatures
            signatures = [tx["signature"] for tx in rpc_data["result"][:limit]]

            if not signatures:
                return []

            # Get enhanced transaction data
            enhanced_url = f"https://api.helius.xyz/v0/transactions?api-key={helius_api_key}"
            enhanced_payload = {"transactions": signatures}

            async with session.post(enhanced_url, json=enhanced_payload) as resp:
                enhanced_data = await resp.json()

            # Process enhanced transactions into contributions
            contributions = []
            for tx in enhanced_data[:limit]:
                if not isinstance(tx, dict):
                    continue

                # Look for native (SOL) transfers TO our wallet
                if "nativeTransfers" in tx:
                    for transfer in tx["nativeTransfers"]:
                        if transfer.get("toUserAccount") == wallet_address:
                            contributions.append(
                                {
                                    "wallet": transfer.get("fromUserAccount", "Unknown")[:4]
                                    + "..."
                                    + transfer.get("fromUserAccount", "Unknown")[-4:]
                                    if transfer.get("fromUserAccount")
                                    else "Unknown",
                                    "token": "SOL",
                                    "amount": transfer.get("amount", 0) / 1_000_000_000,  # Convert lamports to SOL
                                    "timestamp": tx.get("timestamp", int(time.time())),
                                    "description": tx.get("description", "SOL transfer"),
                                }
                            )

                # Look for token transfers TO our wallet
                if "tokenTransfers" in tx:
                    for transfer in tx["tokenTransfers"]:
                        if transfer.get("toUserAccount") == wallet_address:
                            # Get token symbol from metadata or use mint short form
                            token_symbol = "Unknown"
                            if transfer.get("mint"):
                                # Try to get symbol from our token metadata cache
                                try:
                                    with engine.connect() as conn:
                                        result = conn.execute(
                                            text("SELECT symbol FROM token_metadata WHERE token_mint = :token_mint"),
                                            {"token_mint": transfer["mint"]},
                                        ).fetchone()
                                        token_symbol = result[0] if result else transfer["mint"][:8]
                                except Exception:
                                    token_symbol = transfer["mint"][:8]

                            contributions.append(
                                {
                                    "wallet": transfer.get("fromUserAccount", "Unknown")[:4]
                                    + "..."
                                    + transfer.get("fromUserAccount", "Unknown")[-4:]
                                    if transfer.get("fromUserAccount")
                                    else "Unknown",
                                    "token": token_symbol,
                                    "amount": transfer.get("tokenAmount", 0),
                                    "timestamp": tx.get("timestamp", int(time.time())),
                                    "description": tx.get("description", f"{token_symbol} transfer"),
                                }
                            )

            return contributions[:limit]  # Return only the requested number

    except Exception as e:
        logging.error(f"Error getting recent transactions: {e}")
        return []  # Return empty list on error to avoid breaking the API


def process_ai16z_transaction(tx_sig: str, submission_id: int, sender: str, amount: float):
    """Process ai16z token transaction for voting and prize pool."""
    try:
        # Calculate tokens used for voting vs overflow
        max_vote_tokens = float(os.getenv("MAX_VOTE_TOKENS", 100))
        vote_tokens = min(amount, max_vote_tokens)
        overflow_tokens = max(0, amount - max_vote_tokens)

        with engine.begin() as conn:
            # Record the vote in sol_votes table
            conn.execute(
                text("""
                    INSERT OR IGNORE INTO sol_votes
                    (tx_sig, submission_id, sender, amount, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """),
                (tx_sig, submission_id, sender, vote_tokens, int(time.time())),
            )

            # Record overflow as prize pool contribution
            if overflow_tokens > 0:
                conn.execute(
                    text("""
                        INSERT OR IGNORE INTO prize_pool_contributions
                        (tx_sig, token_mint, token_symbol, amount, contributor_wallet, source, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """),
                    (
                        f"{tx_sig}_overflow",  # Unique ID for overflow portion
                        "HeLp6NuQkmYB4pYWo2zYs22mESHXPQYzXbB8n4V98jwC",  # ai16z mint
                        "ai16z",
                        overflow_tokens,
                        sender,
                        "vote_overflow",
                        int(time.time()),
                    ),
                )
            # Transaction automatically commits on context exit
            logging.info(f"Processed vote: {vote_tokens} ai16z vote, {overflow_tokens} ai16z to prize pool")
            return True

    except Exception as e:
        logging.error(f"Transaction processing error: {e}")
        return False


@router.get("/api/test-voting")
async def test_voting():
    """Test endpoint to verify voting functionality works."""
    with engine.connect() as conn:
        # Simple test query
        result = conn.execute(text("SELECT COUNT(*) as count FROM sol_votes"))
        row = result.fetchone()
        return {"vote_count": row[0], "status": "working"}


@router.get("/api/community-scores")
async def get_community_scores():
    """Get community scores for all submissions based on token voting."""
    try:
        with engine.connect() as conn:
            # Get raw vote data grouped by wallet and submission
            result = conn.execute(
                text("""
                SELECT
                  submission_id,
                  sender,
                  SUM(amount) as total_tokens,
                  MAX(timestamp) as last_tx_time
                FROM sol_votes
                GROUP BY submission_id, sender
                """)
            )

            # Calculate vote weights in Python (inline to avoid scope issues)
            submission_scores = {}
            for row in result.fetchall():
                row_dict = dict(row._mapping)
                submission_id = row_dict["submission_id"]
                total_tokens = row_dict["total_tokens"]

                vote_weight = calculate_vote_weight(total_tokens)

                if submission_id not in submission_scores:
                    submission_scores[submission_id] = {"total_score": 0, "unique_voters": 0, "last_vote_time": 0}

                submission_scores[submission_id]["total_score"] += vote_weight
                submission_scores[submission_id]["unique_voters"] += 1
                submission_scores[submission_id]["last_vote_time"] = max(
                    submission_scores[submission_id]["last_vote_time"], row_dict["last_tx_time"]
                )

            # Format response
            scores = []
            for submission_id, data in submission_scores.items():
                scores.append(
                    {
                        "submission_id": submission_id,
                        "community_score": round(data["total_score"], 2),
                        "unique_voters": data["unique_voters"],
                        "last_vote_time": data["last_vote_time"],
                    }
                )

            return scores
    except Exception as e:
        logging.error(f"Error in community scores: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/prize-pool")
async def get_prize_pool():
    """Get crypto-native prize pool data using Helius DAS API."""
    try:
        helius_api_key = os.getenv("HELIUS_API_KEY")
        prize_wallet = os.getenv("PRIZE_WALLET_ADDRESS")
        if not prize_wallet:
            raise ValueError("PRIZE_WALLET_ADDRESS environment variable is required")
        target_sol = float(os.getenv("PRIZE_POOL_TARGET_SOL", 10))

        if not helius_api_key:
            raise HTTPException(status_code=500, detail="Helius API key not configured")

        helius_url = f"https://mainnet.helius-rpc.com/?api-key={helius_api_key}"

        # Fetch real-time token holdings from Helius DAS API
        payload = {
            "jsonrpc": "2.0",
            "id": "prize-pool-live",
            "method": "getAssetsByOwner",
            "params": {
                "ownerAddress": prize_wallet,
                "page": 1,
                "limit": 100,
                "sortBy": {"sortBy": "created", "sortDirection": "desc"},
                "options": {
                    "showUnverifiedCollections": False,
                    "showCollectionMetadata": False,
                    "showGrandTotal": False,
                    "showFungible": True,
                    "showNativeBalance": True,
                    "showInscription": False,
                    "showZeroBalance": False,
                },
            },
        }

        import json
        import time

        import requests

        response = requests.post(helius_url, json=payload)
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            raise HTTPException(status_code=500, detail=f"Helius API error: {data['error']}")

        if not data.get("result", {}).get("items"):
            # Return empty but valid structure
            return {
                "total_sol": 0,
                "target_sol": target_sol,
                "progress_percentage": 0,
                "token_breakdown": {},
                "recent_contributions": [],
            }

        # Process tokens
        token_breakdown = {}
        total_sol = 0

        def get_token_metadata_from_helius(mint_address):
            """Fetch token metadata from Helius DAS API and cache it"""
            try:
                # Check cache first (24 hour cache)
                with engine.connect() as conn:
                    result = conn.execute(
                        text(
                            "SELECT * FROM token_metadata WHERE token_mint = :token_mint AND last_updated > :min_time"
                        ),
                        {"token_mint": mint_address, "min_time": int(time.time()) - 86400},  # 24 hours
                    )
                    cached = result.fetchone()
                    if cached:
                        return {
                            "symbol": cached[2],
                            "name": cached[3],
                            "decimals": cached[4],
                            "logo": cached[6] or cached[5],  # prefer cdn_uri over logo_uri
                            "interface": cached[8],
                        }

                # Fetch from Helius DAS API
                payload = {
                    "jsonrpc": "2.0",
                    "id": f"token-metadata-{mint_address}",
                    "method": "getAsset",
                    "params": {"id": mint_address},
                }

                response = requests.post(helius_url, json=payload)
                response.raise_for_status()
                asset_data = response.json()

                if "error" in asset_data or not asset_data.get("result"):
                    return None

                asset = asset_data["result"]

                # Extract metadata
                symbol = None
                name = None
                decimals = 6  # Default for SPL tokens
                logo_uri = None
                cdn_uri = None
                json_uri = None
                interface_type = asset.get("interface", "Unknown")

                # Get symbol and name from token_info or content
                if asset.get("token_info"):
                    symbol = asset["token_info"].get("symbol")
                    decimals = asset["token_info"].get("decimals", 6)

                if asset.get("content"):
                    content = asset["content"]
                    if not symbol and content.get("metadata"):
                        symbol = content["metadata"].get("symbol")
                        name = content["metadata"].get("name")

                    json_uri = content.get("json_uri")

                    # Get image URLs
                    if content.get("files") and len(content["files"]) > 0:
                        first_file = content["files"][0]
                        logo_uri = first_file.get("uri")
                        cdn_uri = first_file.get("cdn_uri")

                # Cache the metadata
                with engine.begin() as conn:
                    conn.execute(
                        text("""
                            INSERT OR REPLACE INTO token_metadata
                            (token_mint, symbol, name, decimals, logo_uri, cdn_uri, json_uri, interface_type, content_metadata, last_updated)
                            VALUES (:token_mint, :symbol, :name, :decimals, :logo_uri, :cdn_uri, :json_uri, :interface_type, :content_metadata, :last_updated)
                        """),
                        {
                            "token_mint": mint_address,
                            "symbol": symbol,
                            "name": name,
                            "decimals": decimals,
                            "logo_uri": logo_uri,
                            "cdn_uri": cdn_uri,
                            "json_uri": json_uri,
                            "interface_type": interface_type,
                            "content_metadata": json.dumps(asset.get("content", {})),
                            "last_updated": int(time.time()),
                        },
                    )

                return {
                    "symbol": symbol,
                    "name": name,
                    "decimals": decimals,
                    "logo": cdn_uri or logo_uri,  # prefer CDN
                    "interface": interface_type,
                }

            except Exception as e:
                logging.error(f"Error fetching token metadata for {mint_address}: {e}")
                return None

        # Process native SOL balance (special case - always has consistent metadata)
        native_balance = data["result"].get("nativeBalance", {})
        if native_balance and native_balance.get("lamports", 0) > 0:
            sol_amount = native_balance["lamports"] / 1_000_000_000
            total_sol = sol_amount
            token_breakdown["SOL"] = {
                "mint": "So11111111111111111111111111111111111111112",
                "symbol": "SOL",
                "name": "Solana",
                "amount": sol_amount,
                "decimals": 9,
                "logo": "https://raw.githubusercontent.com/solana-labs/token-list/main/assets/mainnet/So11111111111111111111111111111111111111112/logo.png",
            }

        # Process SPL tokens using enhanced metadata
        for asset in data["result"]["items"]:
            if asset.get("token_info") and float(asset["token_info"].get("balance", 0)) > 0:
                mint_address = asset["id"]
                raw_balance = float(asset["token_info"]["balance"])

                # Get enhanced metadata from Helius
                metadata = get_token_metadata_from_helius(mint_address)

                if metadata:
                    decimals = metadata.get("decimals", 6)
                    symbol = metadata.get("symbol") or mint_address[:8]
                    name = metadata.get("name")
                    logo = metadata.get("logo")
                else:
                    # Fallback to basic data from getAssetsByOwner
                    decimals = asset["token_info"].get("decimals", 6)
                    symbol = (
                        asset["token_info"].get("symbol")
                        or asset.get("content", {}).get("metadata", {}).get("symbol")
                        or mint_address[:8]
                    )
                    name = asset.get("content", {}).get("metadata", {}).get("name")
                    logo = None
                    if asset.get("content", {}).get("files"):
                        logo = asset["content"]["files"][0].get("cdn_uri") or asset["content"]["files"][0].get("uri")

                amount = raw_balance / (10**decimals)

                token_breakdown[symbol] = {
                    "mint": mint_address,
                    "symbol": symbol,
                    "name": name,
                    "amount": amount,
                    "decimals": decimals,
                    "logo": logo,
                }

        # Sort tokens: SOL, ai16z, USDC first, then by amount
        priority_tokens = ["SOL", "ai16z", "USDC"]
        sorted_tokens = {}

        # Add priority tokens first
        for token in priority_tokens:
            if token in token_breakdown:
                sorted_tokens[token] = token_breakdown[token]

        # Add remaining tokens sorted by amount
        remaining_tokens = {k: v for k, v in token_breakdown.items() if k not in priority_tokens}
        for token, data in sorted(remaining_tokens.items(), key=lambda x: x[1]["amount"], reverse=True):
            sorted_tokens[token] = data

        # Get recent transactions using Helius Enhanced Transactions API
        recent_contributions = await get_recent_transactions_helius(prize_wallet, helius_api_key)

        return {
            "total_sol": total_sol,
            "target_sol": target_sol,
            "progress_percentage": (total_sol / target_sol) * 100 if target_sol > 0 else 0,
            "token_breakdown": sorted_tokens,
            "recent_contributions": recent_contributions,
        }

    except Exception as e:
        logging.error(f"Error in prize pool: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/prize-pool")
async def websocket_prize_pool_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time prize pool updates."""
    try:
        await websocket.accept()
        await prize_pool_service.add_client(websocket)

        # Keep connection alive and handle disconnection
        try:
            while True:
                # Wait for any message from client (ping/pong or disconnect)
                await websocket.receive_text()
        except WebSocketDisconnect:
            pass

    except Exception as e:
        logging.error(f"WebSocket error: {e}")
    finally:
        await prize_pool_service.remove_client(websocket)


@router.post("/webhook/helius")
async def helius_webhook(request: Request):
    """Handle Helius webhook for Solana transaction processing."""
    try:
        _verify_webhook_auth(request)
        data = await request.json()

        # Extract transaction details
        tx_sig = data.get("signature")
        if not tx_sig:
            logging.warning("Webhook received without transaction signature")
            return {"processed": 0, "error": "No transaction signature"}

        transfers = data.get("tokenTransfers", [])
        if not transfers:
            logging.warning(f"No token transfers in transaction {tx_sig}")
            return {"processed": 0, "error": "No token transfers"}

        processed_count = 0
        AI16Z_MINT = "HeLp6NuQkmYB4pYWo2zYs22mESHXPQYzXbB8n4V98jwC"
        SOL_MINT = "So11111111111111111111111111111111111111112"

        for transfer in transfers:
            mint = transfer.get("mint")

            # Handle ai16z voting transactions
            if mint == AI16Z_MINT:
                submission_id = transfer.get("memo", "").strip()
                sender = transfer.get("fromUserAccount")
                amount = float(transfer.get("tokenAmount", 0))

                if submission_id and sender and amount >= 1:  # Minimum 1 ai16z
                    if process_ai16z_transaction(tx_sig, submission_id, sender, amount):
                        processed_count += 1
                else:
                    logging.warning(
                        f"Invalid ai16z transaction: submission_id={submission_id}, sender={sender}, amount={amount}"
                    )

            # Handle direct SOL donations to prize pool (no memo needed)
            elif mint == SOL_MINT:
                sender = transfer.get("fromUserAccount")
                amount = float(transfer.get("tokenAmount", 0))

                if sender and amount > 0:
                    try:
                        with engine.begin() as conn:
                            conn.execute(
                                text("""
                                    INSERT OR IGNORE INTO prize_pool_contributions
                                    (tx_sig, token_mint, token_symbol, amount, contributor_wallet, source, timestamp)
                                    VALUES (?, ?, ?, ?, ?, ?, ?)
                                """),
                                (tx_sig, SOL_MINT, "SOL", amount, sender, "direct_donation", int(time.time())),
                            )
                            # Transaction automatically commits on context exit
                            processed_count += 1
                            logging.info(f"Processed SOL donation: {amount} SOL from {sender}")
                    except Exception as e:
                        logging.error(f"SOL donation processing error: {e}")

        return {"processed": processed_count, "signature": tx_sig}

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Webhook processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/test")
async def test_webhook(request: Request):
    """Test endpoint to simulate a Helius webhook payload."""
    _require_non_production_test_webhook()
    _verify_webhook_auth(request)

    # Simulate a test ai16z transaction with vote overflow
    test_payload = {
        "signature": "test_tx_sig_webhook_123",
        "tokenTransfers": [
            {
                "mint": "HeLp6NuQkmYB4pYWo2zYs22mESHXPQYzXbB8n4V98jwC",  # ai16z
                "memo": "test-submission-1",
                "fromUserAccount": "wallet_webhook_test",
                "tokenAmount": 150.0,  # 150 ai16z - should split into 100 vote + 50 overflow
            }
        ],
    }

    # Process the transaction directly
    try:
        tx_sig = test_payload["signature"]
        transfer = test_payload["tokenTransfers"][0]
        submission_id = transfer["memo"]
        sender = transfer["fromUserAccount"]
        amount = transfer["tokenAmount"]

        success = process_ai16z_transaction(tx_sig, submission_id, sender, amount)

        return {
            "test_payload": test_payload,
            "processing_result": {"processed": 1 if success else 0, "signature": tx_sig},
            "status": "Test webhook processed successfully" if success else "Test webhook failed",
        }
    except Exception as e:
        return {"test_payload": test_payload, "error": str(e), "status": "Test webhook failed"}


# Community voting endpoints (must be before versioned routes)
@router.get("/api/community-votes/stats")
async def get_vote_stats():
    """Get overall community voting statistics."""
    try:
        from hackathon.backend.collect_votes import VoteProcessor

        processor = VoteProcessor(HACKATHON_DB_PATH)
        stats = processor.get_vote_stats()
        return stats
    except Exception as e:
        import traceback

        error_details = traceback.format_exc()
        logging.error(f"Error getting vote stats: {e}\n{error_details}")
        raise HTTPException(status_code=500, detail=f"Failed to get vote statistics: {e!s}")


@router.get("/api/community-votes/scores")
async def get_community_vote_scores():
    """Get community scores for all submissions."""
    try:
        from hackathon.backend.collect_votes import VoteProcessor

        processor = VoteProcessor(HACKATHON_DB_PATH)
        scores = processor.get_community_scores()
        return scores
    except Exception as e:
        logging.error(f"Error getting community scores: {e}")
        raise HTTPException(status_code=500, detail="Failed to get community scores")


@router.get("/api/submissions/{submission_id}/votes")
async def get_submission_votes(submission_id: int):
    """Get voting details for a specific submission."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                transaction_signature,
                sender_address,
                amount,
                timestamp,
                processed_at
            FROM community_votes
            WHERE submission_id = ?
            ORDER BY timestamp DESC
            """,
            (submission_id,),
        )

        votes = []
        for row in cursor.fetchall():
            sig, sender, amount, timestamp, processed_at = row
            votes.append(
                {
                    "transaction_signature": sig,
                    "sender_address": sender,
                    "amount": amount,
                    "timestamp": timestamp,
                    "processed_at": processed_at,
                }
            )

        conn.close()

        # Calculate summary stats
        if votes:
            total_amount = sum(vote["amount"] for vote in votes)
            unique_voters = len(set(vote["sender_address"] for vote in votes))
            avg_amount = total_amount / len(votes)
        else:
            total_amount = unique_voters = avg_amount = 0

        return {
            "submission_id": submission_id,
            "vote_count": len(votes),
            "unique_voters": unique_voters,
            "total_amount": total_amount,
            "avg_amount": avg_amount,
            "votes": votes,
        }

    except Exception as e:
        logging.error(f"Error getting votes for {submission_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get submission votes")
