#!/usr/bin/env python3
"""Test script for judge scoring system."""

import json
import sqlite3
from judge_scoring import JudgeScorer

def test_scoring():
    """Test the judge scoring system with sample data."""
    
    # Sample project data
    project_data = {
        'submission_id': 'TEST001',
        'project_title': 'DeFi Yield Aggregator',
        'category': 'DeFi',
        'tech_stack': 'Solidity, Python, React',
        'description': 'Smart routing for optimal DeFi yields across chains',
        'how_it_works': 'AI-powered prediction models route funds to highest yields',
        'problem_solved': 'Users lose money to suboptimal yield strategies',
        'technical_highlights': 'Custom ML model with 89% accuracy'
    }
    
    # Sample research data
    research_data = {
        'github_analysis': {
            'quality_score': 85,
            'languages': {'Solidity': {'percentage': 45}, 'Python': {'percentage': 35}}
        },
        'ai_analysis': """
        This project shows strong technical implementation with a novel approach to yield optimization.
        The ML model is well-trained and the smart contract architecture is solid. Market analysis shows
        significant demand for automated yield farming solutions. Main competitors include Yearn and Harvest.
        """
    }
    
    # Test prompt creation
    scorer = JudgeScorer()
    
    print("Testing judge scoring prompts...\n")
    
    judges = ['aimarc', 'aishaw', 'spartan', 'peepo']
    
    for judge in judges:
        print(f"\n{'='*60}")
        print(f"Judge: {judge.upper()}")
        print(f"{'='*60}")
        
        prompt = scorer.create_scoring_prompt(judge, project_data, research_data)
        
        # Show first 500 chars of prompt
        print(prompt[:500] + "...")
        
        # Test score parsing with sample response
        sample_response = """
INNOVATION_SCORE: 8
INNOVATION_REASON: This ML-powered yield routing is clever and addresses a real pain point.

TECHNICAL_SCORE: 7
TECHNICAL_REASON: Solid implementation but could use more comprehensive testing.

MARKET_SCORE: 9
MARKET_REASON: Huge TAM in DeFi yield optimization, clear monetization path.

EXPERIENCE_SCORE: 6
EXPERIENCE_REASON: Functional but needs UI polish for mainstream adoption.

OVERALL_COMMENT: This could be the next Yearn if they nail the execution!
"""
        
        scores, reasoning, comment = scorer.parse_scoring_response(sample_response)
        
        print(f"\nParsed scores: {scores}")
        print(f"Weighted total: {scorer.calculate_weighted_score(judge, scores)}")
        print(f"Overall comment: {comment}")
    
    print("\n✅ Scoring system test complete!")

if __name__ == "__main__":
    test_scoring()