"""
Judge personality definitions for Clank Tank Hackathon Edition.
Each judge has their unique perspective and evaluation style.

All gameable content (personas, weights, criteria, score scale, scoring task,
round2 template) is loaded from the JUDGE_CONFIG environment variable (JSON).
"""

import os
import json
import logging
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
logger = logging.getLogger(__name__)


def _load_judge_config():
    """Load judge configuration from JUDGE_CONFIG env var (JSON-encoded)."""
    raw = os.getenv("JUDGE_CONFIG", "")
    if not raw:
        logger.warning("JUDGE_CONFIG env var not set – judge prompts will be empty")
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse JUDGE_CONFIG JSON: %s", e)
        return {}


_CONFIG = _load_judge_config()

JUDGE_PERSONAS = _CONFIG.get("personas", {})
JUDGE_WEIGHTS = _CONFIG.get("weights", {})
SCORING_CRITERIA = _CONFIG.get("criteria", {})


def get_judge_persona(judge_name):
    """Get the personality description for a judge."""
    return JUDGE_PERSONAS.get(judge_name.lower(), '')


def get_judge_weights(judge_name):
    """Get the scoring weights for a judge."""
    return JUDGE_WEIGHTS.get(judge_name.lower(), {})


def get_score_scale():
    """Get the score scale anchors string."""
    return _CONFIG.get("score_scale", "")


def get_scoring_task():
    """Get the scoring task instructions string."""
    return _CONFIG.get("scoring_task", "")


def get_round2_template():
    """Get the Round 2 synthesis prompt template string."""
    return _CONFIG.get("round2_template", "")
