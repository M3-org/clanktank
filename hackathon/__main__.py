"""Clank Tank hackathon CLI — unified entry point."""

import argparse
import sys


def add_common_args(parser):
    """Add arguments shared by most pipeline commands."""
    parser.add_argument("--submission-id", help="Target a specific submission by ID")
    parser.add_argument("--all", action="store_true", help="Process all eligible submissions")
    parser.add_argument("--version", default="v2", choices=["v1", "v2"], help="Schema version (default: v2)")
    parser.add_argument("--db-file", default=None, help="Database path (default: from .env or data/hackathon.db)")
    parser.add_argument("--output", help="Output file for results (JSON)")
    parser.add_argument("--force", "-f", action="store_true", help="Force recompute / bypass cache")


def main():
    parser = argparse.ArgumentParser(prog="clanktank", description="Clank Tank hackathon pipeline CLI")
    sub = parser.add_subparsers(dest="command", help="Available commands")

    # --- Pipeline commands ---
    research_p = sub.add_parser("research", help="Run AI research on submissions")
    add_common_args(research_p)

    score_p = sub.add_parser("score", help="Round 1 AI judge scoring")
    add_common_args(score_p)
    score_p.add_argument("--round", type=int, default=1, help="Scoring round (default: 1)")

    synthesize_p = sub.add_parser("synthesize", help="Round 2 synthesis with community data")
    add_common_args(synthesize_p)

    leaderboard_p = sub.add_parser("leaderboard", help="Display leaderboard")
    leaderboard_p.add_argument("--version", default="v2", choices=["v1", "v2"])
    leaderboard_p.add_argument("--db-file", default=None)
    leaderboard_p.add_argument("--output", help="Output file")
    leaderboard_p.add_argument("--round", type=int, default=1)

    # --- Server ---
    serve_p = sub.add_parser("serve", help="Start FastAPI API server")
    serve_p.add_argument("--host", default="127.0.0.1", help="Bind host")
    serve_p.add_argument("--port", type=int, default=8000, help="Bind port")

    # --- Database ---
    db_p = sub.add_parser("db", help="Database operations")
    db_sub = db_p.add_subparsers(dest="db_command", help="Database subcommands")
    create_p = db_sub.add_parser("create", help="Initialize database")
    create_p.add_argument("--db", default=None, help="Database path")
    migrate_p = db_sub.add_parser("migrate", help="Run schema migrations")
    migrate_p.add_argument("--dry-run", action="store_true")
    migrate_p.add_argument("--version", default="all", choices=["v1", "v2", "all"])
    migrate_p.add_argument("--db", default=None)

    # --- Content ---
    episode_p = sub.add_parser("episode", help="Generate episode for a submission")
    add_common_args(episode_p)
    episode_p.add_argument("--video-url", help="Video URL for episode")
    episode_p.add_argument("--avatar-url", help="Avatar URL override")
    episode_p.add_argument("--output-dir", help="Episode output directory")
    episode_p.add_argument("--validate-only", action="store_true")
    episode_p.add_argument("--episode-file", help="Existing episode file to validate")

    upload_p = sub.add_parser("upload", help="Upload episode to YouTube")
    add_common_args(upload_p)
    upload_p.add_argument("--dry-run", action="store_true")
    upload_p.add_argument("--limit", type=int)

    # --- Maintenance ---
    sub.add_parser("static-data", help="Generate static JSON files for frontend")

    votes_p = sub.add_parser("votes", help="Collect Solana blockchain votes")
    votes_p.add_argument("--collect", action="store_true")
    votes_p.add_argument("--scores", action="store_true")
    votes_p.add_argument("--stats", action="store_true")
    votes_p.add_argument("--test", action="store_true")
    votes_p.add_argument("--db-path", default=None)

    recovery_p = sub.add_parser("recovery", help="Backup/restore submissions")
    recovery_p.add_argument("--list", action="store_true")
    recovery_p.add_argument("--restore", help="Submission ID to restore")
    recovery_p.add_argument("--validate", help="Backup file to validate")
    recovery_p.add_argument("--db-path", default=None)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Dispatch to modules — rebuild sys.argv for each module's own argparse
    if args.command in ("research", "score", "synthesize", "leaderboard"):
        from hackathon.backend.hackathon_manager import main as manager_main

        new_argv = ["hackathon_manager", f"--{args.command}"]
        if hasattr(args, "submission_id") and args.submission_id:
            new_argv += ["--submission-id", args.submission_id]
        if hasattr(args, "all") and args.all:
            new_argv.append("--all")
        if hasattr(args, "version") and args.version:
            new_argv += ["--version", args.version]
        if hasattr(args, "db_file") and args.db_file:
            new_argv += ["--db-file", args.db_file]
        if hasattr(args, "output") and args.output:
            new_argv += ["--output", args.output]
        if hasattr(args, "force") and args.force:
            new_argv.append("--force")
        if hasattr(args, "round"):
            new_argv += ["--round", str(args.round)]
        sys.argv = new_argv
        manager_main()

    elif args.command == "serve":
        from hackathon.backend.app import main as app_main

        sys.argv = ["app", "--host", args.host, "--port", str(args.port)]
        app_main()

    elif args.command == "db":
        if args.db_command == "create":
            from hackathon.backend.create_db import main as create_main

            sys.argv = ["create_db"] + ([args.db] if args.db else [])
            create_main()
        elif args.db_command == "migrate":
            from hackathon.backend.migrate_schema import main as migrate_main

            new_argv = ["migrate_schema"]
            if args.dry_run:
                new_argv.append("--dry-run")
            if args.version:
                new_argv += ["--version", args.version]
            if args.db:
                new_argv += ["--db", args.db]
            sys.argv = new_argv
            migrate_main()

    elif args.command == "episode":
        from hackathon.scripts.generate_episode import main as episode_main

        new_argv = ["generate_episode"]
        if args.submission_id:
            new_argv += ["--submission-id", args.submission_id]
        if args.version:
            new_argv += ["--version", args.version]
        if args.db_file:
            new_argv += ["--db-file", args.db_file]
        if args.output_dir:
            new_argv += ["--output-dir", args.output_dir]
        if args.validate_only:
            new_argv.append("--validate-only")
        if args.episode_file:
            new_argv += ["--episode-file", args.episode_file]
        sys.argv = new_argv
        episode_main()

    elif args.command == "upload":
        from hackathon.scripts.upload_youtube import main as upload_main

        new_argv = ["upload_youtube"]
        if args.submission_id:
            new_argv += ["--submission-id", args.submission_id]
        if args.all:
            new_argv.append("--all")
        if args.dry_run:
            new_argv.append("--dry-run")
        if args.version:
            new_argv += ["--version", args.version]
        if args.db_file:
            new_argv += ["--db-file", args.db_file]
        sys.argv = new_argv
        upload_main()

    elif args.command == "static-data":
        from hackathon.scripts.generate_static_data import generate_static_data

        generate_static_data()

    elif args.command == "votes":
        from hackathon.scripts.collect_votes import main as votes_main

        new_argv = ["collect_votes"]
        if args.collect:
            new_argv.append("--collect")
        if args.scores:
            new_argv.append("--scores")
        if args.stats:
            new_argv.append("--stats")
        if args.test:
            new_argv.append("--test")
        if args.db_path:
            new_argv += ["--db-path", args.db_path]
        sys.argv = new_argv
        votes_main()

    elif args.command == "recovery":
        from hackathon.scripts.recovery_tool import main as recovery_main

        new_argv = ["recovery_tool"]
        if args.list:
            new_argv.append("--list")
        if args.restore:
            new_argv += ["--restore", args.restore]
        if args.validate:
            new_argv += ["--validate", args.validate]
        if args.db_path:
            new_argv += ["--db-path", args.db_path]
        sys.argv = new_argv
        recovery_main()


if __name__ == "__main__":
    main()
