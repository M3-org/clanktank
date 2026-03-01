"""Central config — reads .env, provides consistent defaults, shared helpers."""

import json
import logging
import math
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]


def load_json_config(env_key: str, default_filename: str) -> dict:
    """Load a JSON config from file path or inline JSON, with fallback to default file.

    Resolution order:
    1. Env var contains '/' or ends with '.json' → treat as file path, load file
    2. Env var set with other content → parse as inline JSON (backward compat)
    3. Env var empty → try default file path ``data/{default_filename}``
    4. Nothing found → warn, return ``{}``
    """
    raw = os.getenv(env_key, "")

    if raw:
        # File path detection
        if "/" in raw or raw.endswith(".json"):
            path = Path(raw) if Path(raw).is_absolute() else REPO_ROOT / raw
            try:
                return json.loads(path.read_text())
            except FileNotFoundError:
                logger.error("%s points to missing file: %s", env_key, path)
                return {}
            except json.JSONDecodeError as e:
                logger.error("Failed to parse JSON from %s: %s", path, e)
                return {}
        # Inline JSON (backward compat)
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse %s as inline JSON: %s", env_key, e)
            return {}

    # Fallback: default file in data/
    default_path = REPO_ROOT / "data" / default_filename
    if default_path.exists():
        try:
            return json.loads(default_path.read_text())
        except json.JSONDecodeError as e:
            logger.error("Failed to parse default config %s: %s", default_path, e)
            return {}

    logger.warning("%s not set and %s not found — returning empty config", env_key, default_path)
    return {}


def resolve_config_path(env_key: str, default_filename: str) -> Path:
    """Resolve the file path for a JSON config (for edit command).

    Returns the path that load_json_config would read from, or the default
    file path if the env var points to inline JSON or is unset.
    """
    raw = os.getenv(env_key, "")
    if raw and ("/" in raw or raw.endswith(".json")):
        return Path(raw) if Path(raw).is_absolute() else REPO_ROOT / raw
    return REPO_ROOT / "data" / default_filename

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
