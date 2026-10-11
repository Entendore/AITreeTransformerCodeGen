"""
pipeline.py — State-machine orchestrator + QThread worker.

The orchestrator sequences the full pipeline:
  PLANNING → DRAFTING → FOL_VALIDATION → GP_MUTATION → EXECUTION → DONE / FAILED

The worker runs entirely in a QThread so the GUI stays responsive.
Communication back to the GUI uses Qt Signals.
"""

from __future__ import annotations

import ast
import logging
from typing import Optional

from PySide6.QtCore import QObject, Signal

from config import Settings
from core.fuzzy import FuzzyLogicController
from core.interpreter import EnvironmentInterpreter, SimulatedEnvironment
from core.logic import GeneticProgrammer, PredicateLogicSkeptic, TreeTransformer
from core.mamba import MambaContextEngine
from models import FuzzyWeights, PipelineResult, PipelineState

logger = logging.getLogger(__name__)


# ===================================================================
# Qt signals for thread-safe GUI updates
# ===================================================================
class PipelineSignals(QObject):
    """Emitted by the worker thread, consumed by the main window."""

    state_changed = Signal(PipelineState, str)       # (state, message)
    ast_generated = Signal(object)                     # ast.AST
    code_generated = Signal(str)                       # Python source
    env_updated = Signal(str)                          # JSON snapshot
    error_highlight = Signal(object)                  # ast.AST node (or None)
    finished = Signal(PipelineResult)                 # final result


# ===================================================================
# QThread worker
# ===================================================================
class PipelineWorker(QObject):
    """
    Runs the Leviathan pipeline in a background thread.

    Instantiate, connect signals, then call ``start(prompt)``.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        super().__init__()
        self._settings = settings or Settings()
        self.signals = PipelineSignals()

        # Sub-systems (stateless — safe to share across invocations)
        self._fuzzy = FuzzyLogicController(self._settings)
        self._mamba = MambaContextEngine()
        self._tree_gen = TreeTransformer()
        self._gp = GeneticProgrammer()
        self._skeptic = PredicateLogicSkeptic(self._settings)

    # ---- entry point -----------------------------------------------------
    def start(self, prompt: str) -> None:
        """Begin pipeline execution for *prompt*."""
        logger.info("Pipeline: starting for prompt=%r", prompt[:60])
        self._emit(PipelineState.PLANNING, "Analysing intent via fuzzy logic …")

        try:
            self._run(prompt)
        except Exception as exc:
            logger.exception("Pipeline: unhandled error")
            self._emit(PipelineState.FAILED, str(exc))
            self.signals.finished.emit(
                PipelineResult(state=PipelineState.FAILED, message=str(exc))
            )

    # ---- internal pipeline -----------------------------------------------
    def _run(self, prompt: str) -> None:
        weights: FuzzyWeights = self._fuzzy.evaluate(prompt)
        self._emit(PipelineState.PLANNING,
                   f"Extracted weights: security={weights.security:.1f}  "
                   f"speed={weights.speed:.1f}  "
                   f"logic_strictness={weights.logic_strictness:.1f}")

        self._mamba.ingest("project_repo")

        # --- Draft ---------------------------------------------------------
        self._emit(PipelineState.DRAFTING, "Tree Transformer assembling AST …")
        current_ast = self._tree_gen.generate(prompt)
        self.signals.ast_generated.emit(current_ast)
        self.signals.code_generated.emit(ast.unparse(current_ast))

        # --- Verify (Z3) ---------------------------------------------------
        ast_valid: Optional[bool] = None
        if weights.logic_strictness > 0.8:
            self._emit(PipelineState.FOL_VALIDATION, "Running Z3 predicate-logic check …")
            ast_valid = self._skeptic.verify(current_ast)

            if not ast_valid:
                self._emit(PipelineState.GP_MUTATION, "UNSAT — logical invariant violated! Triggering GP mutation …")
                current_ast = self._gp.mutate(current_ast)
                self.signals.ast_generated.emit(current_ast)
                self.signals.code_generated.emit(ast.unparse(current_ast))
                ast_valid = self._skeptic.verify(current_ast)
                self._emit(PipelineState.GP_MUTATION,
                            f"Mutation complete — re-verified: {'PASS' if ast_valid else 'STILL FAILING'}")
        else:
            self._emit(PipelineState.FOL_VALIDATION,
                       "Logic strictness below threshold — skipping Z3 verification.")

        # --- Execute ------------------------------------------------------
        self._emit(PipelineState.EXECUTION, "Executing against sandbox environment …")
        env = SimulatedEnvironment()
        interpreter = EnvironmentInterpreter(env)

        try:
            snapshot = interpreter.run(current_ast)
            env_json = snapshot.to_json()
            self.signals.env_updated.emit(env_json)
            self.signals.error_highlight.emit(None)  # clear any error highlights
            self._emit(PipelineState.DONE, "Pipeline completed successfully.")
            self.signals.finished.emit(PipelineResult(
                state=PipelineState.DONE,
                message="Pipeline completed successfully.",
                code=ast.unparse(current_ast),
                env_snapshot=env_json,
                ast_valid=ast_valid,
            ))
        except Exception as exc:
            env_json = env.snapshot().to_json()
            self.signals.env_updated.emit(f"ERROR: {exc}\n\n{env_json}")
            self.signals.error_highlight.emit(interpreter.error_node)
            self._emit(PipelineState.FAILED, f"Execution error: {exc}")
            self.signals.finished.emit(PipelineResult(
                state=PipelineState.FAILED,
                message=str(exc),
                code=ast.unparse(current_ast),
                env_snapshot=env_json,
                ast_valid=ast_valid,
            ))

    # ---- helpers ---------------------------------------------------------
    def _emit(self, state: PipelineState, message: str) -> None:
        logger.info("[%s] %s", state.value, message)
        self.signals.state_changed.emit(state, message)
