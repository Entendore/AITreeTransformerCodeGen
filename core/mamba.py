"""
core/mamba.py — Mamba-style latent context engine.
Provides a thin contextual wrapper around ingested text.

Production notes:
  - Designed as a plug-in interface; swap the body for a real SSM forward pass.
  - Stateless and thread-safe.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class MambaContextEngine:
    """
    Wraps project context into a latent representation.

    In a production system this would hold actual model weights
    and perform selective state-space forward passes.
    """

    def __init__(self) -> None:
        self._context_cache: list[str] = []

    # ---- public ----------------------------------------------------------
    def ingest(self, context: str) -> str:
        """
        Accept a context string and return a latent token.

        The result is cached so duplicate ingestions are no-ops.
        """
        if context in self._context_cache:
            logger.debug("Mamba: cache hit for context=%r", context[:40])
            return f"MAMBA_LATENT({context})"

        self._context_cache.append(context)
        logger.info("Mamba: ingested new context (%d total)", len(self._context_cache))
        return f"MAMBA_LATENT({context})"

    def clear(self) -> None:
        """Purge the context cache."""
        self._context_cache.clear()
        logger.info("Mamba: context cache cleared")
