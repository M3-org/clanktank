"""Central config — reads .env, provides consistent defaults, shared helpers."""

import math
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

REPO_ROOT = Path(__file__).resolve().parents[2]

# Database
HACKATHON_DB_PATH = os.getenv("HACKATHON_DB_PATH", str(REPO_ROOT / "data" / "hackathon.db"))

# API Keys (validated at point of use, not import time)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

# AI model configuration
AI_MODEL_PROVIDER = os.getenv("AI_MODEL_PROVIDER", "openrouter")
AI_MODEL_NAME = os.getenv("AI_MODEL_NAME", "")  # required — set AI_MODEL_NAME in .env (e.g. openrouter/auto)
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

# Research configuration
RESEARCH_CACHE_DIR = os.getenv("RESEARCH_CACHE_DIR", ".cache/research")
RESEARCH_CACHE_EXPIRY_HOURS = int(os.getenv("RESEARCH_CACHE_EXPIRY_HOURS", "24"))

# Voting constants
MIN_VOTE_AMOUNT = float(os.getenv("MIN_VOTE_AMOUNT", "1"))
VOTE_WEIGHT_MULTIPLIER = float(os.getenv("VOTE_WEIGHT_MULTIPLIER", "3"))
VOTE_WEIGHT_CAP = float(os.getenv("VOTE_WEIGHT_CAP", "10"))

# Prize/wallet
PRIZE_WALLET_ADDRESS = os.getenv("PRIZE_WALLET_ADDRESS", "")

# Submission window
SUBMISSION_DEADLINE = os.getenv("SUBMISSION_DEADLINE")


@contextmanager
def get_connection(db_path: str | None = None):
    """Shared sqlite3 context manager with consistent timeout and Row factory."""
    conn = sqlite3.connect(db_path or HACKATHON_DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def calculate_vote_weight(total_tokens_sent: float) -> float:
    """Vote weight using logarithmic formula from voting spec."""
    if total_tokens_sent < MIN_VOTE_AMOUNT:
        return 0
    return min(math.log10(total_tokens_sent + 1) * VOTE_WEIGHT_MULTIPLIER, VOTE_WEIGHT_CAP)
