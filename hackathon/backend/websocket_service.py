"""
WebSocket service for real-time prize pool updates using Helius API.
"""

import asyncio
import json
import logging
import os
from typing import Set, Dict, Any, Optional
import websockets
import requests
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PrizePoolWebSocketService:
    """Real-time prize pool updates via Helius WebSocket."""
    
    def __init__(self):
        self.helius_api_key = os.getenv('HELIUS_API_KEY')
        self.prize_wallet = os.getenv('PRIZE_WALLET_ADDRESS')
        self.helius_ws_url = f"wss://atlas-mainnet.helius-rpc.com?api-key={self.helius_api_key}"
        
        if not self.helius_api_key:
            raise ValueError("HELIUS_API_KEY environment variable required")
        if not self.prize_wallet:
            raise ValueError("PRIZE_WALLET_ADDRESS environment variable required")
        
        # Connected clients
        self.clients: Set[Any] = set()
        
        # Current prize pool data (cached for new clients)
        self.current_data: Optional[Dict] = None
        
        # Helius WebSocket connection
        self.helius_ws = None
        
        # Control flags
        self.running = False

    async def start(self):
        """Start the WebSocket service."""
        if self.running:
            return
            
        self.running = True
        logger.info(f"Starting WebSocket service for wallet: {self.prize_wallet}")
        
        # Load initial prize pool data
        await self.update_prize_pool_data()
        
        # Start Helius WebSocket connection
        asyncio.create_task(self.connect_to_helius())

    async def stop(self):
        """Stop the WebSocket service."""
        self.running = False
        
        if self.helius_ws:
            await self.helius_ws.close()
        
        # Close all client connections
        if self.clients:
            await asyncio.gather(
                *[client.close() for client in self.clients.copy()],
                return_exceptions=True
            )
        
        logger.info("WebSocket service stopped")

    async def add_client(self, websocket):
        """Add a new client connection."""
        self.clients.add(websocket)
        logger.info(f"New client connected. Total clients: {len(self.clients)}")
        
        # Send current data to new client
        if self.current_data:
            try:
                # Ensure clean serialization by creating a fresh dict
                clean_data = {
                    "total_sol": float(self.current_data.get("total_sol", 0)),
                    "target_sol": float(self.current_data.get("target_sol", 10)),
                    "progress_percentage": float(self.current_data.get("progress_percentage", 0)),
                    "token_breakdown": dict(self.current_data.get("token_breakdown", {})),
                    "recent_contributions": list(self.current_data.get("recent_contributions", [])),
                    "last_updated": float(self.current_data.get("last_updated", 0))
                }
                
                message_data = {
                    "type": "prize_pool_update",
                    "data": clean_data
                }
                
                logger.info(f"Sending initial data to client: {clean_data}")
                message_json = json.dumps(message_data)
                # Send as text message, not structured message
                await websocket.send_text(message_json)
                
            except Exception as e:
                logger.error(f"Error sending initial data to client: {e}")
                logger.error(f"Current data type: {type(self.current_data)}")
                logger.error(f"Current data content: {self.current_data}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                self.clients.discard(websocket)

    async def remove_client(self, websocket):
        """Remove a client connection."""
        self.clients.discard(websocket)
        logger.info(f"Client disconnected. Total clients: {len(self.clients)}")

    async def broadcast_to_clients(self, data: Dict):
        """Broadcast data to all connected clients."""
        if not self.clients:
            return
        
        # Ensure clean serialization 
        clean_data = {
            "total_sol": float(data.get("total_sol", 0)),
            "target_sol": float(data.get("target_sol", 10)),
            "progress_percentage": float(data.get("progress_percentage", 0)),
            "token_breakdown": dict(data.get("token_breakdown", {})),
            "recent_contributions": list(data.get("recent_contributions", [])),
            "last_updated": float(data.get("last_updated", 0))
        }
        
        message = json.dumps({
            "type": "prize_pool_update",
            "data": clean_data
        })
        
        # Send to all clients, removing failed connections
        disconnected = []
        for client in self.clients.copy():
            try:
                await client.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to send to client: {e}")
                disconnected.append(client)
        
        # Clean up disconnected clients
        for client in disconnected:
            self.clients.discard(client)
        
        if disconnected:
            logger.info(f"Removed {len(disconnected)} disconnected clients")

    async def connect_to_helius(self):
        """Connect to Helius WebSocket and listen for transactions."""
        while self.running:
            try:
                logger.info("Connecting to Helius WebSocket...")
                
                async with websockets.connect(self.helius_ws_url) as websocket:
                    self.helius_ws = websocket
                    
                    # Subscribe to transactions for our prize wallet
                    subscription_request = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "transactionSubscribe",
                        "params": [
                            {
                                "failed": False,
                                "accountInclude": [self.prize_wallet]
                            },
                            {
                                "commitment": "confirmed",
                                "encoding": "jsonParsed",
                                "transactionDetails": "full",
                                "maxSupportedTransactionVersion": 0
                            }
                        ]
                    }
                    
                    await websocket.send(json.dumps(subscription_request))
                    logger.info(f"Subscribed to transactions for wallet: {self.prize_wallet}")
                    
                    # Listen for messages
                    async for message in websocket:
                        if not self.running:
                            break
                            
                        try:
                            data = json.loads(message)
                            await self.handle_helius_message(data)
                        except Exception as e:
                            logger.error(f"Error processing Helius message: {e}")
                            
            except Exception as e:
                logger.error(f"Helius WebSocket connection error: {e}")
                if self.running:
                    logger.info("Retrying connection in 5 seconds...")
                    await asyncio.sleep(5)

    async def handle_helius_message(self, data: Dict):
        """Handle incoming messages from Helius WebSocket."""
        try:
            # Skip subscription confirmation messages
            if "result" in data and isinstance(data.get("result"), int):
                logger.info(f"Subscription confirmed with ID: {data['result']}")
                return
            
            # Check if this is a transaction notification
            if "params" not in data:
                return
                
            params = data["params"]
            if "result" not in params:
                return
                
            transaction_data = params["result"]
            
            # Log transaction detection
            signature = transaction_data.get("signature", "unknown")
            logger.info(f"New transaction detected: {signature}")
            
            # Check if this affects our prize pool
            if await self.is_prize_pool_transaction(transaction_data):
                logger.info("Prize pool transaction detected, updating data...")
                
                # Refresh prize pool data
                await self.update_prize_pool_data()
                
                # Broadcast to clients
                if self.current_data:
                    await self.broadcast_to_clients(self.current_data)
                    
        except Exception as e:
            logger.error(f"Error handling Helius message: {e}")

    async def is_prize_pool_transaction(self, transaction_data: Dict) -> bool:
        """Check if transaction affects the prize pool."""
        try:
            # Check if our wallet is involved in token transfers
            if "meta" not in transaction_data:
                return False
                
            meta = transaction_data["meta"]
            
            # Check for token balance changes
            if "postTokenBalances" in meta and "preTokenBalances" in meta:
                post_balances = meta["postTokenBalances"]
                pre_balances = meta["preTokenBalances"]
                
                # Check if our wallet has balance changes
                for balance in post_balances:
                    if balance.get("owner") == self.prize_wallet:
                        return True
            
            # Check for SOL balance changes
            if "postBalances" in meta and "preBalances" in meta:
                account_keys = transaction_data.get("transaction", {}).get("message", {}).get("accountKeys", [])
                
                for i, account_key in enumerate(account_keys):
                    if account_key == self.prize_wallet:
                        pre_balance = meta["preBalances"][i] if i < len(meta["preBalances"]) else 0
                        post_balance = meta["postBalances"][i] if i < len(meta["postBalances"]) else 0
                        
                        if pre_balance != post_balance:
                            return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking transaction: {e}")
            return False

    async def update_prize_pool_data(self):
        """Fetch latest prize pool data from backend API."""
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            prize_pool_data = await loop.run_in_executor(None, self.fetch_prize_pool_sync)
            
            logger.info(f"Fetched prize pool data type: {type(prize_pool_data)}")
            logger.info(f"Fetched prize pool data: {prize_pool_data}")
            
            self.current_data = prize_pool_data
            logger.info(f"Updated prize pool data: {prize_pool_data.get('total_sol', 'N/A')} SOL")
            
        except Exception as e:
            logger.error(f"Error updating prize pool data: {e}")

    def fetch_prize_pool_sync(self) -> Dict:
        """Synchronous version of prize pool data fetch."""
        try:
            helius_url = f"https://mainnet.helius-rpc.com/?api-key={self.helius_api_key}"
            
            # Simplified version of the prize pool logic
            payload = {
                "jsonrpc": "2.0",
                "id": "prize-pool-ws",
                "method": "getAssetsByOwner",
                "params": {
                    "ownerAddress": self.prize_wallet,
                    "page": 1,
                    "limit": 100,
                    "displayOptions": {
                        "showNativeBalance": True
                    }
                }
            }
            
            response = requests.post(helius_url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            if 'error' in data:
                raise Exception(f"Helius API error: {data['error']}")
            
            result = data.get('result', {})
            native_balance = float(result.get('nativeBalance', {}).get('lamports', 0)) / 1_000_000_000  # Convert lamports to SOL
            
            # Simplified token processing - just return SOL balance for now
            # TODO: Add full token processing if needed for real-time updates
            
            import time
            return {
                'total_sol': native_balance,
                'target_sol': float(os.getenv('PRIZE_POOL_TARGET_SOL', 10)),
                'progress_percentage': (native_balance / 10) * 100,  # TODO: Use actual target
                'token_breakdown': {
                    'SOL': {
                        'symbol': 'SOL',
                        'amount': native_balance,
                        'mint': 'So11111111111111111111111111111111111111112',
                        'decimals': 9
                    }
                },
                'recent_contributions': [],  # TODO: Add if needed
                'last_updated': time.time()
            }
            
        except Exception as e:
            logger.error(f"Error in sync prize pool fetch: {e}")
            # Return safe defaults
            import time
            return {
                'total_sol': 0,
                'target_sol': 10,
                'progress_percentage': 0,
                'token_breakdown': {},
                'recent_contributions': [],
                'last_updated': time.time()
            }

# Global service instance
prize_pool_service = PrizePoolWebSocketService()