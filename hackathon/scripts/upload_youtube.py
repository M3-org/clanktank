#!/usr/bin/env python3
"""
YouTube Upload Pipeline for Hackathon Episodes.
Uploads recorded videos to YouTube with metadata from the hackathon database.
"""

import argparse
import json
import logging
import os
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import find_dotenv, load_dotenv

# Google/YouTube imports
try:
    import pickle

    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
except ImportError:
    print("Please install required packages:")
    print("pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    sys.exit(1)

from hackathon.backend.config import HACKATHON_DB_PATH
from hackathon.backend.schema import LATEST_SUBMISSION_VERSION, get_fields

# Load environment variables (automatically finds .env in parent directories)
load_dotenv(find_dotenv())

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

RECORDINGS_DIR = os.getenv("HACKATHON_RECORDINGS_DIR", "recordings/hackathon")
YOUTUBE_CREDENTIALS_PATH = os.getenv("YOUTUBE_CREDENTIALS_PATH", "youtube_credentials.json")
CLIENT_SECRETS_PATH = os.getenv("YOUTUBE_CLIENT_SECRETS_PATH", "client_secrets.json")

# YouTube API scopes
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


class YouTubeUploader:
    def __init__(self, db_path=None, version=None):
        """Initialize YouTube uploader."""
        self.db_path = db_path or HACKATHON_DB_PATH
        self.version = version or LATEST_SUBMISSION_VERSION
        self.table = f"hackathon_submissions_{self.version}"
        self.fields = get_fields(self.version)
        self.youtube = self._authenticate()

    def _authenticate(self):
        """Authenticate with YouTube API."""
        creds = None

        # Token file stores the user's access and refresh tokens
        if os.path.exists(YOUTUBE_CREDENTIALS_PATH):
            with open(YOUTUBE_CREDENTIALS_PATH, "rb") as token:
                creds = pickle.load(token)

        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(CLIENT_SECRETS_PATH):
                    logger.error(f"Client secrets file not found: {CLIENT_SECRETS_PATH}")
                    logger.error("Please download from Google Cloud Console")
                    sys.exit(1)

                flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_PATH, SCOPES)
                creds = flow.run_local_server(port=0)

            # Save the credentials for the next run
            with open(YOUTUBE_CREDENTIALS_PATH, "wb") as token:
                pickle.dump(creds, token)

        return build("youtube", "v3", credentials=creds)

    def get_project_metadata(self, submission_id: str) -> dict[str, Any]:
        """Fetch project metadata from database."""
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get submission details
        cursor.execute(
            f"""
            SELECT * FROM {self.table}
            WHERE submission_id = ?
        """,
            (submission_id,),
        )

        row = cursor.fetchone()
        if not row:
            conn.close()
            raise ValueError(f"Submission {submission_id} not found in {self.table}")

        columns = [desc[0] for desc in cursor.description]
        submission = dict(zip(columns, row))

        # Get average score
        cursor.execute(
            """
            SELECT AVG(weighted_total), COUNT(*)
            FROM hackathon_scores
            WHERE submission_id = ? AND round = 1
        """,
            (submission_id,),
        )

        avg_score, judge_count = cursor.fetchone()
        avg_score = avg_score or 0

        # Get judge comments (for description)
        cursor.execute(
            """
            SELECT judge_name, notes
            FROM hackathon_scores
            WHERE submission_id = ? AND round = 1
            ORDER BY judge_name
        """,
            (submission_id,),
        )

        judge_comments = []
        for judge_name, notes_json in cursor.fetchall():
            if notes_json:
                notes = json.loads(notes_json)
                if "overall_comment" in notes:
                    judge_comments.append(f"{judge_name}: {notes['overall_comment']}")

        conn.close()

        return {
            "submission": submission,
            "avg_score": round(avg_score, 2),
            "judge_count": judge_count,
            "judge_comments": judge_comments,
        }

    def generate_video_metadata(self, project_data: dict[str, Any]) -> dict[str, Any]:
        """Generate YouTube metadata for a project."""
        submission = project_data["submission"]

        # Title (max 100 chars)
        title = f"Clank Tank Hackathon: {submission['project_name'][:50]} by {submission['team_name'][:20]}"
        if len(title) > 100:
            title = title[:97] + "..."

        # Description
        description_parts = [
            f"🚀 Project: {submission['project_name']}",
            f"👥 Team: {submission['team_name']}",
            f"📂 Category: {submission['category']}",
            f"⭐ Judge Score: {project_data['avg_score']}/40",
            "",
            "📝 Description:",
            submission["description"],
            "",
            "🔧 Tech Stack:",
            submission.get("tech_stack", "Not specified"),
            "",
            "💡 Problem Solved:",
            submission.get("problem_solved", "Not specified")[:500],
            "",
            "🔗 Links:",
            f"GitHub: {submission.get('github_url', 'N/A')}",
            f"Demo: {submission.get('demo_video_url', 'N/A')}",
        ]

        if submission.get("live_demo_url"):
            description_parts.append(f"Live: {submission['live_demo_url']}")

        # Add judge comments
        if project_data["judge_comments"]:
            description_parts.extend(
                [
                    "",
                    "👨‍⚖️ Judge Comments:",
                ]
            )
            description_parts.extend(project_data["judge_comments"][:4])  # Limit to 4 comments

        description_parts.extend(
            [
                "",
                "🎮 About Clank Tank:",
                "AI judges evaluate hackathon projects in this game show format!",
                "",
                "#hackathon #AI #web3 #coding",
            ]
        )

        description = "\n".join(description_parts)

        # Tags
        tags = [
            "hackathon",
            "AI",
            "coding",
            "programming",
            submission["category"].lower(),
            "clank tank",
            "web3",
        ]

        # Add tech stack tags
        if submission.get("tech_stack"):
            tech_tags = [t.strip().lower() for t in submission["tech_stack"].split(",")][:5]
            tags.extend(tech_tags)

        return {
            "title": title,
            "description": description[:5000],  # YouTube limit
            "tags": tags[:500],  # YouTube allows up to 500 chars total
            "category_id": "28",  # Science & Technology
            "privacy_status": "public",
        }

    def upload_video(self, video_path: str, metadata: dict[str, Any], submission_id: str) -> str | None:
        """Upload a video to YouTube."""
        try:
            # Prepare the upload
            body = {
                "snippet": {
                    "title": metadata["title"],
                    "description": metadata["description"],
                    "tags": metadata["tags"],
                    "categoryId": metadata["category_id"],
                },
                "status": {"privacyStatus": metadata["privacy_status"]},
            }

            # Call the API's videos.insert method
            media = MediaFileUpload(video_path, chunksize=-1, resumable=True)

            logger.info(f"Uploading: {metadata['title']}")

            request = self.youtube.videos().insert(part=",".join(body.keys()), body=body, media_body=media)

            # Execute the upload
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    logger.info(f"Upload progress: {int(status.progress() * 100)}%")

            video_id = response["id"]
            video_url = f"https://youtube.com/watch?v={video_id}"

            logger.info(f"Upload complete: {video_url}")

            # Update database
            self._update_submission_status(submission_id, video_url)

            return video_url

        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return None

    def _update_submission_status(self, submission_id: str, youtube_url: str):
        """Update submission status in database after upload."""
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # Store YouTube URL in a new column or in existing field
            cursor.execute(
                f"""
                UPDATE {self.table}
                SET status = 'published',
                    demo_video_url = ?,
                    updated_at = ?
                WHERE submission_id = ?
            """,
                (youtube_url, datetime.now().isoformat(), submission_id),
            )

            conn.commit()
            logger.info(f"Updated submission {submission_id} to published")

        except Exception as e:
            logger.error(f"Failed to update database: {e}")
            conn.rollback()
        finally:
            conn.close()

    def find_video_for_submission(self, submission_id: str) -> str | None:
        """Find video file for a submission."""
        # Look for video files matching the submission ID
        patterns = [
            f"HACK_*{submission_id}*.mp4",
            f"HACK_*{submission_id}*.webm",
            f"*{submission_id}*.mp4",
            f"*{submission_id}*.webm",
        ]

        recordings_path = Path(RECORDINGS_DIR)
        for pattern in patterns:
            matches = list(recordings_path.glob(pattern))
            if matches:
                # Return the most recent match
                return str(max(matches, key=lambda p: p.stat().st_mtime))

        return None

    def process_submission(self, submission_id: str) -> bool:
        """Process a single submission for upload."""
        try:
            # Get project metadata
            project_data = self.get_project_metadata(submission_id)

            # Find video file
            video_path = self.find_video_for_submission(submission_id)
            if not video_path:
                logger.warning(f"No video found for {submission_id}")
                return False

            logger.info(f"Found video: {video_path}")

            # Generate YouTube metadata
            metadata = self.generate_video_metadata(project_data)

            # Upload video
            video_url = self.upload_video(video_path, metadata, submission_id)

            return video_url is not None

        except Exception as e:
            logger.error(f"Failed to process {submission_id}: {e}")
            return False

    def get_uploadable_submissions(self) -> list[str]:
        """Get all submissions ready for upload."""
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Find scored submissions that aren't published yet
        cursor.execute(
            f"""
            SELECT submission_id
            FROM {self.table}
            WHERE status IN ('scored', 'completed')
            AND submission_id NOT IN (
                SELECT submission_id
                FROM {self.table}
                WHERE status = 'published'
            )
            ORDER BY created_at
        """
        )

        submission_ids = [row[0] for row in cursor.fetchall()]
        conn.close()

        return submission_ids


def main():
    """Main function with CLI interface."""
    parser = argparse.ArgumentParser(description="Upload hackathon videos to YouTube")

    parser.add_argument("--submission-id", help="Upload video for specific submission")
    parser.add_argument("--all", action="store_true", help="Upload all pending videos")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be uploaded without actually uploading",
    )
    parser.add_argument("--limit", type=int, help="Limit number of uploads")
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

    if not args.submission_id and not args.all:
        parser.print_help()
        return

    # Initialize uploader
    try:
        uploader = YouTubeUploader(db_path=args.db_file, version=args.version)
    except Exception as e:
        logger.error(f"Failed to initialize uploader: {e}")
        return

    # Process uploads
    if args.submission_id:
        if args.dry_run:
            project_data = uploader.get_project_metadata(args.submission_id)
            metadata = uploader.generate_video_metadata(project_data)
            video_path = uploader.find_video_for_submission(args.submission_id)

            print(f"\nDry run for {args.submission_id}:")
            print(f"Video file: {video_path}")
            print(f"Title: {metadata['title']}")
            print(f"Tags: {', '.join(metadata['tags'])}")
            print(f"\nDescription:\n{metadata['description']}")
        else:
            success = uploader.process_submission(args.submission_id)
            if success:
                logger.info("Upload completed successfully")
            else:
                logger.error("Upload failed")

    elif args.all:
        submission_ids = uploader.get_uploadable_submissions()

        if args.limit:
            submission_ids = submission_ids[: args.limit]

        logger.info(f"Found {len(submission_ids)} videos to upload")

        success_count = 0
        for submission_id in submission_ids:
            if args.dry_run:
                try:
                    project_data = uploader.get_project_metadata(submission_id)
                    metadata = uploader.generate_video_metadata(project_data)
                    video_path = uploader.find_video_for_submission(submission_id)
                    print(f"\n{submission_id}: {metadata['title']}")
                    print(f"  Video: {video_path}")
                except Exception as e:
                    print(f"\n{submission_id}: ERROR - {e}")
            else:
                if uploader.process_submission(submission_id):
                    success_count += 1

                # Rate limiting
                time.sleep(30)  # YouTube has upload quotas

        if not args.dry_run:
            logger.info(f"Upload complete: {success_count}/{len(submission_ids)} successful")


if __name__ == "__main__":
    main()
