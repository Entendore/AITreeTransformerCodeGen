"""
models.py — Shared enums, exceptions, and data-transfer objects.
Everything the pipeline and GUI agree on lives here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class PipelineState(Enum):
    """Each stage the orchestrator can be in."""
    IDLE = "IDLE"
    PLANNING = "PLANNING"
    DRAFTING = "DRAFTING"
    FOL_VALIDATION = "FOL_VALIDATION"
    GP_MUTATION = "GP_MUTATION"
    EXECUTION = "EXECUTION"
    DONE = "DONE"
    FAILED = "FAILED"


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------
class LeviathanError(Exception):
    """Base for all project exceptions."""

class ValidationError(LeviathanError):
    """Logical invariant violated."""

class InterpretationError(LeviathanError):
    """Runtime error inside the simulated environment."""

class GenerationError(LeviathanError):
    """AST generation / mutation failed."""

class MissingDependencyError(LeviathanError):
    """Optional library (e.g. z3-solver) not installed."""


# ---------------------------------------------------------------------------
# DTOs
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class FuzzyWeights:
    security: float = 0.5
    speed: float = 0.5
    logic_strictness: float = 0.5


@dataclass
class EnvironmentSnapshot:
    variables: Dict[str, Any] = field(default_factory=dict)
    filesystem: Dict[str, Any] = field(default_factory=lambda: {"/": {"app": {}}})
    stdout: List[str] = field(default_factory=list)

    def to_json(self, indent: int = 2) -> str:
        import json
        return json.dumps(
            {"vars": self.variables, "fs": self.filesystem, "stdout": self.stdout},
            indent=indent,
            default=str,
        )


@dataclass(frozen=True)
class PipelineResult:
    state: PipelineState
    message: str
    code: Optional[str] = None
    env_snapshot: Optional[str] = None
    ast_valid: Optional[bool] = None
