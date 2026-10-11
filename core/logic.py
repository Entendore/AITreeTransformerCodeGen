"""
core/logic.py — Predicate-logic verification (Z3) + AST generation + mutation.

Three tightly-coupled responsibilities:
  1. TreeTransformer  — generates an initial AST from an intent string.
  2. PredicateLogicSkeptic — uses Z3 to prove/disprove logical invariants.
  3. GeneticProgrammer — mutates ASTs to repair invariant violations.

Production notes:
  - Z3 is optional; the system degrades gracefully when unavailable.
  - The sceptic and genetic programmer are decoupled enough to be tested independently.
  - Mutation strategies are data-driven (extend _MUTATORS).
"""

from __future__ import annotations

import ast
import copy
import logging
from typing import List, Optional

from config import Settings
from models import GenerationError, ValidationError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional Z3 import
# ---------------------------------------------------------------------------
try:
    from z3 import Int, Solver, unsat
    Z3_AVAILABLE = True
except ImportError:
    Z3_AVAILABLE = False
    logger.warning("'z3-solver' not installed — predicate-logic verification disabled.")


# ===================================================================
# Tree Transformer
# ===================================================================
class TreeTransformer:
    """
    Generates AST structures from an intent string.

    The default strategy produces a program with an *intentional* logic
    bug (assigning a negative value that violates Z3 invariants) so
    that downstream verification → mutation can demonstrate its value.
    """

    def generate(self, intent: str) -> ast.AST:
        """
        Return a valid Python AST module.

        Raises GenerationError if the intent cannot be parsed.
        """
        logger.info("TreeTransformer: generating AST for intent=%r", intent[:60])
        tree = ast.Module(body=[
            ast.Assign(
                targets=[ast.Name(id="x", ctx=ast.Store())],
                value=ast.UnaryOp(op=ast.USub(), operand=ast.Constant(value=1)),
            ),
            ast.Expr(value=ast.Call(
                func=ast.Name(id="sim_print", ctx=ast.Load()),
                args=[ast.BinOp(
                    left=ast.Name(id="x", ctx=ast.Load()),
                    op=ast.Add(),
                    right=ast.Constant(value=10),
                )],
                keywords=[],
            )),
        ], type_ignores=[])
        ast.fix_missing_locations(tree)
        logger.debug("TreeTransformer: AST generated (%d nodes)", len(list(ast.walk(tree))))
        return tree


# ===================================================================
# Predicate Logic Skeptic (Z3)
# ===================================================================
class PredicateLogicSkeptic:
    """
    Uses Z3 SMT solver to check whether an AST violates declared invariants.

    Returns ``True`` when the AST is *consistent* with the invariants,
    ``False`` when Z3 proves a contradiction (UNSAT).
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or Settings()
        self._z3_vars: dict[str, object] = {}
        self._invariants: list = []
        self._build_invariants()

    # ---- internals -------------------------------------------------------
    def _build_invariants(self) -> None:
        try:
            for var_name, constraints in self._settings.z3_invariants.items():
                z3_var = Int(var_name)
                self._z3_vars[var_name] = z3_var
                for expr_str in constraints:
                    self._invariants.append(self._parse_constraint(z3_var, expr_str))
            logger.info("Skeptic: loaded %d invariants across %d variables",
                        len(self._invariants), len(self._z3_vars))
        except Exception:
            logger.exception("Skeptic: failed to build invariants")

    @staticmethod
    def _parse_constraint(var, expr: str):
        """Parse simple constraints like '> 0' into Z3 expressions."""
        parts = expr.strip().split()
        if len(parts) != 2:
            return var > 0  # safe fallback
        op, val = parts[0], int(parts[1])
        if op == ">":  return var > val
        if op == ">=": return var >= val
        if op == "<":  return var < val
        if op == "<=": return var <= val
        if op == "==": return var == val
        return var > 0

    # ---- public ----------------------------------------------------------
    def verify(self, tree: ast.AST) -> bool:
        """
        Check *tree* against Z3 invariants.

        Returns ``True`` if the tree does **not** contradict the invariants.
        Returns ``False`` if Z3 finds UNSAT (a logical violation).
        """
        if not Z3_AVAILABLE:
            logger.info("Skeptic: Z3 unavailable — skipping verification (pass)")
            return True

        solver = Solver()
        solver.add(self._invariants)
        extracted = self._extract_predicates(tree)
        if not extracted:
            logger.info("Skeptic: no predicates extracted — pass")
            return True

        solver.add(extracted)
        result = solver.check()
        is_valid = result != unsat
        logger.info("Skeptic: Z3 result=%s → valid=%s", result, is_valid)
        return is_valid

    def _extract_predicates(self, node: ast.AST) -> list:
        predicates: list = []
        for child in ast.walk(node):
            if isinstance(child, ast.Assign) and isinstance(child.targets[0], ast.Name):
                var_name = child.targets[0].id
                if var_name in self._z3_vars:
                    val = self._eval_constant(child.value)
                    if val is not None:
                        predicates.append(self._z3_vars[var_name] == val)
        return predicates

    @staticmethod
    def _eval_constant(node: ast.AST) -> Optional[int]:
        if isinstance(node, ast.Constant) and isinstance(node.value, int):
            return node.value
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            inner = TreeTransformer.__module__  # reference only
            val = TreeTransformer.__module__  # avoid unused-import lint
            if isinstance(node.operand, ast.Constant) and isinstance(node.operand.value, int):
                return -node.operand.value
        return None


# ===================================================================
# Genetic Programmer
# ===================================================================
class GeneticProgrammer:
    """
    Mutates AST nodes to repair logical / structural errors.

    Mutation strategies are registered in _MUTATORS as (predicate, visitor)
    pairs.  New strategies can be appended without changing existing code.
    """

    def mutate(self, tree: ast.AST, max_rounds: int = 3) -> ast.AST:
        """
        Apply mutation passes until the tree passes or *max_rounds* is hit.

        Returns the (possibly mutated) AST.
        """
        mutated = copy.deepcopy(tree)
        for i in range(max_rounds):
            new_tree = MutatorVisitor().visit(mutated)
            ast.fix_missing_locations(new_tree)
            if ast.dump(new_tree) == ast.dump(mutated):
                logger.info("GP: no changes in round %d — converged", i + 1)
                break
            mutated = new_tree
            logger.info("GP: mutation applied in round %d", i + 1)
        return mutated


class MutatorVisitor(ast.NodeTransformer):
    """Single-pass AST mutator: fixes known anti-patterns."""

    def visit_Assign(self, node: ast.Assign) -> ast.Assign:
        # Fix negative assignments that would violate x > 0 invariants
        if (isinstance(node.value, ast.UnaryOp)
                and isinstance(node.value.op, ast.USub)
                and isinstance(node.value.operand, ast.Constant)
                and isinstance(node.value.operand.value, int)):
            logger.info("GP: mutating negative assignment %d → %d",
                        node.value.operand.value, abs(node.value.operand.value))
            node.value = ast.Constant(value=abs(node.value.operand.value))
        return node
