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


def _help_screen():
    """Print structured help with pipeline steps and usage hints."""
    def _line(step, cmd, color_fn, desc, usage=""):
        col0 = dim(f"{step:>3}.") if step else "    "
        pad1 = " " * (14 - len(cmd))
        pad2 = " " * (34 - len(desc)) if usage else ""
        hint = f"{pad2}{dim(usage)}" if usage else ""
        print(f"  {col0} {color_fn(cmd)}{pad1}{desc}{hint}")

    print(f"  {bold('Pipeline:')}")
    _line(0,  "config",      blue,   "Show env var status / setup",    "config [VAR] [--setup]")
    _line(1,  "db",          blue,   "Database setup and migrations",  "db {create|migrate} [--dry-run]")
    _line(2,  "serve",       blue,   "Start API server",               "serve [--host HOST] [--port PORT]")
    _line(3,  "research",    yellow, "GitHub + AI research",           "research --submission-id ID [--all] [-f]")
    _line(4,  "score",       yellow, "Round 1 AI judge scoring",       "score --submission-id ID [--all] [--round N]")
    _line(5,  "votes",       yellow, "Collect Solana community votes", "votes {--collect|--scores|--stats|--test}")
    _line(6,  "synthesize",  yellow, "Round 2 synthesis",              "synthesize --submission-id ID [--all]")
    _line(7,  "static-data", yellow, "Regenerate JSON for frontend")
    _line(8,  "episode",     yellow, "Generate episode",               "episode --submission-id ID [--validate-only]")
    _line(9,  "record",      yellow, "Record episode video",           "record URL [--headless] [--format webm|mp4]")
    _line(10, "upload",      red,    "Upload to YouTube",              "upload --submission-id ID [--dry-run]")
    _line(11, "cdn",         yellow, "Upload media to Bunny CDN",      "cdn <file|dir> [--remote PATH] [--dry-run]")
    print()
    print(f"  {bold('Quick views:')}")
    _line(0, "status",      green,  "Pipeline overview + next steps")
    _line(0, "leaderboard", green,  "Display final leaderboard",      "leaderboard [--round N] [--output FILE]")
    _line(0, "submissions", green,  "Browse submissions",             "submissions [ID] [-s QUERY] [--status S] [-j]")
    print()
    print(f"  {bold('Examples:')}")
    print(f"    {dim('clanktank status')}")
    print(f"    {dim('clanktank score --submission-id 42')}")
    print(f"    {dim('clanktank score --all')}")
    print(f"    {dim('clanktank leaderboard --round 1')}")
    print()
    print(f"  Run {bold('clanktank <command> --help')} for details.")


def _pick_submission(status_filter=None):
    """Interactive submission picker (TTY only). Returns submission_id string or None."""
    db = _db_path_from_env()
    try:
        conn = _open_db(db)
    except Exception:
        print(red("  Cannot open database."))
        return None
    query = "SELECT submission_id, project_name, status FROM hackathon_submissions_v2"
    params = []
    if status_filter:
        placeholders = ",".join("?" * len(status_filter))
        query += f" WHERE status IN ({placeholders})"
        params = list(status_filter)
    query += " ORDER BY submission_id"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    if not rows:
        print(dim("  No matching submissions found."))
        return None
    for r in rows:
        print(f"  {bold(str(r['submission_id']).rjust(3))}  {r['project_name']}  {dim(r['status'])}")
    print()
    try:
        choice = input(f"  {bold('submission-id')}: ").strip()
        return choice if choice else None
    except (EOFError, KeyboardInterrupt):
        print()
        return None


def _banner():
    """Print compact ASCII banner + quick status."""
    logo = dim(r"""
   ___  _            _     _____           _
  / __\| | __ _ _ _ | | __/__   \__ _ _ _ | | __
 / /   | |/ _` | ' \| |/ /  / /\/ _` | ' \| |/ /
/ /___ | | (_| | | ||   <  / / | (_| | | ||   <
\____/ |_|\__,_|_| ||_|\_\ \/   \__,_|_| ||_|\_\
""".rstrip())
    print(logo)

    # Quick status line
    try:
        import sqlite3

        db = _db_path_from_env()
        conn = sqlite3.connect(db, timeout=5)
        total = conn.execute("SELECT COUNT(*) FROM hackathon_submissions_v2").fetchone()[0]
        conn.close()
        print(f"  {bold(str(total))} submissions  {dim('·')}  DB: {dim(db)}")
    except Exception:
        print(f"  DB: {dim(_db_path_from_env())}")

    deadline = os.getenv("SUBMISSION_DEADLINE")
    if deadline:
        try:
            from datetime import datetime, timezone

            dt = datetime.fromisoformat(deadline)
            now = datetime.now(timezone.utc)
            delta = dt - now
            if delta.total_seconds() <= 0:
                print(f"  Deadline: {red('CLOSED')}  {dim(deadline)}")
            else:
                days = delta.days
                hours, rem = divmod(delta.seconds, 3600)
                mins = rem // 60
                parts = []
                if days:
                    parts.append(f"{days}d")
                if hours:
                    parts.append(f"{hours}h")
                parts.append(f"{mins}m")
                countdown = " ".join(parts)
                print(f"  Deadline: {yellow(countdown)} remaining  {dim(deadline)}")
        except (ValueError, TypeError):
            print(f"  Deadline: {yellow(deadline)}")
    print()


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


def _print_research_md(ta: dict):
    """Render technical_assessment JSON as clean readable markdown."""

    # Section renderers for known keys
    _SECTION_TITLES = {
        "technical_implementation": "Technical Implementation",
        "originality_effort": "Originality & Effort",
        "market_analysis": "Market Analysis",
        "viability_assessment": "Viability Assessment",
        "innovation_rating": "Innovation Rating",
    }

    def _scored_section(title: str, d: dict):
        score = d.get("score", "?")
        justification = d.get("justification", "")
        print(f"### {bold(title)}  {cyan(str(score))}/10\n")
        if justification:
            print(f"{justification}\n")
        for k, v in d.items():
            if k in ("score", "justification"):
                continue
            label = k.replace("_", " ").title()
            if isinstance(v, list):
                print(f"**{label}:**")
                for item in v:
                    print(f"  - {item}")
                print()
            elif isinstance(v, bool):
                print(f"**{label}:** {'Yes' if v else 'No'}")
            elif v:
                print(f"**{label}:** {v}")
        print()

    for key, title in _SECTION_TITLES.items():
        section = ta.get(key)
        if isinstance(section, dict):
            _scored_section(title, section)

    # Judge insights
    insights = ta.get("judge_insights")
    if isinstance(insights, dict):
        print(f"### {bold('Judge Insights')}\n")
        for k, v in insights.items():
            judge = k.replace("_take", "").replace("s_", " ").replace("_", " ").strip()
            if v:
                print(f"**{judge}:** {v}\n")

    # Red flags
    flags = ta.get("red_flags")
    if isinstance(flags, list) and flags:
        print(f"### {bold('Red Flags')}\n")
        for flag in flags:
            print(f"  - {yellow(str(flag))}")
        print()

    # Overall assessment
    overall = ta.get("overall_assessment")
    if isinstance(overall, dict):
        score = overall.get("total_score", "?")
        max_score = overall.get("max_possible", "?")
        rec = overall.get("recommendation", "")
        print(f"### {bold('Overall Assessment')}  {cyan(str(score))}/{max_score}\n")
        if rec:
            print(f"{rec}\n")

    # Any remaining top-level keys we didn't handle
    handled = set(_SECTION_TITLES) | {"judge_insights", "red_flags", "overall_assessment", "summary", "executive_summary"}
    for k, v in ta.items():
        if k in handled:
            continue
        label = k.replace("_", " ").title()
        if isinstance(v, str):
            print(f"**{label}:** {v}\n")
        elif isinstance(v, list):
            print(f"**{label}:**")
            for item in v:
                print(f"  - {item}")
            print()


# ---------------------------------------------------------------------------
# clanktank stats
# ---------------------------------------------------------------------------


def cmd_status(_args):
    """Show pipeline overview: deadline, status breakdown, categories, scores, next steps."""
    import sqlite3
    from datetime import datetime, timezone

    db = _db_path_from_env()
    try:
        conn = _open_db(db)
    except sqlite3.OperationalError as e:
        print(red(f"  Cannot open DB: {e}"))
        sys.exit(1)

    cur = conn.cursor()

    total = cur.execute("SELECT COUNT(*) FROM hackathon_submissions_v2").fetchone()[0]
    if not total:
        print(yellow("\n  No submissions yet."))
        return

    print(f"\n  {bold('Clank Tank')}  {dim('·')}  {bold(str(total))} submissions")

    # Deadline countdown
    deadline = os.getenv("SUBMISSION_DEADLINE")
    if deadline:
        try:
            dt = datetime.fromisoformat(deadline)
            now = datetime.now(timezone.utc)
            delta = dt - now
            if delta.total_seconds() <= 0:
                print(f"  Deadline: {red('CLOSED')}  {dim(deadline)}")
            else:
                days = delta.days
                hours, rem = divmod(delta.seconds, 3600)
                mins = rem // 60
                parts = []
                if days:
                    parts.append(f"{days}d")
                if hours:
                    parts.append(f"{hours}h")
                parts.append(f"{mins}m")
                print(f"  Deadline: {yellow(' '.join(parts))} remaining  {dim(deadline)}")
        except (ValueError, TypeError):
            print(f"  Deadline: {yellow(deadline)}")

    # Pipeline status breakdown
    rows = cur.execute(
        "SELECT status, COUNT(*) AS n FROM hackathon_submissions_v2 GROUP BY status ORDER BY n DESC"
    ).fetchall()
    counts = {r["status"]: r["n"] for r in rows}
    print(f"\n  {bold('Pipeline')}")
    stages = ["submitted", "researched", "scored", "community-voting", "completed", "published"]
    for stage in stages:
        cnt = counts.get(stage, 0)
        if cnt:
            pct = cnt / total * 100
            print(f"  {_status_color(stage):<22}  {_bar(cnt, total)}  {cnt:>3}  {dim(f'{pct:.0f}%')}")

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

    # Next steps
    next_steps = [
        ("submitted",  "clanktank research --all"),
        ("researched", "clanktank score --all"),
        ("scored",     "clanktank synthesize --all"),
        ("completed",  "clanktank episode --submission-id ID"),
    ]
    tips = [(counts.get(s, 0), s, ex) for s, ex in next_steps if counts.get(s, 0)]
    if tips:
        print(f"\n  {bold('Next steps:')}")
        for cnt, status, example in tips:
            print(f"    {green(example.ljust(40))} {dim(f'{cnt} {status}')}")

    print()
    print(dim("  Tip: clanktank submissions to browse, clanktank leaderboard for rankings"))
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
                                # Malformed notes JSON — fall back to other sources below
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
                if getattr(args, "research", False):
                    # Full research as clean markdown
                    try:
                        ta = json.loads(research["technical_assessment"])
                        print(f"\n## {bold('Research')}\n")
                        _print_research_md(ta)
                    except (json.JSONDecodeError, TypeError):
                        print(f"\n## {bold('Research')}\n")
                        print(research["technical_assessment"])
                    print(f"\n{dim('Source: hackathon_research.technical_assessment  (submission_id=' + str(sid) + ')')}")
                    print(dim(f"  DB: {db}"))
                else:
                    try:
                        ta = json.loads(research["technical_assessment"])
                        summary = ta.get("summary") or ta.get("executive_summary") or ""
                        if summary:
                            print(f"\n## {bold('Research')}")
                            print(f"\n{summary}")
                    except (json.JSONDecodeError, TypeError):
                        pass  # malformed research JSON — skip section silently

            print()
            print(dim("  Tip: add -j for JSON, -r/--research for full research"))

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
        print(dim("  Tip: clanktank submissions <id> for detail view"))
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
    ("AI_MODEL_NAME", True, "OpenRouter model ID (e.g. openrouter/auto, anthropic/claude-sonnet-4-5)"),
    ("ENVIRONMENT", False, "development or production"),
    ("GITHUB_TOKEN", False, "Higher GitHub API rate limits"),
    ("HACKATHON_DB_PATH", False, "Default: data/hackathon.db"),
    ("SUBMISSION_DEADLINE", False, "ISO datetime to close submissions"),
    ("DISCORD_GUILD_ID", False, "Guild ID for role-based auth"),
    ("DISCORD_BOT_TOKEN", False, "Bot token for guild role fetching"),
    ("VITE_PRIZE_WALLET_ADDRESS", False, "Expose wallet address to frontend"),
    ("STATIC_DATA_DIR", False, "Frontend static data output dir"),
    ("JUDGE_CONFIG", False, "JSON file path or inline JSON (default: data/judge_config.json)"),
    ("RESEARCH_CONFIG", False, "JSON file path or inline JSON (default: data/research_config.json)"),
    ("HELIUS_API_KEY", False, "Helius API for Solana data"),
    ("BIRDEYE_API_KEY", False, "Birdeye API for token data"),
    ("HELIUS_WEBHOOK_SECRET", False, "Helius webhook HMAC secret"),
    ("BUNNY_STORAGE_ZONE", False, "Bunny CDN storage zone name"),
    ("BUNNY_STORAGE_PASSWORD", False, "Bunny CDN API password"),
    ("BUNNY_CDN_URL", False, "Bunny CDN URL (e.g. https://cdn.elizaos.news)"),
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


def _fmt_prompt(text: str) -> str:
    """Highlight {template_vars} in a prompt string."""
    return re.sub(r"\{(\w+)\}", lambda m: cyan(f"{{{m.group(1)}}}"), text)


def _print_config_value(name: str, data):
    """Pretty-print a parsed JSON config value in a human-readable way."""
    if name == "JUDGE_CONFIG":
        _print_judge_config(data)
    elif name == "RESEARCH_CONFIG":
        _print_research_config(data)
    else:
        import json

        print(json.dumps(data, indent=2))
        print()


def _print_judge_config(data: dict):
    """Render JUDGE_CONFIG as readable sections."""
    # --- Personas ---
    personas = data.get("personas", {})
    if personas:
        print(f"## {bold('Judge Personas')}\n")
        for judge, desc in personas.items():
            print(f"### {cyan(judge)}\n")
            print(f"{desc}\n")

    # --- Criteria ---
    criteria = data.get("criteria", {})
    if criteria:
        print(f"## {bold('Scoring Criteria')}\n")
        for key, c in criteria.items():
            cname = c.get("name", key)
            cdesc = c.get("description", "")
            cmax = c.get("max_score", "?")
            print(f"  {bold(cname):<32} {dim(f'(0-{cmax})')}  {cdesc}")
        print()

    # --- Weights (table) ---
    weights = data.get("weights", {})
    if weights:
        criteria_keys = list(next(iter(weights.values())).keys()) if weights else []
        headers = ["Judge"] + [k.replace("_", " ").title() for k in criteria_keys]
        rows = []
        for judge, w in weights.items():
            row = [judge] + [str(w.get(k, "-")) for k in criteria_keys]
            rows.append(row)
        print(f"## {bold('Weight Multipliers')}\n")
        # Simple table — highlight multipliers above 1.0
        widths = [max(len(h), max(len(r[i]) for r in rows)) for i, h in enumerate(headers)]
        print("  " + "  ".join(bold(h.ljust(widths[i])) for i, h in enumerate(headers)))
        print("  " + "  ".join("─" * w for w in widths))
        for row in rows:
            cells = []
            for i, cell in enumerate(row):
                s = cell.ljust(widths[i])
                if i == 0:
                    s = cyan(s)
                else:
                    try:
                        v = float(cell)
                        if v > 1.0:
                            s = bold(s)
                        elif v < 1.0:
                            s = dim(s)
                    except ValueError:
                        # Non-numeric cell — leave unstyled
                        pass
                cells.append(s)
            print("  " + "  ".join(cells))
        print()

    # --- Score scale ---
    score_scale = data.get("score_scale", "")
    if score_scale:
        print(f"## {bold('Score Scale')}\n")
        print(score_scale.strip())
        print()

    # --- Scoring task ---
    scoring_task = data.get("scoring_task", "")
    if scoring_task:
        print(f"## {bold('Scoring Task')}\n")
        print(_fmt_prompt(scoring_task.strip()))
        print()

    # --- Round 2 template ---
    r2 = data.get("round2_template", "")
    if r2:
        print(f"## {bold('Round 2 Template')}\n")
        print(_fmt_prompt(r2.strip()))
        print()

    # Any remaining keys
    handled = {"personas", "weights", "criteria", "score_scale", "scoring_task", "round2_template"}
    for k, v in data.items():
        if k in handled:
            continue
        import json

        label = k.replace("_", " ").title()
        if isinstance(v, str):
            print(f"## {bold(label)}\n")
            print(_fmt_prompt(v.strip()))
            print()
        else:
            print(f"## {bold(label)}\n")
            print(json.dumps(v, indent=2))
            print()


def _print_research_config(data: dict):
    """Render RESEARCH_CONFIG as readable sections."""
    # --- Penalty thresholds ---
    thresholds = data.get("penalty_thresholds", {})
    if thresholds:
        print(f"## {bold('Penalty Thresholds')}\n")
        for k, v in thresholds.items():
            label = k.replace("_", " ").title()
            print(f"  {label:<28} {bold(str(v))}")
        print()

    # --- All prompt templates ---
    for key, val in data.items():
        if key == "penalty_thresholds":
            continue
        label = key.replace("_", " ").title()
        if isinstance(val, str):
            print(f"## {bold(label)}\n")
            print(_fmt_prompt(val.strip()))
            print()
        elif isinstance(val, dict):
            import json

            print(f"## {bold(label)}\n")
            for sk, sv in val.items():
                slabel = sk.replace("_", " ").title()
                if isinstance(sv, str) and len(sv) > 80:
                    print(f"### {bold(slabel)}\n")
                    print(_fmt_prompt(sv.strip()))
                    print()
                else:
                    print(f"  {slabel:<28} {bold(str(sv))}")
            print()
        else:
            import json

            print(f"## {bold(label)}\n")
            print(json.dumps(val, indent=2))
            print()


def _resolve_json_val(val: str, repo_root) -> dict | None:
    """Given a raw env value, resolve to a parsed dict (file or inline JSON)."""
    import json
    from pathlib import Path

    if not val:
        return None
    # File path?
    if "/" in val or val.endswith(".json"):
        path = Path(val) if Path(val).is_absolute() else repo_root / val
        try:
            return json.loads(path.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            return None
    # Inline JSON
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return None


def cmd_config(args):
    """Show env var status, pretty-print a var, edit config files, or run interactive setup."""
    import json
    import subprocess
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

    # --- Edit a config file ---
    if args.var == "edit":
        edit_target = (args.edit_target or "").upper()
        if not edit_target:
            print(f"Usage: clanktank config edit {cyan('JUDGE_CONFIG')}|{cyan('RESEARCH_CONFIG')}")
            sys.exit(1)

        # Map to default filenames
        defaults = {"JUDGE_CONFIG": "judge_config.json", "RESEARCH_CONFIG": "research_config.json"}
        if edit_target not in defaults:
            print(red(f"Unknown config: {edit_target}. Choose from: {', '.join(defaults)}"))
            sys.exit(1)

        # Resolve file path (same logic as load_json_config)
        raw_val = get_val(edit_target) or ""
        if raw_val and ("/" in raw_val or raw_val.endswith(".json")):
            config_path = Path(raw_val) if Path(raw_val).is_absolute() else REPO_ROOT / raw_val
        else:
            config_path = REPO_ROOT / "data" / defaults[edit_target]

        # If file doesn't exist yet, extract current env value into it
        if not config_path.exists():
            if raw_val and "/" not in raw_val and not raw_val.endswith(".json"):
                # Inline JSON in env — extract to file
                try:
                    parsed = json.loads(raw_val)
                    config_path.parent.mkdir(parents=True, exist_ok=True)
                    config_path.write_text(json.dumps(parsed, indent=2, ensure_ascii=False) + "\n")
                    print(f"Extracted inline {edit_target} to {cyan(str(config_path))}")
                except json.JSONDecodeError:
                    print(red(f"Cannot parse current {edit_target} value as JSON"))
                    sys.exit(1)
            else:
                print(red(f"Config file not found: {config_path}"))
                sys.exit(1)

        editor = os.environ.get("EDITOR", "vi")
        print(f"Opening {cyan(str(config_path))} in {bold(editor)}...")
        result = subprocess.run([editor, str(config_path)])
        if result.returncode != 0:
            print(red(f"Editor exited with code {result.returncode}"))
            sys.exit(1)

        # Validate JSON after edit
        try:
            json.loads(config_path.read_text())
            print(green(f"{edit_target} saved and validated."))
        except json.JSONDecodeError as e:
            print(red(f"WARNING: {config_path} is not valid JSON: {e}"))
            print(yellow("The file was saved but may cause errors at runtime."))
            sys.exit(1)
        return

    # --- Pretty-print a specific var ---
    if args.var:
        var_name = args.var.upper()
        val = get_val(var_name)
        if not val:
            print(red(f"{var_name} is not set."))
            sys.exit(1)
        # Resolve file paths or inline JSON
        parsed = _resolve_json_val(val, REPO_ROOT)
        if parsed is not None:
            print(f"\n{bold(var_name)}\n")
            _print_config_value(var_name, parsed)
        else:
            print(f"\n{bold(var_name)} = {val}\n")
        return

    # Always print status first
    print(f"\n{bold('Clank Tank — environment config')}")
    print(f"  .env: {env_path} {'(exists)' if env_path.exists() else red('(not found)')}\n")

    missing_required = []
    for name, required, desc in ENV_VARS:
        val = get_val(name)
        marker = bold("*") if required else " "
        if val:
            display = "(set)" if _is_sensitive_env_var(name) else val[:14] + "..." if len(val) > 14 else val
            print(f"  {green('✓')} {marker} {name:<34} {dim(display)}")
        elif required:
            print(f"  {red('✗')} {marker} {red(name):<34} {dim(desc)}")
            missing_required.append((name, desc))
        else:
            print(f"  {dim('–')} {marker} {dim(name):<34} {dim(desc)}")

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
    from dotenv import find_dotenv, load_dotenv
    load_dotenv(find_dotenv())

    parser = argparse.ArgumentParser(
        prog="clanktank",
        description=bold("Clank Tank hackathon pipeline CLI"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,  # we handle -h ourselves
    )
    parser.add_argument("-h", "--help", action="store_true", default=False, help="Show help")

    # Override print_help so -h and no-args both show the same good screen
    def _custom_help(file=None):
        _banner()
        _help_screen()

    parser.print_help = _custom_help
    sub = parser.add_subparsers(dest="command", help="Available commands")

    # 0. Config / env setup
    config_p = sub.add_parser("config", help=blue("[setup] Show env var status / interactive setup"))
    config_p.add_argument("var", nargs="?", default=None, help="Pretty-print a var (e.g. JUDGE_CONFIG) or 'edit' to open in $EDITOR")
    config_p.add_argument("edit_target", nargs="?", default=None, help="Config name to edit (e.g. JUDGE_CONFIG)")
    config_p.add_argument("--setup", action="store_true", help="Interactively set missing required variables")

    # 1. Database setup
    db_p = sub.add_parser("db", help=blue("[step 1] Database setup and migrations"))
    db_sub = db_p.add_subparsers(dest="db_command", help="Database subcommands")
    create_p = db_sub.add_parser("create", help="Initialize database")
    create_p.add_argument("--db", default=None, help="Database path")
    create_p.add_argument("-f", "--force", action="store_true", help="Overwrite existing database")
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

    # 7. Static data export
    sub.add_parser("static-data", help=yellow("[step 7] Regenerate JSON for frontend"))

    # 8. Episode generation
    episode_p = sub.add_parser("episode", help=yellow("[step 8] Generate episode for a submission"))
    add_common_args(episode_p)
    episode_p.add_argument("--video-url", help="Video URL for episode")
    episode_p.add_argument("--avatar-url", help="Avatar URL override")
    episode_p.add_argument("--output-dir", help="Episode output directory")
    episode_p.add_argument("--validate-only", action="store_true")
    episode_p.add_argument("--episode-file", help="Existing episode file to validate")

    # 9. Record episode video
    record_p = sub.add_parser("record", help=yellow("[step 9] Record episode video via Puppeteer"))
    record_p.add_argument("url", nargs="?", default=None, help="Shmotime episode URL to record")
    record_p.add_argument("--headless", action="store_true", help="Run Chrome in headless mode")
    record_p.add_argument("--no-record", action="store_true", help="Disable video recording (data export only)")
    record_p.add_argument("--mute", action="store_true", help="Mute audio during recording")
    record_p.add_argument("--quiet", action="store_true", help="Reduce log output")
    record_p.add_argument("--format", default="webm", choices=["webm", "mp4"], help="Video format (default: webm)")
    record_p.add_argument("--output", default=None, help="Output directory (default: ./episodes)")
    record_p.add_argument("--date", default=None, help="Override date for output filenames (YYYY-MM-DD)")
    record_p.add_argument("--width", type=int, default=1920, help="Video width (default: 1920)")
    record_p.add_argument("--height", type=int, default=1080, help="Video height (default: 1080)")
    record_p.add_argument("--fps", type=int, default=30, help="Frame rate (default: 30)")
    record_p.add_argument(
        "--stop-at",
        default="end_postcredits",
        choices=[
            "start_intro", "end_intro", "start_ep", "end_ep",
            "start_credits", "end_credits", "start_postcredits", "end_postcredits", "never",
        ],
        help="When to stop recording (default: end_postcredits)",
    )
    record_p.add_argument("--wait", type=int, default=3600000, help="Max wait time in ms (default: 3600000)")
    record_p.add_argument("--chrome-path", default=None, help="Chrome executable path")
    record_p.add_argument("--no-fix-framerate", action="store_true", help="Disable ffmpeg frame rate post-processing")
    record_p.add_argument("--list", default=None, help="Path to list file for date mapping")

    # 10. Upload to YouTube
    upload_p = sub.add_parser("upload", help=red("[step 10] Upload recorded episode to YouTube"))
    add_common_args(upload_p)
    upload_p.add_argument("--dry-run", action="store_true")
    upload_p.add_argument("--limit", type=int)

    # 11. CDN upload
    cdn_p = sub.add_parser("cdn", help=yellow("[step 11] Upload episode media to Bunny CDN"))
    cdn_p.add_argument("file", nargs="?", help="File or directory to upload")
    cdn_p.add_argument("--dir", "-d", dest="directory", help="Directory to upload (all media files)")
    cdn_p.add_argument("--remote", "-r", help="Remote CDN path (default: derived from local path)")
    cdn_p.add_argument("--dry-run", action="store_true", help="Simulate uploads")
    cdn_p.add_argument("--manifest", "-m", help="Upload from manifest.json")
    cdn_p.add_argument("--update-manifest", action="store_true", help="Update manifest with CDN URLs")
    cdn_p.add_argument("--json", action="store_true", help="Output as JSON")
    cdn_p.add_argument("--stdin", action="store_true", help="Read file paths from stdin")
    cdn_p.add_argument("--max-size", type=float, default=50, help="Max file size in MB (default: 50)")
    cdn_p.add_argument("--no-skip-existing", action="store_true", help="Re-upload existing files")
    cdn_p.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    # --- Read / inspect (green = read-only) ---
    sub.add_parser("status", help=green("Pipeline overview, scores, and next steps"), aliases=["stats"])

    leaderboard_p = sub.add_parser("leaderboard", help=green("Display final leaderboard"))
    leaderboard_p.add_argument("--version", default="v2", choices=["v1", "v2"])
    leaderboard_p.add_argument("--db-file", default=None)
    leaderboard_p.add_argument("--output", help="Output file")
    leaderboard_p.add_argument("--round", type=int, default=None, help="Sort by round (1 or 2); default: combined")

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
    subs_p.add_argument("-r", "--research", action="store_true", help="Show full research data (detail mode)")
    subs_p.add_argument("-j", "--json", action="store_true", help="Output as JSON instead of formatted text")

    args = parser.parse_args()

    if not args.command or args.help:
        _banner()
        _help_screen()
        sys.exit(0)

    if args.command == "config":
        cmd_config(args)
        return

    # Dispatch to modules — rebuild sys.argv for each module's own argparse
    if args.command in ("research", "score", "synthesize", "leaderboard"):
        # Show help if no target specified for commands that need one
        if args.command in ("research", "score", "synthesize"):
            has_target = (hasattr(args, "submission_id") and args.submission_id) or (
                hasattr(args, "all") and args.all
            )
            if not has_target:
                if _IS_TTY:
                    eligible = {
                        "research": ["submitted"],
                        "score": ["researched"],
                        "synthesize": ["scored", "community-voting"],
                    }
                    print(f"\n  {bold('Pick a submission to ' + args.command + ':')}\n")
                    sid = _pick_submission(status_filter=eligible.get(args.command))
                    if sid:
                        args.submission_id = sid
                    else:
                        sys.exit(0)
                else:
                    sub_parsers = {
                        "research": research_p,
                        "score": score_p,
                        "synthesize": synthesize_p,
                    }
                    sub_parsers[args.command].print_help()
                    sys.exit(0)

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

        # Contextual tips
        if args.command == "leaderboard":
            print(dim("\n  Tip: --round 1 to sort by Round 1"))
        elif args.command == "score":
            print(dim("\n  Tip: clanktank leaderboard to see updated rankings"))

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
            from pathlib import Path

            from hackathon.backend.config import HACKATHON_DB_PATH

            db_path = args.db or HACKATHON_DB_PATH
            if Path(db_path).exists() and not args.force:
                print(red(f"Database already exists: {db_path}"))
                print(dim("  Use -f / --force to overwrite."))
                sys.exit(1)

            from hackathon.backend.create_db import main as create_main

            sys.argv = ["create_db"] + (["--db", args.db] if args.db else [])
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
        if not args.submission_id and not args.episode_file:
            if _IS_TTY:
                print(f"\n  {bold('Pick a submission for episode generation:')}\n")
                sid = _pick_submission(status_filter=["scored", "completed", "published"])
                if sid:
                    args.submission_id = sid
                else:
                    sys.exit(0)
            else:
                episode_p.print_help()
                sys.exit(0)

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

    elif args.command == "record":
        import shutil
        import subprocess
        from pathlib import Path

        # Check node is available
        if not shutil.which("node"):
            print(red("node not found — install Node.js to use the recorder."))
            sys.exit(1)

        recorder_script = Path(__file__).resolve().parent / "scripts" / "recorder.js"
        if not recorder_script.exists():
            print(red(f"Recorder script not found: {recorder_script}"))
            sys.exit(1)

        if not args.url:
            record_p.print_help()
            sys.exit(0)

        cmd = ["node", str(recorder_script)]
        if args.headless:
            cmd.append("--headless")
        if args.no_record:
            cmd.append("--no-record")
        if args.mute:
            cmd.append("--mute")
        if args.quiet:
            cmd.append("--quiet")
        if args.no_fix_framerate:
            cmd.append("--no-fix-framerate")
        if args.format != "webm":
            cmd.append(f"--format={args.format}")
        if args.output:
            cmd.append(f"--output={args.output}")
        if args.date:
            cmd.append(f"--date={args.date}")
        if args.width != 1920:
            cmd.append(f"--width={args.width}")
        if args.height != 1080:
            cmd.append(f"--height={args.height}")
        if args.fps != 30:
            cmd.append(f"--fps={args.fps}")
        if args.stop_at != "end_postcredits":
            cmd.append(f"--stop-recording-at={args.stop_at}")
        if args.wait != 3600000:
            cmd.append(f"--wait={args.wait}")
        if args.chrome_path:
            cmd.append(f"--chrome-path={args.chrome_path}")
        if args.list:
            cmd.append(f"--list={args.list}")
        cmd.append(args.url)

        print(f"{yellow('Recording')} {args.url}")
        print(dim(f"  {' '.join(cmd)}"))
        result = subprocess.run(cmd)
        if result.returncode == 0:
            print(dim("\n  Tip: clanktank upload to publish to YouTube"))
        sys.exit(result.returncode)

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

    elif args.command == "cdn":
        from hackathon.scripts.cdn_upload import main as cdn_main

        new_argv = ["cdn_upload"]
        if args.file:
            new_argv.append(args.file)
        if args.directory:
            new_argv += ["--dir", args.directory]
        if args.remote:
            new_argv += ["--remote", args.remote]
        if args.dry_run:
            new_argv.append("--dry-run")
        if args.manifest:
            new_argv += ["--manifest", args.manifest]
        if args.update_manifest:
            new_argv.append("--update-manifest")
        if args.json:
            new_argv.append("--json")
        if args.stdin:
            new_argv.append("--stdin")
        if args.max_size != 50:
            new_argv += ["--max-size", str(args.max_size)]
        if args.no_skip_existing:
            new_argv.append("--no-skip-existing")
        if args.verbose:
            new_argv.append("--verbose")
        sys.argv = new_argv
        cdn_main()

    elif args.command in ("status", "stats"):
        cmd_status(args)

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
        import asyncio
        asyncio.run(votes_main())



if __name__ == "__main__":
    main()
