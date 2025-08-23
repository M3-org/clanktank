#!/usr/bin/env python3
"""
Quick test script for the WebSocket prize pool service.
"""

import asyncio
import json
import websockets
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

async def test_websocket_client():
    """Test client to connect to our WebSocket service."""
    
    print("🔗 Testing WebSocket connection to prize pool service...")
    
    try:
        # Connect to our WebSocket endpoint
        uri = "ws://localhost:8000/ws/prize-pool"
        
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket!")
            
            # Listen for messages
            print("📡 Listening for updates...")
            
            try:
                while True:
                    message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    data = json.loads(message)
                    
                    print(f"📦 Received update:")
                    print(f"   Type: {data.get('type')}")
                    
                    if 'data' in data:
                        prize_data = data['data']
                        print(f"   Total SOL: {prize_data.get('total_sol', 'N/A')}")
                        print(f"   Target SOL: {prize_data.get('target_sol', 'N/A')}")
                        print(f"   Progress: {prize_data.get('progress_percentage', 0):.1f}%")
                        
                        tokens = prize_data.get('token_breakdown', {})
                        print(f"   Tokens: {list(tokens.keys())}")
                    
                    print("---")
                    
            except asyncio.TimeoutError:
                print("⏰ No updates received in 30 seconds")
                
    except ConnectionRefusedError:
        print("❌ Connection refused - is the server running?")
        print("   Start with: cd hackathon/backend && python app.py")
        
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")

if __name__ == "__main__":
    print("🚀 WebSocket Prize Pool Test")
    print("=" * 40)
    
    asyncio.run(test_websocket_client())