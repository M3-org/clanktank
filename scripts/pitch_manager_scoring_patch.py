#!/usr/bin/env python3
"""
Patch for pitch_manager.py to add hackathon scoring commands.
This shows the modifications needed to integrate judge scoring.
"""

# Add to imports:
"""
from judge_scoring import JudgeScorer
"""

# Add to argparse setup (after line 78):
"""
# Hackathon scoring commands
parser.add_argument(
    "--score",
    nargs=3,
    metavar=('SUBMISSION_ID', 'JUDGE', 'ROUND'),
    help="Score a project with specific judge (e.g., --score ABC123 aimarc 1)"
)

parser.add_argument(
    "--score-all",
    type=int,
    metavar='ROUND',
    help="Have all judges score all unscored projects for a round"
)

parser.add_argument(
    "--show-scores",
    type=str,
    metavar='SUBMISSION_ID',
    help="Display all scores for a project"
)

parser.add_argument(
    "--leaderboard",
    action="store_true",
    help="Show hackathon leaderboard with final scores"
)
"""

# Add scoring functions:
def score_project(db_file, submission_id, judge_name, round_num):
    """Score a specific project with a specific judge."""
    scorer = JudgeScorer(db_path=db_file)
    
    # Get project data
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT project_title, pitch_info, category, tech_stack, research_findings
        FROM pitches WHERE submission_id = ?
    """, (submission_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        logger.error(f"Project {submission_id} not found")
        return
    
    title, pitch_info_json, category, tech_stack, research_json = result
    
    # Parse data
    pitch_info = json.loads(pitch_info_json) if pitch_info_json else {}
    research_data = json.loads(research_json) if research_json else {}
    
    project_data = {
        'submission_id': submission_id,
        'project_title': title,
        'category': category,
        'tech_stack': tech_stack,
        'description': pitch_info.get('description', ''),
        'how_it_works': pitch_info.get('how_it_works', ''),
        'problem_solved': pitch_info.get('problem_solved', ''),
        'technical_highlights': pitch_info.get('technical_highlights', '')
    }
    
    # Score the project
    logger.info(f"Scoring {title} with judge {judge_name} for round {round_num}")
    scoring_data = scorer.score_project(judge_name, submission_id, project_data, research_data, round_num)
    
    if scoring_data:
        logger.info(f"Scoring complete. Weighted total: {scoring_data['weighted_total']}")
    else:
        logger.error("Scoring failed")

def score_all_projects(db_file, round_num):
    """Have all judges score all projects for a round."""
    scorer = JudgeScorer(db_path=db_file)
    scorer.score_all_projects(round_num)

def show_project_scores(db_file, submission_id):
    """Display all scores for a project."""
    scorer = JudgeScorer(db_path=db_file)
    scores = scorer.get_project_scores(submission_id)
    
    if not scores:
        logger.info(f"No scores found for {submission_id}")
        return
    
    # Get project title
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT project_title FROM pitches WHERE submission_id = ?", (submission_id,))
    result = cursor.fetchone()
    conn.close()
    
    title = result[0] if result else submission_id
    
    print(f"\n{'='*60}")
    print(f"Scores for: {title}")
    print(f"{'='*60}")
    
    for score_data in scores:
        print(f"\n{score_data['judge'].upper()} (Round {score_data['round']})")
        print(f"Weighted Total: {score_data['weighted_total']}")
        print("\nCriteria Scores:")
        for criterion, value in score_data['scores'].items():
            print(f"  {criterion.replace('_', ' ').title()}: {value}/10")
        print(f"\nOverall Comment: {score_data['overall_comment']}")
        print("-" * 40)

def show_leaderboard(db_file):
    """Display hackathon leaderboard."""
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Use the view created in migration
    cursor.execute("""
        SELECT 
            project_title,
            category,
            ROUND(avg_innovation, 1) as innovation,
            ROUND(avg_technical, 1) as technical,
            ROUND(avg_market, 1) as market,
            ROUND(avg_experience, 1) as experience,
            ROUND(total_score, 2) as judge_score,
            ROUND(community_bonus, 2) as community,
            ROUND(final_score, 2) as total
        FROM hackathon_final_scores
        ORDER BY final_score DESC
        LIMIT 20
    """)
    
    results = cursor.fetchall()
    conn.close()
    
    if not results:
        logger.info("No scored projects found")
        return
    
    print(f"\n{'='*80}")
    print("CLANK TANK HACKATHON LEADERBOARD")
    print(f"{'='*80}")
    print(f"{'Rank':<5} {'Project':<25} {'Category':<12} {'Judge':<8} {'Comm':<6} {'TOTAL':<8}")
    print(f"{'-'*5} {'-'*25} {'-'*12} {'-'*8} {'-'*6} {'-'*8}")
    
    for i, row in enumerate(results, 1):
        title = row[0][:24] + '…' if len(row[0]) > 25 else row[0]
        print(f"{i:<5} {title:<25} {row[1]:<12} {row[6]:<8} {row[7]:<6} {row[8]:<8}")
    
    print(f"\n{'='*80}")

# Add to main() function:
"""
# In the main() function, add handling for new commands:

if args.score:
    submission_id, judge_name, round_num = args.score
    score_project(args.db_file, submission_id, judge_name, int(round_num))

elif args.score_all:
    score_all_projects(args.db_file, args.score_all)

elif args.show_scores:
    show_project_scores(args.db_file, args.show_scores)

elif args.leaderboard:
    show_leaderboard(args.db_file)
"""