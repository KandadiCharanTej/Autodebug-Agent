"""
Pattern Memory Store — learns from past error→fix patterns.
Stores patterns in a local JSON file and provides similarity matching.
"""
import json
import os
import time
from difflib import SequenceMatcher

PATTERN_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns.json")
MAX_PATTERNS = 100


def _load_patterns() -> list:
    """Load patterns from disk."""
    try:
        if os.path.exists(PATTERN_FILE):
            with open(PATTERN_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError):
        pass
    return []


def _save_patterns(patterns: list):
    """Persist patterns to disk."""
    try:
        with open(PATTERN_FILE, "w", encoding="utf-8") as f:
            json.dump(patterns, f, indent=2, ensure_ascii=False)
    except IOError:
        pass


def save_pattern(error_type: str, cause: str, fix_explanation: str, updated_code: str, language: str):
    """Save a successful error→fix pattern."""
    patterns = _load_patterns()

    entry = {
        "error_type": error_type,
        "cause": cause,
        "fix_explanation": fix_explanation,
        "updated_code": updated_code[:500],  # Cap stored code size
        "language": language,
        "timestamp": time.time(),
    }

    # Avoid duplicates (same error_type + similar cause)
    for p in patterns:
        if p["error_type"] == error_type and _similarity(p["cause"], cause) > 0.85:
            return  # Already stored a very similar pattern

    patterns.insert(0, entry)

    # FIFO cap
    if len(patterns) > MAX_PATTERNS:
        patterns = patterns[:MAX_PATTERNS]

    _save_patterns(patterns)


def find_similar(error_type: str, cause: str) -> dict | None:
    """Find a similar past pattern. Returns the best match or None."""
    patterns = _load_patterns()
    if not patterns:
        return None

    best_match = None
    best_score = 0

    for p in patterns:
        # Exact error_type match gets a boost
        type_score = 0.4 if p["error_type"].lower() == error_type.lower() else 0
        cause_score = _similarity(p.get("cause", ""), cause) * 0.6

        total = type_score + cause_score

        if total > best_score and total >= 0.5:
            best_score = total
            best_match = p

    if best_match:
        return {
            "error_type": best_match["error_type"],
            "cause": best_match["cause"],
            "fix_explanation": best_match["fix_explanation"],
            "language": best_match["language"],
            "similarity": round(best_score * 100),
        }
    return None


def get_pattern_count() -> int:
    """Return total number of stored patterns."""
    return len(_load_patterns())


def _similarity(a: str, b: str) -> float:
    """Compute string similarity ratio (0.0 to 1.0)."""
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()
