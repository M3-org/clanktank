"""Clank Tank hackathon CLI — unified entry point."""

import argparse
import os
import re
import sys

# ANSI color helpers — no-op when stdout is not a TTY
_IS_TTY = sys.stdout.isatty()
_SUPPRESS_COLOR = False  # set to True by --json flag


def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if (_IS_TTY and not _SUPPRESS_COLOR) else text


def blue(t):
    return _c("34", t)


def cyan(t):
    return _c("36", t)


def green(t):
    return _c("32", t)


def yellow(t):
    return _c("33", t)


def red(t):
    return _c("31", t)


def dim(t):
    return _c("2", t)


def bold(t):
    return _c("1", t)


# Color scheme:
#   blue   = infrastructure (db, serve, config)
#   yellow = write/mutate pipeline (research, score, votes --collect, synthesize, episode, upload)
#   green  = read-only (leaderboard, static-data)
#   red    = irreversible external action (upload to YouTube)


# ---------------------------------------------------------------------------
# Shared read-command helpers — stdlib only, no package imports
# ---------------------------------------------------------------------------


def _db_path_from_env() -> str:
    """Get DB path from env or .env file, falling back to default."""
    from pathlib import Path

    val = os.getenv("HACKATHON_DB_PATH")
    if not val:
        env_path = Path(__file__).resolve().parents[1] / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("HACKATHON_DB_PATH="):
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    return val or str(Path(__file__).resolve().parents[1] / "data" / "hackathon.db")


def _open_db(db_path: str):
    """Open sqlite3 connection with Row factory."""
    import sqlite3

    conn = sqlite3.connect(db_path, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def _table(headers: list[str], rows: list[list], col_colors=None):
    """Print a left-aligned table with separator. col_colors: list of color fns or None."""
    widths = [len(h) for h in headers]
    str_rows = [[str(c) if c is not None else "-" for c in row] for row in rows]
    for row in str_rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    sep = "  ".join("─" * w for w in widths)
    header = "  ".join(bold(h.ljust(widths[i])) for i, h in enumerate(headers))
    print(header)
    print(dim(sep))
    for row in str_rows:
        cells = []
        for i, cell in enumerate(row):
            s = cell.ljust(widths[i])
            if col_colors and i < len(col_colors) and col_colors[i]:
                s = col_colors[i](s)
            cells.append(s)
        print("  ".join(cells))
    print(dim(sep))
    print(dim(f"  {len(rows)} row{'s' if len(rows) != 1 else ''}"))


def _status_color(status: str):
    return {
        "submitted": lambda t: _c("37", t),  # white
        "researched": yellow,
        "scored": cyan,
        "community-voting": lambda t: _c("35", t),  # magenta
        "completed": green,
        "published": lambda t: _c("32;1", t),  # bright green
    }.get(status, dim)(status)


def _bar(n: int, total: int, width: int = 20) -> str:
    filled = round(width * n / total) if total else 0
    return green("█" * filled) + dim("░" * (width - filled))


# ---------------------------------------------------------------------------
# clanktank stats
# ---------------------------------------------------------------------------


def cmd_stats(args):
    import sqlite3

    db = _db_path_from_env()
    try:
        conn = _open_db(db)
    except sqlite3.OperationalError as e:
        print(red(f"Cannot open DB: {e}"))
        sys.exit(1)

    cur = conn.cursor()

    total = cur.execute("SELECT COUNT(*) FROM hackathon_submissions_v2").fetchone()[0]
    if not total:
        print(yellow("No submissions yet."))
        return

    print(f"\n{bold('Clank Tank')}  {dim('•')}  {bold(str(total))} submissions\n")

    # Status breakdown
    rows = cur.execute(
        "SELECT status, COUNT(*) AS n FROM hackathon_submissions_v2 GROUP BY status ORDER BY n DESC"
    ).fetchall()
    print(f"  {bold('Status')}")
    for r in rows:
        pct = r["n"] / total * 100
        print(f"  {_status_color(r['status']):<22}  {_bar(r['n'], total)}  {r['n']:>3}  {dim(f'{pct:.0f}%')}")

    # Category breakdown
    cat_rows = cur.execute(
        "SELECT category, COUNT(*) AS n FROM hackathon_submissions_v2 GROUP BY category ORDER BY n DESC"
    ).fetchall()
    print(f"\n  {bold('Category')}")
    for r in cat_rows:
        print(f"  {r['category']:<22}  {_bar(r['n'], total)}  {r['n']:>3}")

    # Score summary
    score_row = cur.execute(
        "SELECT AVG(weighted_total)/4 AS avg, MAX(weighted_total)/4 AS hi, "
        "MIN(weighted_total)/4 AS lo, COUNT(DISTINCT submission_id) AS scored "
        "FROM hackathon_scores WHERE round = 1"
    ).fetchone()
    if score_row and score_row["scored"]:
        print(f"\n  {bold('Scores')}  {dim('(0-10 scale, Round 1)')}")
        print(f"  Scored:   {score_row['scored']} / {total}")
        print(f"  Average:  {score_row['avg']:.2f}")
        print(f"  Range:    {score_row['lo']:.1f} – {score_row['hi']:.1f}")
    print()
    conn.close()


# ---------------------------------------------------------------------------
# clanktank submissions  (list, detail, or search)
# ---------------------------------------------------------------------------


def cmd_submissions(args):
    import json
    import sqlite3

    global _SUPPRESS_COLOR
    if getattr(args, "json", False):
        _SUPPRESS_COLOR = True

    db = _db_path_from_env()
    try:
        conn = _open_db(db)
    except sqlite3.OperationalError as e:
        print(red(f"Cannot open DB: {e}"))
        sys.exit(1)

    # --- Detail mode ---
    if args.id is not None:
        row = conn.execute(
            "SELECT * FROM hackathon_submissions_v2 WHERE submission_id = ?",
            (args.id,),
        ).fetchone()
        if not row:
            print(red(f"Submission {args.id} not found."))
            sys.exit(1)

        r = dict(row)
        sid = r["submission_id"]

        scores = conn.execute(
            "SELECT judge_name, innovation, technical_execution, market_potential, "
            "user_experience, weighted_total, round, community_bonus, final_verdict, notes "
            "FROM hackathon_scores WHERE submission_id = ? ORDER BY round, judge_name",
            (args.id,),
        ).fetchall()

        research = conn.execute(
            "SELECT technical_assessment FROM hackathon_research WHERE submission_id = ?",
            (args.id,),
        ).fetchone()

        if args.json:
            out = {
                "submission_id": sid,
                "project_name": r["project_name"],
                "status": r["status"],
                "category": r["category"],
                "description": r.get("description"),
                "github_url": r.get("github_url"),
                "project_image": r.get("project_image"),
            }
            if not args.brief:
                score_list = []
                for s in scores:
                    entry = {
                        "judge": s["judge_name"],
                        "round": s["round"],
                        "innovation": s["innovation"],
                        "technical_execution": s["technical_execution"],
                        "market_potential": s["market_potential"],
                        "user_experience": s["user_experience"],
                        "weighted_total": s["weighted_total"],
                        "community_bonus": s["community_bonus"],
                    }
                    if s["notes"]:
                        try:
                            entry["notes"] = json.loads(s["notes"])
                        except (json.JSONDecodeError, TypeError):
                            entry["notes"] = s["notes"]
                    score_list.append(entry)
                out["scores"] = score_list
                if research and research["technical_assessment"]:
                    try:
                        ta = json.loads(research["technical_assessment"])
                    except (json.JSONDecodeError, TypeError):
                        ta = research["technical_assessment"]
                    out["research"] = {"technical_assessment": ta}
                else:
                    out["research"] = None
            print(json.dumps(out, indent=2, default=str))
        else:
            name = r["project_name"]
            status = r["status"]
            category = r["category"]
            desc = r.get("description") or ""

            # --- Header ---
            print()
            print(f"# {bold(name)}")
            print()
            meta = [f"**Status:** {_status_color(status)}", f"**Category:** {category}"]
            print(" | ".join(meta))
            if desc:
                print(f"\n{desc}")
            print()

            # --- Links ---
            links = [
                ("GitHub", r.get("github_url")),
                ("Demo", r.get("demo_video_url")),
                ("Discord", r.get("discord_handle")),
                ("Twitter", r.get("twitter_handle")),
                ("Solana", r.get("solana_address")),
                ("Submitted", r.get("created_at", "")[:19]),
            ]
            active_links = [(lbl, v) for lbl, v in links if v]
            if active_links:
                for label, val in active_links:
                    print(f"- **{label}:** {val}")
                print()

            # --- Scores ---
            if scores and not args.brief:
                # Group scores by judge, merge R1 + R2 into one row
                r1_scores = {s["judge_name"]: s for s in scores if s["round"] == 1}
                r2_scores = {s["judge_name"]: s for s in scores if s["round"] == 2}
                judges = list(dict.fromkeys(s["judge_name"] for s in scores))  # preserve order
                has_r2 = bool(r2_scores)

                print(f"## {bold('Scores')}")
                print()

                def _pad(text: str, width: int, right: bool = False) -> str:
                    """Pad by visible length, ignoring ANSI escape codes."""
                    import re
                    visible = len(re.sub(r"\033\[[0-9;]*m", "", text))
                    pad = " " * max(0, width - visible)
                    return (pad + text) if right else (text + pad)

                if _IS_TTY:
                    # Box-drawing table for terminal
                    W = 10  # column width
                    r2_hdr = f"┬{'─' * (W + 2)}" if has_r2 else ""
                    r2_mid = f"┼{'─' * (W + 2)}" if has_r2 else ""
                    r2_bot = f"┴{'─' * (W + 2)}" if has_r2 else ""
                    sep = f"{'─' * (W + 2)}"
                    print(f"  ┌{sep}┬{sep}┬{sep}┬{sep}┬{sep}┬{sep}{r2_hdr}┐")
                    h = [bold("Judge"), bold("Innovation"), bold("Technical"), bold("Market"), bold("UX"), bold("R1")]
                    row = f"  │ {_pad(h[0], W)} │ {_pad(h[1], W, True)} │ {_pad(h[2], W, True)} │ {_pad(h[3], W, True)} │ {_pad(h[4], W, True)} │ {_pad(h[5], W, True)} "
                    if has_r2:
                        row += f"│ {_pad(bold('R2'), W, True)} "
                    print(row + "│")
                    print(f"  ├{sep}┼{sep}┼{sep}┼{sep}┼{sep}┼{sep}{r2_mid}┤")
                    for j in judges:
                        r1 = r1_scores.get(j)
                        r2 = r2_scores.get(j)
                        inn = f"{r1['innovation']:.0f}" if r1 and r1["innovation"] is not None else "-"
                        tech = f"{r1['technical_execution']:.0f}" if r1 and r1["technical_execution"] is not None else "-"
                        mkt = f"{r1['market_potential']:.0f}" if r1 and r1["market_potential"] is not None else "-"
                        ux = f"{r1['user_experience']:.0f}" if r1 and r1["user_experience"] is not None else "-"
                        r1_tot = f"{r1['weighted_total'] / 4:.1f}" if r1 and r1["weighted_total"] is not None else "-"
                        row = f"  │ {_pad(cyan(j), W)} │ {_pad(inn, W, True)} │ {_pad(tech, W, True)} │ {_pad(mkt, W, True)} │ {_pad(ux, W, True)} │ {_pad(bold(r1_tot), W, True)} "
                        if has_r2:
                            r2_tot = f"{r2['weighted_total'] / 4:.1f}" if r2 and r2["weighted_total"] is not None else "-"
                            row += f"│ {_pad(bold(r2_tot), W, True)} "
                        print(row + "│")
                    print(f"  └{sep}┴{sep}┴{sep}┴{sep}┴{sep}┴{sep}{r2_bot}┘")
                else:
                    # Plain markdown table for piping
                    r2_hdr = " R2 |" if has_r2 else ""
                    r2_sep = "------:|" if has_r2 else ""
                    print(f"| Judge | Innovation | Technical | Market | UX | R1 | {r2_hdr}")
                    print(f"|-------|----------:|---------:|------:|---:|-----:| {r2_sep}")
                    for j in judges:
                        r1 = r1_scores.get(j)
                        r2 = r2_scores.get(j)
                        inn = f"{r1['innovation']:.0f}" if r1 and r1["innovation"] is not None else "-"
                        tech = f"{r1['technical_execution']:.0f}" if r1 and r1["technical_execution"] is not None else "-"
                        mkt = f"{r1['market_potential']:.0f}" if r1 and r1["market_potential"] is not None else "-"
                        ux = f"{r1['user_experience']:.0f}" if r1 and r1["user_experience"] is not None else "-"
                        r1_tot = f"{r1['weighted_total'] / 4:.1f}" if r1 and r1["weighted_total"] is not None else "-"
                        r2_cell = ""
                        if has_r2:
                            r2_tot = f"{r2['weighted_total'] / 4:.1f}" if r2 and r2["weighted_total"] is not None else "-"
                            r2_cell = f" {r2_tot} |"
                        print(f"| {j} | {inn} | {tech} | {mkt} | {ux} | {r1_tot} |{r2_cell}")

                # --- Judge Commentary (grouped by judge) ---
                print(f"\n## {bold('Judge Commentary')}")
                for j in judges:
                    r1 = r1_scores.get(j)
                    r2 = r2_scores.get(j)
                    comments = []
                    for label, s in [("R1", r1), ("R2", r2)]:
                        if not s:
                            continue
                        comment = ""
                        if s["notes"]:
                            try:
                                nd = json.loads(s["notes"])
                                comment = nd.get("overall_comment") or nd.get("round2_final_verdict") or ""
                            except (json.JSONDecodeError, TypeError):
                                pass
                        if not comment and s["final_verdict"]:
                            try:
                                comment = json.loads(s["final_verdict"]).get("final_verdict", "")
                            except (json.JSONDecodeError, TypeError):
                                comment = str(s["final_verdict"])
                        if comment:
                            comments.append((label, comment))
                    if comments:
                        print(f"\n### {j}")
                        for label, comment in comments:
                            print(f"\n**{label}:** {comment}")

            elif scores:
                print(f"## {bold('Scores')}  {dim('(use without -b to see details)')}")

            # --- Research ---
            if research and research["technical_assessment"] and not args.brief:
                try:
                    ta = json.loads(research["technical_assessment"])
                    summary = ta.get("summary") or ta.get("executive_summary") or ""
                    if summary:
                        print(f"\n## {bold('Research')}")
                        print(f"\n{summary}")
                except (json.JSONDecodeError, TypeError):
                    pass  # malformed research JSON — skip section silently

            print()

        conn.close()
        return

    # --- Search / list mode ---
    where_clauses = []
    params: list = []

    if args.search:
        term = f"%{args.search}%"
        where_clauses.append("(s.project_name LIKE ? OR s.category LIKE ? OR s.description LIKE ?)")
        params.extend([term, term, term])

    if args.status:
        where_clauses.append("s.status = ?")
        params.append(args.status)

    where = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    rows = conn.execute(
        f"""
        SELECT
            s.submission_id,
            s.project_name,
            s.category,
            s.status,
            s.github_url,
            s.project_image,
            ROUND(AVG(sc.weighted_total) / 4.0, 1) AS avg_score,
            COUNT(DISTINCT sc.judge_name) AS judges
        FROM hackathon_submissions_v2 s
        LEFT JOIN hackathon_scores sc ON s.submission_id = sc.submission_id AND sc.round = 1
        {where}
        GROUP BY s.submission_id
        ORDER BY avg_score DESC NULLS LAST, s.created_at DESC
        """,
        params,
    ).fetchall()

    if not rows:
        print(yellow("No submissions found."))
        conn.close()
        return

    if args.json:
        out = [
            {
                "submission_id": r["submission_id"],
                "project_name": r["project_name"],
                "category": r["category"],
                "status": r["status"],
                "github_url": r["github_url"],
                "project_image": r["project_image"],
                "avg_score": r["avg_score"],
                "judges": r["judges"],
            }
            for r in rows
        ]
        print(json.dumps(out, indent=2, default=str))
    else:
        print()
        headers = ["ID", "Project", "Category", "Status", "Score", "Judges"]
        table_rows = [
            [
                r["submission_id"],
                r["project_name"][:32],
                r["category"][:16],
                r["status"],
                f"{r['avg_score']:.1f}" if r["avg_score"] else "-",
                f"{r['judges']}/4" if r["judges"] else "0/4",
            ]
            for r in rows
        ]
        col_colors = [
            dim,  # ID
            None,  # Project (no color)
            dim,  # Category
            lambda t: _status_color(t.strip()),  # Status (strip padding before coloring)
            green,  # Score
            dim,  # Judges
        ]
        _table(headers, table_rows, col_colors)
        print()

    conn.close()


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
    ("OPENROUTER_API_KEY", True, "AI research + judge scoring"),
    ("DISCORD_CLIENT_ID", True, "Discord OAuth login"),
    ("DISCORD_CLIENT_SECRET", True, "Discord OAuth login"),
    ("DISCORD_TOKEN", True, "Discord bot (community voting)"),
    ("PRIZE_WALLET_ADDRESS", True, "Solana wallet to watch for votes"),
    ("GITHUB_TOKEN", False, "Higher GitHub API rate limits"),
    ("HACKATHON_DB_PATH", False, "Default: data/hackathon.db"),
    ("SUBMISSION_DEADLINE", False, "ISO datetime to close submissions"),
    ("DISCORD_GUILD_ID", False, "Guild ID for role-based auth"),
    ("DISCORD_BOT_TOKEN", False, "Bot token for guild role fetching"),
    ("VITE_PRIZE_WALLET_ADDRESS", False, "Expose wallet address to frontend"),
    ("AI_MODEL_NAME", True, "OpenRouter model ID (e.g. openrouter/auto, anthropic/claude-sonnet-4-5)"),
    ("STATIC_DATA_DIR", False, "Frontend static data output dir"),
]


def _is_sensitive_env_var(name: str) -> bool:
    """Treat credential-like env vars as sensitive to avoid leaking values in terminal output."""
    markers = ("KEY", "SECRET", "TOKEN", "PASSWORD")
    return any(marker in name for marker in markers)


def _set_env_key(env_path, key: str, value: str):
    """Write a single key=value to .env, updating in-place if it exists, appending if not.

    Never touches other lines. Preserves comments, ordering, and existing values.
    """

    lines = env_path.read_text().splitlines() if env_path.exists() else []
    key_pattern = re.compile(rf"^\s*{re.escape(key)}\s*=")
    updated = False
    for i, line in enumerate(lines):
        # Match KEY=value with optional whitespace around '=' while ignoring comments.
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        if key_pattern.match(line) or line.strip() == key:
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
            display = "(set)" if _is_sensitive_env_var(name) else val[:14] + "..." if len(val) > 14 else val
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
            dim("Pipeline order:\n") + f"  {blue('db')} → {blue('serve')} → {yellow('research')} → {yellow('score')} → "
            f"{yellow('votes')} → {yellow('synthesize')} → {green('leaderboard')} → "
            f"{yellow('episode')} → {red('upload')}\n\n"
            + dim("Colors: ")
            + blue("blue")
            + dim("=infra  ")
            + yellow("yellow")
            + dim("=writes  ")
            + green("green")
            + dim("=reads  ")
            + red("red")
            + dim("=irreversible")
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
    score_p.add_argument("--round", type=int, default=None, help="Scoring round (default: 1)")

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
    leaderboard_p.add_argument("--round", type=int, default=None, help="Sort by round (1 or 2); default: combined")

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

    # --- Read / inspect (green = read-only) ---
    sub.add_parser("stats", help=green("Hackathon overview: counts, categories, score summary"))

    subs_p = sub.add_parser("submissions", help=green("Browse submissions (list, detail, or search)"))
    subs_p.add_argument("id", type=int, nargs="?", default=None, help="Submission ID — shows detail view")
    subs_p.add_argument("-s", "--search", default=None, help="Search project name, category, or description")
    subs_p.add_argument(
        "--status",
        default=None,
        choices=["submitted", "researched", "scored", "community-voting", "completed", "published"],
        help="Filter by status (list/search mode)",
    )
    subs_p.add_argument("-b", "--brief", action="store_true", help="Omit scores and research (detail mode)")
    subs_p.add_argument("-j", "--json", action="store_true", help="Output as JSON instead of formatted text")

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
        if hasattr(args, "round") and args.round is not None:
            new_argv += ["--round", str(args.round)]
        sys.argv = new_argv
        manager_main()

    elif args.command == "serve":
        import subprocess

        result = subprocess.run(
            ["uvicorn", "hackathon.backend.app:app", "--host", args.host, "--port", str(args.port)]
        )
        sys.exit(result.returncode)

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
        if args.video_url:
            new_argv += ["--video-url", args.video_url]
        if args.avatar_url:
            new_argv += ["--avatar-url", args.avatar_url]
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
        if args.limit is not None:
            new_argv += ["--limit", str(args.limit)]
        sys.argv = new_argv
        upload_main()

    elif args.command == "stats":
        cmd_stats(args)

    elif args.command == "submissions":
        cmd_submissions(args)

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
