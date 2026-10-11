"""
core/interpreter.py — Sandbox environment and AST interpreter.

Two components:
  1. SimulatedEnvironment  — a tiny dict-based runtime (vars / fs / stdout).
  2. EnvironmentInterpreter — walks the AST and evaluates it in the sandbox.

Production notes:
  - No use of exec/eval — pure AST walking.
  - The environment is intentionally minimal and auditable.
  - All runtime errors are wrapped in InterpretationError (from models).
"""

from __future__ import annotations

import ast
import logging
from typing import Any, Dict, List, Optional

from models import EnvironmentSnapshot, InterpretationError

logger = logging.getLogger(__name__)


# ===================================================================
# Simulated Environment
# ===================================================================
class SimulatedEnvironment:
    """
    Lightweight sandbox with three isolated namespaces:
      - variables  (name → value)
      - filesystem (nested dict)
      - stdout     (list of printed strings)
    """

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.variables: Dict[str, Any] = {}
        self.filesystem: Dict[str, Any] = {"/": {"app": {}}}
        self.stdout: List[str] = []
        logger.info("Environment: reset")

    def snapshot(self) -> EnvironmentSnapshot:
        return EnvironmentSnapshot(
            variables=dict(self.variables),
            filesystem=self.filesystem,
            stdout=list(self.stdout),
        )


# ===================================================================
# AST Interpreter
# ===================================================================
class EnvironmentInterpreter:
    """
    Walks a Python AST and evaluates it against a SimulatedEnvironment.

    Supported node types:
      - Module, Assign, Expr, Call (sim_print only), BinOp (+ -),
        Constant, Name, UnaryOp (+ -).
    Everything else raises InterpretationError.
    """

    def __init__(self, env: SimulatedEnvironment) -> None:
        self.env = env
        self._error_node: Optional[ast.AST] = None

    @property
    def error_node(self) -> Optional[ast.AST]:
        """The AST node that caused the last error, if any."""
        return self._error_node

    # ---- public ----------------------------------------------------------
    def run(self, tree: ast.AST) -> EnvironmentSnapshot:
        """
        Execute *tree* inside the sandbox. Returns an EnvironmentSnapshot.

        Raises InterpretationError on any runtime fault.
        """
        self._error_node = None
        try:
            self.visit(tree)
        except InterpretationError:
            raise
        except Exception as exc:
            raise InterpretationError(str(exc)) from exc

        snapshot = self.env.snapshot()
        logger.info("Interpreter finished — vars=%s stdout=%s",
                     list(self.env.variables.keys()), self.env.stdout)
        return snapshot

    # ---- AST visitors ----------------------------------------------------
    def visit_Module(self, node: ast.Module) -> None:
        for child in node.body:
            self.visit(child)

    def visit_Assign(self, node: ast.Assign) -> None:
        name = self._target_name(node.targets[0])
        self.env.variables[name] = self._eval(node.value)
        logger.debug("Interpreter: %s = %s", name, self.env.variables[name])

    def visit_Expr(self, node: ast.Expr) -> None:
        if isinstance(node.value, ast.Call):
            self._call(node.value)
        else:
            raise InterpretationError(f"Unsupported Expr: {type(node.value).__name__}")

    # ---- helpers ---------------------------------------------------------
    def _target_name(self, target: ast.AST) -> str:
        if isinstance(target, ast.Name):
            return target.id
        raise InterpretationError(f"Unsupported assignment target: {type(target).__name__}")

    def _eval(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            if node.id in self.env.variables:
                return self.env.variables[node.id]
            self._error_node = node
            raise InterpretationError(f"Undefined variable: {node.id}")
        if isinstance(node, ast.BinOp):
            left = self._eval(node.left)
            right = self._eval(node.right)
            if isinstance(node.op, ast.Add):  return left + right
            if isinstance(node.op, ast.Sub):  return left - right
            if isinstance(node.op, ast.Mult): return left * right
            if isinstance(node.op, ast.Div):  return left / right
            raise InterpretationError(f"Unsupported BinOp: {type(node.op).__name__}")
        if isinstance(node, ast.UnaryOp):
            operand = self._eval(node.operand)
            if isinstance(node.op, ast.UAdd): return +operand
            if isinstance(node.op, ast.USub): return -operand
        self._error_node = node
        raise InterpretationError(f"Unsupported expression: {type(node).__name__}")

    def _call(self, node: ast.Call) -> None:
        name = node.func.id if isinstance(node.func, ast.Name) else None
        if name == "sim_print":
            if not node.args:
                self._error_node = node
                raise InterpretationError("sim_print() requires exactly 1 argument")
            value = self._eval(node.args[0])
            self.env.stdout.append(str(value))
        else:
            self._error_node = node
            raise InterpretationError(f"Unknown function: {name}")
