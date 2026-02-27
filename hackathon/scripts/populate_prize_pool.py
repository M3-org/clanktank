#!/usr/bin/env python3
"""
Script to populate the prize pool with real data from Helius API.
This fetches the actual token holdings for the prize wallet and populates the database.
"""

import os
import sys
import time
from pathlib import Path

import requests

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from sqlalchemy import text  # noqa: E402

from hackathon.backend.app import engine  # noqa: E402

# Prize wallet address from environment
PRIZE_WALLET_ADDRESS = os.getenv("PRIZE_WALLET_ADDRESS")
if not PRIZE_WALLET_ADDRESS:
    raise ValueError("PRIZE_WALLET_ADDRESS environment variable is required")


def fetch_real_token_holdings():
    """Fetch real token holdings from Helius API"""
    helius_api_key = os.getenv("HELIUS_API_KEY")
    if not helius_api_key:
        print("❌ HELIUS_API_KEY not found in environment")
        return []

    helius_url = f"https://mainnet.helius-rpc.com/?api-key={helius_api_key}"

    payload = {
        "jsonrpc": "2.0",
        "id": "prize-pool-population",
        "method": "getAssetsByOwner",
        "params": {
            "ownerAddress": PRIZE_WALLET_ADDRESS,
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

    try:
        print(f"📡 Fetching token holdings from Helius for {PRIZE_WALLET_ADDRESS}...")
        response = requests.post(helius_url, json=payload)
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            print(f"❌ Helius API error: {data['error']}")
            return []

        if not data.get("result", {}).get("items"):
            print("⚠️  No items found in Helius response")
            return []

        tokens = []

        # Process native SOL balance
        native_balance = data["result"].get("nativeBalance", {})
        if native_balance and native_balance.get("lamports", 0) > 0:
            sol_amount = native_balance["lamports"] / 1_000_000_000
            tokens.append(
                {
                    "mint": "So11111111111111111111111111111111111111112",
                    "symbol": "SOL",
                    "amount": sol_amount,
                    "decimals": 9,
                }
            )
            print(f"  📍 SOL: {sol_amount:.4f}")

        # Process SPL tokens
        for asset in data["result"]["items"]:
            if asset.get("token_info") and float(asset["token_info"].get("balance", 0)) > 0:
                decimals = asset["token_info"].get("decimals", 6)
                raw_balance = float(asset["token_info"]["balance"])
                amount = raw_balance / (10**decimals)
                symbol = (
                    asset["token_info"].get("symbol")
                    or asset.get("content", {}).get("metadata", {}).get("symbol")
                    or asset["id"][:8]
                )

                tokens.append({"mint": asset["id"], "symbol": symbol, "amount": amount, "decimals": decimals})
                print(f"  📍 {symbol}: {amount:.4f}")

        print(f"✅ Found {len(tokens)} tokens with balances")
        return tokens

    except Exception as e:
        print(f"❌ Error fetching from Helius: {e}")
        return []


def populate_database(tokens):
    """Populate the prize_pool_contributions table with real data"""
    if not tokens:
        print("❌ No tokens to populate")
        return

    try:
        with engine.begin() as conn:
            # Clear existing prize pool data
            print("🧹 Clearing existing prize pool data...")
            conn.execute(text("DELETE FROM prize_pool_contributions WHERE source = 'real_balance'"))

            # Insert real token holdings
            print("💰 Inserting real token holdings...")
            current_time = int(time.time())

            for token in tokens:
                conn.execute(
                    text("""
                        INSERT INTO prize_pool_contributions
                        (tx_sig, token_mint, token_symbol, amount, contributor_wallet, source, timestamp)
                        VALUES (:tx_sig, :token_mint, :token_symbol, :amount, :contributor_wallet, :source, :timestamp)
                    """),
                    {
                        "tx_sig": f"real_balance_{token['mint']}",  # Unique tx_sig for real balance
                        "token_mint": token["mint"],
                        "token_symbol": token["symbol"],
                        "amount": token["amount"],
                        "contributor_wallet": PRIZE_WALLET_ADDRESS,
                        "source": "real_balance",  # New source type for actual wallet balance
                        "timestamp": current_time,
                    },
                )
                print(f"  ✅ Inserted {token['symbol']}: {token['amount']:.4f}")

            print(f"🎉 Successfully populated {len(tokens)} tokens in prize pool database")

    except Exception as e:
        print(f"❌ Database error: {e}")


def main():
    print("🚀 Starting prize pool population with real Helius data...\n")

    # Fetch real data
    tokens = fetch_real_token_holdings()

    if not tokens:
        print("❌ No token data fetched, exiting")
        return

    # Populate database
    populate_database(tokens)

    print("\n✨ Prize pool population complete!")
    print("📊 You can now test the /api/prize-pool endpoint with real data")


if __name__ == "__main__":
    main()
