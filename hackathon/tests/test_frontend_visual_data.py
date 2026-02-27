#!/usr/bin/env python3
"""
Frontend Visual Data Generator

Creates realistic test submissions via API using TestClient (with mocked Discord auth)
to populate the frontend for visual testing and development.
"""

from fastapi.testclient import TestClient

# Test submission data for frontend visibility
FRONTEND_VISUAL_SUBMISSIONS = [
    {
        "project_name": "DeFi Yield Optimizer",
        "discord_handle": "yieldmaster#1234",
        "category": "DeFi",
        "description": "An automated yield farming protocol that maximizes returns across multiple DeFi platforms using advanced algorithmic strategies.",
        "twitter_handle": "@yieldoptimizer",
        "github_url": "https://github.com/defi-labs/yield-optimizer",
        "demo_video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "problem_solved": "DeFi users struggle to find optimal yield opportunities and often lose money due to manual management. Our protocol automates this process.",
        "favorite_part": "The auto-compounding mechanism that can increase yields by 15-30% compared to manual farming.",
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
        "favorite_part": "The biometric authentication system that makes transactions both secure and seamless.",
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
        "favorite_part": "The anti-cheat system powered by on-chain verification that ensures fair play.",
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
        "favorite_part": "The machine learning model that can detect novel attack vectors by analyzing thousands of exploits.",
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
        "favorite_part": "The quadratic voting system that ensures fair representation while preventing plutocracy.",
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
        "favorite_part": "The AI-powered trait generation system that helps artists create unique, valuable collections.",
    },
]


def test_populate_frontend_visual_data(client: TestClient):
    """Test that populates frontend with visual test data."""

    print("\n🎨 Frontend Visual Data Generator")
    print("=" * 50)

    successful_submissions = []
    failed_submissions = []

    # Submit test data
    print(f"📤 Submitting {len(FRONTEND_VISUAL_SUBMISSIONS)} test submissions...")

    for i, submission in enumerate(FRONTEND_VISUAL_SUBMISSIONS, 1):
        print(f"   [{i}/{len(FRONTEND_VISUAL_SUBMISSIONS)}] Submitting: {submission['project_name']}")

        response = client.post("/api/submissions", json=submission)

        if response.status_code == 201:
            result = response.json()
            successful_submissions.append(
                {
                    "submission_id": result.get("submission_id"),
                    "project_name": submission["project_name"],
                    "category": submission["category"],
                }
            )
            print(f"   ✅ Success - ID: {result.get('submission_id')}")
        else:
            failed_submissions.append(
                {"project_name": submission["project_name"], "error": f"HTTP {response.status_code}: {response.text}"}
            )
            print(f"   ❌ Failed - HTTP {response.status_code}: {response.text}")

    # Summary
    print("\n📊 Summary:")
    print(f"   ✅ Successful submissions: {len(successful_submissions)}")
    print(f"   ❌ Failed submissions: {len(failed_submissions)}")

    if successful_submissions:
        print("\n🎉 Frontend visual data populated successfully!")
        print("   Frontend URL: http://localhost:5173")
        print("   Backend URL: http://localhost:8000")

        # Show submission details
        print("\n📋 Created Submissions:")
        for result in successful_submissions:
            print(f"   - {result['submission_id']}: {result['project_name']} [{result['category']}]")

        # Show category breakdown
        print("\n🏷️  Category breakdown:")
        categories = {}
        for result in successful_submissions:
            cat = result["category"]
            categories[cat] = categories.get(cat, 0) + 1

        for category, count in categories.items():
            print(f"   - {category}: {count} submissions")

    if failed_submissions:
        print("\n⚠️  Failed submissions:")
        for result in failed_submissions:
            print(f"   - {result['project_name']}: {result['error']}")

    # Verify we can retrieve the data
    print("\n🔍 Verifying data retrieval...")

    # Test submissions endpoint
    submissions_response = client.get("/api/submissions")
    if submissions_response.status_code == 200:
        submissions_data = submissions_response.json()
        print(f"   ✅ Submissions endpoint: {len(submissions_data)} submissions found")
    else:
        print(f"   ❌ Submissions endpoint failed: {submissions_response.status_code}")

    # Test leaderboard endpoint
    leaderboard_response = client.get("/api/leaderboard")
    if leaderboard_response.status_code == 200:
        leaderboard_data = leaderboard_response.json()
        print(f"   ✅ Leaderboard endpoint: {len(leaderboard_data)} entries found")
    else:
        print(f"   ❌ Leaderboard endpoint failed: {leaderboard_response.status_code}")

    # Test stats endpoint
    stats_response = client.get("/api/stats")
    if stats_response.status_code == 200:
        stats_data = stats_response.json()
        print(f"   ✅ Stats endpoint: {stats_data.get('total_submissions', 0)} total submissions")
    else:
        print(f"   ❌ Stats endpoint failed: {stats_response.status_code}")

    print("\n✨ Frontend visual data generation complete!")
    print("   Visit http://localhost:5173 to see the populated dashboard")

    # Assert that we successfully created at least some submissions
    assert len(successful_submissions) > 0, "Should have created at least one submission"
    assert len(successful_submissions) >= len(FRONTEND_VISUAL_SUBMISSIONS) // 2, (
        "Should have created at least half the submissions"
    )


if __name__ == "__main__":
    # Run as standalone script
    print("🚀 Running Frontend Visual Data Generator")
    print("Note: This runs the test via pytest to use the Discord auth mock")
    print(
        "Run: python -m pytest hackathon/tests/test_frontend_visual_data.py::test_populate_frontend_visual_data -v -s"
    )
