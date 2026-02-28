#!/usr/bin/env bash
# hackathon/tests/test_cli.sh
#
# Integration tests for the clanktank CLI.
# Exercises every subcommand and meaningful flag combination.
# Does NOT call external APIs or mutate the production database.
#
# Usage:
#   bash hackathon/tests/test_cli.sh
#
# Prerequisites:
#   - Run from the repo root directory
#   - data/hackathon.db must exist with data
#   - jq must be installed (for JSON validation tests)
#   - Full deps are NOT required; tests that need them are auto-skipped

set -uo pipefail

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PASS=0
FAIL=0
SKIP=0

GREEN='\033[32m'
RED='\033[31m'
YELLOW='\033[33m'
DIM='\033[2m'
RESET='\033[0m'

CT="uv run clanktank"

check() {
    local desc="$1" expected="$2"; shift 2
    local output actual
    output=$("$@" 2>&1); actual=$?
    if [ "$actual" -eq "$expected" ]; then
        echo -e "${GREEN}PASS${RESET}  $desc"
        ((PASS++))
    else
        echo -e "${RED}FAIL${RESET}  $desc ${DIM}(expected exit $expected, got $actual)${RESET}"
        echo "$output" | head -3 | sed 's/^/      /'
        ((FAIL++))
    fi
}

check_contains() {
    local desc="$1" pattern="$2"; shift 2
    local output
    output=$("$@" 2>&1); true
    if echo "$output" | grep -q "$pattern"; then
        echo -e "${GREEN}PASS${RESET}  $desc"
        ((PASS++))
    else
        echo -e "${RED}FAIL${RESET}  $desc ${DIM}(pattern '$pattern' not found)${RESET}"
        echo "$output" | head -3 | sed 's/^/      /'
        ((FAIL++))
    fi
}

check_json() {
    local desc="$1"; shift
    local output
    output=$("$@" 2>&1) || true
    if echo "$output" | jq empty 2>/dev/null; then
        echo -e "${GREEN}PASS${RESET}  $desc"
        ((PASS++))
    else
        echo -e "${RED}FAIL${RESET}  $desc ${DIM}(invalid JSON)${RESET}"
        echo "$output" | head -3 | sed 's/^/      /'
        ((FAIL++))
    fi
}

check_json_value() {
    local desc="$1" jq_filter="$2" expected_value="$3"; shift 3
    local output actual_value
    output=$("$@" 2>&1) || true
    actual_value=$(echo "$output" | jq -r "$jq_filter" 2>/dev/null) || actual_value=""
    if [ "$actual_value" = "$expected_value" ]; then
        echo -e "${GREEN}PASS${RESET}  $desc"
        ((PASS++))
    else
        echo -e "${RED}FAIL${RESET}  $desc ${DIM}(expected '$expected_value', got '$actual_value')${RESET}"
        ((FAIL++))
    fi
}

skip() {
    echo -e "${YELLOW}SKIP${RESET}  $1 ${DIM}($2)${RESET}"
    ((SKIP++))
}

# ---------------------------------------------------------------------------
# Environment detection
# ---------------------------------------------------------------------------

echo ""
echo "=== Clank Tank CLI Integration Tests ==="
echo ""

# Verify we're in the repo root
if [ ! -f "hackathon/__main__.py" ]; then
    echo "ERROR: Run this script from the repo root directory."
    exit 1
fi

# Check for jq
HAS_JQ=false
if command -v jq &>/dev/null; then
    HAS_JQ=true
fi

# Check whether full deps (requests, aiohttp, etc.) are importable.
# Module-dispatching commands (leaderboard, votes, static-data, episode, upload)
# require these; they are skipped if missing to keep the test portable.
HAS_FULL_DEPS=false
if uv run python -c "import requests, aiohttp" 2>/dev/null; then
    HAS_FULL_DEPS=true
fi

echo "  jq available:   $HAS_JQ"
echo "  full deps:      $HAS_FULL_DEPS"
echo ""

# ---------------------------------------------------------------------------
# 1. Top-level
# ---------------------------------------------------------------------------
echo "--- top-level ---"

check      "help flag"                  0  $CT --help
check      "no command → help + exit 1" 1  $CT
check      "nonexistent command → exit 2" 2  $CT nonexistent

check_contains "help lists 'research'"  "research"  $CT --help
check_contains "help lists 'submissions'" "submissions" $CT --help

# ---------------------------------------------------------------------------
# 2. config (self-contained in __main__.py)
# ---------------------------------------------------------------------------
echo ""
echo "--- config ---"

check          "config exits 0"         0  $CT config
check          "config --help"          0  $CT config --help
check_contains "config shows OPENROUTER" "OPENROUTER" $CT config
check_contains "config shows .env path"  ".env"       $CT config
# --setup is interactive; skipped

# ---------------------------------------------------------------------------
# 3. db subcommands
# ---------------------------------------------------------------------------
echo ""
echo "--- db ---"

check          "db (no subcommand) → exit 1" 1  $CT db
check          "db --help"                   0  $CT db --help
check          "db create --help"            0  $CT db create --help
check          "db migrate --help"           0  $CT db migrate --help

check          "db migrate --dry-run"                        0  $CT db migrate --dry-run
check          "db migrate --dry-run --version v2"           0  $CT db migrate --dry-run --version v2
check          "db migrate --dry-run --version v1"           0  $CT db migrate --dry-run --version v1
check          "db migrate --dry-run --version all"          0  $CT db migrate --dry-run --version all
check_contains "db migrate --dry-run mentions table"  "Checking table"  $CT db migrate --dry-run

# ---------------------------------------------------------------------------
# 4. serve (help only — process is long-running)
# ---------------------------------------------------------------------------
echo ""
echo "--- serve ---"

check          "serve --help"             0  $CT serve --help
check_contains "serve --help shows --host" "host"  $CT serve --help
check_contains "serve --help shows --port" "port"  $CT serve --help

# ---------------------------------------------------------------------------
# 5. Pipeline commands (--help only; real runs need external APIs)
# ---------------------------------------------------------------------------
echo ""
echo "--- pipeline (help only) ---"

check "research --help"   0  $CT research --help
check "score --help"      0  $CT score --help
check "synthesize --help" 0  $CT synthesize --help
check "upload --help"     0  $CT upload --help
check "episode --help"    0  $CT episode --help

# ---------------------------------------------------------------------------
# 6. votes
# ---------------------------------------------------------------------------
echo ""
echo "--- votes ---"

check "votes --help" 0  $CT votes --help

if $HAS_FULL_DEPS; then
    check          "votes --stats"  0  $CT votes --stats
    check          "votes --scores" 0  $CT votes --scores
    check          "votes --test"   0  $CT votes --test
else
    skip "votes --stats"  "aiohttp not installed"
    skip "votes --scores" "aiohttp not installed"
    skip "votes --test"   "aiohttp not installed"
fi

# --collect skipped (writes to DB + Solana RPC)

# ---------------------------------------------------------------------------
# 7. leaderboard
# ---------------------------------------------------------------------------
echo ""
echo "--- leaderboard ---"

check          "leaderboard --help"                          0  $CT leaderboard --help
check_contains "leaderboard --help shows version choices"  "v1"  $CT leaderboard --help

if $HAS_FULL_DEPS; then
    check          "leaderboard (default)"            0  $CT leaderboard
    check          "leaderboard --version v2"         0  $CT leaderboard --version v2
    check          "leaderboard --version v1"         0  $CT leaderboard --version v1
    check          "leaderboard --round 1"            0  $CT leaderboard --round 1
    check          "leaderboard --round 2"            0  $CT leaderboard --round 2
    check          "leaderboard --version v2 --round 1" 0 $CT leaderboard --version v2 --round 1
else
    skip "leaderboard"                   "requests not installed"
    skip "leaderboard --version v2"      "requests not installed"
    skip "leaderboard --version v1"      "requests not installed"
    skip "leaderboard --round 1"         "requests not installed"
    skip "leaderboard --round 2"         "requests not installed"
    skip "leaderboard --version v2 --round 1" "requests not installed"
fi

# ---------------------------------------------------------------------------
# 8. stats (self-contained in __main__.py)
# ---------------------------------------------------------------------------
echo ""
echo "--- stats ---"

check          "stats exits 0"                0  $CT stats
check_contains "stats shows 'submissions'"  "submissions" $CT stats
check_contains "stats shows status breakdown" "completed"   $CT stats
check_contains "stats shows Scores section"   "Scores"      $CT stats

# ---------------------------------------------------------------------------
# 9. submissions (self-contained in __main__.py)
# ---------------------------------------------------------------------------
echo ""
echo "--- submissions ---"

# List mode
check          "submissions (list all)"     0  $CT submissions
check          "submissions --help"         0  $CT submissions --help
check_contains "submissions shows ID header"      "ID"      $CT submissions
check_contains "submissions shows Project header" "Project" $CT submissions

# Status filter
check          "submissions --status completed"       0  $CT submissions --status completed
check          "submissions --status submitted"       0  $CT submissions --status submitted
check          "submissions --status researched"      0  $CT submissions --status researched
check          "submissions --status scored"          0  $CT submissions --status scored
check          "submissions --status community-voting" 0 $CT submissions --status community-voting
check          "submissions --status published"       0  $CT submissions --status published
check          "submissions --status invalid → exit 2" 2 $CT submissions --status invalid

check_contains "submissions --status completed shows rows" "completed" $CT submissions --status completed
check_contains "submissions --status submitted shows empty" "No submissions found" $CT submissions --status submitted

# JSON list mode
check      "submissions -j exits 0"   0  $CT submissions -j
check      "submissions -j --status completed" 0  $CT submissions -j --status completed

# Search mode
check          "submissions -s DeFi"          0  $CT submissions -s "DeFi"
check          "submissions -s gaming"         0  $CT submissions -s "gaming"
check_contains "submissions -s DeFi finds Otaku" "Otaku"        $CT submissions -s "DeFi"
check_contains "submissions -s zzznomatch empty" "No submissions found" $CT submissions -s "zzznomatch"
check          "submissions -s DeFi -j"        0  $CT submissions -s "DeFi" -j
check          "submissions -s DeFi --status completed" 0 $CT submissions -s "DeFi" --status completed

# Detail mode
check          "submissions 1 (detail)"       0  $CT submissions 1
check          "submissions 10 (Otaku)"       0  $CT submissions 10
check          "submissions 10 -b (brief)"    0  $CT submissions 10 -b
check          "submissions 10 -j"            0  $CT submissions 10 -j
check          "submissions 10 -j -b"         0  $CT submissions 10 -j -b
check          "submissions 9999 not found → exit 1" 1 $CT submissions 9999

check_contains "submissions 10 shows Otaku"   "Otaku"   $CT submissions 10
check_contains "submissions 1 shows detail"   "#1"      $CT submissions 1
check_contains "submissions 9999 shows error" "not found" $CT submissions 9999

# ---------------------------------------------------------------------------
# 10. JSON output validation (requires jq)
# ---------------------------------------------------------------------------
echo ""
echo "--- JSON validation ---"

if $HAS_JQ; then
    check_json "submissions -j is valid JSON"    $CT submissions -j
    check_json "submissions 10 -j is valid JSON" $CT submissions 10 -j
    check_json "submissions 10 -j -b is valid JSON" $CT submissions 10 -j -b
    check_json "submissions -s DeFi -j is valid JSON" $CT submissions -s "DeFi" -j

    check_json_value "submissions 10 -j has submission_id=10" ".submission_id" "10" $CT submissions 10 -j
    check_json_value "submissions 10 -j -b has submission_id=10" ".submission_id" "10" $CT submissions 10 -j -b

    # Array checks
    _len=$(uv run clanktank submissions -j 2>/dev/null | jq 'length')
    if [ "${_len:-0}" -ge 1 ]; then
        echo -e "${GREEN}PASS${RESET}  submissions -j | jq 'length' >= 1  (got $_len)"
        ((PASS++))
    else
        echo -e "${RED}FAIL${RESET}  submissions -j should return array with length >= 1"
        ((FAIL++))
    fi

    # Brief mode should NOT include scores or research keys
    _has_scores=$(uv run clanktank submissions 10 -j -b 2>/dev/null | jq 'has("scores")')
    if [ "$_has_scores" = "false" ]; then
        echo -e "${GREEN}PASS${RESET}  submissions 10 -j -b omits scores key"
        ((PASS++))
    else
        echo -e "${RED}FAIL${RESET}  submissions 10 -j -b should omit scores key"
        ((FAIL++))
    fi

    # Full JSON should include scores
    _has_scores_full=$(uv run clanktank submissions 10 -j 2>/dev/null | jq 'has("scores")')
    if [ "$_has_scores_full" = "true" ]; then
        echo -e "${GREEN}PASS${RESET}  submissions 10 -j includes scores key"
        ((PASS++))
    else
        echo -e "${RED}FAIL${RESET}  submissions 10 -j should include scores key"
        ((FAIL++))
    fi
else
    skip "JSON validation suite" "jq not installed"
fi

# ---------------------------------------------------------------------------
# 11. episode
# ---------------------------------------------------------------------------
echo ""
echo "--- episode ---"

check "episode --help" 0  $CT episode --help
check_contains "episode --help shows --validate-only" "validate-only" $CT episode --help
check_contains "episode --help shows --episode-file"  "episode-file"  $CT episode --help

if $HAS_FULL_DEPS; then
    # --validate-only with no file exits non-zero (missing required context)
    check "episode --validate-only (no file) → non-zero" 1  $CT episode --validate-only
else
    skip "episode --validate-only" "deps not installed"
fi

# ---------------------------------------------------------------------------
# 12. static-data
# ---------------------------------------------------------------------------
echo ""
echo "--- static-data ---"

if $HAS_FULL_DEPS; then
    check "static-data exits 0" 0  $CT static-data
else
    skip "static-data" "dotenv not installed"
fi

# ---------------------------------------------------------------------------
# 13. recovery
# ---------------------------------------------------------------------------
echo ""
echo "--- recovery ---"

check          "recovery --help"  0  $CT recovery --help
check          "recovery --list"  0  $CT recovery --list
check_contains "recovery --list shows backup info" "backup" $CT recovery --list

# --restore and --validate skipped (write to DB / need specific file path)

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
echo ""
echo "========================================="
total=$((PASS + FAIL + SKIP))
echo "Results: ${GREEN}$PASS passed${RESET}, ${RED}$FAIL failed${RESET}, ${YELLOW}$SKIP skipped${RESET}  ($total total)"
echo ""

if [ "$FAIL" -eq 0 ]; then
    echo -e "${GREEN}All tests passed.${RESET}"
    exit 0
else
    echo -e "${RED}$FAIL test(s) failed.${RESET}"
    exit 1
fi
