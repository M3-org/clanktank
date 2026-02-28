"""Clank Tank hackathon CLI — unified entry point."""

import argparse
import os
import sys

# ANSI color helpers — no-op when stdout is not a TTY
_IS_TTY = sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _IS_TTY else text


def blue(t):   return _c("34", t)
def cyan(t):   return _c("36", t)
def green(t):  return _c("32", t)
def yellow(t): return _c("33", t)
def red(t):    return _c("31", t)
def dim(t):    return _c("2", t)
def bold(t):   return _c("1", t)


# Color scheme:
#   blue   = infrastructure (db, serve, config)
#   yellow = write/mutate pipeline (research, score, votes --collect, synthesize, episode, upload)
#   green  = read-only (leaderboard, static-data)
#   red    = irreversible external action (upload to YouTube)


def add_common_args(parser):
    """Add arguments shared by most pipeline commands."""
    parser.add_argument("--submission-id", help="Target a specific submission by ID")
    parser.add_argument("--all", action="store_true", help="Process all eligible submissions")
    parser.add_argument("--version", default="v2", choices=["v1", "v2"], help="Schema version (default: v2)")
    parser.add_argument("--db-file", default=None, help="Database path (default: from .env or data/hackathon.db)")
    parser.add_argument("--output", help="Output file for results (JSON)")
    parser.add_argument("--force", "-f", action="store_true", help="Force recompute / bypass cache")


ENV_VARS = [
    # (name, required, description)
    ("OPENROUTER_API_KEY",        True,  "AI research + judge scoring"),
    ("DISCORD_CLIENT_ID",         True,  "Discord OAuth login"),
    ("DISCORD_CLIENT_SECRET",     True,  "Discord OAuth login"),
    ("DISCORD_TOKEN",             True,  "Discord bot (community voting)"),
    ("PRIZE_WALLET_ADDRESS",      True,  "Solana wallet to watch for votes"),
    ("GITHUB_TOKEN",              False, "Higher GitHub API rate limits"),
    ("HACKATHON_DB_PATH",         False, "Default: data/hackathon.db"),
    ("SUBMISSION_DEADLINE",       False, "ISO datetime to close submissions"),
    ("DISCORD_GUILD_ID",          False, "Guild ID for role-based auth"),
    ("DISCORD_BOT_TOKEN",         False, "Bot token for guild role fetching"),
    ("VITE_PRIZE_WALLET_ADDRESS", False, "Expose wallet address to frontend"),
    ("AI_MODEL_NAME",             False, "Default: anthropic/claude-3-opus"),
    ("STATIC_DATA_DIR",           False, "Frontend static data output dir"),
]


def _set_env_key(env_path, key: str, value: str):
    """Write a single key=value to .env, updating in-place if it exists, appending if not.

    Never touches other lines. Preserves comments, ordering, and existing values.
    """

    lines = env_path.read_text().splitlines() if env_path.exists() else []
    updated = False
    for i, line in enumerate(lines):
        # Match KEY= or KEY =  (with optional whitespace)
        stripped = line.strip()
        if stripped.startswith(f"{key}=") or stripped == f"{key}":
            lines[i] = f"{key}={value}"
            updated = True
            break
    if not updated:
        lines.append(f"{key}={value}")
    env_path.write_text("\n".join(lines) + "\n")


def cmd_config(args):
    """Show env var status, or run interactive setup for missing vars."""
    from pathlib import Path

    # Standalone — no hackathon imports so this works before deps are installed
    REPO_ROOT = Path(__file__).resolve().parents[1]
    env_path = REPO_ROOT / ".env"

    # Load .env file values so status reflects what's actually configured,
    # not just what's exported in the current shell session
    env_file_vals: dict[str, str] = {}
    if env_path.exists():
        for raw in env_path.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            env_file_vals[k.strip()] = v.strip().strip('"').strip("'")

    def get_val(name: str) -> str | None:
        return os.getenv(name) or env_file_vals.get(name) or None

    # Always print status first
    print(f"\n{bold('Clank Tank — environment config')}")
    print(f"  .env: {env_path} {'(exists)' if env_path.exists() else red('(not found)')}\n")

    missing_required = []
    for name, required, desc in ENV_VARS:
        val = get_val(name)
        if val:
            display = val[:14] + "..." if len(val) > 14 else val
            print(f"  {green('✓')} {name:<36} {dim(display)}")
        elif required:
            print(f"  {red('✗')} {red(name):<36} {dim(desc)}")
            missing_required.append((name, desc))
        else:
            print(f"  {dim('–')} {dim(name):<36} {dim(desc)}")

    print()
    if not missing_required:
        print(f"{green('✓ All required variables are set')}\n")
        return

    print(f"{yellow(f'{len(missing_required)} required variable(s) missing')}\n")

    if not args.setup:
        print(f"  Run {cyan('clanktank config --setup')} to set them interactively\n")
        return

    # Interactive setup — only prompt for missing required vars
    if not env_path.exists():
        print(f"{dim('Creating')} {env_path}\n")
        env_path.touch()

    print(f"{bold('Interactive setup')} — press Enter to skip a value\n")
    wrote: list[str] = []
    for name, desc in missing_required:
        try:
            val = input(f"  {yellow(name)} ({desc}): ").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{dim('Aborted')}")
            sys.exit(0)
        if val:
            _set_env_key(env_path, name, val)
            wrote.append(name)
        else:
            print(f"  {dim('skipped')}")

    print()
    if wrote:
        print(f"{green('✓')} Wrote {len(wrote)} variable(s) to {env_path}")
        for name in wrote:
            print(f"  {green('+')} {name}")
    else:
        print(f"{dim('No changes written')}")
    print()


def main():
    parser = argparse.ArgumentParser(
        prog="clanktank",
        description=bold("Clank Tank hackathon pipeline CLI"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            dim("Pipeline order:\n") +
            f"  {blue('db')} → {blue('serve')} → {yellow('research')} → {yellow('score')} → "
            f"{yellow('votes')} → {yellow('synthesize')} → {green('leaderboard')} → "
            f"{yellow('episode')} → {red('upload')}\n\n" +
            dim("Colors: ") + blue("blue") + dim("=infra  ") +
            yellow("yellow") + dim("=writes  ") +
            green("green") + dim("=reads  ") +
            red("red") + dim("=irreversible")
        ),
    )
    sub = parser.add_subparsers(dest="command", help="Available commands")

    # 0. Config / env setup
    config_p = sub.add_parser("config", help=blue("[setup] Show env var status / interactive setup"))
    config_p.add_argument("--setup", action="store_true", help="Interactively set missing required variables")

    # 1. Database setup
    db_p = sub.add_parser("db", help=blue("[step 1] Database setup and migrations"))
    db_sub = db_p.add_subparsers(dest="db_command", help="Database subcommands")
    create_p = db_sub.add_parser("create", help="Initialize database")
    create_p.add_argument("--db", default=None, help="Database path")
    migrate_p = db_sub.add_parser("migrate", help="Run schema migrations")
    migrate_p.add_argument("--dry-run", action="store_true")
    migrate_p.add_argument("--version", default="all", choices=["v1", "v2", "all"])
    migrate_p.add_argument("--db", default=None)

    # 2. API server
    serve_p = sub.add_parser("serve", help=blue("[step 2] Start API server + accept submissions"))
    serve_p.add_argument("--host", default="127.0.0.1", help="Bind host")
    serve_p.add_argument("--port", type=int, default=8000, help="Bind port")

    # 3. AI research
    research_p = sub.add_parser("research", help=yellow("[step 3] GitHub + AI research on submissions"))
    add_common_args(research_p)

    # 4. Round 1 scoring
    score_p = sub.add_parser("score", help=yellow("[step 4] Round 1 AI judge scoring"))
    add_common_args(score_p)
    score_p.add_argument("--round", type=int, default=1, help="Scoring round (default: 1)")

    # 5. Community votes
    votes_p = sub.add_parser("votes", help=yellow("[step 5] Collect Solana community votes"))
    votes_p.add_argument("--collect", action="store_true", help=yellow("write: pull new transactions"))
    votes_p.add_argument("--scores", action="store_true", help=green("read: compute weighted scores"))
    votes_p.add_argument("--stats", action="store_true", help=green("read: show vote summary"))
    votes_p.add_argument("--test", action="store_true")
    votes_p.add_argument("--db-path", default=None)

    # 6. Round 2 synthesis
    synthesize_p = sub.add_parser("synthesize", help=yellow("[step 6] Round 2 synthesis (AI + community)"))
    add_common_args(synthesize_p)

    # 7. Leaderboard
    leaderboard_p = sub.add_parser("leaderboard", help=green("[step 7] Display final leaderboard"))
    leaderboard_p.add_argument("--version", default="v2", choices=["v1", "v2"])
    leaderboard_p.add_argument("--db-file", default=None)
    leaderboard_p.add_argument("--output", help="Output file")
    leaderboard_p.add_argument("--round", type=int, default=1)

    # 8. Episode generation
    episode_p = sub.add_parser("episode", help=yellow("[step 8] Generate episode for a submission"))
    add_common_args(episode_p)
    episode_p.add_argument("--video-url", help="Video URL for episode")
    episode_p.add_argument("--avatar-url", help="Avatar URL override")
    episode_p.add_argument("--output-dir", help="Episode output directory")
    episode_p.add_argument("--validate-only", action="store_true")
    episode_p.add_argument("--episode-file", help="Existing episode file to validate")

    # 9. Upload to YouTube
    upload_p = sub.add_parser("upload", help=red("[step 9] Upload recorded episode to YouTube"))
    add_common_args(upload_p)
    upload_p.add_argument("--dry-run", action="store_true")
    upload_p.add_argument("--limit", type=int)

    # --- Utilities ---
    sub.add_parser("static-data", help=green("Regenerate static JSON files for frontend"))

    recovery_p = sub.add_parser("recovery", help=dim("Backup/restore submissions"))
    recovery_p.add_argument("--list", action="store_true")
    recovery_p.add_argument("--restore", help="Submission ID to restore")
    recovery_p.add_argument("--validate", help="Backup file to validate")
    recovery_p.add_argument("--db-path", default=None)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "config":
        cmd_config(args)
        return

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
        if not args.db_command:
            db_p.print_help()
            sys.exit(1)
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
