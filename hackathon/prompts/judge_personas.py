"""
Judge personality definitions for Clank Tank Hackathon Edition.
Each judge has their unique perspective and evaluation style.

All gameable content (personas, weights, criteria, score scale, scoring task,
round2 template) is loaded from the JUDGE_CONFIG environment variable (JSON)
or from ``data/judge_config.json``.
"""

from hackathon.backend.config import load_json_config

_CONFIG = load_json_config("JUDGE_CONFIG", "judge_config.json")

JUDGE_PERSONAS = _CONFIG.get("personas", {})
JUDGE_WEIGHTS = _CONFIG.get("weights", {})
SCORING_CRITERIA = _CONFIG.get("criteria", {})


def get_judge_persona(judge_name):
    """Get the personality description for a judge."""
    return JUDGE_PERSONAS.get(judge_name.lower(), "")


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
