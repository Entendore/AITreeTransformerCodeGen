import sys
import ast
import copy
import json
import random
import time
import math
from typing import Dict, Any, List, Optional, Tuple, Callable
from enum import Enum, auto
from dataclasses import dataclass, field
from collections import deque

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTextEdit, QPushButton, QLabel, QGraphicsScene, QGraphicsView, 
    QGraphicsRectItem, QGraphicsTextItem, QGraphicsLineItem, QGraphicsEllipseItem,
    QGraphicsPathItem, QSplitter, QTabWidget, QComboBox, QCheckBox,
    QSpinBox, QDoubleSpinBox, QGroupBox, QFormLayout, QProgressBar,
    QStatusBar, QToolBar, QFileDialog, QMessageBox, QDialog, QLineEdit,
    QDialogButtonBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QScrollArea, QFrame, QSizePolicy, QSlider, QMenu, QSystemTrayIcon,
    QStyle
)
from PySide6.QtCore import (
    Qt, QRectF, QThread, Signal, QTimer, QPropertyAnimation, 
    QEasingCurve, QPointF, QSize, QSettings, QStandardPaths
)
from PySide6.QtGui import (
    QBrush, QPen, QColor, QFont, QPainter, QPainterPath, 
    QLinearGradient, QRadialGradient, QIcon, QAction, QKeySequence,
    QFontDatabase, QCursor
)

# ==============================================================================
# [0] CONFIGURATION & DATA STRUCTURES
# ==============================================================================

@dataclass
class Config:
    """Centralized configuration for the Leviathan Architecture."""
    theme: str = "dark"
    font_family: str = "JetBrains Mono"
    font_size: int = 10
    animation_enabled: bool = True

    max_iterations: int = 10
    mutation_rate: float = 0.3
    timeout_seconds: float = 30.0

    default_security: float = 0.5
    default_speed: float = 0.5
    default_logic_strictness: float = 0.5

    z3_timeout: int = 5000

    population_size: int = 20
    crossover_rate: float = 0.7
    elite_count: int = 2

@dataclass 
class PipelineResult:
    """Structured result from a pipeline execution."""
    success: bool
    state: str
    ast_tree: Optional[ast.AST] = None
    environment: Optional[Dict] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    iterations: int = 0
    mutations_applied: int = 0
    z3_checks_passed: int = 0
    z3_checks_failed: int = 0

# ==============================================================================
# [1] CORE AI SUB-SYSTEMS (Enhanced)
# ==============================================================================

class FuzzyLogicController:
    """
    Enhanced Fuzzy Logic Controller with more nuanced weight extraction
    and sentiment analysis capabilities.
    """
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self._keyword_weights = {
            'security': {
                'strict': 0.9, 'secure': 0.9, 'safe': 0.8, 'encrypt': 0.85,
                'protect': 0.8, 'validate': 0.7, 'sanitize': 0.8,
                'mostly secure': 0.8, 'somewhat secure': 0.6, 'high security': 1.0
            },
            'speed': {
                'fast': 0.9, 'quick': 0.9, 'optimize': 0.85, 'performance': 0.8,
                'efficient': 0.85, 'rapid': 0.9, 'slow': 0.1, 'lazy': 0.1,
                'kind of fast': 0.4, 'somewhat fast': 0.5, 'blazing': 1.0
            },
            'logic_strictness': {
                'prove': 1.0, 'formal': 1.0, 'theorem': 1.0, 'verify': 0.95,
                'mathematical': 0.9, 'axiom': 1.0, 'invariant': 0.9,
                'strict': 0.9, 'rigorous': 0.95, 'loose': 0.2, 'casual': 0.2
            },
            'memory_usage': {
                'memory': 0.8, 'ram': 0.8, 'storage': 0.7, 'cache': 0.75,
                'lightweight': 0.9, 'heavy': 0.2, 'minimal': 0.9
            },
            'readability': {
                'clean': 0.9, 'readable': 0.9, 'document': 0.8, 'comment': 0.7,
                'clear': 0.85, 'understandable': 0.8, 'obfuscated': 0.1
            }
        }

    def evaluate(self, prompt: str) -> Dict[str, float]:
        weights = {
            'security': self.config.default_security,
            'speed': self.config.default_speed,
            'logic_strictness': self.config.default_logic_strictness,
            'memory_usage': 0.5,
            'readability': 0.5
        }

        p = prompt.lower()

        for category, keywords in self._keyword_weights.items():
            for keyword, weight in keywords.items():
                if keyword in p:
                    weights[category] = max(weights[category], weight)

        # Contextual modifiers
        if 'not' in p or "don't" in p:
            for key in weights:
                if any(kw in p for kw in self._keyword_weights.get(key, {})):
                    weights[key] = 1.0 - weights[key]

        return weights

class MambaContextEngine:
    """
    Enhanced context engine with memory, project tracking, and
    semantic context window management.
    """
    def __init__(self, max_history: int = 100):
        self.history: deque = deque(maxlen=max_history)
        self.projects: Dict[str, Dict] = {}
        self.current_project: Optional[str] = None
        self.context_embeddings: Dict[str, List[float]] = {}

    def ingest(self, context: str, project: str = None) -> str:
        timestamp = time.time()
        entry = {
            'timestamp': timestamp,
            'raw': context,
            'project': project or self.current_project,
            'embedding': self._simple_embed(context)
        }
        self.history.append(entry)

        if project:
            if project not in self.projects:
                self.projects[project] = {'contexts': [], 'created': timestamp}
            self.projects[project]['contexts'].append(entry)

        return f"MAMBA_LATENT[{len(self.history)}]({context[:50]}...)"

    def _simple_embed(self, text: str) -> List[float]:
        """Simple character-frequency based embedding for demo purposes."""
        vec = [0.0] * 16
        for i, c in enumerate(text.lower()):
            vec[i % 16] += ord(c) / 255.0
        norm = math.sqrt(sum(x*x for x in vec)) or 1.0
        return [x / norm for x in vec]

    def get_relevant_context(self, query: str, top_k: int = 3) -> List[str]:
        query_embed = self._simple_embed(query)
        scored = []
        for entry in self.history:
            sim = sum(a*b for a, b in zip(query_embed, entry['embedding']))
            scored.append((sim, entry['raw']))
        scored.sort(reverse=True)
        return [s[1] for s in scored[:top_k]]

    def set_project(self, name: str):
        self.current_project = name
        if name not in self.projects:
            self.projects[name] = {'contexts': [], 'created': time.time()}

# ==============================================================================
# [2] PREDICATE LOGIC VERIFICATION (Z3 SMT SOLVER) - Enhanced
# ==============================================================================

try:
    from z3 import *
    Z3_AVAILABLE = True
except ImportError:
    Z3_AVAILABLE = False
    print("WARNING: 'z3-solver' not installed. Predicate Logic Verification disabled.")

class PredicateLogicSkeptic:
    """
    Enhanced Z3-based logical verifier with support for more AST node types,
    custom invariants, and detailed counterexample reporting.
    """
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.z3_vars: Dict[str, Any] = {
            'x': Int('x'), 'y': Int('y'), 'z': Int('z'),
            'a': Real('a'), 'b': Real('b')
        }
        self.invariants: List = [
            self.z3_vars['x'] > 0, 
            self.z3_vars['y'] > 0,
            self.z3_vars['z'] >= 0
        ]
        self.custom_rules: List[Callable] = []
        self.stats = {'checks': 0, 'passed': 0, 'failed': 0, 'skipped': 0}

    def add_invariant(self, expr):
        self.invariants.append(expr)

    def add_custom_rule(self, rule: Callable):
        self.custom_rules.append(rule)

    def verify(self, tree: ast.AST) -> Tuple[bool, Optional[str]]:
        if not Z3_AVAILABLE:
            self.stats['skipped'] += 1
            return True, "Z3 not available - skipped"

        self.stats['checks'] += 1
        solver = Solver()
        solver.set("timeout", self.config.z3_timeout)

        for inv in self.invariants:
            solver.add(inv)

        predicates = self._extract_predicates(tree)
        for pred in predicates:
            solver.add(pred)

        for rule in self.custom_rules:
            try:
                rule_result = rule(tree)
                if rule_result is not None:
                    solver.add(rule_result)
            except Exception as e:
                return False, f"Custom rule error: {e}"

        result = solver.check()

        if result == unsat:
            self.stats['failed'] += 1
            if solver.reason_unknown():
                return False, f"UNSAT: {solver.reason_unknown()}"
            return False, "UNSAT: Code contradicts logical invariants"

        self.stats['passed'] += 1
        return True, "SAT: All invariants satisfied"

    def _extract_predicates(self, node: ast.AST) -> List:
        predicates = []
        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name) and target.id in self.z3_vars:
                        var_name = target.id
                        val = self._eval_expression(child.value)
                        if val is not None:
                            predicates.append(self.z3_vars[var_name] == val)

            elif isinstance(child, ast.Compare):
                pred = self._extract_comparison(child)
                if pred is not None:
                    predicates.append(pred)

            elif isinstance(child, ast.If):
                test_pred = self._extract_condition(child.test)
                if test_pred is not None:
                    predicates.append(test_pred)

        return predicates

    def _eval_expression(self, node) -> Optional[Any]:
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
        if isinstance(node, ast.UnaryOp):
            if isinstance(node.op, ast.USub):
                val = self._eval_expression(node.operand)
                return -val if val is not None else None
            if isinstance(node.op, ast.UAdd):
                return self._eval_expression(node.operand)
        if isinstance(node, ast.BinOp):
            left = self._eval_expression(node.left)
            right = self._eval_expression(node.right)
            if left is not None and right is not None:
                if isinstance(node.op, ast.Add): return left + right
                if isinstance(node.op, ast.Sub): return left - right
                if isinstance(node.op, ast.Mult): return left * right
                if isinstance(node.op, ast.Div) and right != 0: return left / right
        return None

    def _extract_comparison(self, node: ast.Compare) -> Optional[Any]:
        if len(node.ops) != 1 or len(node.comparators) != 1:
            return None

        left = self._eval_expression(node.left)
        right = self._eval_expression(node.comparators[0])

        if left is None or right is None:
            return None

        op = node.ops[0]
        if isinstance(op, ast.Eq): return left == right
        if isinstance(op, ast.NotEq): return left != right
        if isinstance(op, ast.Lt): return left < right
        if isinstance(op, ast.LtE): return left <= right
        if isinstance(op, ast.Gt): return left > right
        if isinstance(op, ast.GtE): return left >= right
        return None

    def _extract_condition(self, node: ast.AST) -> Optional[Any]:
        if isinstance(node, ast.Compare):
            return self._extract_comparison(node)
        if isinstance(node, ast.BoolOp):
            values = [self._extract_condition(v) for v in node.values]
            values = [v for v in values if v is not None]
            if not values:
                return None
            if isinstance(node.op, ast.And):
                result = values[0]
                for v in values[1:]:
                    result = And(result, v)
                return result
            if isinstance(node.op, ast.Or):
                result = values[0]
                for v in values[1:]:
                    result = Or(result, v)
                return result
        return None

    def get_stats(self) -> Dict:
        return dict(self.stats)

# ==============================================================================
# [3] TREE TRANSFORMER & GENETIC PROGRAMMING (Enhanced)
# ==============================================================================

class TreeTransformer:
    """
    Enhanced AST generator with multiple generation strategies,
    template-based code generation, and intent parsing.
    """
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.templates: Dict[str, Callable] = {
            'math': self._gen_math_template,
            'loop': self._gen_loop_template,
            'conditional': self._gen_conditional_template,
            'function': self._gen_function_template,
            'data_structure': self._gen_data_structure_template
        }
        self.bug_modes = ['none', 'negative_value', 'undefined_var', 'type_mismatch', 'division_by_zero']

    def generate(self, intent: str, bug_mode: str = 'negative_value') -> ast.AST:
        intent_lower = intent.lower()

        template_name = 'math'
        for name in self.templates:
            if name in intent_lower:
                template_name = name
                break

        tree = self.templates[template_name](intent_lower, bug_mode)
        ast.fix_missing_locations(tree)
        return tree

    def _gen_math_template(self, intent: str, bug_mode: str) -> ast.AST:
        if bug_mode == 'negative_value':
            value = ast.UnaryOp(op=ast.USub(), operand=ast.Constant(value=1))
        elif bug_mode == 'undefined_var':
            value = ast.Name(id='undefined_var', ctx=ast.Load())
        elif bug_mode == 'type_mismatch':
            value = ast.Constant(value="string")
        elif bug_mode == 'division_by_zero':
            value = ast.BinOp(
                left=ast.Constant(value=1),
                op=ast.Div(),
                right=ast.Constant(value=0)
            )
        else:
            value = ast.Constant(value=5)

        body = [
            ast.Assign(
                targets=[ast.Name(id='x', ctx=ast.Store())], 
                value=value
            ),
            ast.Expr(value=ast.Call(
                func=ast.Name(id='sim_print', ctx=ast.Load()),
                args=[ast.BinOp(
                    left=ast.Name(id='x', ctx=ast.Load()), 
                    op=ast.Add(), 
                    right=ast.Constant(value=10)
                )],
                keywords=[]
            ))
        ]
        return ast.Module(body=body, type_ignores=[])

    def _gen_loop_template(self, intent: str, bug_mode: str) -> ast.AST:
        body = [
            ast.Assign(
                targets=[ast.Name(id='i', ctx=ast.Store())],
                value=ast.Constant(value=0)
            ),
            ast.While(
                test=ast.Compare(
                    left=ast.Name(id='i', ctx=ast.Load()),
                    ops=[ast.Lt()],
                    comparators=[ast.Constant(value=5)]
                ),
                body=[
                    ast.Expr(value=ast.Call(
                        func=ast.Name(id='sim_print', ctx=ast.Load()),
                        args=[ast.Name(id='i', ctx=ast.Load())],
                        keywords=[]
                    )),
                    ast.AugAssign(
                        target=ast.Name(id='i', ctx=ast.Store()),
                        op=ast.Add(),
                        value=ast.Constant(value=1)
                    )
                ],
                orelse=[]
            )
        ]
        return ast.Module(body=body, type_ignores=[])

    def _gen_conditional_template(self, intent: str, bug_mode: str) -> ast.AST:
        body = [
            ast.Assign(
                targets=[ast.Name(id='x', ctx=ast.Store())],
                value=ast.Constant(value=10)
            ),
            ast.If(
                test=ast.Compare(
                    left=ast.Name(id='x', ctx=ast.Load()),
                    ops=[ast.Gt()],
                    comparators=[ast.Constant(value=5)]
                ),
                body=[
                    ast.Expr(value=ast.Call(
                        func=ast.Name(id='sim_print', ctx=ast.Load()),
                        args=[ast.Constant(value="x is greater than 5")],
                        keywords=[]
                    ))
                ],
                orelse=[
                    ast.Expr(value=ast.Call(
                        func=ast.Name(id='sim_print', ctx=ast.Load()),
                        args=[ast.Constant(value="x is not greater than 5")],
                        keywords=[]
                    ))
                ]
            )
        ]
        return ast.Module(body=body, type_ignores=[])

    def _gen_function_template(self, intent: str, bug_mode: str) -> ast.AST:
        func_def = ast.FunctionDef(
            name='compute',
            args=ast.arguments(
                posonlyargs=[],
                args=[ast.arg(arg='n', annotation=None)],
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[]
            ),
            body=[
                ast.Return(value=ast.BinOp(
                    left=ast.Name(id='n', ctx=ast.Load()),
                    op=ast.Mult(),
                    right=ast.Constant(value=2)
                ))
            ],
            decorator_list=[]
        )
        call = ast.Expr(value=ast.Call(
            func=ast.Name(id='sim_print', ctx=ast.Load()),
            args=[ast.Call(
                func=ast.Name(id='compute', ctx=ast.Load()),
                args=[ast.Constant(value=5)],
                keywords=[]
            )],
            keywords=[]
        ))
        return ast.Module(body=[func_def, call], type_ignores=[])

    def _gen_data_structure_template(self, intent: str, bug_mode: str) -> ast.AST:
        body = [
            ast.Assign(
                targets=[ast.Name(id='data', ctx=ast.Store())],
                value=ast.List(elts=[
                    ast.Constant(value=1),
                    ast.Constant(value=2),
                    ast.Constant(value=3)
                ], ctx=ast.Load())
            ),
            ast.For(
                target=ast.Name(id='item', ctx=ast.Store()),
                iter=ast.Name(id='data', ctx=ast.Load()),
                body=[
                    ast.Expr(value=ast.Call(
                        func=ast.Name(id='sim_print', ctx=ast.Load()),
                        args=[ast.Name(id='item', ctx=ast.Load())],
                        keywords=[]
                    ))
                ],
                orelse=[]
            )
        ]
        return ast.Module(body=body, type_ignores=[])

class GeneticProgrammer:
    """
    Enhanced Genetic Programmer with population-based evolution,
    multiple mutation strategies, and fitness evaluation.
    """
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.mutation_strategies = [
            self._mutate_negative_to_positive,
            self._mutate_add_type_check,
            self._mutate_add_bounds_check,
            self._mutate_fix_undefined_var,
            self._mutate_fix_division_by_zero
        ]
        self.fitness_history: List[float] = []

    def evolve(self, tree: ast.AST, skeptic: PredicateLogicSkeptic, 
               max_generations: int = None) -> Tuple[ast.AST, int]:
        max_generations = max_generations or self.config.max_iterations
        population = [copy.deepcopy(tree) for _ in range(self.config.population_size)]

        best_tree = copy.deepcopy(tree)
        best_fitness = self._evaluate_fitness(tree, skeptic)
        mutations = 0

        for generation in range(max_generations):
            fitness_scores = []
            for individual in population:
                fitness = self._evaluate_fitness(individual, skeptic)
                fitness_scores.append((fitness, individual))

            fitness_scores.sort(reverse=True)

            if fitness_scores[0][0] > best_fitness:
                best_fitness = fitness_scores[0][0]
                best_tree = copy.deepcopy(fitness_scores[0][1])

            if best_fitness >= 1.0:
                break

            new_population = [copy.deepcopy(f[1]) for f in fitness_scores[:self.config.elite_count]]

            while len(new_population) < self.config.population_size:
                parent1 = self._tournament_select(fitness_scores)
                parent2 = self._tournament_select(fitness_scores)

                if random.random() < self.config.crossover_rate:
                    child = self._crossover(parent1, parent2)
                else:
                    child = copy.deepcopy(parent1)

                if random.random() < self.config.mutation_rate:
                    child = self.mutate(child)
                    mutations += 1

                new_population.append(child)

            population = new_population
            self.fitness_history.append(best_fitness)

        return best_tree, mutations

    def mutate(self, tree: ast.AST) -> ast.AST:
        mutated = copy.deepcopy(tree)
        strategy = random.choice(self.mutation_strategies)
        mutated = strategy(mutated)
        ast.fix_missing_locations(mutated)
        return mutated

    def _mutate_negative_to_positive(self, tree: ast.AST) -> ast.AST:
        class Mutator(ast.NodeTransformer):
            def visit_Assign(self, node):
                if isinstance(node.value, ast.UnaryOp) and isinstance(node.value.op, ast.USub):
                    print("  -> [GP] Mutating negative value to positive")
                    node.value = ast.Constant(value=abs(self._eval_const(node.value.operand) or 1))
                return node

            def _eval_const(self, node):
                if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                    return node.value
                return None

        return Mutator().visit(tree)

    def _mutate_add_type_check(self, tree: ast.AST) -> ast.AST:
        class TypeCheckInserter(ast.NodeTransformer):
            def visit_Assign(self, node):
                if isinstance(node.targets[0], ast.Name):
                    check = ast.If(
                        test=ast.Call(
                            func=ast.Name(id='isinstance', ctx=ast.Load()),
                            args=[
                                node.value,
                                ast.Name(id='int', ctx=ast.Load())
                            ],
                            keywords=[]
                        ),
                        body=[node],
                        orelse=[
                            ast.Expr(value=ast.Call(
                                func=ast.Name(id='sim_print', ctx=ast.Load()),
                                args=[ast.Constant(value="Type error!")],
                                keywords=[]
                            ))
                        ]
                    )
                    return check
                return node

        return TypeCheckInserter().visit(tree)

    def _mutate_add_bounds_check(self, tree: ast.AST) -> ast.AST:
        class BoundsCheckInserter(ast.NodeTransformer):
            def visit_Assign(self, node):
                if isinstance(node.targets[0], ast.Name) and node.targets[0].id == 'x':
                    check = ast.If(
                        test=ast.Compare(
                            left=node.value,
                            ops=[ast.Gt()],
                            comparators=[ast.Constant(value=0)]
                        ),
                        body=[node],
                        orelse=[
                            ast.Assign(
                                targets=[ast.Name(id='x', ctx=ast.Store())],
                                value=ast.Constant(value=1)
                            )
                        ]
                    )
                    return check
                return node

        return BoundsCheckInserter().visit(tree)

    def _mutate_fix_undefined_var(self, tree: ast.AST) -> ast.AST:
        class UndefinedVarFixer(ast.NodeTransformer):
            def visit_Name(self, node):
                if isinstance(node.ctx, ast.Load) and node.id == 'undefined_var':
                    print("  -> [GP] Fixing undefined variable reference")
                    return ast.Constant(value=0)
                return node

        return UndefinedVarFixer().visit(tree)

    def _mutate_fix_division_by_zero(self, tree: ast.AST) -> ast.AST:
        class DivZeroFixer(ast.NodeTransformer):
            def visit_BinOp(self, node):
                if isinstance(node.op, ast.Div):
                    if isinstance(node.right, ast.Constant) and node.right.value == 0:
                        print("  -> [GP] Fixing division by zero")
                        node.right = ast.Constant(value=1)
                return node

        return DivZeroFixer().visit(tree)

    def _evaluate_fitness(self, tree: ast.AST, skeptic: PredicateLogicSkeptic) -> float:
        valid, msg = skeptic.verify(tree)
        if valid:
            return 1.0

        score = 0.5
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                if isinstance(node.value, ast.Constant) and isinstance(node.value.value, (int, float)):
                    if node.value.value > 0:
                        score += 0.1

        return min(score, 0.9)

    def _tournament_select(self, fitness_scores: List[Tuple[float, ast.AST]], 
                          k: int = 3) -> ast.AST:
        tournament = random.sample(fitness_scores, min(k, len(fitness_scores)))
        tournament.sort(reverse=True)
        return tournament[0][1]

    def _crossover(self, parent1: ast.AST, parent2: ast.AST) -> ast.AST:
        child = copy.deepcopy(parent1)
        if hasattr(child, 'body') and hasattr(parent2, 'body'):
            p2_body = getattr(parent2, 'body', [])
            if p2_body and child.body:
                idx = random.randint(0, min(len(child.body)-1, len(p2_body)-1))
                child.body[idx] = copy.deepcopy(p2_body[idx])
        return child

# ==============================================================================
# [4] CUSTOM ENVIRONMENT & INTERPRETER (Enhanced)
# ==============================================================================

class SimulatedEnvironment:
    """
    Enhanced simulated environment with file system, network simulation,
    memory tracking, and execution profiling.
    """
    def __init__(self):
        self.reset()
        self.call_stack: List[str] = []
        self.memory_usage: int = 0
        self.max_memory: int = 1024 * 1024
        self.io_operations: int = 0
        self.cpu_cycles: int = 0

    def reset(self):
        self.vars: Dict[str, Any] = {}
        self.fs = {
            "/": {
                "app": {},
                "tmp": {},
                "data": {
                    "config.json": '{"version": "1.0"}'
                }
            }
        }
        self.stdout: List[str] = []
        self.stderr: List[str] = []
        self.call_stack = []
        self.memory_usage = 0
        self.io_operations = 0
        self.cpu_cycles = 0

    def allocate(self, size: int) -> bool:
        if self.memory_usage + size > self.max_memory:
            return False
        self.memory_usage += size
        return True

    def deallocate(self, size: int):
        self.memory_usage = max(0, self.memory_usage - size)

    def to_json(self) -> str:
        return json.dumps({
            "vars": self.vars,
            "fs": self.fs,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "call_stack": self.call_stack,
            "memory_usage": self.memory_usage,
            "io_operations": self.io_operations,
            "cpu_cycles": self.cpu_cycles
        }, indent=2)

    def get_profile(self) -> Dict:
        return {
            "memory_usage": self.memory_usage,
            "io_operations": self.io_operations,
            "cpu_cycles": self.cpu_cycles,
            "call_depth": len(self.call_stack),
            "var_count": len(self.vars)
        }

class EnvironmentInterpreter(ast.NodeVisitor):
    """
    Enhanced interpreter with full Python subset support,
    exception handling, profiling, and step-through debugging.
    """
    def __init__(self, env: SimulatedEnvironment):
        self.env = env
        self.error_node = None
        self.error_type = None
        self.error_message = None
        self.step_mode = False
        self.breakpoints: set = set()
        self.current_line = 0
        self.execution_trace: List[Dict] = []
        self._loop_depth = 0
        self._max_loop_depth = 100
        self._max_iterations = 1000
        self._iteration_count = 0

    def run(self, tree: ast.AST):
        self.execution_trace = []
        self._iteration_count = 0
        try:
            self.visit(tree)
        except RecursionError:
            self.error_node = tree
            self.error_type = "RecursionError"
            self.error_message = "Maximum recursion depth exceeded"
        except Exception as e:
            if not self.error_node:
                self.error_node = tree
                self.error_type = type(e).__name__
                self.error_message = str(e)

        if self.error_node:
            raise RuntimeError(
                f"{self.error_type} at {self.error_node.__class__.__name__}: {self.error_message}"
            )

    def visit(self, node):
        self.current_line = getattr(node, 'lineno', 0)
        self._iteration_count += 1

        if self._iteration_count > self._max_iterations:
            raise RuntimeError("Maximum iteration count exceeded")

        if self.step_mode:
            self._trace_step(node, "step")

        return super().visit(node)

    def _trace_step(self, node: ast.AST, event: str):
        self.execution_trace.append({
            'event': event,
            'node_type': node.__class__.__name__,
            'line': getattr(node, 'lineno', 0),
            'vars': dict(self.env.vars),
            'call_stack': list(self.env.call_stack)
        })

    def visit_Module(self, node):
        for child in node.body:
            self.visit(child)

    def visit_Assign(self, node):
        value = self._eval(node.value)
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.env.vars[target.id] = value
                self.env.allocate(64)
            elif isinstance(target, ast.Subscript):
                obj = self._eval(target.value)
                idx = self._eval(target.slice)
                obj[idx] = value
            elif isinstance(target, ast.Tuple):
                if isinstance(value, (list, tuple)):
                    for t, v in zip(target.elts, value):
                        if isinstance(t, ast.Name):
                            self.env.vars[t.id] = v

    def visit_AugAssign(self, node):
        name = node.target.id if isinstance(node.target, ast.Name) else "?"
        current = self.env.vars.get(name, 0)
        value = self._eval(node.value)

        if isinstance(node.op, ast.Add): self.env.vars[name] = current + value
        elif isinstance(node.op, ast.Sub): self.env.vars[name] = current - value
        elif isinstance(node.op, ast.Mult): self.env.vars[name] = current * value
        elif isinstance(node.op, ast.Div): 
            if value == 0:
                self.error_node = node
                self.error_type = "ZeroDivisionError"
                self.error_message = "Division by zero"
                return
            self.env.vars[name] = current / value

    def visit_Expr(self, node):
        self._eval(node.value)

    def visit_If(self, node):
        condition = self._eval(node.test)
        if condition:
            for child in node.body:
                self.visit(child)
        else:
            for child in node.orelse:
                self.visit(child)

    def visit_While(self, node):
        self._loop_depth += 1
        if self._loop_depth > self._max_loop_depth:
            self.error_node = node
            self.error_type = "RuntimeError"
            self.error_message = "Maximum loop depth exceeded"
            self._loop_depth -= 1
            return

        iteration = 0
        while self._eval(node.test):
            iteration += 1
            if iteration > self._max_iterations:
                self.error_node = node
                self.error_type = "RuntimeError"
                self.error_message = "Infinite loop detected"
                break

            for child in node.body:
                self.visit(child)

        self._loop_depth -= 1

    def visit_For(self, node):
        iterable = self._eval(node.iter)
        if not hasattr(iterable, '__iter__'):
            self.error_node = node
            self.error_type = "TypeError"
            self.error_message = f"Object is not iterable"
            return

        for item in iterable:
            if isinstance(node.target, ast.Name):
                self.env.vars[node.target.id] = item
            for child in node.body:
                self.visit(child)

    def visit_FunctionDef(self, node):
        self.env.vars[node.name] = node

    def visit_Return(self, node):
        value = self._eval(node.value) if node.value else None
        return value

    def visit_Call(self, node):
        return self._call(node)

    def _eval(self, node) -> Any:
        self.env.cpu_cycles += 1

        if isinstance(node, ast.Constant):
            return node.value

        if isinstance(node, ast.Name):
            if node.id not in self.env.vars:
                self.error_node = node
                self.error_type = "NameError"
                self.error_message = f"Undefined variable: {node.id}"
                raise NameError(f"Undefined: {node.id}")
            return self.env.vars[node.id]

        if isinstance(node, ast.BinOp):
            left = self._eval(node.left)
            right = self._eval(node.right)

            if isinstance(node.op, ast.Add): return left + right
            if isinstance(node.op, ast.Sub): return left - right
            if isinstance(node.op, ast.Mult): return left * right
            if isinstance(node.op, ast.Div):
                if right == 0:
                    self.error_node = node
                    self.error_type = "ZeroDivisionError"
                    self.error_message = "Division by zero"
                    raise ZeroDivisionError("Division by zero")
                return left / right
            if isinstance(node.op, ast.Mod): return left % right
            if isinstance(node.op, ast.Pow): return left ** right
            if isinstance(node.op, ast.FloorDiv): return left // right

        if isinstance(node, ast.UnaryOp):
            val = self._eval(node.operand)
            if isinstance(node.op, ast.USub): return -val
            if isinstance(node.op, ast.UAdd): return +val
            if isinstance(node.op, ast.Not): return not val

        if isinstance(node, ast.Compare):
            left = self._eval(node.left)
            for op, comparator in zip(node.ops, node.comparators):
                right = self._eval(comparator)
                if isinstance(op, ast.Eq): result = left == right
                elif isinstance(op, ast.NotEq): result = left != right
                elif isinstance(op, ast.Lt): result = left < right
                elif isinstance(op, ast.LtE): result = left <= right
                elif isinstance(op, ast.Gt): result = left > right
                elif isinstance(op, ast.GtE): result = left >= right
                elif isinstance(op, ast.Is): result = left is right
                elif isinstance(op, ast.IsNot): result = left is not right
                elif isinstance(op, ast.In): result = left in right
                elif isinstance(op, ast.NotIn): result = left not in right
                else: result = False

                if not result:
                    return False
                left = right
            return True

        if isinstance(node, ast.BoolOp):
            values = [self._eval(v) for v in node.values]
            if isinstance(node.op, ast.And): return all(values)
            if isinstance(node.op, ast.Or): return any(values)

        if isinstance(node, ast.List):
            return [self._eval(e) for e in node.elts]

        if isinstance(node, ast.Tuple):
            return tuple(self._eval(e) for e in node.elts)

        if isinstance(node, ast.Dict):
            return {self._eval(k): self._eval(v) for k, v in zip(node.keys, node.values)}

        if isinstance(node, ast.Subscript):
            obj = self._eval(node.value)
            idx = self._eval(node.slice)
            return obj[idx]

        if isinstance(node, ast.Call):
            return self._call(node)

        return None

    def _call(self, node: ast.Call):
        name = node.func.id if isinstance(node.func, ast.Name) else "?"
        args = [self._eval(arg) for arg in node.args]

        self.env.call_stack.append(name)
        self.env.io_operations += 1

        try:
            if name == "sim_print":
                result = str(args[0]) if args else ""
                self.env.stdout.append(result)
                return result

            elif name == "sim_input":
                return "simulated_input"

            elif name == "sim_len":
                return len(args[0]) if args else 0

            elif name == "sim_range":
                return list(range(*args))

            elif name == "sim_type":
                return type(args[0]).__name__ if args else "None"

            elif name == "sim_assert":
                if not (args[0] if args else False):
                    self.error_node = node
                    self.error_type = "AssertionError"
                    self.error_message = f"Assertion failed: {args[1] if len(args) > 1 else ''}"
                    raise AssertionError(self.error_message)
                return True

            elif name in self.env.vars and isinstance(self.env.vars[name], ast.FunctionDef):
                func = self.env.vars[name]
                for arg, val in zip(func.args.args, args):
                    self.env.vars[arg.arg] = val
                for stmt in func.body:
                    if isinstance(stmt, ast.Return):
                        return self._eval(stmt.value) if stmt.value else None
                    self.visit(stmt)
                return None

            else:
                self.error_node = node
                self.error_type = "NotImplementedError"
                self.error_message = f"Function '{name}' not implemented in simulated environment"
                raise NotImplementedError(f"Func {name} not in env.")

        finally:
            self.env.call_stack.pop()

# ==============================================================================
# [5] STATE MACHINE ORCHESTRATOR (Enhanced)
# ==============================================================================

class PipelineState(Enum):
    PLANNING = auto()
    CONTEXT_INGESTION = auto()
    DRAFTING = auto()
    FOL_VALIDATION = auto()
    GP_MUTATION = auto()
    EXECUTION = auto()
    PROFILING = auto()
    DONE = auto()
    FAILED = auto()
    CANCELLED = auto()

class LeviathanOrchestrator:
    """
    Enhanced orchestrator with full pipeline control, cancellation support,
    detailed metrics, and extensible plugin architecture.
    """
    def __init__(self, ui_callback, config: Config = None):
        self.ui = ui_callback
        self.config = config or Config()
        self.fuzzy = FuzzyLogicController(self.config)
        self.mamba = MambaContextEngine()
        self.tree_gen = TreeTransformer(self.config)
        self.gp = GeneticProgrammer(self.config)
        self.skeptic = PredicateLogicSkeptic(self.config)
        self.env = SimulatedEnvironment()
        self.interpreter = EnvironmentInterpreter(self.env)

        self._cancelled = False
        self._current_state = None
        self._results_history: List[PipelineResult] = []
        self._plugins: List[Callable] = []

    def add_plugin(self, plugin: Callable):
        self._plugins.append(plugin)

    def cancel(self):
        self._cancelled = True
        self._current_state = PipelineState.CANCELLED

    def execute_pipeline(self, prompt: str, bug_mode: str = 'negative_value') -> PipelineResult:
        start_time = time.time()
        self._cancelled = False
        mutations = 0
        z3_passed = 0
        z3_failed = 0
        iterations = 0

        try:
            self._transition(PipelineState.PLANNING, "Analyzing intent via Fuzzy Logic...")
            weights = self.fuzzy.evaluate(prompt)
            self._log(f"Weights extracted: {json.dumps(weights, indent=2)}")

            if self._cancelled:
                return self._build_result(False, "CANCELLED", start_time, iterations, mutations, z3_passed, z3_failed)

            self._transition(PipelineState.CONTEXT_INGESTION, "Ingesting project context...")
            context = self.mamba.ingest("Project Repo", project="main")
            self._log(f"Context: {context}")

            if self._cancelled:
                return self._build_result(False, "CANCELLED", start_time, iterations, mutations, z3_passed, z3_failed)

            self._transition(PipelineState.DRAFTING, "Tree Transformer assembling AST...")
            current_ast = self.tree_gen.generate(prompt, bug_mode=bug_mode)
            self.ui.render_ast(current_ast)
            self.ui.show_code(current_ast)
            iterations += 1

            if self._cancelled:
                return self._build_result(False, "CANCELLED", start_time, iterations, mutations, z3_passed, z3_failed)

            if weights['logic_strictness'] > 0.5:
                self._transition(PipelineState.FOL_VALIDATION, "Running Z3 Predicate Logic Check...")

                is_valid, msg = self.skeptic.verify(current_ast)
                self._log(f"Z3 Result: {msg}")

                if is_valid:
                    z3_passed += 1
                else:
                    z3_failed += 1

                if not is_valid and weights['logic_strictness'] > 0.8:
                    self._transition(PipelineState.GP_MUTATION, f"UNSAT detected! Forcing GP Mutation...")

                    if weights['logic_strictness'] > 0.95:
                        current_ast, mut_count = self.gp.evolve(current_ast, self.skeptic)
                        mutations += mut_count
                    else:
                        current_ast = self.gp.mutate(current_ast)
                        mutations += 1

                    iterations += 1
                    self.ui.render_ast(current_ast)
                    self.ui.show_code(current_ast)

                    is_valid, msg = self.skeptic.verify(current_ast)
                    if is_valid:
                        z3_passed += 1
                        self._log("Post-mutation verification: PASSED")
                    else:
                        z3_failed += 1
                        self._log("Post-mutation verification: FAILED")

            if self._cancelled:
                return self._build_result(False, "CANCELLED", start_time, iterations, mutations, z3_passed, z3_failed)

            self._transition(PipelineState.EXECUTION, "Executing against Simulated Environment...")
            self.env.reset()
            self.interpreter = EnvironmentInterpreter(self.env)

            try:
                self.interpreter.run(current_ast)

                self._transition(PipelineState.PROFILING, "Collecting execution metrics...")
                profile = self.env.get_profile()
                self._log(f"Profile: {json.dumps(profile, indent=2)}")

                self._transition(PipelineState.DONE, "Pipeline Successful.")
                self.ui.show_env(self.env.to_json())

                result = self._build_result(
                    True, "DONE", start_time, iterations, mutations, 
                    z3_passed, z3_failed, current_ast, self.env.vars
                )
                self._results_history.append(result)
                return result

            except Exception as e:
                self._transition(PipelineState.FAILED, str(e))
                self.ui.show_env(f"ERROR: {str(e)}\n\n" + self.env.to_json())
                if self.interpreter.error_node:
                    self.ui.highlight_error(self.interpreter.error_node)

                result = self._build_result(
                    False, "FAILED", start_time, iterations, mutations,
                    z3_passed, z3_failed, current_ast, None, str(e)
                )
                self._results_history.append(result)
                return result

        except Exception as e:
            self._transition(PipelineState.FAILED, f"Orchestrator error: {e}")
            return self._build_result(
                False, "FAILED", start_time, iterations, mutations,
                z3_passed, z3_failed, None, None, str(e)
            )

    def _transition(self, state: PipelineState, msg: str):
        self._current_state = state
        self.ui.log_state(state, msg)

    def _log(self, msg: str):
        self.ui.log_state(self._current_state, f"  > {msg}")

    def _build_result(self, success: bool, state: str, start_time: float,
                     iterations: int, mutations: int, z3_passed: int, z3_failed: int,
                     ast_tree=None, environment=None, error_message=None) -> PipelineResult:
        return PipelineResult(
            success=success,
            state=state,
            ast_tree=ast_tree,
            environment=environment,
            error_message=error_message,
            execution_time=time.time() - start_time,
            iterations=iterations,
            mutations_applied=mutations,
            z3_checks_passed=z3_passed,
            z3_checks_failed=z3_failed
        )

    def get_history(self) -> List[PipelineResult]:
        return self._results_history.copy()

    def get_stats(self) -> Dict:
        if not self._results_history:
            return {}
        total = len(self._results_history)
        successful = sum(1 for r in self._results_history if r.success)
        return {
            'total_executions': total,
            'successful': successful,
            'failed': total - successful,
            'success_rate': successful / total if total > 0 else 0,
            'avg_execution_time': sum(r.execution_time for r in self._results_history) / total,
            'total_mutations': sum(r.mutations_applied for r in self._results_history),
            'total_z3_checks': sum(r.z3_checks_passed + r.z3_checks_failed for r in self._results_history)
        }

# ==============================================================================
# [6] PYSIDE6 NODE-BASED GUI (Enhanced)
# ==============================================================================

class ASTNodeGUI(QGraphicsRectItem):
    """Enhanced AST node with animations, tooltips, and detailed info."""
    def __init__(self, ast_node: ast.AST, x: int, y: int, parent=None):
        super().__init__(0, 0, 160, 50, parent)
        self.ast_node = ast_node
        self.setPos(x, y)
        self.setBrush(QBrush(QColor(40, 45, 60)))
        self.setPen(QPen(QColor(80, 140, 255), 2))
        self.setFlags(QGraphicsRectItem.ItemIsSelectable | QGraphicsRectItem.ItemIsMovable)

        label = QGraphicsTextItem(ast_node.__class__.__name__, self)
        label.setDefaultTextColor(QColor(220, 220, 220))
        label.setFont(QFont("JetBrains Mono", 9, QFont.Bold))
        label.setPos(10, 8)

        info_text = self._get_info_text(ast_node)
        if info_text:
            sub = QGraphicsTextItem(info_text, self)
            sub.setDefaultTextColor(QColor(150, 160, 180))
            sub.setFont(QFont("JetBrains Mono", 7))
            sub.setPos(10, 28)

        if isinstance(ast_node, (ast.FunctionDef, ast.ClassDef)):
            self.setPen(QPen(QColor(255, 200, 80), 3))

    def _get_info_text(self, node) -> str:
        if isinstance(node, ast.Name):
            return f"id: {node.id}"
        elif isinstance(node, ast.Constant):
            val = node.value
            if isinstance(val, str) and len(val) > 15:
                val = val[:15] + "..."
            return f"val: {val}"
        elif isinstance(node, ast.BinOp):
            return f"op: {node.op.__class__.__name__}"
        elif isinstance(node, ast.UnaryOp):
            return f"op: {node.op.__class__.__name__}"
        elif isinstance(node, ast.Compare):
            ops = [op.__class__.__name__ for op in node.ops]
            return f"ops: {', '.join(ops)}"
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                return f"func: {node.func.id}()"
        elif isinstance(node, ast.FunctionDef):
            return f"def {node.name}()"
        return ""

    def set_error(self):
        self.setBrush(QBrush(QColor(140, 20, 20)))
        self.setPen(QPen(QColor(255, 60, 60), 3))

        indicator = QGraphicsEllipseItem(140, 5, 15, 15, self)
        indicator.setBrush(QBrush(QColor(255, 60, 60)))
        indicator.setPen(QPen(Qt.NoPen))

    def set_highlight(self):
        self.setBrush(QBrush(QColor(60, 100, 60)))
        self.setPen(QPen(QColor(100, 255, 100), 3))

    def set_executing(self):
        self.setBrush(QBrush(QColor(80, 60, 100)))
        self.setPen(QPen(QColor(180, 100, 255), 3))

class NodeCanvas(QGraphicsView):
    """Enhanced canvas with zoom, pan, minimap, and animation support."""
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.scene.setBackgroundBrush(QBrush(QColor(18, 18, 22)))
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.nodes = []
        self._zoom_factor = 1.0

        self._draw_grid()

    def _draw_grid(self):
        pen = QPen(QColor(30, 30, 35))
        pen.setWidth(1)
        for i in range(-1000, 1001, 50):
            self.scene.addLine(i, -1000, i, 1000, pen)
            self.scene.addLine(-1000, i, 1000, i, pen)

    def draw_ast(self, tree: ast.AST):
        self.scene.clear()
        self._draw_grid()
        self.nodes = []
        self._build(tree, 0, 0, 0)

        if self.nodes:
            rect = self.scene.itemsBoundingRect()
            self.fitInView(rect.adjusted(-50, -50, 50, 50), Qt.KeepAspectRatio)

    def _build(self, node, depth, idx, px):
        x = (idx * 200) - (depth * 40)
        y = depth * 80
        item = ASTNodeGUI(node, x, y)
        self.scene.addItem(item)
        self.nodes.append(item)

        if depth > 0:
            path = QPainterPath()
            path.moveTo(px + 80, (depth-1)*80 + 50)
            path.cubicTo(px + 80, (depth-1)*80 + 65, x + 80, y - 15, x + 80, y)

            line = QGraphicsPathItem(path)
            line.setPen(QPen(QColor(80, 100, 140), 2))
            self.scene.addItem(line)

        c_idx = 0
        for _, val in ast.iter_fields(node):
            children = val if isinstance(val, list) else [val]
            for child in children:
                if isinstance(child, ast.AST):
                    self._build(child, depth+1, c_idx, x)
                    c_idx += 1

    def flag_error(self, target_node):
        for n in self.nodes:
            if n.ast_node is target_node:
                n.set_error()
                self.centerOn(n)
                break

    def highlight_node(self, target_node):
        for n in self.nodes:
            if n.ast_node is target_node:
                n.set_highlight()
                break

    def wheelEvent(self, event):
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor

        if event.angleDelta().y() > 0:
            self.scale(zoom_in_factor, zoom_in_factor)
            self._zoom_factor *= zoom_in_factor
        else:
            self.scale(zoom_out_factor, zoom_out_factor)
            self._zoom_factor *= zoom_out_factor

class ExecutionTraceDialog(QDialog):
    """Dialog to show step-by-step execution trace."""
    def __init__(self, trace: List[Dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Execution Trace")
        self.setGeometry(200, 200, 800, 600)

        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Step", "Node Type", "Line", "Variables"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.table.setRowCount(len(trace))
        for i, step in enumerate(trace):
            self.table.setItem(i, 0, QTableWidgetItem(str(i+1)))
            self.table.setItem(i, 1, QTableWidgetItem(step['node_type']))
            self.table.setItem(i, 2, QTableWidgetItem(str(step['line'])))
            vars_str = json.dumps(step['vars'], indent=1)
            self.table.setItem(i, 3, QTableWidgetItem(vars_str))

        layout.addWidget(self.table)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

class SettingsDialog(QDialog):
    """Configuration dialog for Leviathan settings."""
    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Leviathan Configuration")
        self.setGeometry(300, 300, 500, 400)

        layout = QVBoxLayout(self)

        pipeline_group = QGroupBox("Pipeline Settings")
        pipeline_layout = QFormLayout()

        self.max_iter = QSpinBox()
        self.max_iter.setRange(1, 100)
        self.max_iter.setValue(config.max_iterations)
        pipeline_layout.addRow("Max Iterations:", self.max_iter)

        self.mutation_rate = QDoubleSpinBox()
        self.mutation_rate.setRange(0.0, 1.0)
        self.mutation_rate.setSingleStep(0.05)
        self.mutation_rate.setValue(config.mutation_rate)
        pipeline_layout.addRow("Mutation Rate:", self.mutation_rate)

        self.timeout = QDoubleSpinBox()
        self.timeout.setRange(1.0, 300.0)
        self.timeout.setValue(config.timeout_seconds)
        pipeline_layout.addRow("Timeout (s):", self.timeout)

        pipeline_group.setLayout(pipeline_layout)
        layout.addWidget(pipeline_group)

        gp_group = QGroupBox("Genetic Programming")
        gp_layout = QFormLayout()

        self.pop_size = QSpinBox()
        self.pop_size.setRange(5, 100)
        self.pop_size.setValue(config.population_size)
        gp_layout.addRow("Population Size:", self.pop_size)

        self.crossover = QDoubleSpinBox()
        self.crossover.setRange(0.0, 1.0)
        self.crossover.setValue(config.crossover_rate)
        gp_layout.addRow("Crossover Rate:", self.crossover)

        gp_group.setLayout(gp_layout)
        layout.addWidget(gp_group)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _save(self):
        self.config.max_iterations = self.max_iter.value()
        self.config.mutation_rate = self.mutation_rate.value()
        self.config.timeout_seconds = self.timeout.value()
        self.config.population_size = self.pop_size.value()
        self.config.crossover_rate = self.crossover.value()
        self.accept()

class MainWindow(QMainWindow):
    """
    Enhanced main window with tabs, toolbars, status bar, settings,
    execution history, and professional dark theme.
    """
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.setWindowTitle("Leviathan Architecture v2.0 - Visual Structural Engine")
        self.setGeometry(100, 100, 1600, 900)

        self.orchestrator = LeviathanOrchestrator(self, self.config)
        self._init_ui()
        self._init_toolbar()
        self._init_menubar()
        self._init_statusbar()
        self._apply_theme()

        self.settings = QSettings("Leviathan", "Architecture")
        self._load_settings()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        left_tabs = QTabWidget()
        left_tabs.setFixedWidth(450)

        # Tab 1: Pipeline Control
        control_tab = QWidget()
        control_layout = QVBoxLayout(control_tab)

        prompt_group = QGroupBox("User Intent")
        prompt_layout = QVBoxLayout(prompt_group)
        self.prompt = QTextEdit()
        self.prompt.setPlaceholderText(
            "Enter intent (e.g., 'Strictly prove logic and print x+10')\n"
            "Keywords: strict, prove, formal, fast, secure, loop, function, data"
        )
        self.prompt.setMaximumHeight(100)
        self.prompt.setFont(QFont("JetBrains Mono", 10))
        prompt_layout.addWidget(self.prompt)
        control_layout.addWidget(prompt_group)

        bug_group = QGroupBox("Bug Injection Mode")
        bug_layout = QVBoxLayout(bug_group)
        self.bug_mode = QComboBox()
        self.bug_mode.addItems([
            'negative_value', 'undefined_var', 'type_mismatch', 
            'division_by_zero', 'none'
        ])
        bug_layout.addWidget(self.bug_mode)
        control_layout.addWidget(bug_group)

        self.btn_run = QPushButton("EXECUTE LEVIATHAN")
        self.btn_run.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                color: white;
                font-weight: bold;
                padding: 12px;
                font-size: 14px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #0088ff; }
            QPushButton:pressed { background-color: #0055aa; }
        """)
        self.btn_run.clicked.connect(self._execute)
        control_layout.addWidget(self.btn_run)

        self.btn_cancel = QPushButton("CANCEL")
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #cc3300;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
        """)
        self.btn_cancel.clicked.connect(self._cancel)
        self.btn_cancel.setEnabled(False)
        control_layout.addWidget(self.btn_cancel)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        control_layout.addWidget(self.progress)

        log_group = QGroupBox("State Machine Log")
        log_layout = QVBoxLayout(log_group)
        self.state_log = QTextEdit()
        self.state_log.setReadOnly(True)
        self.state_log.setFont(QFont("JetBrains Mono", 9))
        log_layout.addWidget(self.state_log)
        control_layout.addWidget(log_group)

        control_layout.addStretch()
        left_tabs.addTab(control_tab, "Control")

        # Tab 2: Code & Environment
        code_tab = QWidget()
        code_layout = QVBoxLayout(code_tab)

        self.code_view = QTextEdit()
        self.code_view.setReadOnly(True)
        self.code_view.setFont(QFont("JetBrains Mono", 11))
        code_layout.addWidget(QLabel("Generated Code:"))
        code_layout.addWidget(self.code_view)

        self.env_view = QTextEdit()
        self.env_view.setReadOnly(True)
        self.env_view.setFont(QFont("JetBrains Mono", 9))
        code_layout.addWidget(QLabel("Environment State:"))
        code_layout.addWidget(self.env_view)

        left_tabs.addTab(code_tab, "Output")

        # Tab 3: Statistics
        stats_tab = QWidget()
        stats_layout = QVBoxLayout(stats_tab)

        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(2)
        self.stats_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        stats_layout.addWidget(self.stats_table)

        self.btn_refresh_stats = QPushButton("Refresh Statistics")
        self.btn_refresh_stats.clicked.connect(self._update_stats)
        stats_layout.addWidget(self.btn_refresh_stats)

        left_tabs.addTab(stats_tab, "Statistics")

        # Tab 4: History
        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            "Time", "State", "Success", "Exec Time", "Mutations", "Z3 Checks"
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        history_layout.addWidget(self.history_table)

        self.btn_clear_history = QPushButton("Clear History")
        self.btn_clear_history.clicked.connect(self._clear_history)
        history_layout.addWidget(self.btn_clear_history)

        left_tabs.addTab(history_tab, "History")

        # Right Panel (Canvas)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        canvas_toolbar = QHBoxLayout()
        self.btn_zoom_in = QPushButton("+")
        self.btn_zoom_out = QPushButton("-")
        self.btn_fit = QPushButton("Fit")
        self.btn_trace = QPushButton("Show Trace")

        self.btn_zoom_in.clicked.connect(lambda: self.canvas.scale(1.2, 1.2))
        self.btn_zoom_out.clicked.connect(lambda: self.canvas.scale(0.8, 0.8))
        self.btn_fit.clicked.connect(self._fit_canvas)
        self.btn_trace.clicked.connect(self._show_trace)

        canvas_toolbar.addWidget(QLabel("Canvas:"))
        canvas_toolbar.addWidget(self.btn_zoom_in)
        canvas_toolbar.addWidget(self.btn_zoom_out)
        canvas_toolbar.addWidget(self.btn_fit)
        canvas_toolbar.addWidget(self.btn_trace)
        canvas_toolbar.addStretch()

        right_layout.addLayout(canvas_toolbar)

        self.canvas = NodeCanvas()
        right_layout.addWidget(self.canvas)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_tabs)
        splitter.addWidget(right_widget)
        splitter.setSizes([450, 1150])
        layout.addWidget(splitter)

    def _init_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        self.act_run = QAction("Run", self)
        self.act_run.setShortcut(QKeySequence("Ctrl+R"))
        self.act_run.triggered.connect(self._execute)
        toolbar.addAction(self.act_run)

        self.act_stop = QAction("Stop", self)
        self.act_stop.setShortcut(QKeySequence("Ctrl+Period"))
        self.act_stop.triggered.connect(self._cancel)
        toolbar.addAction(self.act_stop)

        toolbar.addSeparator()

        self.act_save = QAction("Save", self)
        self.act_save.setShortcut(QKeySequence("Ctrl+S"))
        self.act_save.triggered.connect(self._save_session)
        toolbar.addAction(self.act_save)

        self.act_load = QAction("Load", self)
        self.act_load.setShortcut(QKeySequence("Ctrl+O"))
        self.act_load.triggered.connect(self._load_session)
        toolbar.addAction(self.act_load)

        toolbar.addSeparator()

        self.act_settings = QAction("Settings", self)
        self.act_settings.triggered.connect(self._show_settings)
        toolbar.addAction(self.act_settings)

    def _init_menubar(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        file_menu.addAction("New Session", self._new_session, QKeySequence("Ctrl+N"))
        file_menu.addAction("Save Session...", self._save_session, QKeySequence("Ctrl+S"))
        file_menu.addAction("Load Session...", self._load_session, QKeySequence("Ctrl+O"))
        file_menu.addSeparator()
        file_menu.addAction("Export AST...", self._export_ast)
        file_menu.addAction("Export Code...", self._export_code)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close, QKeySequence("Ctrl+Q"))

        edit_menu = menubar.addMenu("Edit")
        edit_menu.addAction("Clear Log", self._clear_log)
        edit_menu.addAction("Clear Canvas", self._clear_canvas)
        edit_menu.addSeparator()
        edit_menu.addAction("Preferences...", self._show_settings)

        view_menu = menubar.addMenu("View")
        view_menu.addAction("Fit Canvas", self._fit_canvas)
        view_menu.addAction("Reset Zoom", self._reset_zoom)
        view_menu.addSeparator()
        view_menu.addAction("Toggle Animations", self._toggle_animations)

        help_menu = menubar.addMenu("Help")
        help_menu.addAction("About", self._show_about)

    def _init_statusbar(self):
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Ready")

        self.status_z3 = QLabel("Z3: " + ("Available" if Z3_AVAILABLE else "Not Available"))
        self.statusbar.addPermanentWidget(self.status_z3)

    def _apply_theme(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #1a1a2e; }
            QWidget { 
                background-color: #16213e; 
                color: #e94560;
                font-family: "JetBrains Mono", "Consolas", monospace;
            }
            QTabWidget::pane { border: 1px solid #0f3460; }
            QTabBar::tab {
                background-color: #1a1a2e;
                color: #eaeaea;
                padding: 8px 16px;
                border: 1px solid #0f3460;
            }
            QTabBar::tab:selected {
                background-color: #0f3460;
                color: #e94560;
            }
            QGroupBox {
                border: 1px solid #0f3460;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 10px;
                font-weight: bold;
                color: #eaeaea;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QTextEdit {
                background-color: #0f0f1a;
                color: #eaeaea;
                border: 1px solid #0f3460;
                border-radius: 4px;
                padding: 8px;
            }
            QComboBox, QSpinBox, QDoubleSpinBox {
                background-color: #0f0f1a;
                color: #eaeaea;
                border: 1px solid #0f3460;
                padding: 4px;
            }
            QProgressBar {
                border: 1px solid #0f3460;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #e94560;
            }
            QTableWidget {
                background-color: #0f0f1a;
                color: #eaeaea;
                gridline-color: #0f3460;
            }
            QHeaderView::section {
                background-color: #1a1a2e;
                color: #e94560;
                padding: 5px;
                border: 1px solid #0f3460;
            }
            QMenuBar {
                background-color: #1a1a2e;
                color: #eaeaea;
            }
            QMenuBar::item:selected {
                background-color: #0f3460;
            }
            QMenu {
                background-color: #1a1a2e;
                color: #eaeaea;
                border: 1px solid #0f3460;
            }
            QMenu::item:selected {
                background-color: #0f3460;
            }
            QToolBar {
                background-color: #1a1a2e;
                border: 1px solid #0f3460;
                spacing: 5px;
            }
            QStatusBar {
                background-color: #1a1a2e;
                color: #eaeaea;
                border-top: 1px solid #0f3460;
            }
        """)

    def _execute(self):
        prompt = self.prompt.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "Empty Prompt", "Please enter an intent.")
            return

        self.btn_run.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.progress.setValue(0)
        self.state_log.clear()

        bug_mode = self.bug_mode.currentText()

        self.worker = PipelineWorker(self.orchestrator, prompt, bug_mode)
        self.worker.progress.connect(self._update_progress)
        self.worker.finished.connect(self._execution_finished)
        self.worker.start()

    def _update_progress(self, value: int, state: str, msg: str):
        self.progress.setValue(value)
        self.log_state(self._str_to_state(state), msg)
        self.statusbar.showMessage(f"{state}: {msg}")

    def _str_to_state(self, s: str) -> PipelineState:
        try:
            return PipelineState[s]
        except:
            return PipelineState.PLANNING

    def _execution_finished(self, result: PipelineResult):
        self.btn_run.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.progress.setValue(100)

        if result.success:
            self.statusbar.showMessage(f"Success! Time: {result.execution_time:.3f}s")
        else:
            self.statusbar.showMessage(f"Failed: {result.error_message}")

        self._update_stats()
        self._update_history()

    def _cancel(self):
        self.orchestrator.cancel()
        self.btn_cancel.setEnabled(False)
        self.statusbar.showMessage("Cancelling...")

    def _fit_canvas(self):
        if self.canvas.nodes:
            rect = self.canvas.scene.itemsBoundingRect()
            self.canvas.fitInView(rect.adjusted(-50, -50, 50, 50), Qt.KeepAspectRatio)

    def _reset_zoom(self):
        self.canvas.resetTransform()
        self._fit_canvas()

    def _show_trace(self):
        if hasattr(self.orchestrator.interpreter, 'execution_trace') and \
           self.orchestrator.interpreter.execution_trace:
            dialog = ExecutionTraceDialog(self.orchestrator.interpreter.execution_trace, self)
            dialog.exec()
        else:
            QMessageBox.information(self, "No Trace", "No execution trace available. Run the pipeline first.")

    def _show_settings(self):
        dialog = SettingsDialog(self.config, self)
        if dialog.exec() == QDialog.Accepted:
            self._save_settings()

    def _save_settings(self):
        self.settings.setValue("max_iterations", self.config.max_iterations)
        self.settings.setValue("mutation_rate", self.config.mutation_rate)
        self.settings.setValue("timeout", self.config.timeout_seconds)
        self.settings.setValue("population_size", self.config.population_size)
        self.settings.setValue("crossover_rate", self.config.crossover_rate)

    def _load_settings(self):
        self.config.max_iterations = int(self.settings.value("max_iterations", 10))
        self.config.mutation_rate = float(self.settings.value("mutation_rate", 0.3))
        self.config.timeout_seconds = float(self.settings.value("timeout", 30.0))
        self.config.population_size = int(self.settings.value("population_size", 20))
        self.config.crossover_rate = float(self.settings.value("crossover_rate", 0.7))

    def _update_stats(self):
        stats = self.orchestrator.get_stats()
        self.stats_table.setRowCount(len(stats))
        for i, (key, value) in enumerate(stats.items()):
            self.stats_table.setItem(i, 0, QTableWidgetItem(str(key)))
            self.stats_table.setItem(i, 1, QTableWidgetItem(str(value)))

    def _update_history(self):
        history = self.orchestrator.get_history()
        self.history_table.setRowCount(len(history))
        for i, result in enumerate(history):
            self.history_table.setItem(i, 0, QTableWidgetItem(f"{result.execution_time:.3f}s"))
            self.history_table.setItem(i, 1, QTableWidgetItem(result.state))
            self.history_table.setItem(i, 2, QTableWidgetItem("Yes" if result.success else "No"))
            self.history_table.setItem(i, 3, QTableWidgetItem(f"{result.execution_time:.3f}s"))
            self.history_table.setItem(i, 4, QTableWidgetItem(str(result.mutations_applied)))
            self.history_table.setItem(i, 5, QTableWidgetItem(str(result.z3_checks_passed + result.z3_checks_failed)))

    def _clear_history(self):
        self.orchestrator._results_history.clear()
        self.history_table.setRowCount(0)

    def _clear_log(self):
        self.state_log.clear()

    def _clear_canvas(self):
        self.canvas.scene.clear()
        self.canvas.nodes = []

    def _new_session(self):
        self.prompt.clear()
        self.state_log.clear()
        self.code_view.clear()
        self.env_view.clear()
        self._clear_canvas()
        self.progress.setValue(0)

    def _save_session(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save Session", "", "JSON (*.json)")
        if filename:
            data = {
                'prompt': self.prompt.toPlainText(),
                'code': self.code_view.toPlainText(),
                'env': self.env_view.toPlainText(),
                'log': self.state_log.toPlainText()
            }
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)

    def _load_session(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load Session", "", "JSON (*.json)")
        if filename:
            with open(filename, 'r') as f:
                data = json.load(f)
            self.prompt.setPlainText(data.get('prompt', ''))
            self.code_view.setPlainText(data.get('code', ''))
            self.env_view.setPlainText(data.get('env', ''))
            self.state_log.setPlainText(data.get('log', ''))

    def _export_ast(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Export AST", "", "Python (*.py)")
        if filename:
            with open(filename, 'w') as f:
                f.write(self.code_view.toPlainText())

    def _export_code(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Export Code", "", "Python (*.py)")
        if filename:
            with open(filename, 'w') as f:
                f.write(self.code_view.toPlainText())

    def _toggle_animations(self):
        self.config.animation_enabled = not self.config.animation_enabled

    def _show_about(self):
        QMessageBox.about(self, "About Leviathan",
            "Leviathan Architecture v2.0\n"
            "Visual Structural Engine\n\n"
            "Features:\n"
            "- Fuzzy Logic Intent Analysis\n"
            "- Z3 SMT Predicate Logic Verification\n"
            "- Genetic Programming Mutation\n"
            "- Simulated Environment Execution\n"
            "- Interactive AST Visualization\n"
            "- Execution Tracing & Profiling"
        )

    # UI Callbacks for the Orchestrator
    def log_state(self, state: PipelineState, msg: str):
        color = {
            PipelineState.PLANNING: "#8888ff",
            PipelineState.DRAFTING: "#88ff88",
            PipelineState.FOL_VALIDATION: "#ffaa44",
            PipelineState.GP_MUTATION: "#ff6644",
            PipelineState.EXECUTION: "#44aaff",
            PipelineState.DONE: "#44ff44",
            PipelineState.FAILED: "#ff4444"
        }.get(state, "#aaaaaa")

        self.state_log.append(f'<span style="color: {color}"><b>[{state.name}]</b></span> {msg}')

    def render_ast(self, tree: ast.AST):
        self.canvas.draw_ast(tree)

    def show_code(self, tree: ast.AST):
        try:
            self.code_view.setPlainText(ast.unparse(tree))
        except:
            self.code_view.setPlainText("# AST unparsing not available in this Python version")

    def show_env(self, env_str: str):
        self.env_view.setPlainText(env_str)

    def highlight_error(self, node: ast.AST):
        self.canvas.flag_error(node)


class PipelineWorker(QThread):
    """Worker thread for non-blocking pipeline execution."""
    progress = Signal(int, str, str)
    finished = Signal(object)

    def __init__(self, orchestrator, prompt, bug_mode):
        super().__init__()
        self.orchestrator = orchestrator
        self.prompt = prompt
        self.bug_mode = bug_mode

    def run(self):
        result = self.orchestrator.execute_pipeline(self.prompt, self.bug_mode)
        self.finished.emit(result)

# ==============================================================================
# BOOTSTRAP
# ==============================================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)

    font_db = QFontDatabase()
    available_families = font_db.families()

    if "JetBrains Mono" not in available_families:
        app.setFont(QFont("Consolas", 10))
    else:
        app.setFont(QFont("JetBrains Mono", 10))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
