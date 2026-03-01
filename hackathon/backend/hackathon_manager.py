#!/usr/bin/env python3
"""
Hackathon Manager - AI Judge Scoring System.
Implements personality-based evaluation with weighted scoring for hackathon submissions.
Works exclusively with the hackathon database.
"""

import argparse
import json
import logging
import os
import re
import sqlite3
import time
from datetime import datetime
from typing import Any

import requests
from dotenv import find_dotenv, load_dotenv

# Load environment variables (automatically finds .env in parent directories)
load_dotenv(find_dotenv())

# Import versioned schema helpers
from hackathon.backend.schema import LATEST_SUBMISSION_VERSION, get_fields  # noqa: E402

# Import judge personas and weights
from hackathon.prompts.judge_personas import (  # noqa: E402
    JUDGE_PERSONAS,
    JUDGE_WEIGHTS,
    get_judge_persona,
    get_round2_template,
    get_score_scale,
    get_scoring_task,
)

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Configuration — centralized in config module
from hackathon.backend.config import (  # noqa: E402
    AI_MODEL_NAME,
    BASE_URL,
    HACKATHON_DB_PATH,
    OPENROUTER_API_KEY,
)

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "submission_schema.json")


def get_judge_recent_evaluations(db_path, judge_name, limit=3):
    """Get judge's recent evaluation notes for variety checking."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Get last N evaluations by this judge, ordered by most recent
        cursor.execute(
            """
            SELECT notes FROM hackathon_scores
            WHERE judge_name = ? AND notes IS NOT NULL
            ORDER BY created_at DESC
            LIMIT ?
        """,
            (judge_name, limit),
        )

        results = cursor.fetchall()
        recent_notes = [row[0] for row in results if row[0]]
        return recent_notes

    except sqlite3.Error as e:
        logger.warning(f"Could not fetch recent evaluations for {judge_name}: {e}")
        return []
    finally:
        conn.close()


def add_variety_instruction(db_path, judge_name, base_prompt):
    """Add variety instruction based on judge's recent database evaluations."""
    recent_notes = get_judge_recent_evaluations(db_path, judge_name)

    if recent_notes:
        # Show judge their recent evaluation patterns to encourage variety
        recent_summary = "\n".join([f"• {note[:100]}..." if len(note) > 100 else f"• {note}" for note in recent_notes])

        variety_instruction = f"""
EVALUATION VARIETY REMINDER:
Your last {len(recent_notes)} evaluation(s) for reference (avoid repeating similar patterns):
{recent_summary}

When evaluating this project, vary your language, sentence structure, and critical angles to keep your assessments fresh and distinctive.
"""
        return base_prompt + variety_instruction

    return base_prompt


def get_v2_fields_from_schema():
    with open(SCHEMA_PATH) as f:
        schema = json.load(f)
    return [f["name"] for f in schema["schemas"]["v2"]]


# In all scoring and prompt logic, use get_v2_fields_from_schema() for field access and validation.


class HackathonManager:
    def __init__(self, db_path=None, version=None, force=False):
        """Initialize the hackathon manager."""
        if not OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")

        self.db_path = db_path or HACKATHON_DB_PATH
        self.version = version or LATEST_SUBMISSION_VERSION
        self.table = f"hackathon_submissions_{self.version}"
        self.fields = get_fields(self.version)
        self.force = force

        from hackathon.backend.http_client import create_session

        self.session = create_session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/m3-org/clanktank",
                "X-Title": "Clank Tank Hackathon Judge Scoring",
            }
        )
        self.headers = dict(self.session.headers)

    def create_scoring_prompt(
        self,
        judge_name: str,
        project_data: dict[str, Any],
        research_data: dict[str, Any],
    ) -> str:
        """Create a detailed scoring prompt for a specific judge."""
        persona = JUDGE_PERSONAS.get(judge_name, "")

        # Score scale loaded from JUDGE_CONFIG env var
        SCALE = get_score_scale()

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
        contributors = github_analysis.get("contributors_count", 1) if github_analysis else 1

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
Name: {project_data.get("project_name", "Untitled")}
Category: {project_data.get("category", "Unknown")}
Description: {project_data.get("description", "No description")}

Problem solved: {project_data.get("problem_solved", "Not provided")}
Favorite part: {project_data.get("favorite_part", "Not provided")}
Solana Address: {project_data.get("solana_address", "Not provided")}

RESEARCH FINDINGS:
Is Fork: {is_fork}
Contributors: {contributors}
{red_flags_section}
AI Research: {json.dumps(ai_research, indent=2) if ai_research else "No AI research available"}

{get_scoring_task()}"""

        # Add variety instruction based on recent evaluations
        prompt_with_variety = add_variety_instruction(self.db_path, judge_name, prompt)
        return prompt_with_variety

    def parse_scoring_response(self, response_text: str) -> dict[str, Any]:
        """Parse the AI's scoring response into structured data.

        Raises:
            ValueError: If required scores cannot be parsed from response.
        """
        scores = {}
        reasons = {}
        overall_comment = ""
        parse_errors = []

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
                    except (ValueError, IndexError) as e:
                        parse_errors.append(f"Could not parse score for {key}: {e}")

        # Validate we have all required scores - FAIL LOUDLY instead of defaulting
        required_scores = [
            "innovation",
            "technical_execution",
            "market_potential",
            "user_experience",
        ]
        missing_scores = [c for c in required_scores if c not in scores]
        if missing_scores:
            parse_errors.append(f"Missing required scores: {missing_scores}")

        if parse_errors:
            error_msg = f"AI scoring parse failed: {'; '.join(parse_errors)}"
            logger.error(error_msg)
            logger.error(f"Raw response (first 500 chars): {response_text[:500]}")
            raise ValueError(error_msg)

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

        logger.info(f"Score normalization: mean {cur_mean:.1f} → {sum(normalized) / len(normalized):.1f}")
        return normalized

    def calculate_weighted_score(self, judge_name: str, raw_scores: dict[str, float], normalize: bool = False) -> float:
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
            # Fail if any required score is missing (caller should have validated)
            missing = [k for k in score_mapping if k not in raw_scores]
            if missing:
                raise ValueError(f"Missing required scores for normalization: {missing}")
            score_values = [raw_scores[key] for key in score_mapping]
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
        project_data: dict[str, Any],
        research_data: dict[str, Any],
    ) -> dict[str, Any]:
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
            logger.info(f"Getting scores from {judge_name} for {project_data['project_name']}")
            response = self.session.post(BASE_URL, json=payload, timeout=self.session.timeout)
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

        except requests.exceptions.RequestException as e:
            # Network/API errors - propagate so caller can decide on retry
            logger.error(f"API request failed for {judge_name}: {e}")
            raise RuntimeError(f"AI API request failed for judge {judge_name}: {e}") from e
        except ValueError as e:
            # Parse errors - propagate with context
            logger.error(f"Score parsing failed for {judge_name}: {e}")
            raise RuntimeError(f"AI score parsing failed for judge {judge_name}: {e}") from e
        except Exception as e:
            # Unexpected errors - log and propagate
            logger.error(f"Unexpected error getting scores from {judge_name}: {e}")
            raise RuntimeError(f"Unexpected AI scoring error for judge {judge_name}: {e}") from e

    def score_submission(self, submission_id: str, round_num: int = 1) -> list[dict[str, Any]]:
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
                raise ValueError(f"Submission {submission_id} not found in {self.table}")

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
                judge_scores = self.get_ai_scores(judge_name, project_data, research_data)
                judge_scores["submission_id"] = submission_id
                judge_scores["round"] = round_num

                # Save to database (UPSERT: replace existing score for same submission/judge/round)
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO hackathon_scores
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

    def score_all_researched(self, round_num: int = 1) -> dict[str, Any]:
        """Score all submissions with research data (or force re-score all if force=True)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if self.force:
            # Force mode: score all submissions that have research data, regardless of existing scores
            cursor.execute(
                f"""
                SELECT s.submission_id, s.project_name
                FROM {self.table} s
                INNER JOIN hackathon_research r ON s.submission_id = r.submission_id
                ORDER BY s.created_at
                """
            )
            logger.info("Force flag enabled - will re-score all submissions with research data")
        else:
            # Normal mode: only score submissions with status 'researched'
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

    def get_leaderboard(self, sort_by_round: int | None = None) -> list[dict[str, Any]]:
        """Get the leaderboard with R1 and R2 scores side by side.

        ``sort_by_round`` controls the sort column:
        - 1  → sort by Round 1 score
        - 2  → sort by Round 2 score (default)
        """
        if sort_by_round is None:
            sort_by_round = 2

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        sort_col = "r2.avg_score" if sort_by_round == 2 else "r1.avg_score"
        cursor.execute(
            f"""
            SELECT
                s.submission_id,
                s.project_name,
                s.category,
                r1.avg_score  AS r1_score,
                r1.judge_count AS r1_judges,
                r2.avg_score  AS r2_score,
                r2.judge_count AS r2_judges
            FROM {self.table} s
            LEFT JOIN (
                SELECT submission_id,
                       AVG(weighted_total) AS avg_score,
                       COUNT(DISTINCT judge_name) AS judge_count
                FROM hackathon_scores WHERE round = 1
                GROUP BY submission_id
            ) r1 ON s.submission_id = r1.submission_id
            LEFT JOIN (
                SELECT submission_id,
                       AVG(weighted_total) AS avg_score,
                       COUNT(DISTINCT judge_name) AS judge_count
                FROM hackathon_scores WHERE round = 2
                GROUP BY submission_id
            ) r2 ON s.submission_id = r2.submission_id
            WHERE r1.avg_score IS NOT NULL OR r2.avg_score IS NOT NULL
            ORDER BY COALESCE({sort_col}, 0) DESC
        """,
        )

        leaderboard = []
        for row in cursor.fetchall():
            r1 = round(row[3], 2) if row[3] else None
            r2 = round(row[5], 2) if row[5] else None
            leaderboard.append(
                {
                    "rank": len(leaderboard) + 1,
                    "submission_id": row[0],
                    "project_name": row[1],
                    "category": row[2],
                    "r1_score": r1,
                    "r1_judges": row[4] or 0,
                    "r2_score": r2,
                    "r2_judges": row[6] or 0,
                }
            )

        conn.close()
        return leaderboard

    def analyze_score_distribution(self, round_num: int = 1) -> dict[str, Any]:
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
            (
                submission_id,
                project_name,
                category,
                judge_name,
                innovation,
                technical,
                market,
                experience,
                weighted_total,
                notes,
            ) = row

            if submission_id not in projects:
                projects[submission_id] = {
                    "project_name": project_name,
                    "category": category,
                    "judges": {},
                    "avg_score": 0,
                    "score_variance": 0,
                }

            # Parse notes to extract reasoning
            try:
                judge_notes = json.loads(notes) if notes else {}
            except Exception:
                judge_notes = {"raw": notes}

            projects[submission_id]["judges"][judge_name] = {
                "innovation": innovation,
                "technical_execution": technical,
                "market_potential": market,
                "user_experience": experience,
                "weighted_total": weighted_total,
                "notes": judge_notes,
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
                "good": len([s for s in all_scores if 24 <= s < 32]),  # 6-8 avg
                "average": len([s for s in all_scores if 16 <= s < 24]),  # 4-6 avg
                "poor": len([s for s in all_scores if s < 16]),  # <4 avg
            },
        }

        # Rank projects
        ranked_projects = sorted(projects.items(), key=lambda x: x[1]["avg_score"], reverse=True)

        return {
            "distribution_stats": distribution_stats,
            "projects": dict(ranked_projects),
            "rankings": [(project_id, data["project_name"], data["avg_score"]) for project_id, data in ranked_projects],
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
            (pid, data)
            for pid, data in projects.items()
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
- Ranked #{target_rank} out of {stats["total_projects"]} projects
- Score: {target_score:.1f} (Hackathon mean: {stats["mean"]:.1f}, median: {stats["median"]:.1f})
- Percentile: {percentile:.0f}th percentile
- Judge consensus: {"High" if target_project["score_variance"] < 2 else "Low"} (variance: {target_project["score_variance"]:.1f})

COMPETITIVE LANDSCAPE:
- {len(better_projects)} projects scored higher{f" (avg gap: {(sum(p['avg_score'] for p in better_projects) / len(better_projects) - target_score):.1f} points)" if better_projects else ""}
- {len(worse_projects)} projects scored lower
- {len(similar_projects)} projects in similar score range (±2 points)

RELATIVE POSITIONING:
{f"This project outperformed {percentile:.0f}% of submissions" if percentile > 50 else f"This project underperformed compared to {100 - percentile:.0f}% of submissions"}
{"" if len(better_criticisms) == 0 else f"Common issues in higher-ranked projects that this project might share: {'; '.join(better_criticisms[:2])}"}
{"" if len(worse_strengths) == 0 else f"Potential advantages over lower-ranked projects: {'; '.join(worse_strengths[:2])}"}
"""

        return reasoning.strip()

    def run_round2_synthesis(self, project_id: str | None = None):
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
            cursor.execute(f"SELECT submission_id FROM {self.table} WHERE status = 'community-voting'")

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
            r1_scores = {row[0]: {"score": row[1], "notes": json.loads(row[2] or "{}")} for row in cursor.fetchall()}

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
                    distribution_analysis,
                )

                # Parse structured response
                parsed_response = self._parse_round2_response(round2_response)

                # Calculate Round 2 score based on structured response
                final_score = self._calculate_judge_round2_score(
                    judge, r1_scores[judge]["score"], round2_response, community_data[project_id]
                )

                # Store Round 2 data with flattened, logical structure (UPSERT)
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO hackathon_scores
                    (submission_id, judge_name, round, weighted_total, notes, created_at)
                    VALUES (?, ?, 2, ?, ?, ?)
                """,
                    (
                        project_id,
                        judge,
                        final_score,
                        json.dumps(
                            {
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
                                "synthesis_timestamp": datetime.now().isoformat(),
                            }
                        ),
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
        """Get community feedback data from unified likes_dislikes table as context for Round 2 synthesis."""
        import statistics

        community_data = {}
        all_reaction_counts = []

        # First pass: collect all like/dislike data and counts for statistical analysis
        for project_id in project_ids:
            # Get total votes for this project from likes_dislikes table
            cursor.execute(
                "SELECT COUNT(*) FROM likes_dislikes WHERE submission_id = ?",
                (project_id,),
            )
            total_reactions = cursor.fetchone()[0]
            all_reaction_counts.append(total_reactions)

            # Get like/dislike breakdown from likes_dislikes table
            cursor.execute(
                "SELECT action, COUNT(*) FROM likes_dislikes WHERE submission_id = ? GROUP BY action",
                (project_id,),
            )
            vote_breakdown = {row[0]: row[1] for row in cursor.fetchall()}

            # Get unique voters from likes_dislikes table
            cursor.execute(
                "SELECT COUNT(DISTINCT discord_id) FROM likes_dislikes WHERE submission_id = ?",
                (project_id,),
            )
            unique_voters = cursor.fetchone()[0]

            # Store basic data for now
            community_data[project_id] = {
                "total_reactions": total_reactions,
                "unique_voters": unique_voters,
                "reaction_breakdown": vote_breakdown,  # Now contains 'like' and 'dislike' counts
                "engagement_level": "pending",  # Will calculate after getting distribution
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
                "mean": mean_reactions if len(all_reaction_counts) > 1 else 0,
            }

        return community_data

    def _parse_round2_response(self, response_text: str) -> dict[str, Any]:
        """Parse Round 2 judge response with structured JSON format."""
        import json
        import re

        # Try to extract JSON from the response
        json_match = re.search(r"```json\s*\n(.*?)\n```", response_text, re.DOTALL)
        if not json_match:
            # Try to find JSON without code blocks
            json_match = re.search(r"(\{.*\})", response_text, re.DOTALL)

        if json_match:
            try:
                json_data = json.loads(json_match.group(1))

                # Validate required fields
                required_fields = ["final_verdict", "score_revision"]
                if all(field in json_data for field in required_fields):
                    return {
                        "final_verdict": json_data.get("final_verdict", ""),
                        "score_revision": json_data.get("score_revision", {}),
                        "reasoning": json_data.get("reasoning", ""),
                        "community_influence": json_data.get("community_influence", "none"),
                        "confidence": json_data.get("confidence", "medium"),
                    }
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON from Round 2 response: {e}")

        # Fallback: treat entire response as final_verdict
        logger.warning("Round 2 response not in expected JSON format, using as final_verdict")
        return {
            "final_verdict": response_text.strip(),
            "score_revision": {"type": "none"},
            "reasoning": "Non-structured response",
            "community_influence": "unknown",
            "confidence": "low",
        }

    def _calculate_judge_round2_score(self, judge_name, round1_score, round2_response, community_context):
        """Calculate Round 2 score based on structured judge response."""

        # Parse the structured response
        parsed_response = self._parse_round2_response(round2_response)
        score_revision = parsed_response.get("score_revision", {})

        # Handle different types of score revisions
        revision_type = score_revision.get("type", "none")

        if revision_type == "explicit":
            # Direct score override
            new_score = score_revision.get("new_score")
            if new_score is not None and 0 <= new_score <= 40:
                logger.info(f"{judge_name} provided explicit score revision: {new_score}/40")
                return round(float(new_score), 2)

        elif revision_type == "adjustment":
            # Relative adjustment from Round 1
            adjustment = score_revision.get("adjustment", 0)
            reason = score_revision.get("reason", "")
            final_score = max(0, min(40, round1_score + adjustment))
            logger.info(f"{judge_name} adjusted score by {adjustment:+.1f}: {round1_score} → {final_score} ({reason})")
            return round(final_score, 2)

        elif revision_type == "none":
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

    def _generate_final_verdict_with_comparison(
        self, project_id, judge, r1_data, community_context, comparative_reasoning, distribution_analysis
    ):
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

        # Format community feedback for context (now like/dislike votes)
        vote_breakdown = community_context.get("reaction_breakdown", {})
        likes = vote_breakdown.get("like", 0)
        dislikes = vote_breakdown.get("dislike", 0)

        if likes + dislikes > 0:
            total_votes = likes + dislikes
            like_percentage = (likes / total_votes) * 100 if total_votes > 0 else 0
            feedback_summary = (
                f"- Likes: {likes} ({like_percentage:.0f}%)\n- Dislikes: {dislikes} ({100 - like_percentage:.0f}%)"
            )
        else:
            feedback_summary = "No community votes yet"

        # Find this project's ranking context
        projects = distribution_analysis.get("projects", {})
        if project_id in projects:
            ranked_projects = sorted(projects.items(), key=lambda x: x[1]["avg_score"], reverse=True)
            next((i + 1 for i, (pid, _) in enumerate(ranked_projects) if pid == project_id), None)

        # Round 2 template loaded from JUDGE_CONFIG env var
        round2_tpl = get_round2_template()
        prompt = round2_tpl.format(
            judge=judge.upper(),
            overall_comment=r1_data.get("notes", {}).get("overall_comment", "No specific notes available"),
            r1_score=f"{r1_data['score']:.1f}",
            feedback_summary=feedback_summary,
            total_reactions=community_context["total_reactions"],
            unique_voters=community_context["unique_voters"],
            engagement_level=community_context["engagement_level"],
            comparative_reasoning=comparative_reasoning,
            project_name=project_name,
            category=category,
            description=description,
        )

        try:
            logger.info(f"Getting structured final verdict from {judge} for {project_name}")
            response = self.session.post(
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
                timeout=self.session.timeout,
            )

            if response.ok:
                return response.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.warning(f"Failed to get structured final verdict from {judge}: {e}")

        # Fallback response in JSON format
        return f"""{{
  "final_verdict": "Maintaining Round 1 assessment of {r1_data["score"]:.1f}/40 considering community feedback pattern and competitive ranking.",
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
    score_group.add_argument("--leaderboard", action="store_true", help="Show current leaderboard")
    score_group.add_argument(
        "--synthesize",
        action="store_true",
        help="Run Round 2 synthesis combining judge scores with community feedback",
    )
    score_group.add_argument(
        "--research",
        action="store_true",
        help="Run AI research on submissions",
    )

    # Scoring options
    parser.add_argument("--submission-id", help="Score a specific submission by ID")
    parser.add_argument("--all", action="store_true", help="Score all researched submissions")
    parser.add_argument("--round", type=int, default=None, help="Round number (scoring default: 1, leaderboard: combined)")
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
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force re-score all submissions, even if they already have scores",
    )

    args = parser.parse_args()

    if not any([args.score, args.leaderboard, args.synthesize, args.research]):
        parser.print_help()
        return

    # Initialize manager
    try:
        manager = HackathonManager(db_path=args.db_file, version=args.version, force=args.force)
    except ValueError as e:
        logger.error(f"Initialization failed: {e}")
        logger.error("Please ensure OPENROUTER_API_KEY is set in your .env file")
        return

    # Execute commands
    if args.score:
        score_round = args.round or 1
        if args.submission_id:
            try:
                scores = manager.score_submission(args.submission_id, score_round)
                if args.output:
                    with open(args.output, "w") as f:
                        json.dump(scores, f, indent=2)
                    logger.info(f"Scores saved to {args.output}")
                else:
                    print(json.dumps(scores, indent=2))
            except Exception as e:
                logger.error(f"Scoring failed: {e}")

        elif args.all:
            results = manager.score_all_researched(score_round)
            logger.info(f"Scoring complete: {results['scored']} succeeded, {results['failed']} failed")

            if args.output:
                with open(args.output, "w") as f:
                    json.dump(results, f, indent=2)

        else:
            logger.error("Please specify --submission-id or --all")

    elif args.leaderboard:
        sort_round = getattr(args, "round", None)
        leaderboard = manager.get_leaderboard(sort_by_round=sort_round)

        if args.output:
            with open(args.output, "w") as f:
                json.dump(leaderboard, f, indent=2)
            logger.info(f"Leaderboard saved to {args.output}")
        else:
            sort_label = f"Round {sort_round}" if sort_round else "Round 2"
            print(f"\n{'=' * 70}")
            print(f"CLANK TANK HACKATHON LEADERBOARD  (sorted by {sort_label})")
            print(f"{'=' * 70}")
            print(f"{'Rank':<6}{'Project':<28}{'Category':<16}{'R1':>8}{'R2':>8}")
            print(f"{'-' * 70}")

            for entry in leaderboard:
                r1 = f"{entry['r1_score']:.1f}" if entry["r1_score"] is not None else "-"
                r2 = f"{entry['r2_score']:.1f}" if entry["r2_score"] is not None else "-"
                print(
                    f"{entry['rank']:<6}{entry['project_name'][:26]:<28}{entry['category'][:14]:<16}{r1:>8}{r2:>8}"
                )

            print(f"{'=' * 70}\n")

    elif args.synthesize:
        if args.submission_id:
            manager.run_round2_synthesis(args.submission_id)
        elif args.all:
            manager.run_round2_synthesis()
        else:
            logger.error("Please specify --submission-id or --all for synthesis")

    elif args.research:
        from hackathon.backend.research import HackathonResearcher

        researcher = HackathonResearcher(db_path=args.db_file, version=args.version, force=args.force)
        if args.submission_id:
            results = researcher.research_submission(args.submission_id)
            if args.output:
                with open(args.output, "w") as f:
                    json.dump(results, f, indent=2)
                logger.info(f"Results saved to {args.output}")
            else:
                print(json.dumps(results, indent=2))
        elif args.all:
            results = researcher.research_all_pending()
            logger.info(f"Researched {len(results)} submissions")
            if args.output:
                with open(args.output, "w") as f:
                    json.dump(results, f, indent=2)
        else:
            logger.error("Please specify --submission-id or --all")


if __name__ == "__main__":
    main()
