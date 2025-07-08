#!/usr/bin/env python3
"""
Hackathon Manager - AI Judge Scoring System.
Implements personality-based evaluation with weighted scoring for hackathon submissions.
Works exclusively with the hackathon database.
"""

import os
import json
import logging
import sqlite3
import requests
import argparse
import re
import time
from datetime import datetime
from typing import Dict, Any, List
from dotenv import load_dotenv

# Import versioned schema helpers
from hackathon.backend.schema import LATEST_SUBMISSION_VERSION, get_fields

# Import judge personas and weights
from hackathon.prompts.judge_personas import (
    JUDGE_PERSONAS,
    JUDGE_WEIGHTS,
    get_judge_persona,
)

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
HACKATHON_DB_PATH = os.getenv("HACKATHON_DB_PATH", "data/hackathon.db")
AI_MODEL_PROVIDER = os.getenv("AI_MODEL_PROVIDER", "openrouter")
AI_MODEL_NAME = os.getenv("AI_MODEL_NAME", "anthropic/claude-3-opus")

# OpenRouter API configuration
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "submission_schema.json")


def get_v2_fields_from_schema():
    with open(SCHEMA_PATH) as f:
        schema = json.load(f)
    return [f["name"] for f in schema["schemas"]["v2"]]


# In all scoring and prompt logic, use get_v2_fields_from_schema() for field access and validation.


class HackathonManager:
    def __init__(self, db_path=None, version=None):
        """Initialize the hackathon manager."""
        if not OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")

        self.db_path = db_path or os.getenv("HACKATHON_DB_PATH", "data/hackathon.db")
        self.version = version or LATEST_SUBMISSION_VERSION
        self.table = f"hackathon_submissions_{self.version}"
        self.fields = get_fields(self.version)

        self.headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/m3-org/clanktank",
            "X-Title": "Clank Tank Hackathon Judge Scoring",
        }

    def create_scoring_prompt(
        self,
        judge_name: str,
        project_data: Dict[str, Any],
        research_data: Dict[str, Any],
    ) -> str:
        """Create a detailed scoring prompt for a specific judge."""
        persona = JUDGE_PERSONAS.get(judge_name, "")
        
        # Hardened scoring scale with explicit anchors
        SCALE = """
SCORE SCALE (use these anchors):
10 – Benchmark-setting, better than 95% of open-source projects
 8 – Strong; minor issues only experts notice
 6 – Adequate; clear rough edges
 4 – Significant gaps or shortcuts
 2 – Barely functional / mostly boilerplate
 0 – Non-working, plagiarized, or irrelevant
"""

        # Parse research data
        github_analysis = {}
        ai_research = {}

        if "github_analysis" in research_data:
            github_analysis = (
                json.loads(research_data["github_analysis"])
                if isinstance(research_data["github_analysis"], str)
                else research_data["github_analysis"]
            )

        if "market_research" in research_data:
            market_research = (
                json.loads(research_data["market_research"])
                if isinstance(research_data["market_research"], str)
                else research_data["market_research"]
            )
            ai_research.update(market_research)

        if "technical_assessment" in research_data:
            tech_assessment = (
                json.loads(research_data["technical_assessment"])
                if isinstance(research_data["technical_assessment"], str)
                else research_data["technical_assessment"]
            )
            ai_research.update(tech_assessment)

        # Extract key insights and red flags from research
        is_fork = github_analysis.get("is_fork", False) if github_analysis else False
        contributors = (
            github_analysis.get("contributors_count", 1) if github_analysis else 1
        )
        
        # Extract red flags from AI research if available
        red_flags = ai_research.get("Red Flags", []) if isinstance(ai_research.get("Red Flags"), list) else []
        red_flags_section = ""
        if red_flags:
            red_flags_section = f"""
RESEARCH-IDENTIFIED RED FLAGS:
{chr(10).join(f"• {flag}" for flag in red_flags)}
"""

        prompt = f"""{persona}

{SCALE}

You are judging this hackathon project for Clank Tank. Evaluate it based on your unique perspective.

PROJECT DETAILS:
Name: {project_data.get('project_name', 'Untitled')}
Category: {project_data.get('category', 'Unknown')}
Description: {project_data.get('description', 'No description')}

Problem solved: {project_data.get('problem_solved', 'Not provided')}
Favorite part: {project_data.get('favorite_part', 'Not provided')}
Solana Address: {project_data.get('solana_address', 'Not provided')}

RESEARCH FINDINGS:
Is Fork: {is_fork}
Contributors: {contributors}
{red_flags_section}
AI Research: {json.dumps(ai_research, indent=2) if ai_research else 'No AI research available'}

SCORING TASK:
Rate each criterion from 0-10 (whole numbers only).
**Your reasoning must cite at least one weakness or risk.**
Do not give >8 unless you reference a concrete, verifiable feature that meets production-grade standards.
Provide your reasoning in 2-3 sentences for each score, staying true to your personality.

Format your response EXACTLY like this:
INNOVATION_SCORE: [0-10]
INNOVATION_REASON: [Your reasoning - must include at least one criticism or concern]

TECHNICAL_SCORE: [0-10]
TECHNICAL_REASON: [Your reasoning - must include at least one criticism or concern]

MARKET_SCORE: [0-10]
MARKET_REASON: [Your reasoning - must include at least one criticism or concern]

EXPERIENCE_SCORE: [0-10]
EXPERIENCE_REASON: [Your reasoning - must include at least one criticism or concern]

OVERALL_COMMENT: [One punchy line summarizing your view of this project in your unique style]"""

        return prompt

    def parse_scoring_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the AI's scoring response into structured data."""
        scores = {}
        reasons = {}
        overall_comment = ""

        # Parse scores and reasons using regex
        patterns = {
            "innovation": r"INNOVATION_SCORE:\s*(\d+)",
            "innovation_reason": r"INNOVATION_REASON:\s*(.+?)(?=\n[A-Z]|$)",
            "technical_execution": r"TECHNICAL_SCORE:\s*(\d+)",
            "technical_reason": r"TECHNICAL_REASON:\s*(.+?)(?=\n[A-Z]|$)",
            "market_potential": r"MARKET_SCORE:\s*(\d+)",
            "market_reason": r"MARKET_REASON:\s*(.+?)(?=\n[A-Z]|$)",
            "user_experience": r"EXPERIENCE_SCORE:\s*(\d+)",
            "experience_reason": r"EXPERIENCE_REASON:\s*(.+?)(?=\n[A-Z]|$)",
            "overall": r"OVERALL_COMMENT:\s*(.+?)(?=\n|$)",
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, response_text, re.MULTILINE | re.DOTALL)
            if match:
                if "reason" in key:
                    reasons[key.replace("_reason", "")] = match.group(1).strip()
                elif key == "overall":
                    overall_comment = match.group(1).strip()
                else:
                    try:
                        score = int(match.group(1))
                        scores[key] = max(0, min(10, score))
                    except (ValueError, IndexError):
                        logger.warning(
                            f"Could not parse score for {key}, defaulting to 5."
                        )
                        scores[key] = 5

        # Validate we have all required scores, default if missing
        required_scores = [
            "innovation",
            "technical_execution",
            "market_potential",
            "user_experience",
        ]
        for criterion in required_scores:
            if criterion not in scores:
                logger.warning(f"Missing score for {criterion}, defaulting to 5")
                scores[criterion] = 5

        return {
            "scores": scores,
            "reasons": reasons,
            "overall_comment": overall_comment,
        }

    def renormalize_scores(self, scores, target_mean=6):
        """Post-hoc score normalization to prevent grade inflation."""
        if not scores:
            return scores
        
        cur_mean = sum(scores) / len(scores)
        if cur_mean == 0:
            return scores
            
        factor = target_mean / cur_mean
        normalized = [max(0, min(10, round(s * factor, 1))) for s in scores]
        
        logger.info(f"Score normalization: mean {cur_mean:.1f} → {sum(normalized)/len(normalized):.1f}")
        return normalized

    def calculate_weighted_score(
        self, judge_name: str, raw_scores: Dict[str, float], normalize: bool = False
    ) -> float:
        """Calculate the weighted total score for a judge."""
        weights = JUDGE_WEIGHTS.get(judge_name, {})
        weighted_total = 0

        # Map score keys to weight keys
        score_mapping = {
            "innovation": "innovation",
            "technical_execution": "technical_execution",
            "market_potential": "market_potential",
            "user_experience": "user_experience",
        }

        # Apply normalization if requested
        if normalize:
            score_values = [raw_scores.get(key, 5) for key in score_mapping.keys()]
            normalized_values = self.renormalize_scores(score_values)
            normalized_scores = dict(zip(score_mapping.keys(), normalized_values))
        else:
            normalized_scores = raw_scores

        for score_key, weight_key in score_mapping.items():
            if score_key in normalized_scores and weight_key in weights:
                weighted_total += normalized_scores[score_key] * weights[weight_key]

        return round(weighted_total, 2)

    def get_ai_scores(
        self,
        judge_name: str,
        project_data: Dict[str, Any],
        research_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Get AI-generated scores for a specific judge."""
        prompt = self.create_scoring_prompt(judge_name, project_data, research_data)

        payload = {
            "model": AI_MODEL_NAME,
            "messages": [
                {
                    "role": "system",
                    "content": f"You are {judge_name}, a judge in the Clank Tank hackathon. Stay in character and evaluate projects from your unique perspective.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 1500,
        }

        try:
            logger.info(
                f"Getting scores from {judge_name} for {project_data['project_name']}"
            )
            response = requests.post(BASE_URL, json=payload, headers=self.headers)
            response.raise_for_status()

            result = response.json()
            content = result["choices"][0]["message"]["content"]

            # Parse the response
            parsed = self.parse_scoring_response(content)

            # Calculate weighted score
            weighted_total = self.calculate_weighted_score(judge_name, parsed["scores"])

            # Compile final scores
            judge_scores = {
                "judge_name": judge_name,
                "innovation": parsed["scores"]["innovation"],
                "technical_execution": parsed["scores"]["technical_execution"],
                "market_potential": parsed["scores"]["market_potential"],
                "user_experience": parsed["scores"]["user_experience"],
                "weighted_total": weighted_total,
                "notes": json.dumps(
                    {
                        "reasons": parsed["reasons"],
                        "overall_comment": parsed["overall_comment"],
                    }
                ),
            }

            return judge_scores

        except Exception as e:
            logger.error(f"Failed to get scores from {judge_name}: {e}")
            # Return default scores on error
            return {
                "judge_name": judge_name,
                "innovation": 5,
                "technical_execution": 5,
                "market_potential": 5,
                "user_experience": 5,
                "weighted_total": 20.0,
                "notes": json.dumps({"error": str(e)}),
            }

    def score_submission(
        self, submission_id: str, round_num: int = 1
    ) -> List[Dict[str, Any]]:
        """Score a single submission with all judges."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                f"""
                SELECT * FROM {self.table} 
                WHERE submission_id = ?
            """,
                (submission_id,),
            )

            row = cursor.fetchone()
            if not row:
                raise ValueError(
                    f"Submission {submission_id} not found in {self.table}"
                )

            # Convert to dictionary
            columns = [desc[0] for desc in cursor.description]
            project_data = dict(zip(columns, row))

            # Fetch research data
            cursor.execute(
                """
                SELECT * FROM hackathon_research 
                WHERE submission_id = ?
            """,
                (submission_id,),
            )

            research_row = cursor.fetchone()
            research_data = {}
            if research_row:
                research_columns = [desc[0] for desc in cursor.description]
                research_data = dict(zip(research_columns, research_row))

            # Get scores from each judge
            all_scores = []
            judges = ["aimarc", "aishaw", "spartan", "peepo"]

            for judge_name in judges:
                judge_scores = self.get_ai_scores(
                    judge_name, project_data, research_data
                )
                judge_scores["submission_id"] = submission_id
                judge_scores["round"] = round_num

                # Save to database
                cursor.execute(
                    """
                    INSERT INTO hackathon_scores 
                    (submission_id, judge_name, round, innovation, technical_execution,
                     market_potential, user_experience, weighted_total, notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        submission_id,
                        judge_scores["judge_name"],
                        round_num,
                        judge_scores["innovation"],
                        judge_scores["technical_execution"],
                        judge_scores["market_potential"],
                        judge_scores["user_experience"],
                        judge_scores["weighted_total"],
                        judge_scores["notes"],
                        datetime.now().isoformat(),
                    ),
                )

                all_scores.append(judge_scores)

                # Rate limiting
                time.sleep(1)

            # Update submission status
            cursor.execute(
                f"""
                UPDATE {self.table} 
                SET status = 'scored', updated_at = ?
                WHERE submission_id = ?
            """,
                (datetime.now().isoformat(), submission_id),
            )

            conn.commit()
            
            # Simple audit logging
            from hackathon.backend.simple_audit import log_system_action
            log_system_action("submission_scored", submission_id)
            
            logger.info(f"Scoring completed for {submission_id}")

            return all_scores

        except Exception as e:
            logger.error(f"Failed to score submission {submission_id}: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def score_all_researched(self, round_num: int = 1) -> Dict[str, Any]:
        """Score all submissions with status 'researched'."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            f"""
            SELECT submission_id, project_name 
            FROM {self.table} 
            WHERE status = 'researched'
            ORDER BY created_at
        """
        )

        pending_submissions = cursor.fetchall()
        conn.close()

        if not pending_submissions:
            logger.info("No researched submissions to score")
            return {"scored": 0, "failed": 0}

        logger.info(f"Found {len(pending_submissions)} submissions to score")

        results = {"scored": 0, "failed": 0}

        for submission_id, project_name in pending_submissions:
            try:
                logger.info(f"Scoring: {project_name} ({submission_id})")
                self.score_submission(submission_id, round_num)
                results["scored"] += 1

            except Exception as e:
                logger.error(f"Failed to score {submission_id}: {e}")
                results["failed"] += 1
                continue

        return results

    def get_leaderboard(self, round_num: int = None) -> List[Dict[str, Any]]:
        """Get the current leaderboard with average scores from the latest available round."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # If no round specified, use the latest available round
        if round_num is None:
            cursor.execute("SELECT MAX(round) FROM hackathon_scores")
            latest_round = cursor.fetchone()[0] or 1
            round_num = latest_round

        cursor.execute(
            f"""
            SELECT 
                s.submission_id,
                s.project_name,
                s.category,
                AVG(sc.weighted_total) as avg_score,
                COUNT(DISTINCT sc.judge_name) as judge_count
            FROM {self.table} s
            JOIN hackathon_scores sc ON s.submission_id = sc.submission_id
            WHERE sc.round = ?
            GROUP BY s.submission_id
            ORDER BY avg_score DESC
        """,
            (round_num,),
        )

        leaderboard = []
        for row in cursor.fetchall():
            leaderboard.append(
                {
                    "rank": len(leaderboard) + 1,
                    "submission_id": row[0],
                    "project_name": row[1],
                    "category": row[2],
                    "avg_score": round(row[3], 2),
                    "judge_count": row[4],
                }
            )

        conn.close()
        return leaderboard

    def analyze_score_distribution(self, round_num: int = 1) -> Dict[str, Any]:
        """Analyze the distribution of scores across all submissions for comparative reasoning."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all scores for the round
        cursor.execute(
            """
            SELECT 
                s.submission_id,
                s.project_name,
                s.category,
                sc.judge_name,
                sc.innovation,
                sc.technical_execution,
                sc.market_potential,
                sc.user_experience,
                sc.weighted_total,
                sc.notes
            FROM hackathon_scores sc
            JOIN hackathon_submissions_v2 s ON sc.submission_id = s.submission_id
            WHERE sc.round = ?
            ORDER BY sc.weighted_total DESC
            """,
            (round_num,),
        )
        
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            return {"error": "No scores found for this round"}
        
        # Organize data
        projects = {}
        all_scores = []
        
        for row in results:
            submission_id, project_name, category, judge_name, innovation, technical, market, experience, weighted_total, notes = row
            
            if submission_id not in projects:
                projects[submission_id] = {
                    "project_name": project_name,
                    "category": category,
                    "judges": {},
                    "avg_score": 0,
                    "score_variance": 0
                }
            
            # Parse notes to extract reasoning
            try:
                judge_notes = json.loads(notes) if notes else {}
            except:
                judge_notes = {"raw": notes}
            
            projects[submission_id]["judges"][judge_name] = {
                "innovation": innovation,
                "technical_execution": technical,
                "market_potential": market,
                "user_experience": experience,
                "weighted_total": weighted_total,
                "notes": judge_notes
            }
            
            all_scores.append(weighted_total)
        
        # Calculate statistics
        import statistics
        
        for project_id in projects:
            judge_scores = [judge_data["weighted_total"] for judge_data in projects[project_id]["judges"].values()]
            projects[project_id]["avg_score"] = statistics.mean(judge_scores)
            projects[project_id]["score_variance"] = statistics.variance(judge_scores) if len(judge_scores) > 1 else 0
        
        # Overall distribution stats
        distribution_stats = {
            "mean": statistics.mean(all_scores),
            "median": statistics.median(all_scores),
            "std_dev": statistics.stdev(all_scores) if len(all_scores) > 1 else 0,
            "min": min(all_scores),
            "max": max(all_scores),
            "total_projects": len(projects),
            "score_ranges": {
                "excellent": len([s for s in all_scores if s >= 32]),  # 8+ avg
                "good": len([s for s in all_scores if 24 <= s < 32]),   # 6-8 avg
                "average": len([s for s in all_scores if 16 <= s < 24]), # 4-6 avg
                "poor": len([s for s in all_scores if s < 16])          # <4 avg
            }
        }
        
        # Rank projects
        ranked_projects = sorted(projects.items(), key=lambda x: x[1]["avg_score"], reverse=True)
        
        return {
            "distribution_stats": distribution_stats,
            "projects": dict(ranked_projects),
            "rankings": [(project_id, data["project_name"], data["avg_score"]) for project_id, data in ranked_projects]
        }

    def generate_comparative_reasoning(self, target_project_id: str, round_num: int = 1) -> str:
        """Generate comparative reasoning for a project against others in the same round."""
        distribution_data = self.analyze_score_distribution(round_num)
        
        if "error" in distribution_data:
            return "No comparative data available for reasoning."
        
        projects = distribution_data["projects"]
        stats = distribution_data["distribution_stats"]
        rankings = distribution_data["rankings"]
        
        if target_project_id not in projects:
            return "Target project not found in score distribution."
        
        target_project = projects[target_project_id]
        target_score = target_project["avg_score"]
        
        # Find project's rank
        target_rank = next((i + 1 for i, (pid, _, _) in enumerate(rankings) if pid == target_project_id), None)
        
        # Identify comparative context
        better_projects = [p for p in projects.values() if p["avg_score"] > target_score]
        worse_projects = [p for p in projects.values() if p["avg_score"] < target_score]
        
        # Find most similar projects (within 2 points)
        similar_projects = [
            (pid, data) for pid, data in projects.items() 
            if pid != target_project_id and abs(data["avg_score"] - target_score) <= 2.0
        ]
        
        # Extract common criticisms from better projects
        better_criticisms = []
        for project_data in better_projects[:3]:  # Top 3 better projects
            for judge_data in project_data["judges"].values():
                reasons = judge_data.get("notes", {}).get("reasons", {})
                for criterion, reason in reasons.items():
                    if "but" in reason.lower() or "however" in reason.lower() or "concern" in reason.lower():
                        better_criticisms.append(f"{criterion}: {reason}")
        
        # Extract common strengths from worse projects
        worse_strengths = []
        for project_data in worse_projects[-3:]:  # Bottom 3 worse projects
            for judge_data in project_data["judges"].values():
                reasons = judge_data.get("notes", {}).get("reasons", {})
                for criterion, reason in reasons.items():
                    if any(word in reason.lower() for word in ["good", "strong", "impressive", "solid"]):
                        worse_strengths.append(f"{criterion}: {reason}")
        
        # Generate comparative summary
        percentile = (len(worse_projects) / len(projects)) * 100 if projects else 0
        
        reasoning = f"""
COMPARATIVE ANALYSIS FOR {target_project["project_name"]}:

RANKING CONTEXT:
- Ranked #{target_rank} out of {stats['total_projects']} projects
- Score: {target_score:.1f} (Hackathon mean: {stats['mean']:.1f}, median: {stats['median']:.1f})
- Percentile: {percentile:.0f}th percentile
- Judge consensus: {'High' if target_project['score_variance'] < 2 else 'Low'} (variance: {target_project['score_variance']:.1f})

COMPETITIVE LANDSCAPE:
- {len(better_projects)} projects scored higher (avg gap: {(sum(p['avg_score'] for p in better_projects) / len(better_projects) - target_score):.1f} points)
- {len(worse_projects)} projects scored lower
- {len(similar_projects)} projects in similar score range (±2 points)

RELATIVE POSITIONING:
{f"This project outperformed {percentile:.0f}% of submissions" if percentile > 50 else f"This project underperformed compared to {100-percentile:.0f}% of submissions"}
{"" if len(better_criticisms) == 0 else f"Common issues in higher-ranked projects that this project might share: {'; '.join(better_criticisms[:2])}"}
{"" if len(worse_strengths) == 0 else f"Potential advantages over lower-ranked projects: {'; '.join(worse_strengths[:2])}"}
"""
        
        return reasoning.strip()

    def run_round2_synthesis(self, project_id: str = None):
        """Enhanced Round 2 synthesis with comparative reasoning and distribution analysis."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get projects ready for Round 2
        if project_id:
            cursor.execute(
                f"SELECT submission_id FROM {self.table} WHERE submission_id = ? AND status = 'community-voting'",
                (project_id,),
            )
        else:
            cursor.execute(
                f"SELECT submission_id FROM {self.table} WHERE status = 'community-voting'"
            )

        project_ids = [row[0] for row in cursor.fetchall()]

        if not project_ids:
            print("No projects ready for Round 2 synthesis")
            conn.close()
            return

        # Get comparative analysis for all projects
        print(f"Analyzing score distribution across {len(project_ids)} projects...")
        distribution_analysis = self.analyze_score_distribution(round_num=1)
        
        # Get community feedback data (as context, not bonus)
        community_data = self._get_community_feedback_context(cursor, project_ids)

        for project_id in project_ids:
            print(f"\nProcessing Round 2 for {project_id}...")

            # Get Round 1 scores
            cursor.execute(
                "SELECT judge_name, weighted_total, notes FROM hackathon_scores WHERE submission_id = ? AND round = 1",
                (project_id,),
            )
            r1_scores = {
                row[0]: {"score": row[1], "notes": json.loads(row[2] or "{}")}
                for row in cursor.fetchall()
            }

            # Generate comparative reasoning
            comparative_reasoning = self.generate_comparative_reasoning(project_id, round_num=1)

            # Generate final verdicts with comparative context
            for judge in ["aimarc", "aishaw", "peepo", "spartan"]:
                if judge not in r1_scores:
                    continue

                # Get structured Round 2 response
                round2_response = self._generate_final_verdict_with_comparison(
                    project_id, 
                    judge, 
                    r1_scores[judge], 
                    community_data[project_id],
                    comparative_reasoning,
                    distribution_analysis
                )
                
                # Parse structured response
                parsed_response = self._parse_round2_response(round2_response)
                
                # Calculate Round 2 score based on structured response
                final_score = self._calculate_judge_round2_score(
                    judge, r1_scores[judge]["score"], round2_response, community_data[project_id]
                )

                # Store Round 2 data with flattened, logical structure
                cursor.execute(
                    """
                    INSERT INTO hackathon_scores 
                    (submission_id, judge_name, round, weighted_total, notes, created_at)
                    VALUES (?, ?, 2, ?, ?, ?)
                """,
                    (
                        project_id,
                        judge,
                        final_score,
                        json.dumps({
                            # Round 2 core data
                            "round2_final_verdict": parsed_response.get("final_verdict", ""),
                            "round2_reasoning": parsed_response.get("reasoning", ""),
                            "score_revision": parsed_response.get("score_revision", {}),
                            "community_influence": parsed_response.get("community_influence", "unknown"),
                            "confidence": parsed_response.get("confidence", "medium"),
                            
                            # Context data
                            "round1_score": r1_scores[judge]["score"],
                            "comparative_reasoning": comparative_reasoning,
                            "community_context": community_data[project_id],
                            
                            # Metadata
                            "judge_persona": judge,
                            "submission_id": project_id,
                            "synthesis_timestamp": datetime.now().isoformat()
                        }),
                        datetime.now().isoformat(),
                    ),
                )

            # Update submission status
            cursor.execute(
                f"UPDATE {self.table} SET status = 'completed' WHERE submission_id = ?",
                (project_id,),
            )
            print(f"✓ Round 2 completed for {project_id}")

        conn.commit()
        
        # Simple audit logging
        from hackathon.backend.simple_audit import log_system_action
        log_system_action("round2_synthesis_completed", project_id or f"bulk_{len(project_ids)}_projects")
        
        conn.close()

    def _get_community_feedback_context(self, cursor, project_ids):
        """Get community feedback data as context for Round 2 synthesis."""
        import statistics
        
        community_data = {}
        all_reaction_counts = []
        
        # First pass: collect all reaction data and counts for statistical analysis
        for project_id in project_ids:
            # Get total reactions for this project
            cursor.execute(
                "SELECT COUNT(*) FROM community_feedback WHERE submission_id = ?",
                (project_id,),
            )
            total_reactions = cursor.fetchone()[0]
            all_reaction_counts.append(total_reactions)
            
            # Get reaction breakdown
            cursor.execute(
                "SELECT reaction_type, COUNT(*) FROM community_feedback WHERE submission_id = ? GROUP BY reaction_type",
                (project_id,),
            )
            reaction_breakdown = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Get unique voters
            cursor.execute(
                "SELECT COUNT(DISTINCT discord_user_id) FROM community_feedback WHERE submission_id = ?",
                (project_id,),
            )
            unique_voters = cursor.fetchone()[0]
            
            # Store basic data for now
            community_data[project_id] = {
                "total_reactions": total_reactions,
                "unique_voters": unique_voters,
                "reaction_breakdown": reaction_breakdown,
                "engagement_level": "pending"  # Will calculate after getting distribution
            }
        
        # Calculate statistical thresholds based on distribution
        if len(all_reaction_counts) > 1:
            try:
                median_reactions = statistics.median(all_reaction_counts)
                mean_reactions = statistics.mean(all_reaction_counts)
                
                # Use median-based thresholds for more robust classification
                # High: Above median + (median * 0.5)
                # Medium: Above median
                # Low: Below median
                high_threshold = median_reactions + (median_reactions * 0.5)
                medium_threshold = median_reactions
                
                # Fallback to mean-based if median is 0
                if median_reactions == 0:
                    high_threshold = mean_reactions * 1.5
                    medium_threshold = mean_reactions * 0.5
                    
            except statistics.StatisticsError:
                # Fallback to simple thresholds if statistics fail
                high_threshold = 5
                medium_threshold = 2
        else:
            # Single project fallback
            high_threshold = 5
            medium_threshold = 2
        
        # Second pass: assign engagement levels based on calculated thresholds
        for project_id in community_data:
            total_reactions = community_data[project_id]["total_reactions"]
            
            if total_reactions >= high_threshold:
                engagement_level = "high"
            elif total_reactions >= medium_threshold:
                engagement_level = "medium"
            else:
                engagement_level = "low"
                
            community_data[project_id]["engagement_level"] = engagement_level
            
            # Add threshold info for transparency
            community_data[project_id]["thresholds"] = {
                "high": high_threshold,
                "medium": medium_threshold,
                "median": median_reactions if len(all_reaction_counts) > 1 else 0,
                "mean": mean_reactions if len(all_reaction_counts) > 1 else 0
            }

        return community_data

    def _parse_round2_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Round 2 judge response with structured JSON format."""
        import json
        import re
        
        # Try to extract JSON from the response
        json_match = re.search(r'```json\s*\n(.*?)\n```', response_text, re.DOTALL)
        if not json_match:
            # Try to find JSON without code blocks
            json_match = re.search(r'(\{.*\})', response_text, re.DOTALL)
        
        if json_match:
            try:
                json_data = json.loads(json_match.group(1))
                
                # Validate required fields
                required_fields = ['final_verdict', 'score_revision']
                if all(field in json_data for field in required_fields):
                    return {
                        'final_verdict': json_data.get('final_verdict', ''),
                        'score_revision': json_data.get('score_revision', {}),
                        'reasoning': json_data.get('reasoning', ''),
                        'community_influence': json_data.get('community_influence', 'none'),
                        'confidence': json_data.get('confidence', 'medium')
                    }
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON from Round 2 response: {e}")
        
        # Fallback: treat entire response as final_verdict
        logger.warning("Round 2 response not in expected JSON format, using as final_verdict")
        return {
            'final_verdict': response_text.strip(),
            'score_revision': {'type': 'none'},
            'reasoning': 'Non-structured response',
            'community_influence': 'unknown',
            'confidence': 'low'
        }

    def _calculate_judge_round2_score(self, judge_name, round1_score, round2_response, community_context):
        """Calculate Round 2 score based on structured judge response."""
        
        # Parse the structured response
        parsed_response = self._parse_round2_response(round2_response)
        score_revision = parsed_response.get('score_revision', {})
        
        # Handle different types of score revisions
        revision_type = score_revision.get('type', 'none')
        
        if revision_type == 'explicit':
            # Direct score override
            new_score = score_revision.get('new_score')
            if new_score is not None and 0 <= new_score <= 40:
                logger.info(f"{judge_name} provided explicit score revision: {new_score}/40")
                return round(float(new_score), 2)
        
        elif revision_type == 'adjustment':
            # Relative adjustment from Round 1
            adjustment = score_revision.get('adjustment', 0)
            reason = score_revision.get('reason', '')
            final_score = max(0, min(40, round1_score + adjustment))
            logger.info(f"{judge_name} adjusted score by {adjustment:+.1f}: {round1_score} → {final_score} ({reason})")
            return round(final_score, 2)
        
        elif revision_type == 'none':
            # No score change, maintain Round 1 score
            logger.info(f"{judge_name} maintained Round 1 score: {round1_score}/40")
            return round1_score
        
        # Fallback for malformed responses
        logger.warning(f"{judge_name} provided invalid score revision format, maintaining Round 1 score")
        return round1_score

    def _calculate_community_bonuses(self, cursor, project_ids):
        """DEPRECATED: Community feedback is now contextual, not automatic bonus."""
        # Keep for backward compatibility, but returns zero bonuses
        community_data = {}
        for project_id in project_ids:
            community_data[project_id] = {"reactions": 0, "bonus": 0}
        return community_data

    def _generate_final_verdict_with_comparison(self, project_id, judge, r1_data, community_context, comparative_reasoning, distribution_analysis):
        """Generate final verdict with comparative context and community feedback as reasoning signal."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT project_name, description, category FROM {self.table} WHERE submission_id = ?",
            (project_id,),
        )
        project_name, description, category = cursor.fetchone()
        conn.close()

        # Get judge persona for context
        persona = get_judge_persona(judge)

        # Format community feedback for context
        reaction_breakdown = community_context.get("reaction_breakdown", {})
        feedback_summary = "\n".join([
            f"- {reaction_type.replace('_', ' ').title()}: {count} votes"
            for reaction_type, count in reaction_breakdown.items()
        ]) if reaction_breakdown else "No community votes yet"

        # Find this project's ranking context
        projects = distribution_analysis.get("projects", {})
        target_rank = None
        if project_id in projects:
            ranked_projects = sorted(projects.items(), key=lambda x: x[1]["avg_score"], reverse=True)
            target_rank = next((i + 1 for i, (pid, _) in enumerate(ranked_projects) if pid == project_id), None)

        prompt = f"""You are {judge.upper()}, one of the Clank Tank hackathon judges. In Round 1, you provided the following analysis:

ROUND 1 ASSESSMENT:
{r1_data.get('notes', {}).get('overall_comment', 'No specific notes available')}
Your Round 1 weighted score: {r1_data['score']:.1f}/40

COMMUNITY FEEDBACK SIGNAL:
{feedback_summary}
Total reactions: {community_context['total_reactions']} from {community_context['unique_voters']} unique users
Engagement level: {community_context['engagement_level']}

COMPARATIVE CONTEXT:
{comparative_reasoning}

PROJECT DETAILS:
{project_name} ({category}): {description}

YOUR FINAL SYNTHESIS TASK:
Provide your Round 2 assessment in the following JSON format:

```json
{{
  "final_verdict": "Your 2-3 sentence final perspective as {judge.upper()}",
  "score_revision": {{
    "type": "none|adjustment|explicit",
    "new_score": 25.0,
    "adjustment": -2.5,
    "reason": "Brief explanation for score change"
  }},
  "reasoning": "Detailed explanation of your assessment",
  "community_influence": "none|minimal|moderate|significant",
  "confidence": "low|medium|high"
}}
```

SCORE REVISION TYPES:
- "none": Keep Round 1 score unchanged
- "adjustment": Modify Round 1 score by +/- amount (use "adjustment" field)
- "explicit": Replace with entirely new score (use "new_score" field)

Consider:
1. Does your initial technical assessment hold up against the comparative data?
2. What does the community feedback pattern suggest about user appeal vs technical merit?
3. Given the competitive landscape, should you revise your scoring reasoning?
4. If adjusting your score, be explicit about the new value and reasoning.

Respond ONLY with the JSON structure above."""

        try:
            logger.info(f"Getting structured final verdict from {judge} for {project_name}")
            response = requests.post(
                BASE_URL,
                json={
                    "model": AI_MODEL_NAME,
                    "messages": [
                        {"role": "system", "content": persona},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 600,
                    "temperature": 0.3,
                },
                headers=self.headers,
            )

            if response.ok:
                return response.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.warning(f"Failed to get structured final verdict from {judge}: {e}")

        # Fallback response in JSON format
        return f"""{{
  "final_verdict": "Maintaining Round 1 assessment of {r1_data['score']:.1f}/40 considering community feedback pattern and competitive ranking.",
  "score_revision": {{"type": "none"}},
  "reasoning": "API error occurred during Round 2 synthesis",
  "community_influence": "unknown",
  "confidence": "low"
}}"""


def main():
    """Main function with CLI interface."""
    parser = argparse.ArgumentParser(description="Hackathon Judge Scoring System")

    # Scoring commands
    score_group = parser.add_mutually_exclusive_group()
    score_group.add_argument(
        "--score",
        action="store_true",
        help="Score submissions (use with --submission-id or --all)",
    )
    score_group.add_argument(
        "--leaderboard", action="store_true", help="Show current leaderboard"
    )
    score_group.add_argument(
        "--synthesize",
        action="store_true",
        help="Run Round 2 synthesis combining judge scores with community feedback",
    )

    # Scoring options
    parser.add_argument("--submission-id", help="Score a specific submission by ID")
    parser.add_argument(
        "--all", action="store_true", help="Score all researched submissions"
    )
    parser.add_argument(
        "--round", type=int, default=1, help="Round number (default: 1)"
    )
    parser.add_argument("--output", help="Output file for results (JSON)")
    parser.add_argument(
        "--version",
        type=str,
        default="latest",
        choices=["latest", "v1", "v2"],
        help="Submission schema version to use (default: latest)",
    )
    parser.add_argument(
        "--db-file",
        type=str,
        default=None,
        help="Path to the hackathon SQLite database file (default: env or data/hackathon.db)",
    )

    args = parser.parse_args()

    if not any([args.score, args.leaderboard, args.synthesize]):
        parser.print_help()
        return

    # Initialize manager
    try:
        manager = HackathonManager(db_path=args.db_file, version=args.version)
    except ValueError as e:
        logger.error(f"Initialization failed: {e}")
        logger.error("Please ensure OPENROUTER_API_KEY is set in your .env file")
        return

    # Execute commands
    if args.score:
        if args.submission_id:
            try:
                scores = manager.score_submission(args.submission_id, args.round)
                if args.output:
                    with open(args.output, "w") as f:
                        json.dump(scores, f, indent=2)
                    logger.info(f"Scores saved to {args.output}")
                else:
                    print(json.dumps(scores, indent=2))
            except Exception as e:
                logger.error(f"Scoring failed: {e}")

        elif args.all:
            results = manager.score_all_researched(args.round)
            logger.info(
                f"Scoring complete: {results['scored']} succeeded, {results['failed']} failed"
            )

            if args.output:
                with open(args.output, "w") as f:
                    json.dump(results, f, indent=2)

        else:
            logger.error("Please specify --submission-id or --all")

    elif args.leaderboard:
        leaderboard = manager.get_leaderboard(args.round)

        if args.output:
            with open(args.output, "w") as f:
                json.dump(leaderboard, f, indent=2)
            logger.info(f"Leaderboard saved to {args.output}")
        else:
            print(f"\n{'='*60}")
            print(f"CLANK TANK HACKATHON LEADERBOARD - ROUND {args.round}")
            print(f"{'='*60}")
            print(f"{'Rank':<6}{'Project':<30}{'Team':<20}{'Score':<10}")
            print(f"{'-'*60}")

            for entry in leaderboard:
                print(
                    f"{entry['rank']:<6}{entry['project_name'][:28]:<30}{entry['team_name'][:18]:<20}{entry['avg_score']:<10}"
                )

            print(f"{'='*60}\n")

    elif args.synthesize:
        if args.submission_id:
            manager.run_round2_synthesis(args.submission_id)
        elif args.all:
            manager.run_round2_synthesis()
        else:
            logger.error("Please specify --submission-id or --all for synthesis")


if __name__ == "__main__":
    main()
