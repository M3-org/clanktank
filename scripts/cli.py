"""
Clank Tank CLI — browse hackathon data and draft submissions.

Usage:
    python -m hackathon.cli leaderboard        # Ranked leaderboard (default)
    python -m hackathon.cli submissions        # Browse all submissions
    python -m hackathon.cli show <id>          # Submission detail + judge scores
    python -m hackathon.cli stats              # Hackathon stats
    python -m hackathon.cli draft              # Interactive → prefilled submit URL
"""

import argparse
import csv
import io
import json
import os
import shutil
import sys
import urllib.parse
import webbrowser

import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_URL = os.environ.get("CLANKTANK_API_URL", "http://localhost:8000").rstrip("/")
WEB_URL = os.environ.get("CLANKTANK_WEB_URL", "http://localhost:5173").rstrip("/")
TIMEOUT = 10

CATEGORIES = ["DeFi", "Agents", "Gaming", "Infrastructure", "Social", "Other"]

# ---------------------------------------------------------------------------
# Color / formatting helpers
# ---------------------------------------------------------------------------

def _supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if not hasattr(sys.stdout, "isatty"):
        return False
    return sys.stdout.isatty()

USE_COLOR = _supports_color()


def _c(code: str, text: str) -> str:
    if not USE_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"


def dim(t: str) -> str:
    return _c("2", t)


def green(t: str) -> str:
    return _c("32", t)


def bright_green(t: str) -> str:
    return _c("92", t)


def yellow(t: str) -> str:
    return _c("33", t)


def bold(t: str) -> str:
    return _c("1", t)


def cyan(t: str) -> str:
    return _c("36", t)


def score_color(val: float | None) -> str:
    if val is None:
        return dim("—")
    s = f"{val:.1f}"
    if val > 7:
        return green(s)
    if val > 4:
        return yellow(s)
    return dim(s)


STATUS_COLORS = {
    "submitted": dim,
    "researched": yellow,
    "scored": green,
    "community-voting": cyan,
    "completed": bright_green,
    "published": bright_green,
}


def colored_status(status: str) -> str:
    fn = STATUS_COLORS.get(status, dim)
    return fn(status)


TROPHY = {1: "\U0001f947", 2: "\U0001f948", 3: "\U0001f949"}  # gold, silver, bronze


def term_width() -> int:
    return shutil.get_terminal_size((80, 24)).columns

# ---------------------------------------------------------------------------
# Table drawing
# ---------------------------------------------------------------------------

def _visible_len(s: str) -> int:
    """Length of string ignoring ANSI escape sequences."""
    import re
    return len(re.sub(r"\033\[[0-9;]*m", "", s))


def _pad(s: str, width: int) -> str:
    """Pad string to width accounting for ANSI codes."""
    return s + " " * max(0, width - _visible_len(s))


def _rpad(s: str, width: int) -> str:
    """Right-align string accounting for ANSI codes."""
    return " " * max(0, width - _visible_len(s)) + s


def draw_table(headers: list[str], rows: list[list[str]], alignments: list[str] | None = None):
    """Draw a box-drawn table. alignments: 'l' or 'r' per column."""
    if not rows:
        print(dim("  (no data)"))
        return

    ncols = len(headers)
    if alignments is None:
        alignments = ["l"] * ncols

    # Compute column widths
    col_widths = [_visible_len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], _visible_len(cell))

    # Clamp total width to terminal
    tw = term_width()
    total = sum(col_widths) + ncols * 3 + 1  # borders + padding
    if total > tw and ncols > 1:
        # Shrink the widest column
        excess = total - tw
        widest = col_widths.index(max(col_widths))
        col_widths[widest] = max(4, col_widths[widest] - excess)

    def hline(left, mid, right, fill="─"):
        parts = [left]
        for i, w in enumerate(col_widths):
            parts.append(fill * (w + 2))
            parts.append(mid if i < ncols - 1 else right)
        return "".join(parts)

    def dataline(cells):
        parts = ["│"]
        for i, cell in enumerate(cells):
            padder = _rpad if alignments[i] == "r" else _pad
            # Truncate if needed
            vl = _visible_len(cell)
            if vl > col_widths[i]:
                # Rough truncation — strip ANSI, truncate, re-apply
                import re
                raw = re.sub(r"\033\[[0-9;]*m", "", cell)
                cell = raw[: col_widths[i] - 1] + "…"
            parts.append(" " + padder(cell, col_widths[i]) + " │")
        return "".join(parts)

    print(hline("┌", "┬", "┐"))
    print(dataline([bold(h) for h in headers]))
    print(hline("├", "┼", "┤"))
    for row in rows:
        print(dataline(row))
    print(hline("└", "┴", "┘"))

# ---------------------------------------------------------------------------
# API client
# ---------------------------------------------------------------------------

def api_get(path: str, params: dict | None = None) -> dict | list:
    url = f"{API_URL}{path}"
    try:
        resp = requests.get(url, params=params, timeout=TIMEOUT)
    except requests.ConnectionError:
        print(f"Could not connect to Clank Tank API at {API_URL}", file=sys.stderr)
        print("Is the backend running? Start it with:", file=sys.stderr)
        print(f"  uvicorn hackathon.backend.app:app --port 8000", file=sys.stderr)
        sys.exit(1)
    except requests.Timeout:
        print(f"Request timed out connecting to {API_URL}", file=sys.stderr)
        sys.exit(1)

    if resp.status_code != 200:
        print(f"API error: {resp.status_code} {resp.reason}", file=sys.stderr)
        try:
            detail = resp.json().get("detail", "")
            if detail:
                print(f"  {detail}", file=sys.stderr)
        except Exception:
            pass
        sys.exit(1)

    return resp.json()

# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def output_json(data):
    json.dump(data, sys.stdout, indent=2, default=str)
    print()


def output_csv_rows(headers: list[str], rows: list[list[str]]):
    writer = csv.writer(sys.stdout)
    writer.writerow(headers)
    writer.writerows(rows)

# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_leaderboard(args):
    data = api_get("/api/leaderboard")

    if args.limit:
        data = data[: args.limit]

    if args.json:
        return output_json(data)

    headers = ["Rank", "Project", "Category", "Score", "Community"]

    def make_row(entry):
        rank = entry.get("rank", "")
        trophy = TROPHY.get(rank, "")
        rank_s = f"{trophy} {rank}" if trophy else str(rank)
        return [
            rank_s,
            entry.get("project_name", ""),
            entry.get("category", ""),
            score_color(entry.get("final_score")),
            score_color(entry.get("community_score")),
        ]

    rows = [make_row(e) for e in data]

    if args.csv:
        plain = [[str(e.get("rank", "")), e.get("project_name", ""),
                   e.get("category", ""), str(e.get("final_score", "")),
                   str(e.get("community_score", ""))] for e in data]
        return output_csv_rows(headers, plain)

    print()
    print(bold("  Clank Tank Leaderboard"))
    print()
    draw_table(headers, rows, ["r", "l", "l", "r", "r"])
    print()


def cmd_submissions(args):
    params = {}
    if args.category:
        params["category"] = args.category
    if args.status:
        params["status"] = args.status

    data = api_get("/api/submissions", params=params if params else None)

    if args.json:
        return output_json(data)

    headers = ["ID", "Project", "Category", "Status"]

    def make_row(s):
        return [
            str(s.get("submission_id", "")),
            s.get("project_name", ""),
            s.get("category", ""),
            colored_status(s.get("status", "")),
        ]

    rows = [make_row(s) for s in data]

    if args.csv:
        plain = [[str(s.get("submission_id", "")), s.get("project_name", ""),
                   s.get("category", ""), s.get("status", "")] for s in data]
        return output_csv_rows(headers, plain)

    print()
    print(bold(f"  Submissions ({len(data)})"))
    print()
    draw_table(headers, rows, ["r", "l", "l", "l"])
    print()


def cmd_show(args):
    data = api_get(f"/api/submissions/{args.id}", params={"include": "scores,research,community"})

    if args.json:
        return output_json(data)

    if args.csv:
        # Flat key-value for CSV
        flat = {k: v for k, v in data.items() if not isinstance(v, (dict, list))}
        headers = list(flat.keys())
        return output_csv_rows(headers, [[str(v) for v in flat.values()]])

    sid = data.get("submission_id", "")
    name = data.get("project_name", "")
    category = data.get("category", "")
    status = data.get("status", "")

    # Header box
    tw = min(term_width(), 60)
    inner = tw - 4  # padding inside box

    print()
    print("╔" + "═" * (tw - 2) + "╗")
    title_line = f"  {bold(name)}"
    id_str = f"#{sid}"
    # Compute padding for right-aligned ID
    gap = inner - _visible_len(title_line) - len(id_str)
    print("║" + title_line + " " * max(1, gap) + dim(id_str) + "  ║")
    cat_line = f"  Category: {category}"
    print("║" + cat_line + " " * (inner - len(cat_line)) + "  ║")
    stat_line = f"  Status: {colored_status(status)}"
    stat_pad = inner - _visible_len(stat_line)
    print("║" + stat_line + " " * max(0, stat_pad) + "  ║")
    print("╚" + "═" * (tw - 2) + "╝")

    # Description
    desc = data.get("description", "")
    if desc:
        print()
        print(bold("  Description"))
        print("  " + "─" * 40)
        # Word wrap
        for line in _wrap(desc, tw - 4):
            print(f"  {line}")

    # Links
    github = data.get("github_url", "")
    demo = data.get("demo_video_url", "")
    if github or demo:
        print()
        print(bold("  Links"))
        print("  " + "─" * 40)
        if github:
            print(f"  GitHub:  {cyan(github)}")
        if demo:
            print(f"  Demo:    {cyan(demo)}")

    # Judge Scores
    scores = data.get("scores", [])
    if scores:
        print()
        print(bold("  Judge Scores"))
        print("  " + "─" * 40)

        judge_display = {
            "aimarc": "AI Marc (Visionary VC)",
            "aishaw": "AI Shaw (Code Custodian)",
            "spartan": "Spartan (Token Economist)",
            "peepo": "Peepo (Community Vibes)",
        }

        for s in scores:
            jname = s.get("judge_name", "")
            display = judge_display.get(jname, jname)
            wt = s.get("weighted_total")
            wt_str = score_color(wt) if wt is not None else ""
            print(f"  {bold(display):40s} {wt_str}")

            inn = s.get("innovation", "")
            tech = s.get("technical_execution", "")
            mkt = s.get("market_potential", "")
            ux = s.get("user_experience", "")
            print(dim(f"    Innovation: {inn}  Technical: {tech}  Market: {mkt}  UX: {ux}"))

    # Community
    cscore = data.get("community_score")
    cfeedback = data.get("community_feedback")
    if cscore is not None or cfeedback:
        print()
        print(bold("  Community"))
        print("  " + "─" * 40)
        if cscore is not None:
            print(f"  Score: {score_color(cscore)}")
        if cfeedback:
            total = cfeedback.get("total_votes", 0)
            print(f"  Total votes: {total}")

    print()


def _wrap(text: str, width: int) -> list[str]:
    """Simple word-wrap."""
    lines = []
    for paragraph in text.split("\n"):
        if not paragraph.strip():
            lines.append("")
            continue
        words = paragraph.split()
        current = ""
        for w in words:
            if current and len(current) + 1 + len(w) > width:
                lines.append(current)
                current = w
            else:
                current = f"{current} {w}" if current else w
        if current:
            lines.append(current)
    return lines


def cmd_stats(args):
    data = api_get("/api/stats")

    if args.json:
        return output_json(data)

    if args.csv:
        # Output two sections
        print("# By Status")
        writer = csv.writer(sys.stdout)
        writer.writerow(["status", "count"])
        for k, v in data.get("by_status", {}).items():
            writer.writerow([k, v])
        print()
        print("# By Category")
        writer.writerow(["category", "count"])
        for k, v in data.get("by_category", {}).items():
            writer.writerow([k, v])
        return

    total = data.get("total_submissions", 0)
    by_status = data.get("by_status", {})
    by_category = data.get("by_category", {})

    print()
    print(bold("  Clank Tank Hackathon"))
    print("  " + "═" * 30)
    print(f"  Total Submissions: {bold(str(total))}")
    print()

    # Side-by-side columns
    status_lines = [bold("  By Status")]
    status_lines.append("  " + "─" * 18)
    for s, c in sorted(by_status.items(), key=lambda x: -x[1]):
        status_lines.append(f"  {colored_status(s):20s} {c:>3}")

    cat_lines = [bold("By Category")]
    cat_lines.append("─" * 20)
    for cat, c in sorted(by_category.items(), key=lambda x: -x[1]):
        cat_lines.append(f"{cat:18s} {c:>3}")

    max_lines = max(len(status_lines), len(cat_lines))
    status_lines += [""] * (max_lines - len(status_lines))
    cat_lines += [""] * (max_lines - len(cat_lines))

    col_gap = 6
    for sl, cl in zip(status_lines, cat_lines):
        sl_padded = _pad(sl, 28)
        print(f"{sl_padded}{' ' * col_gap}{cl}")

    print()


def cmd_draft(args):
    """Interactive draft builder — outputs a prefilled submission URL."""
    print()
    print(bold("  Draft a Clank Tank Submission"))
    print("  " + "─" * 40)
    print(dim("  Fill in your project details. A prefilled URL will be generated."))
    print()

    def prompt_required(label: str) -> str:
        while True:
            val = input(f"  {bold(label)}: ").strip()
            if val:
                return val
            print(dim("    (required)"))

    def prompt_optional(label: str) -> str:
        return input(f"  {bold(label)} {dim('(optional)')}: ").strip()

    def prompt_category() -> str:
        print(f"  {bold('Category')}:")
        for i, cat in enumerate(CATEGORIES, 1):
            print(f"    {i}. {cat}")
        while True:
            choice = input("  Choose [1-6]: ").strip()
            try:
                idx = int(choice)
                if 1 <= idx <= len(CATEGORIES):
                    return CATEGORIES[idx - 1]
            except ValueError:
                pass
            print(dim("    Pick a number 1-6"))

    fields = {}
    fields["project_name"] = prompt_required("Project Name")
    fields["category"] = prompt_category()
    fields["description"] = prompt_required("Description")
    fields["github_url"] = prompt_required("GitHub URL")
    fields["demo_video_url"] = prompt_required("Demo Video URL")

    print()
    print(dim("  Optional fields (press Enter to skip):"))
    fields["discord_handle"] = prompt_optional("Discord Handle")
    fields["twitter_handle"] = prompt_optional("Twitter Handle")
    fields["problem_solved"] = prompt_optional("Problem Solved")
    fields["favorite_part"] = prompt_optional("Favorite Part")
    fields["solana_address"] = prompt_optional("Solana Address")

    # Remove empty optional fields
    fields = {k: v for k, v in fields.items() if v}

    draft_json = json.dumps(fields)
    encoded = urllib.parse.quote(draft_json)
    url = f"{WEB_URL}/?draft={encoded}"

    print()
    print(bold("  Your prefilled submission URL:"))
    print()
    print(f"  {cyan(url)}")
    print()

    try:
        open_it = input("  Open in browser? [Y/n] ").strip().lower()
        if open_it in ("", "y", "yes"):
            webbrowser.open(url)
            print(dim("  Opened! Review the form and hit Submit in your browser."))
    except (EOFError, KeyboardInterrupt):
        pass

    print()

# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        prog="clanktank",
        description="Clank Tank CLI — browse hackathon data and draft submissions.",
    )
    sub = parser.add_subparsers(dest="command")

    # leaderboard
    p_lb = sub.add_parser("leaderboard", aliases=["lb"], help="Ranked leaderboard with scores")
    p_lb.add_argument("--limit", type=int, help="Max entries to show")
    p_lb.add_argument("--json", action="store_true", help="Output raw JSON")
    p_lb.add_argument("--csv", action="store_true", help="Output CSV")

    # submissions
    p_sub = sub.add_parser("submissions", aliases=["subs"], help="Browse all submissions")
    p_sub.add_argument("--category", help="Filter by category")
    p_sub.add_argument("--status", help="Filter by status")
    p_sub.add_argument("--json", action="store_true", help="Output raw JSON")
    p_sub.add_argument("--csv", action="store_true", help="Output CSV")

    # show
    p_show = sub.add_parser("show", help="Submission detail + judge scores")
    p_show.add_argument("id", type=int, help="Submission ID")
    p_show.add_argument("--json", action="store_true", help="Output raw JSON")
    p_show.add_argument("--csv", action="store_true", help="Output CSV")

    # stats
    p_stats = sub.add_parser("stats", help="Hackathon stats")
    p_stats.add_argument("--json", action="store_true", help="Output raw JSON")
    p_stats.add_argument("--csv", action="store_true", help="Output CSV")

    # draft
    sub.add_parser("draft", help="Interactive draft → prefilled submit URL")

    args = parser.parse_args(argv)

    # Default to leaderboard
    cmd = args.command
    if cmd is None:
        cmd = "leaderboard"
        # Re-parse with defaults
        args = parser.parse_args(["leaderboard"] + (argv or []))

    dispatch = {
        "leaderboard": cmd_leaderboard,
        "lb": cmd_leaderboard,
        "submissions": cmd_submissions,
        "subs": cmd_submissions,
        "show": cmd_show,
        "stats": cmd_stats,
        "draft": cmd_draft,
    }

    fn = dispatch.get(cmd)
    if fn:
        try:
            fn(args)
        except KeyboardInterrupt:
            print()
            sys.exit(130)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
