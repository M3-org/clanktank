#!/usr/bin/env python3
"""
Frontend Data Generator Test

Creates realistic test submissions via API endpoints to populate the frontend
for visual testing and development. This test generates submissions that 
appear on the web app dashboard.
"""

import requests
import json
import time
import uuid
from typing import Dict, List

# API Configuration
API_BASE_URL = "http://localhost:8000"
API_SUBMISSIONS_URL = f"{API_BASE_URL}/api/submissions"

# Test submission data for frontend visibility
FRONTEND_TEST_SUBMISSIONS = [
    {
        "project_name": "DeFi Yield Optimizer",
        "discord_handle": "yieldmaster#1234",
        "category": "DeFi",
        "description": "An automated yield farming protocol that maximizes returns across multiple DeFi platforms using advanced algorithmic strategies.",
        "twitter_handle": "@yieldoptimizer",
        "github_url": "https://github.com/defi-labs/yield-optimizer",
        "demo_video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "problem_solved": "DeFi users struggle to find optimal yield opportunities and often lose money due to manual management. Our protocol automates this process.",
        "favorite_part": "The auto-compounding mechanism that can increase yields by 15-30% compared to manual farming."
    },
    {
        "project_name": "Solana Mobile Wallet",
        "discord_handle": "mobilewallet#5678",
        "category": "Infrastructure", 
        "description": "A secure, user-friendly mobile wallet specifically designed for Solana ecosystem with built-in DeFi integrations.",
        "twitter_handle": "@solanamobile",
        "github_url": "https://github.com/solana-mobile/wallet-app",
        "demo_video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "problem_solved": "Current Solana wallets are complex and intimidating for mainstream users. We built a simple, secure solution.",
        "favorite_part": "The biometric authentication system that makes transactions both secure and seamless."
    },
    {
        "project_name": "GameFi Arena",
        "discord_handle": "gamedev#9999",
        "category": "Gaming",
        "description": "A competitive gaming platform where players can stake tokens, compete in tournaments, and earn rewards through skill-based gameplay.",
        "twitter_handle": "@gamefiarena",
        "github_url": "https://github.com/gamefi/arena-platform",
        "demo_video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "problem_solved": "Traditional gaming doesn't reward skilled players financially. We created a fair, skill-based earning mechanism.",
        "favorite_part": "The anti-cheat system powered by on-chain verification that ensures fair play."
    },
    {
        "project_name": "AI Code Auditor",
        "discord_handle": "aiauditor#2023",
        "category": "AI/Agents",
        "description": "An AI-powered smart contract auditing tool that automatically detects vulnerabilities, gas optimizations, and security issues.",
        "twitter_handle": "@aicodeaudit",
        "github_url": "https://github.com/ai-audit/smart-contract-analyzer",
        "demo_video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "problem_solved": "Smart contract audits are expensive and time-consuming. Our AI provides instant, comprehensive analysis.",
        "favorite_part": "The machine learning model that can detect novel attack vectors by analyzing thousands of exploits."
    },
    {
        "project_name": "Social Impact DAO",
        "discord_handle": "socialimpact#7777",
        "category": "Social",
        "description": "A decentralized autonomous organization focused on funding and coordinating social impact projects through community governance.",
        "twitter_handle": "@socialimpactdao",
        "github_url": "https://github.com/social-dao/governance-platform",
        "demo_video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "problem_solved": "Traditional charity lacks transparency and community involvement. We enable direct, transparent, community-driven impact.",
        "favorite_part": "The quadratic voting system that ensures fair representation while preventing plutocracy."
    },
    {
        "project_name": "NFT Creator Studio",
        "discord_handle": "nftcreator#3333",
        "category": "Other",
        "description": "A no-code platform for artists to create, mint, and sell NFTs with built-in royalty management and community features.",
        "twitter_handle": "@nftcreatorstudio",
        "github_url": "https://github.com/nft-studio/creator-platform",
        "demo_video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "problem_solved": "Artists struggle with the technical complexity of NFT creation. We make it accessible to everyone.",
        "favorite_part": "The AI-powered trait generation system that helps artists create unique, valuable collections."
    }
]

def generate_unique_submission_id() -> int:
    """Generate a unique submission ID for testing."""
    return int(time.time() * 1000) % 1000000  # Use timestamp to ensure uniqueness

def submit_via_api(submission_data: Dict) -> Dict:
    """Submit a single submission via API."""
    try:
        response = requests.post(
            API_SUBMISSIONS_URL,
            json=submission_data,
            headers={
                "Content-Type": "application/json"
            },
            timeout=30
        )
        
        if response.status_code == 201:
            return {
                "success": True,
                "submission_id": response.json().get("submission_id"),
                "data": submission_data
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}",
                "data": submission_data
            }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Request failed: {str(e)}",
            "data": submission_data
        }

def check_api_health() -> bool:
    """Check if the API is running and accessible."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/stats", timeout=10)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def populate_frontend_data():
    """Main function to populate frontend with test data."""
    print("🚀 Frontend Data Generator")
    print("=" * 50)
    
    # Check API health
    print("1. Checking API health...")
    if not check_api_health():
        print("❌ API is not accessible. Please start the backend server:")
        print("   uvicorn hackathon.backend.app:app --host 0.0.0.0 --port 8000")
        return False
    
    print("✅ API is running and accessible")
    
    # Submit test data
    print(f"\n2. Submitting {len(FRONTEND_TEST_SUBMISSIONS)} test submissions...")
    successful_submissions = []
    failed_submissions = []
    
    for i, submission in enumerate(FRONTEND_TEST_SUBMISSIONS, 1):
        print(f"   [{i}/{len(FRONTEND_TEST_SUBMISSIONS)}] Submitting: {submission['project_name']}")
        
        result = submit_via_api(submission)
        
        if result["success"]:
            successful_submissions.append(result)
            print(f"   ✅ Success - ID: {result['submission_id']}")
        else:
            failed_submissions.append(result)
            print(f"   ❌ Failed - {result['error']}")
        
        # Small delay to avoid overwhelming the API
        time.sleep(0.5)
    
    # Summary
    print("\n3. Summary:")
    print(f"   ✅ Successful submissions: {len(successful_submissions)}")
    print(f"   ❌ Failed submissions: {len(failed_submissions)}")
    
    if successful_submissions:
        print(f"\n🎉 Frontend data populated successfully!")
        print(f"   Visit: http://localhost:5173 to see the submissions")
        print(f"   API Dashboard: {API_BASE_URL}/api/submissions")
        
        # Show submission IDs
        print("\n📋 Created Submission IDs:")
        for result in successful_submissions:
            print(f"   - {result['submission_id']}: {result['data']['project_name']}")
    
    if failed_submissions:
        print(f"\n⚠️  Some submissions failed:")
        for result in failed_submissions:
            print(f"   - {result['data']['project_name']}: {result['error']}")
    
    return len(successful_submissions) > 0

if __name__ == "__main__":
    success = populate_frontend_data()
    exit(0 if success else 1)