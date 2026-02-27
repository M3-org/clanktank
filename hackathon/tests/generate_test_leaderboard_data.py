#!/usr/bin/env python3
"""
Generate realistic test data for leaderboard visualization
Uses existing test patterns and creates scored submissions with variety
"""

import json
import os
import random
import sys
import uuid
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

import subprocess

from fastapi.testclient import TestClient

from hackathon.backend.app import app


def generate_realistic_submissions():
    """Generate realistic hackathon submissions with variety"""

    project_ideas = [
        {
            "name": "AI Code Reviewer Pro",
            "category": "AI/Agents",
            "description": "An AI agent that automatically reviews pull requests, suggests improvements, and learns from team coding patterns to provide personalized feedback.",
            "problem": "Manual code reviews are time-consuming and inconsistent across team members",
            "favorite": "The AI learns each developer's style and provides tailored suggestions",
            "github": "https://github.com/aicodereview/pr-assistant",
            "demo": "https://youtube.com/watch?v=dQw4w9WgXcQ",
            "twitter": "@aicodereview",
            "solana": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
        },
        {
            "name": "DeFi Yield Optimizer",
            "category": "DeFi",
            "description": "Automated yield farming strategy that optimizes across multiple Solana protocols, rebalancing based on APY changes and risk assessment.",
            "problem": "Manual yield farming is inefficient and risky for most users",
            "favorite": "The risk-adjusted optimization that protects principal while maximizing yield",
            "github": "https://github.com/defi-optimizer/yield-max",
            "demo": "https://youtube.com/watch?v=yield_demo",
            "twitter": "@yieldoptimizer",
            "solana": "8RzQGnUJzaGYdJLkfFYVzSwqvRgxdR3bXzKNTMN8pump",
        },
        {
            "name": "Solana Social Recovery",
            "category": "Consumer/Social",
            "description": "Social recovery wallet system where trusted friends can help recover access without exposing private keys, using cryptographic proofs.",
            "problem": "Lost wallet access leads to permanent fund loss, existing recovery is complex",
            "favorite": "Zero-knowledge proofs ensure privacy while enabling social recovery",
            "github": "https://github.com/social-recovery/solana-guardian",
            "demo": "https://youtube.com/watch?v=social_recovery",
            "twitter": "@socialwallet",
            "solana": "7VsQGnUJzaGYdJLkfFYVzSwqvRgxdR3bXzKNTMN8pump",
        },
        {
            "name": "NFT Creator Studio",
            "category": "Consumer/Social",
            "description": "AI-powered NFT creation platform that generates artwork, suggests pricing, and handles minting with one-click deployment to Solana.",
            "problem": "Creating and launching NFT collections requires technical expertise most artists lack",
            "favorite": "The AI analyzes successful collections to suggest optimal traits and pricing",
            "github": "https://github.com/nft-studio/creator-ai",
            "demo": "https://youtube.com/watch?v=nft_creator",
            "twitter": "@nftcreatrstudio",
            "solana": "6VsQGnUJzaGYdJLkfFYVzSwqvRgxdR3bXzKNTMN8pump",
        },
        {
            "name": "Memecoin Launch Assistant",
            "category": "DeFi",
            "description": "Complete memecoin launch toolkit with fair launch mechanics, anti-rug features, and community governance built on Solana.",
            "problem": "Most memecoin launches are scams or lack proper tokenomics and community features",
            "favorite": "Built-in anti-rug mechanisms that lock liquidity and ensure fair distribution",
            "github": "https://github.com/memecoin-tools/fair-launch",
            "demo": "https://youtube.com/watch?v=memecoin_launch",
            "twitter": "@memelaunchpad",
            "solana": "5VsQGnUJzaGYdJLkfFYVzSwqvRgxdR3bXzKNTMN8pump",
        },
        {
            "name": "Pump.fun Analytics Pro",
            "category": "AI/Agents",
            "description": "AI agent that analyzes pump.fun launches, predicts success probability, and provides real-time trading signals based on on-chain data.",
            "problem": "Most pump.fun tokens fail quickly, traders need better tools to identify winners",
            "favorite": "Real-time sentiment analysis combined with on-chain metrics for accurate predictions",
            "github": "https://github.com/pump-analytics/signal-bot",
            "demo": "https://youtube.com/watch?v=pump_analytics",
            "twitter": "@pumpanalytics",
            "solana": "4VsQGnUJzaGYdJLkfFYVzSwqvRgxdR3bXzKNTMN8pump",
        },
        {
            "name": "DAO Governance Simulator",
            "category": "Consumer/Social",
            "description": "Simulation platform for testing DAO governance proposals before going live, modeling economic impacts and voter behavior.",
            "problem": "DAO proposals often have unintended consequences that could be prevented with testing",
            "favorite": "Monte Carlo simulations that model complex voter behavior patterns",
            "github": "https://github.com/dao-sim/governance-lab",
            "demo": "https://youtube.com/watch?v=dao_simulator",
            "twitter": "@daosimulator",
            "solana": "3VsQGnUJzaGYdJLkfFYVzSwqvRgxdR3bXzKNTMN8pump",
        },
        {
            "name": "Solana Mobile Wallet",
            "category": "Consumer/Social",
            "description": "Next-gen mobile wallet with biometric security, seamless dApp integration, and built-in social features for sharing transactions.",
            "problem": "Current mobile wallets are clunky and don't leverage modern smartphone capabilities",
            "favorite": "Biometric transaction signing with zero-knowledge proofs for privacy",
            "github": "https://github.com/mobile-wallet/solana-bio",
            "demo": "https://youtube.com/watch?v=mobile_wallet",
            "twitter": "@solanamobile",
            "solana": "2VsQGnUJzaGYdJLkfFYVzSwqvRgxdR3bXzKNTMN8pump",
        },
    ]

    # Discord handles and avatars for variety
    discord_users = [
        {"handle": "cryptobuilder", "id": "123456789012345678", "avatar": "a1b2c3d4e5f6789012345678901234ab"},
        {"handle": "solanadev", "id": "234567890123456789", "avatar": "b2c3d4e5f6789012345678901234abcd"},
        {"handle": "defi_degen", "id": "345678901234567890", "avatar": "c3d4e5f6789012345678901234abcdef"},
        {"handle": "nft_artist", "id": "456789012345678901", "avatar": "d4e5f6789012345678901234abcdef01"},
        {"handle": "pump_hunter", "id": "567890123456789012", "avatar": "e5f6789012345678901234abcdef0123"},
        {"handle": "dao_governor", "id": "678901234567890123", "avatar": "f6789012345678901234abcdef012345"},
        {"handle": "mobile_dev", "id": "789012345678901234", "avatar": "6789012345678901234abcdef0123456"},
        {"handle": "yield_farmer", "id": "890123456789012345", "avatar": "789012345678901234abcdef01234567"},
    ]

    return list(zip(project_ideas, discord_users))


def generate_judge_scores(project_category, base_quality="good"):
    """Generate realistic judge scores based on project category and quality"""

    # Base score ranges by quality
    score_ranges = {"excellent": (8.0, 10.0), "good": (6.0, 8.5), "average": (4.0, 7.0), "poor": (2.0, 5.0)}

    min_score, max_score = score_ranges[base_quality]

    # Judge personalities with different weightings
    judges = {
        "aimarc": {
            "strengths": ["market_potential", "user_experience"],
            "multipliers": {
                "innovation": 0.8,
                "technical_execution": 1.0,
                "market_potential": 1.3,
                "user_experience": 1.2,
            },
        },
        "aishaw": {
            "strengths": ["technical_execution", "innovation"],
            "multipliers": {
                "innovation": 1.3,
                "technical_execution": 1.4,
                "market_potential": 0.9,
                "user_experience": 0.8,
            },
        },
        "spartan": {
            "strengths": ["market_potential", "technical_execution"],
            "multipliers": {
                "innovation": 1.0,
                "technical_execution": 1.2,
                "market_potential": 1.4,
                "user_experience": 0.7,
            },
        },
        "peepo": {
            "strengths": ["user_experience", "innovation"],
            "multipliers": {
                "innovation": 1.2,
                "technical_execution": 0.7,
                "market_potential": 1.0,
                "user_experience": 1.5,
            },
        },
    }

    judge_scores = []

    for judge_name, judge_info in judges.items():
        # Generate base scores
        scores = {
            "innovation": random.uniform(min_score, max_score),
            "technical_execution": random.uniform(min_score, max_score),
            "market_potential": random.uniform(min_score, max_score),
            "user_experience": random.uniform(min_score, max_score),
        }

        # Apply judge-specific multipliers
        for metric, multiplier in judge_info["multipliers"].items():
            scores[metric] = min(10.0, scores[metric] * multiplier)

        # Calculate weighted total (realistic backend calculation)
        weighted_total = sum(scores.values()) / 4.0

        # Generate comments based on scores
        comments = generate_judge_comment(judge_name, scores, project_category)

        judge_scores.append(
            {"judge_name": judge_name, "scores": scores, "weighted_total": weighted_total, "comment": comments}
        )

    return judge_scores


def generate_judge_comment(judge_name, scores, category):
    """Generate realistic judge comments based on scores and judge personality"""

    avg_score = sum(scores.values()) / 4.0

    comment_templates = {
        "aimarc": {
            "high": "Strong market fit and clear monetization strategy. I can see this scaling rapidly with the right go-to-market approach.",
            "medium": "Decent business potential but needs clearer value proposition. Revenue model could be better defined.",
            "low": "Struggling to see the business case here. Market opportunity seems limited and monetization unclear.",
        },
        "aishaw": {
            "high": "Excellent technical execution with clean, scalable architecture. Code quality is impressive and shows deep understanding.",
            "medium": "Solid technical foundation but could benefit from better optimization and more robust error handling.",
            "low": "Technical implementation feels rushed. Architecture could be more thoughtful and code needs refactoring.",
        },
        "spartan": {
            "high": "This has serious DeFi alpha potential. Tokenomics are sound and the protocol design is battle-tested.",
            "medium": "Interesting DeFi mechanics but needs more robust economic models. Security audit would be critical.",
            "low": "DeFi protocols require extreme attention to detail. This needs significant work on security and incentive alignment.",
        },
        "peepo": {
            "high": "Based UX that even my grandma could use. The design is clean and the user flow is *chef's kiss*.",
            "medium": "Pretty good UX but could use more intuitive onboarding. Some workflows feel a bit clunky.",
            "low": "UX needs major work. Too complex for normies and missing key user-friendly features.",
        },
    }

    if avg_score >= 7.5:
        tier = "high"
    elif avg_score >= 5.5:
        tier = "medium"
    else:
        tier = "low"

    return comment_templates[judge_name][tier]


def create_test_submissions_with_scores():
    """Create submissions and add scores to database"""

    # Reset database
    subprocess.run(["python3", "-m", "hackathon.backend.create_db"], check=True)

    # Set up test authentication token
    import time as time_module

    test_token = f"test-{uuid.uuid4().hex}-{int(time_module.time())}"
    os.environ["TEST_AUTH_TOKEN"] = test_token
    headers = {"Authorization": f"Bearer {test_token}"}

    client = TestClient(app)
    submissions_data = generate_realistic_submissions()

    # Quality distribution for variety
    quality_levels = ["excellent", "good", "good", "average", "good", "average", "good", "average"]

    created_submissions = []

    for _i, ((project, discord_user), quality) in enumerate(zip(submissions_data, quality_levels)):
        f"test-{uuid.uuid4().hex[:8]}"

        # Create submission
        submission_payload = {
            "project_name": project["name"],
            "discord_handle": discord_user["handle"],
            "category": project["category"],
            "description": project["description"],
            "github_url": project["github"],
            "demo_video_url": project["demo"],
            "twitter_handle": project["twitter"],
            "problem_solved": project["problem"],
            "favorite_part": project["favorite"],
            "solana_address": project["solana"],
            "discord_avatar": discord_user["avatar"],
            "discord_id": discord_user["id"],
        }

        response = client.post("/api/submissions", json=submission_payload, headers=headers)
        assert response.status_code == 201, f"Failed to create submission: {response.text}"

        submission_id = response.json()["submission_id"]
        created_submissions.append(
            {"id": submission_id, "name": project["name"], "category": project["category"], "quality": quality}
        )

        # Add judge scores
        judge_scores = generate_judge_scores(project["category"], quality)

        for judge_data in judge_scores:
            add_score_to_database(
                submission_id,
                judge_data["judge_name"],
                judge_data["scores"],
                judge_data["weighted_total"],
                judge_data["comment"],
            )

        print(f"Created submission: {project['name']} ({quality}) - {submission_id}")

    # Add some community feedback for variety
    add_community_feedback(created_submissions, client, headers)

    # Clean up: Remove test token from environment
    if "TEST_AUTH_TOKEN" in os.environ:
        del os.environ["TEST_AUTH_TOKEN"]

    print(f"\n✅ Successfully created {len(created_submissions)} test submissions with scores!")
    print("You can now view the leaderboard at: http://localhost:5173/leaderboard")

    return created_submissions


def add_score_to_database(submission_id, judge_name, scores, weighted_total, comment):
    """Add judge scores directly to database"""
    from sqlalchemy import create_engine, text

    from hackathon.backend.app import HACKATHON_DB_PATH

    engine = create_engine(f"sqlite:///{HACKATHON_DB_PATH}")

    with engine.connect() as conn:
        # Round 1 scores
        conn.execute(
            text("""
                INSERT INTO hackathon_scores
                (submission_id, judge_name, round, innovation, technical_execution,
                 market_potential, user_experience, weighted_total, notes, community_bonus)
                VALUES (:submission_id, :judge_name, 1, :innovation, :technical_execution,
                        :market_potential, :user_experience, :weighted_total, :notes, 0.0)
            """),
            {
                "submission_id": submission_id,
                "judge_name": judge_name,
                "innovation": scores["innovation"],
                "technical_execution": scores["technical_execution"],
                "market_potential": scores["market_potential"],
                "user_experience": scores["user_experience"],
                "weighted_total": weighted_total,
                "notes": json.dumps({"overall_comment": comment}),
            },
        )

        # Round 2 synthesis (slightly adjusted scores)
        round2_adjustment = random.uniform(-0.5, 0.8)  # Community influence
        round2_total = min(10.0, max(0.0, weighted_total + round2_adjustment))

        synthesis_comment = f"After community feedback: {comment.split('.')[0].lower()}. " + (
            "Community response was very positive."
            if round2_adjustment > 0.2
            else "Mixed community reactions."
            if round2_adjustment > -0.2
            else "Community had some concerns."
        )

        conn.execute(
            text("""
                INSERT INTO hackathon_scores
                (submission_id, judge_name, round, innovation, technical_execution,
                 market_potential, user_experience, weighted_total, notes, community_bonus, final_verdict)
                VALUES (:submission_id, :judge_name, 2, :innovation, :technical_execution,
                        :market_potential, :user_experience, :weighted_total, :notes, :community_bonus, :final_verdict)
            """),
            {
                "submission_id": submission_id,
                "judge_name": judge_name,
                "innovation": scores["innovation"],
                "technical_execution": scores["technical_execution"],
                "market_potential": scores["market_potential"],
                "user_experience": scores["user_experience"],
                "weighted_total": round2_total,
                "notes": json.dumps({"round2_final_verdict": synthesis_comment}),
                "community_bonus": round2_adjustment,
                "final_verdict": synthesis_comment,
            },
        )

        conn.commit()


def add_community_feedback(submissions, client, headers):
    """Add some community likes/dislikes for realism"""
    for submission in submissions[:5]:  # Add feedback to first 5 submissions
        # Simulate some community voting
        for _ in range(random.randint(2, 8)):
            action = random.choice(["like", "like", "like", "dislike"])  # Bias toward likes

            try:
                client.post(
                    f"/api/submissions/{submission['id']}/like-dislike", json={"action": action}, headers=headers
                )
                # Don't assert since we expect some to fail (same user voting multiple times)
            except Exception:
                pass  # Expected: duplicate votes from same user are rejected


if __name__ == "__main__":
    try:
        submissions = create_test_submissions_with_scores()

        print("\n🎯 Test Data Summary:")
        for sub in submissions:
            print(f"  • {sub['name']} ({sub['category']}) - {sub['quality']} quality")

        print(f"\n📊 Database location: {Path(__file__).parent.parent.parent / 'data' / 'hackathon.db'}")
        print("🚀 Start the frontend with: npm run dev")
        print("🏆 View leaderboard at: http://localhost:5173/leaderboard")

    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        sys.exit(1)
