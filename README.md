# Clank Tank

An AI-powered game show where entrepreneurs pitch to simulated judges. Projects are researched by AI, scored by four judge personas, voted on by the community, then turned into episodes.

<div align="center">
  <a href="https://m3org.com/tv/">Website</a> •
  <a href="https://tally.so/r/3X8EKO">Submit a Pitch</a> •
  <a href="https://www.youtube.com/watch?v=R-oObQtsksw">Watch an Episode</a>
</div>

---

## Two deployments

### Hackathon Edition (primary)

AI judging system for hackathon competitions. Submissions arrive through a web dashboard, get researched, scored by four AI judges, voted on with Solana tokens, then turned into episodes.

→ **[hackathon/README.md](hackathon/README.md)** for the full pipeline and CLI reference

Quick start:
```bash
uv sync
clanktank --help
```

Live dashboard: [m3org.com/tv/hackathon](https://m3org.com/tv/hackathon)

### Main Platform

Full production pipeline: Tally/Typeform → Google Sheets → SQLite → AI research → script generation → PlayCanvas rendering → video recording → YouTube.

```bash
# Import submissions from Google Sheets
python scripts/sheet_processor.py -s "Block Tank Pitch Submission" -o ./data -j --db-file pitches.db

# Research and manage pitches
python scripts/pitch_manager.py --db-file data/pitches.db --list --filter-status submitted
python scripts/pitch_manager.py --db-file data/pitches.db --research <id>

# Record an episode
node scripts/shmotime-recorder.js <episode-url>

# Upload to YouTube
python scripts/upload_to_youtube.py --from-json metadata.json
```

---

## Cast

<div align="center">
  <table>
    <tr>
      <td align="center"><img src="media/cast/aimarc_headshot.png" width="80px"/><br/><b>aimarc</b></td>
      <td align="center"><img src="media/cast/aishaw_headshot.png" width="80px"/><br/><b>aishaw</b></td>
      <td align="center"><img src="media/cast/spartan_headshot.png" width="80px"/><br/><b>spartan</b></td>
      <td align="center"><img src="media/cast/peepo_headshot.png" width="80px"/><br/><b>peepo</b></td>
      <td align="center"><img src="media/cast/elizahost_headshot.png" width="80px"/><br/><b>Eliza (host)</b></td>
    </tr>
  </table>
</div>

---

## Setup

```bash
# Clone and install
git clone https://github.com/m3org/clanktank
cd clanktank
uv sync

# Configure environment
cp .env.example .env
clanktank config        # shows what's missing
clanktank config --setup  # interactive setup
```

Required env vars: `OPENROUTER_API_KEY`, `DISCORD_CLIENT_ID`, `DISCORD_CLIENT_SECRET`, `DISCORD_TOKEN`, `PRIZE_WALLET_ADDRESS`

---

## Tech stack

- **Backend**: Python, FastAPI, SQLite, SQLAlchemy, Pydantic
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS
- **AI**: OpenRouter (judge scoring + research), Anthropic Claude (scripts), Perplexity (research)
- **Integrations**: ElevenLabs (voice), Discord.py (voting), Google APIs (Sheets, YouTube), Solana (voting)
- **Recording**: Puppeteer-based video capture of PlayCanvas-rendered episodes

---

*AI judge decisions are simulated and do not constitute real investment advice.*
