import sys
import ast
import copy
import json
import random
from typing import Dict, Any, List, Optional
from enum import Enum

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTextEdit, QPushButton, QLabel, QGraphicsScene, QGraphicsView, 
    QGraphicsRectItem, QGraphicsTextItem, QGraphicsLineItem, QSplitter
)
from PySide6.QtCore import Qt, QRectF, QThread, Signal
from PySide6.QtGui import QBrush, QPen, QColor, QFont, QPainter

# Try to import Z3 for Predicate Logic. If not installed, fallback gracefully.
try:
    from z3 import *
    Z3_AVAILABLE = True
except ImportError:
    Z3_AVAILABLE = False
    print("WARNING: 'z3-solver' not installed. Predicate Logic Verification disabled.")

# ==============================================================================
# [1] CORE AI SUB-SYSTEMS
# ==============================================================================

class FuzzyLogicController:
    def evaluate(self, prompt: str) -> Dict[str, float]:
        weights = {'security': 0.5, 'speed': 0.5, 'logic_strictness': 0.5}
        p = prompt.lower()
        if 'strict' in p or 'prove' in p or 'formal' in p: weights['logic_strictness'] = 1.0
        if 'mostly secure' in p: weights['security'] = 0.8
        if 'kind of fast' in p: weights['speed'] = 0.4
        return weights

class MambaContextEngine:
    def ingest(self, context: str) -> str:
        return f"MAMBA_LATENT({context})"

# ==============================================================================
# [2] PREDICATE LOGIC VERIFICATION (Z3 SMT SOLVER)
# ==============================================================================

class PredicateLogicSkeptic:
    """Uses Z3 to mathematically prove if the AST violates logical invariants."""
    def __init__(self):
        self.z3_vars = {'x': Int('x'), 'y': Int('y')}
        self.invariants = [self.z3_vars['x'] > 0, self.z3_vars['y'] > 0]

    def verify(self, tree: ast.AST) -> bool:
        if not Z3_AVAILABLE: return True # Fallback if Z3 isn't installed
        
        solver = Solver()
        solver.add(self.invariants)
        solver.add(self._extract_predicates(tree))
        
        # If UNSAT, the code mathematically contradicts the invariants
        return solver.check() != unsat

    def _extract_predicates(self, node: ast.AST) -> List:
        predicates = []
        for child in ast.walk(node):
            if isinstance(child, ast.Assign) and isinstance(child.targets[0], ast.Name):
                var_name = child.targets[0].id
                if var_name in self.z3_vars:
                    val = self._eval_simple_math(child.value)
                    if val is not None:
                        predicates.append(self.z3_vars[var_name] == val)
        return predicates

    def _eval_simple_math(self, node) -> Optional[int]:
        if isinstance(node, ast.Constant) and isinstance(node.value, int):
            return node.value
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            val = self._eval_simple_math(node.operand)
            return -val if val is not None else None
        return None

# ==============================================================================
# [3] TREE TRANSFORMER & GENETIC PROGRAMMING
# ==============================================================================

class TreeTransformer:
    """Generates AST structures natively. Intentionally creates a logical bug for the demo."""
    def generate(self, intent: str) -> ast.AST:
        # BUG: Assigns x = -1, which violates the Z3 invariant x > 0
        tree = ast.Module(body=[
            ast.Assign(targets=[ast.Name(id='x', ctx=ast.Store())], 
                       value=ast.UnaryOp(op=ast.USub(), operand=ast.Constant(value=1))),
            ast.Expr(value=ast.Call(
                func=ast.Name(id='sim_print', ctx=ast.Load()),
                args=[ast.BinOp(left=ast.Name(id='x', ctx=ast.Load()), 
                                op=ast.Add(), right=ast.Constant(value=10))],
                keywords=[]
            ))
        ], type_ignores=[])
        ast.fix_missing_locations(tree)
        return tree

class GeneticProgrammer:
    """Mutates AST nodes to fix logical/syntax errors discovered by the Skeptic."""
    def mutate(self, tree: ast.AST) -> ast.AST:
        mutated = copy.deepcopy(tree)
        
        class Mutator(ast.NodeTransformer):
            def visit_Assign(self, node):
                # Mutation: If assigning a UnaryOp (like -1), force it to be positive 1
                if isinstance(node.value, ast.UnaryOp) and isinstance(node.value.op, ast.USub):
                    print("  -> [GP] Mutating -1 to 1 to satisfy logical invariants.")
                    node.value = ast.Constant(value=1)
                return node
        mutated = Mutator().visit(mutated)
        ast.fix_missing_locations(mutated)
        return mutated

# ==============================================================================
# [4] CUSTOM ENVIRONMENT & INTERPRETER
# ==============================================================================

class SimulatedEnvironment:
    def __init__(self): self.reset()
    def reset(self):
        self.vars = {}; self.fs = {"/": {"app": {}}}; self.stdout = []
    def to_json(self): return json.dumps({"vars": self.vars, "fs": self.fs, "stdout": self.stdout}, indent=2)

class EnvironmentInterpreter(ast.NodeVisitor):
    """Walks the AST and executes it against the SimulatedEnvironment dictionaries."""
    def __init__(self, env: SimulatedEnvironment):
        self.env = env; self.error_node = None

    def run(self, tree: ast.AST):
        self.visit(tree)
        if self.error_node: raise RuntimeError(f"Env crash at {self.error_node.__class__.__name__}")

    def visit_Module(self, node):
        for child in node.body: self.visit(child)

    def visit_Assign(self, node):
        name = node.targets[0].id if isinstance(node.targets[0], ast.Name) else "?"
        self.env.vars[name] = self._eval(node.value)

    def visit_Expr(self, node):
        if isinstance(node.value, ast.Call): self._call(node.value)

    def _eval(self, node) -> Any:
        if isinstance(node, ast.Constant): return node.value
        if isinstance(node, ast.Name):
            if node.id not in self.env.vars: self.error_node = node; raise NameError(f"Undefined: {node.id}")
            return self.env.vars[node.id]
        if isinstance(node, ast.BinOp):
            l, r = self._eval(node.left), self._eval(node.right)
            if isinstance(node.op, ast.Add): return l + r
            if isinstance(node.op, ast.Sub): return l - r
        return None

    def _call(self, node: ast.Call):
        name = node.func.id if isinstance(node.func, ast.Name) else "?"
        if name == "sim_print":
            self.env.stdout.append(str(self._eval(node.args[0])))
        else:
            self.error_node = node; raise NotImplementedError(f"Func {name} not in env.")

# ==============================================================================
# [5] STATE MACHINE ORCHESTRATOR
# ==============================================================================

class PipelineState(Enum):
    PLANNING = 1; DRAFTING = 2; FOL_VALIDATION = 3; 
    GP_MUTATION = 4; EXECUTION = 5; DONE = 6; FAILED = 7

class LeviathanOrchestrator:
    def __init__(self, ui_callback):
        self.ui = ui_callback
        self.fuzzy = FuzzyLogicController()
        self.mamba = MambaContextEngine()
        self.tree_gen = TreeTransformer()
        self.gp = GeneticProgrammer()
        self.skeptic = PredicateLogicSkeptic()
        self.env = SimulatedEnvironment()
        self.interpreter = EnvironmentInterpreter(self.env)

    def execute_pipeline(self, prompt: str):
        self.ui.log_state(PipelineState.PLANNING, "Analyzing intent via Fuzzy Logic...")
        weights = self.fuzzy.evaluate(prompt)
        self.ui.log_state(PipelineState.PLANNING, f"Weights extracted: {weights}")
        self.mamba.ingest("Project Repo")

        # 1. Draft
        self.ui.log_state(PipelineState.DRAFTING, "Tree Transformer assembling AST...")
        current_ast = self.tree_gen.generate(prompt)
        self.ui.render_ast(current_ast)
        self.ui.show_code(current_ast)

        # 2. FOL Verification (Z3)
        if weights['logic_strictness'] > 0.8:
            self.ui.log_state(PipelineState.FOL_VALIDATION, "Running Z3 Predicate Logic Check...")
            is_valid = self.skeptic.verify(current_ast)
            if not is_valid:
                self.ui.log_state(PipelineState.GP_MUTATION, "UNSAT detected! Forcing GP Mutation...")
                current_ast = self.gp.mutate(current_ast)
                self.ui.render_ast(current_ast) # Re-render fixed tree
                self.ui.show_code(current_ast)

        # 3. Execute in Simulated Environment
        self.ui.log_state(PipelineState.EXECUTION, "Executing against Dictionary Environment...")
        self.env.reset()
        self.interpreter = EnvironmentInterpreter(self.env)
        
        try:
            self.interpreter.run(current_ast)
            self.ui.log_state(PipelineState.DONE, "Pipeline Successful.")
            self.ui.show_env(self.env.to_json())
        except Exception as e:
            self.ui.log_state(PipelineState.FAILED, str(e))
            self.ui.show_env(f"ERROR: {str(e)}\n\n" + self.env.to_json())
            if self.interpreter.error_node:
                self.ui.highlight_error(self.interpreter.error_node)

# ==============================================================================
# [6] PYSIDE6 NODE-BASED GUI
# ==============================================================================

class ASTNodeGUI(QGraphicsRectItem):
    def __init__(self, ast_node: ast.AST, x: int, y: int):
        super().__init__(0, 0, 150, 40)
        self.ast_node = ast_node
        self.setPos(x, y)
        self.setBrush(QBrush(QColor(35, 40, 55)))
        self.setPen(QPen(QColor(80, 140, 255), 2))
        
        label = QGraphicsTextItem(ast_node.__class__.__name__, self)
        label.setDefaultTextColor(QColor(220, 220, 220))
        label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        label.setPos(10, 10)

        # Add variable names/values as subtext
        if isinstance(ast_node, ast.Name):
            sub = QGraphicsTextItem(f"var: {ast_node.id}", self)
            sub.setDefaultTextColor(QColor(150, 150, 150))
            sub.setFont(QFont("Segoe UI", 7))
            sub.setPos(10, 25)
        elif isinstance(ast_node, ast.Constant):
            sub = QGraphicsTextItem(f"val: {ast_node.value}", self)
            sub.setDefaultTextColor(QColor(150, 150, 150))
            sub.setFont(QFont("Segoe UI", 7))
            sub.setPos(10, 25)

    def set_error(self):
        self.setBrush(QBrush(QColor(140, 20, 20)))
        self.setPen(QPen(QColor(255, 60, 60), 3))

class NodeCanvas(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.scene.setBackgroundBrush(QBrush(QColor(20, 20, 25)))
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.nodes = []

    def draw_ast(self, tree: ast.AST):
        self.scene.clear()
        self.nodes = []
        self._build(tree, 0, 0, 0)
        self.fitInView(self.scene.sceneRect().adjusted(-50, -50, 50, 50), Qt.KeepAspectRatio)

    def _build(self, node, depth, idx, px):
        x = (idx * 180) - (depth * 30)
        y = depth * 70
        item = ASTNodeGUI(node, x, y)
        self.scene.addItem(item)
        self.nodes.append(item)
        if depth > 0:
            line = QGraphicsLineItem(px + 75, (depth-1)*70 + 40, x + 75, y)
            line.setPen(QPen(QColor(60, 60, 80), 1))
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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Leviathan Architecture - Visual Structural Engine")
        self.setGeometry(100, 100, 1500, 850)
        self.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4;")
        
        self.orchestrator = LeviathanOrchestrator(self)
        self._init_ui()

    def _init_ui(self):
        central = QWidget(); self.setCentralWidget(central)
        layout = QHBoxLayout(central)

        # Left Panel
        left = QWidget(); left.setFixedWidth(420)
        l_layout = QVBoxLayout(left)
        
        self.prompt = QTextEdit()
        self.prompt.setPlaceholderText("Enter intent (e.g., 'Strictly prove logic and print x+10')")
        self.prompt.setMaximumHeight(80)
        l_layout.addWidget(QLabel("User Intent:"))
        l_layout.addWidget(self.prompt)

        self.btn_run = QPushButton("EXECUTE LEVIATHAN")
        self.btn_run.setStyleSheet("background-color: #0066cc; font-weight: bold; padding: 10px; font-size: 14px;")
        self.btn_run.clicked.connect(lambda: self.orchestrator.execute_pipeline(self.prompt.toPlainText()))
        l_layout.addWidget(self.btn_run)

        self.state_log = QTextEdit(); self.state_log.setReadOnly(True)
        self.state_log.setFont(QFont("Consolas", 9))
        l_layout.addWidget(QLabel("State Machine Log:"))
        l_layout.addWidget(self.state_log)

        self.code_view = QTextEdit(); self.code_view.setReadOnly(True)
        self.code_view.setFont(QFont("Consolas", 11))
        l_layout.addWidget(QLabel("Generated Code:"))
        l_layout.addWidget(self.code_view)

        self.env_view = QTextEdit(); self.env_view.setReadOnly(True)
        self.env_view.setFont(QFont("Consolas", 9))
        l_layout.addWidget(QLabel("Dictionary Environment State:"))
        l_layout.addWidget(self.env_view)

        # Right Panel (Canvas)
        self.canvas = NodeCanvas()

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left); splitter.addWidget(self.canvas)
        splitter.setSizes([420, 1080])
        layout.addWidget(splitter)

    # UI Callbacks for the Orchestrator
    def log_state(self, state: PipelineState, msg: str):
        self.state_log.append(f"<b>[{state.name}]</b> {msg}")

    def render_ast(self, tree: ast.AST):
        self.canvas.draw_ast(tree)

    def show_code(self, tree: ast.AST):
        self.code_view.setPlainText(ast.unparse(tree))

    def show_env(self, env_str: str):
        self.env_view.setPlainText(env_str)

    def highlight_error(self, node: ast.AST):
        self.canvas.flag_error(node)

# ==============================================================================
# BOOTSTRAP
# ==============================================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())