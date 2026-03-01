# Clank Tank Hackathon

AI-powered hackathon judging system. Submissions come in through the web dashboard, get researched by AI, scored by four judge personas, voted on by the community, then turned into episodes.

## Quick start

```bash
clanktank --help   # see all commands in pipeline order
```

---

## Pipeline

```
db → serve → research → score → votes → synthesize → leaderboard → episode → upload
```

### Step 1 — Database setup

```bash
clanktank db create            # first time only
clanktank db migrate --dry-run # check what would change
clanktank db migrate           # apply migrations
```

### Step 2 — Start the server

```bash
clanktank serve                          # dev (localhost:8000)
clanktank serve --host 0.0.0.0 --port 8000  # expose to network
```

Frontend in a separate terminal:
```bash
cd hackathon/frontend
npm install && npm run dev     # proxies /api → localhost:8000
```

Submissions arrive via the web form and are stored in `data/hackathon.db`.

### Step 3 — Research

Runs GitHub analysis (via GitIngest) + AI market/technical research for each submission.

```bash
clanktank research --submission-id <id> --version v2
clanktank research --all --version v2        # all pending
clanktank research --all --force --version v2  # re-run even if cached
```

### Step 4 — Score (Round 1)

Four AI judges score each submission on Innovation, Technical Execution, Market Potential, and UX (0–10 each, personality-weighted).

```bash
clanktank score --submission-id <id> --version v2
clanktank score --all --version v2
```

**Judges:** aimarc (visionary VC), aishaw (code custodian), spartan (token economist), peepo (community vibes)

### Step 5 — Community votes

Collect on-chain Solana votes (ai16z tokens) from the prize wallet.

```bash
clanktank votes --collect          # pull new transactions
clanktank votes --scores           # compute weighted vote scores
clanktank votes --stats            # show vote summary
```

### Step 6 — Synthesize (Round 2)

Combines Round 1 AI scores with community vote data into a final verdict (+2.0 max community bonus).

```bash
clanktank synthesize --submission-id <id> --version v2
clanktank synthesize --all --version v2
```

### Step 7 — Leaderboard

```bash
clanktank leaderboard --version v2
clanktank leaderboard --version v2 --output results.json
```

Or hit the API: `GET /api/leaderboard`

### Step 8 — Generate episodes

Creates judge dialogue scripts for PlayCanvas rendering.

```bash
clanktank episode --submission-id <id> --version v2
clanktank episode --submission-id <id> --validate-only --episode-file <path>  # validate existing file
```

### Step 9 — Upload to YouTube

```bash
clanktank upload --submission-id <id>
clanktank upload --all --dry-run   # preview what would upload
```

---

## Utilities

```bash
clanktank static-data     # regenerate /public/data/ JSON for static frontend
```

---

## Schema changes

The schema in `backend/submission_schema.json` is the single source of truth.

```bash
clanktank db migrate           # apply schema changes to DB
python -m hackathon.backend.sync_schema_to_frontend  # regenerate TS types
# or: cd hackathon/frontend && npm run sync-schema
```

---

## Development

```bash
ruff check hackathon/          # lint
ruff format hackathon/         # format
uv run pytest hackathon/tests/        # Python unit + integration tests
bash hackathon/tests/test_cli.sh      # CLI integration tests (89 checks)
```

### Environment variables (`.env` at repo root)

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENROUTER_API_KEY` | ✅ | AI research + judge scoring |
| `DISCORD_CLIENT_ID` | ✅ | Discord OAuth |
| `DISCORD_CLIENT_SECRET` | ✅ | Discord OAuth |
| `DISCORD_TOKEN` | ✅ | Discord bot (community voting) |
| `PRIZE_WALLET_ADDRESS` | ✅ | Solana wallet to watch for votes |
| `HACKATHON_DB_PATH` | optional | Default: `data/hackathon.db` |
| `GITHUB_TOKEN` | optional | Higher GitHub API rate limits |
| `SUBMISSION_DEADLINE` | optional | ISO datetime to close submissions |
| `VITE_PRIZE_WALLET_ADDRESS` | optional | Exposes wallet to frontend |

---

## Architecture

```
hackathon/
├── backend/
│   ├── app.py               # FastAPI composition root (~263 lines)
│   ├── config.py            # All env vars + DB helper + vote weight
│   ├── http_client.py       # Shared requests session (retry/timeout)
│   ├── models.py            # Pydantic models
│   ├── routes/
│   │   ├── auth.py          # Discord OAuth routes
│   │   ├── submissions.py   # Submission CRUD, leaderboard, stats
│   │   └── voting.py        # Prize pool, webhooks, WebSocket
│   ├── hackathon_manager.py # AI judge scoring + synthesis
│   ├── research.py          # GitHub + AI research pipeline
│   ├── github_analyzer.py   # GitIngest integration
│   └── schema.py            # Versioned schema helpers
├── scripts/
│   ├── generate_episode.py
│   ├── generate_static_data.py
│   ├── collect_votes.py
│   ├── upload_youtube.py
│   └── ...
├── bots/
│   └── discord_bot.py       # Community voting via Discord reactions
├── prompts/
│   ├── judge_personas.py    # aimarc, aishaw, spartan, peepo
│   └── show_config.py       # Episode format + dialogue structure
├── frontend/               # React + TypeScript + Vite
└── tests/
```

**Status flow:** `submitted → researched → scored → community-voting → completed → published`
