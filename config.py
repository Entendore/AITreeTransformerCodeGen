"""
config.py — Central configuration for Leviathan.
All tunables, constants, and logging setup live here.
Override via environment variables (see Settings.from_env()).
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
LOG_DIR = PROJECT_ROOT / "logs"

# ---------------------------------------------------------------------------
# Default logging
# ---------------------------------------------------------------------------
def _setup_logging(level: str = "INFO") -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    fmt = "%(asctime)s │ %(levelname)-8s │ %(name)-24s │ %(message)s"
    handlers: list[logging.Handler] = [
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / "leviathan.log", encoding="utf-8"),
    ]
    logging.basicConfig(level=level, format=fmt, handlers=handlers)


# ---------------------------------------------------------------------------
# Dataclass settings (override with LEVIATHAN_<KEY> env vars)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Settings:
    """Immutable application settings."""

    log_level: str = "INFO"
    window_width: int = 1500
    window_height: int = 850
    left_panel_width: int = 440
    canvas_bg: str = "#141419"
    node_brush: str = "#232837"
    node_pen: str = "#508cff"
    error_brush: str = "#8c1414"
    error_pen: str = "#ff3c3c"
    accent_color: str = "#0066cc"
    font_family: str = "Segoe UI"
    font_size: int = 10
    code_font_family: str = "Consolas"
    code_font_size: int = 11
    code_font_size_small: int = 9

    # Z3 invariants: variable name -> (operator_str, threshold)
    z3_invariants: Dict[str, List[str]] = field(default_factory=lambda: {
        "x": ["> 0"],
        "y": ["> 0"],
    })

    # Fuzzy rules: keyword -> weight adjustments
    fuzzy_keywords: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        "strict":  {"logic_strictness": 1.0},
        "prove":   {"logic_strictness": 1.0},
        "formal":  {"logic_strictness": 1.0},
        "secure":  {"security": 0.8},
        "fast":    {"speed": 0.4},
        "slow":    {"speed": 0.8},
        "safe":    {"security": 1.0},
    })

    @classmethod
    def from_env(cls) -> "Settings":
        """Create settings, overriding fields from LEVIATHAN_<KEY> env vars."""
        overrides: dict = {}
        for key, val in os.environ.items():
            if key.startswith("LEVIATHAN_"):
                attr = key[len("LEVIATHAN_"):].lower()
                if hasattr(cls, attr):
                    overrides[attr] = val
        return cls(**overrides)
