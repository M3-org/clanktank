#!/usr/bin/env python3
"""Generate static JSON files for static site deployment."""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from sqlalchemy import create_engine, text

load_dotenv(find_dotenv())

from hackathon.backend.config import HACKATHON_DB_PATH  # noqa: E402
from hackathon.backend.routes.submissions import get_score_columns  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
STATIC_DATA_DIR = os.getenv(
    "STATIC_DATA_DIR",
    str(REPO_ROOT / "hackathon" / "dashboard" / "frontend" / "public" / "data"),
)


def generate_static_data():
    """Generate static JSON files for static site deployment."""
    print("Generating static data files...")

    engine = create_engine(f"sqlite:///{HACKATHON_DB_PATH}")

    # Create output directory
    output_dir = Path(STATIC_DATA_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    with engine.connect() as conn:
        # Generate submissions.json
        result = conn.execute(
            text(
                """
            SELECT
                s.submission_id,
                s.project_name,
                s.category,
                s.status,
                s.created_at,
                s.project_image,
                s.owner_discord_id as discord_id,
                u.avatar as discord_avatar,
                AVG(sc.weighted_total) as avg_score,
                COUNT(DISTINCT sc.judge_name) as judge_count,
                u.username as discord_handle
            FROM hackathon_submissions_v2 s
            LEFT JOIN hackathon_scores sc ON s.submission_id = sc.submission_id AND sc.round = 1
            JOIN users u ON s.owner_discord_id = u.discord_id
            GROUP BY s.submission_id
            ORDER BY s.created_at DESC
        """
            )
        )

        submissions = []
        for row in result.fetchall():
            row_dict = dict(row._mapping)
            submissions.append(
                {
                    "submission_id": row_dict["submission_id"],
                    "project_name": row_dict["project_name"],
                    "category": row_dict["category"],
                    "status": row_dict["status"],
                    "created_at": row_dict["created_at"],
                    "avg_score": (round(row_dict["avg_score"], 2) if row_dict["avg_score"] else None),
                    "judge_count": (row_dict["judge_count"] if row_dict["judge_count"] else 0),
                    "discord_handle": row_dict["discord_handle"],
                    "discord_username": row_dict["discord_handle"],
                    "discord_id": row_dict.get("discord_id"),
                    "discord_avatar": row_dict.get("discord_avatar"),
                    "project_image": row_dict.get("project_image"),
                }
            )

        with open(output_dir / "submissions.json", "w") as f:
            json.dump(submissions, f, indent=2)

        print(f"Generated submissions.json with {len(submissions)} entries")

        # Generate individual submission files
        submission_dir = output_dir / "submission"
        submission_dir.mkdir(exist_ok=True)

        for submission in submissions:
            sid = submission["submission_id"]
            details_result = conn.execute(
                text(
                    "SELECT s.*, u.avatar as discord_avatar FROM hackathon_submissions_v2 s "
                    "JOIN users u ON s.owner_discord_id = u.discord_id "
                    "WHERE s.submission_id = :submission_id"
                ),
                {"submission_id": sid},
            )
            details = details_result.fetchone()
            detail_dict = dict(details._mapping)
            # Add frontend-expected field aliases
            detail_dict["discord_id"] = detail_dict.get("owner_discord_id")
            detail_dict["discord_username"] = detail_dict.get("discord_handle")

            # --- Scores ---
            score_fields = [
                "judge_name",
                "innovation",
                "technical_execution",
                "market_potential",
                "user_experience",
                "weighted_total",
                "notes",
                "round",
                "community_bonus",
                "final_verdict",
                "created_at",
            ]
            actual_score_fields = get_score_columns(conn, score_fields)
            if actual_score_fields:
                scores_result = conn.execute(
                    text(
                        f"""
                        SELECT {", ".join(actual_score_fields)} FROM (
                            SELECT {", ".join(actual_score_fields)},
                                   ROW_NUMBER() OVER (PARTITION BY judge_name, round ORDER BY created_at DESC) as rn
                            FROM hackathon_scores
                            WHERE submission_id = :submission_id
                        ) ranked_scores
                        WHERE rn = 1
                        ORDER BY judge_name, round
                        """
                    ),
                    {"submission_id": sid},
                )
                scores = []
                for score_row in scores_result.fetchall():
                    score_dict = dict(score_row._mapping)
                    if "notes" in score_dict:
                        try:
                            score_dict["notes"] = json.loads(score_dict["notes"]) if score_dict["notes"] else {}
                        except (json.JSONDecodeError, TypeError):
                            score_dict["notes"] = {"raw": score_dict["notes"]} if score_dict["notes"] else {}
                    scores.append(score_dict)
                detail_dict["scores"] = scores
            else:
                detail_dict["scores"] = []

            # --- Avg score ---
            avg_result = conn.execute(
                text(
                    "SELECT AVG(weighted_total) as avg_score FROM hackathon_scores WHERE submission_id = :submission_id"
                ),
                {"submission_id": sid},
            )
            avg_row = avg_result.fetchone()
            detail_dict["avg_score"] = round(avg_row.avg_score, 2) if avg_row and avg_row.avg_score else None

            # --- Research ---
            research_result = conn.execute(
                text(
                    "SELECT github_analysis, market_research, technical_assessment "
                    "FROM hackathon_research WHERE submission_id = :submission_id"
                ),
                {"submission_id": sid},
            )
            research_row = research_result.fetchone()
            if research_row:
                r = dict(research_row._mapping)
                detail_dict["research"] = {
                    "github_analysis": json.loads(r["github_analysis"]) if r["github_analysis"] else None,
                    "market_research": None,  # Deprecated: included in technical_assessment
                    "technical_assessment": json.loads(r["technical_assessment"])
                    if r["technical_assessment"]
                    else None,
                }
            else:
                detail_dict["research"] = None

            # --- Community score / likes / dislikes ---
            community_result = conn.execute(
                text(
                    """
                    SELECT
                        SUM(CASE WHEN action = 'like' THEN 1 ELSE 0 END) as likes,
                        SUM(CASE WHEN action = 'dislike' THEN 1 ELSE 0 END) as dislikes,
                        CASE WHEN COUNT(*) > 0 THEN
                            (SUM(CASE WHEN action = 'like' THEN 1.0 ELSE 0.0 END) / COUNT(*)) * 10
                        ELSE 0 END as community_score
                    FROM likes_dislikes
                    WHERE CAST(submission_id AS INTEGER) = :submission_id
                    """
                ),
                {"submission_id": sid},
            )
            community_row = community_result.fetchone()
            if community_row:
                detail_dict["likes"] = community_row.likes or 0
                detail_dict["dislikes"] = community_row.dislikes or 0
                detail_dict["community_score"] = round(community_row.community_score or 0.0, 1)
            else:
                detail_dict["likes"] = 0
                detail_dict["dislikes"] = 0
                detail_dict["community_score"] = 0.0

            # --- Static flags ---
            detail_dict["can_edit"] = False
            detail_dict["is_creator"] = False

            with open(submission_dir / f"{sid}.json", "w") as f:
                json.dump(detail_dict, f, indent=2)

        # Generate leaderboard.json
        leaderboard_result = conn.execute(
            text(
                """
            SELECT
                s.submission_id,
                s.project_name,
                s.category,
                s.demo_video_url as youtube_url,
                s.status,
                s.owner_discord_id as discord_id,
                u.avatar as discord_avatar,
                AVG(sc.weighted_total) as avg_score,
                u.username as discord_handle
            FROM hackathon_submissions_v2 s
            JOIN hackathon_scores sc ON s.submission_id = sc.submission_id
            JOIN users u ON s.owner_discord_id = u.discord_id
            WHERE s.status IN ('scored', 'completed', 'published') AND sc.round = 1
            GROUP BY s.submission_id
            ORDER BY avg_score DESC
        """
            )
        )
        leaderboard = []
        rank = 1
        for row in leaderboard_result.fetchall():
            row_dict = dict(row._mapping)
            leaderboard.append(
                {
                    "rank": rank,
                    "submission_id": row_dict["submission_id"],
                    "project_name": row_dict["project_name"],
                    "category": row_dict["category"],
                    "final_score": round(row_dict["avg_score"], 2),
                    "youtube_url": row_dict["youtube_url"],
                    "status": row_dict["status"],
                    "discord_handle": row_dict["discord_handle"],
                    "discord_id": row_dict.get("discord_id"),
                    "discord_avatar": row_dict.get("discord_avatar"),
                    "discord_username": row_dict["discord_handle"],
                }
            )
            rank += 1
        with open(output_dir / "leaderboard.json", "w") as f:
            json.dump(leaderboard, f, indent=2)
        print(f"Generated leaderboard.json with {len(leaderboard)} entries")

        # Generate stats.json
        stats = {
            "total_submissions": len(submissions),
            "by_status": {},
            "by_category": {},
            "generated_at": datetime.now().isoformat(),
        }

        for submission in submissions:
            status = submission["status"]
            category = submission["category"]

            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1

        with open(output_dir / "stats.json", "w") as f:
            json.dump(stats, f, indent=2)

        # Generate config.json
        config = {
            "submission_deadline": None,
            "current_time": datetime.now().isoformat(),
            "can_submit": False,
            "submission_window_open": False,
        }
        with open(output_dir / "config.json", "w") as f:
            json.dump(config, f, indent=2)

        # Generate /api/ mirror for static site (so /api/*.json paths work)
        api_dir = output_dir.parent / "api"
        api_dir.mkdir(parents=True, exist_ok=True)

        # Copy top-level JSON files to api/
        for json_file in ["submissions.json", "leaderboard.json", "stats.json"]:
            src = output_dir / json_file
            if src.exists():
                shutil.copy2(src, api_dir / json_file)

        # Copy individual submission files to api/submissions/{id}.json
        api_submissions_dir = api_dir / "submissions"
        api_submissions_dir.mkdir(exist_ok=True)
        src_submission_dir = output_dir / "submission"
        if src_submission_dir.exists():
            for f in src_submission_dir.glob("*.json"):
                shutil.copy2(f, api_submissions_dir / f.name)

        # Generate index.html listing available endpoints
        index_html = """<!DOCTYPE html>
<html><head><title>Clank Tank API</title></head>
<body>
<h1>Clank Tank Static API</h1>
<ul>
<li><a href="submissions.json">/api/submissions.json</a></li>
<li><a href="leaderboard.json">/api/leaderboard.json</a></li>
<li><a href="stats.json">/api/stats.json</a></li>
</ul>
</body></html>"""
        with open(api_dir / "index.html", "w") as f:
            f.write(index_html)

        print(f"Generated /api/ mirror with {len(list(api_dir.glob('*.json')))} top-level files")
        print("Static data generation complete!")


if __name__ == "__main__":
    generate_static_data()
