"""
core/fuzzy.py — Keyword-driven fuzzy weight extraction.
Analyses a natural-language prompt and returns numerical weights that
control downstream pipeline behaviour.

Production notes:
  - Rules are data-driven (loaded from config.fuzzy_keywords).
  - Easily extensible: add new keywords in config.py.
  - Thread-safe (pure function, no mutable state).
"""

from __future__ import annotations

import logging
from typing import Dict

from config import Settings
from models import FuzzyWeights

logger = logging.getLogger(__name__)


class FuzzyLogicController:
    """Maps prompt text → pipeline control weights."""

    DEFAULT_WEIGHTS: FuzzyWeights = FuzzyWeights()

    def __init__(self, settings: Settings | None = None) -> None:
        self._rules = (settings or Settings()).fuzzy_keywords

    # ---- public ----------------------------------------------------------
    def evaluate(self, prompt: str) -> FuzzyWeights:
        """
        Scan *prompt* for known keywords and build a FuzzyWeights object.

        Returns a FuzzyWeights with all values clamped to [0.0, 1.0].
        """
        tokens = set(prompt.lower().split())
        matched: Dict[str, float] = {}
        for token in tokens:
            if token in self._rules:
                for attr, delta in self._rules[token].items():
                    matched[attr] = max(matched.get(attr, 0.0), delta)
                    logger.debug("Fuzzy: token=%r matched %s=%.1f", token, attr, delta)

        weights = FuzzyWeights(
            security=min(1.0, matched.get("security", self.DEFAULT_WEIGHTS.security)),
            speed=min(1.0, matched.get("speed", self.DEFAULT_WEIGHTS.speed)),
            logic_strictness=min(1.0, matched.get("logic_strictness", self.DEFAULT_WEIGHTS.logic_strictness)),
        )
        logger.info("Fuzzy weights for prompt: %s", weights)
        return weights
