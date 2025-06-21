#!/usr/bin/env python3
"""Test script for hackathon sheet processor."""

import json
import sqlite3

# Create test data that simulates Google Sheets format
test_data = [
    # Headers row
    [
        "Submission ID", "Project Name", "One-line Description", "Category",
        "Team/Builder Name", "Contact Email", "Discord Handle", "Twitter/X Handle",
        "Demo Video URL", "GitHub Repo Link", "Live Demo URL",
        "How does it work?", "What problem does it solve?",
        "What's the coolest technical part?", "What are you building next?",
        "Tech Stack", "Additional Team Members"
    ],
    # Sample submission 1
    [
        "HACK001", "DeFi Yield Aggregator", "Smart routing for optimal DeFi yields across chains",
        "DeFi", "Team Alpha", "team@alpha.com", "alpha#1234", "@teamalpha",
        "https://youtube.com/watch?v=demo1", "https://github.com/teamalpha/yield-agg",
        "https://yield-agg.vercel.app",
        "Our protocol automatically finds and routes funds to the highest yielding DeFi protocols across multiple chains using AI-powered prediction models.",
        "DeFi users lose money to suboptimal yield strategies and high gas costs from manual rebalancing.",
        "We built a custom ML model that predicts yield changes 24h in advance with 89% accuracy using on-chain data.",
        "Adding support for 10 more chains and launching our governance token.",
        "Solidity, Python, TensorFlow, React, ethers.js",
        "Alice (Smart Contracts), Bob (ML), Charlie (Frontend)"
    ],
    # Sample submission 2 - with some missing optional fields
    [
        "HACK002", "AI Code Assistant", "GPT-powered coding assistant for Solidity",
        "AI/Agents", "SolBot Team", "contact@solbot.ai", "solbot#5678", "",
        "https://vimeo.com/demo2", "https://github.com/solbot/assistant",
        "",
        "Integration with VSCode that provides real-time Solidity suggestions.",
        "Solidity developers waste time on boilerplate and common patterns.",
        "Custom trained model on 1M+ verified smart contracts.",
        "IDE plugins for all major editors.",
        "TypeScript, Python, OpenAI API",
        ""
    ]
]

def test_hackathon_processing():
    """Test the hackathon data processing."""
    print("Testing hackathon data processing...")
    
    # Simulate sheet processing
    headers = test_data[0]
    submissions = []
    
    for row in test_data[1:]:
        # Map data
        data = {}
        mapping = {
            'Project Name': 'project_title',
            'One-line Description': 'description',
            'Category': 'category',
            'Team/Builder Name': 'team_name',
            'Demo Video URL': 'demo_video_url',
            'GitHub Repo Link': 'github_url',
            'Tech Stack': 'tech_stack'
        }
        
        for col, field in mapping.items():
            if col in headers:
                idx = headers.index(col)
                if idx < len(row):
                    data[field] = row[idx]
        
        submissions.append(data)
        print(f"\nProcessed: {data.get('project_title', 'Unknown')}")
        print(f"  Category: {data.get('category', 'N/A')}")
        print(f"  GitHub: {data.get('github_url', 'N/A')}")
    
    # Test database insertion
    print("\nTesting database operations...")
    conn = sqlite3.connect('data/pitches.db')
    cursor = conn.cursor()
    
    # Check if hackathon fields exist
    cursor.execute("PRAGMA table_info(pitches)")
    columns = [col[1] for col in cursor.fetchall()]
    
    hackathon_fields = ['category', 'github_url', 'demo_video_url', 'tech_stack']
    missing = [f for f in hackathon_fields if f not in columns]
    
    if missing:
        print(f"❌ Missing hackathon fields in database: {missing}")
    else:
        print("✅ All hackathon fields present in database")
    
    # Check hackathon_scores table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='hackathon_scores'")
    if cursor.fetchone():
        print("✅ hackathon_scores table exists")
    else:
        print("❌ hackathon_scores table missing")
    
    conn.close()
    
    # Save test data as JSON
    with open('data/test_hackathon_submissions.json', 'w') as f:
        json.dump({
            "type": "hackathon_test_data",
            "submissions": submissions
        }, f, indent=2)
    print("\nTest data saved to data/test_hackathon_submissions.json")

if __name__ == "__main__":
    test_hackathon_processing()