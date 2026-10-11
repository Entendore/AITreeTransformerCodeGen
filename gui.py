"""
gui.py — All PySide6 visual components.

Contains:
  - ASTNodeGUI     — a single node in the AST tree view.
  - NodeCanvas     — QGraphicsView that renders the full AST.
  - MainWindow     — application shell with splitter layout.

All colours and fonts are pulled from config.Settings so the entire
look-and-feel is tweakable from one place.
"""

from __future__ import annotations

import ast
import logging
from typing import List, Optional

from PySide6.QtCore import Qt, QRectF, QThread
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication, QGraphicsLineItem, QGraphicsRectItem, QGraphicsScene,
    QGraphicsTextItem, QGraphicsView, QHBoxLayout, QLabel, QMainWindow,
    QPushButton, QSplitter, QTextEdit, QWidget,
)

from config import Settings
from models import PipelineState
from pipeline import PipelineWorker

logger = logging.getLogger(__name__)


# ===================================================================
# AST Node Widget
# ===================================================================
class ASTNodeGUI(QGraphicsRectItem):
    """Visual representation of a single AST node on the canvas."""

    WIDTH = 150
    HEIGHT = 44

    def __init__(self, ast_node: ast.AST, x: int, y: int, settings: Settings) -> None:
        super().__init__(0, 0, self.WIDTH, self.HEIGHT)
        self.ast_node = ast_node
        self.setPos(x, y)
        self.setBrush(QBrush(QColor(settings.node_brush)))
        self.setPen(QPen(QColor(settings.node_pen), 2))

        # Primary label
        label = QGraphicsTextItem(ast_node.__class__.__name__, self)
        label.setDefaultTextColor(QColor(220, 220, 220))
        label.setFont(QFont(settings.font_family, 9, QFont.Bold))
        label.setPos(10, 8)

        # Sub-label (variable name / value)
        sub_text = ""
        if isinstance(ast_node, ast.Name):
            sub_text = f"var: {ast_node.id}"
        elif isinstance(ast_node, ast.Constant):
            sub_text = f"val: {ast_node.value!r}"
        elif isinstance(ast_node, ast.BinOp):
            sub_text = f"op: {type(ast_node.op).__name__}"
        if sub_text:
            sub = QGraphicsTextItem(sub_text, self)
            sub.setDefaultTextColor(QColor(150, 150, 150))
            sub.setFont(QFont(settings.font_family, 7))
            sub.setPos(10, 28)

    def set_error_style(self) -> None:
        """Highlight this node as the source of an error."""
        s = Settings()  # reuse defaults for error colours
        self.setBrush(QBrush(QColor(s.error_brush)))
        self.setPen(QPen(QColor(s.error_pen), 3))


# ===================================================================
# AST Canvas
# ===================================================================
class NodeCanvas(QGraphicsView):
    """Interactive QGraphicsView that renders an AST as a node tree."""

    def __init__(self, settings: Settings | None = None) -> None:
        super().__init__()
        self._settings = settings or Settings()
        self._scene = QGraphicsScene(self)
        self._scene.setBackgroundBrush(QBrush(QColor(self._settings.canvas_bg)))
        self.setScene(self._scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.nodes: List[ASTNodeGUI] = []

    def draw_ast(self, tree: ast.AST) -> None:
        """Clear and re-draw the entire AST."""
        self._scene.clear()
        self.nodes.clear()
        self._build(tree, depth=0, index=0, parent_x=None)
        if self._scene.sceneRect().isValid():
            self.fitInView(self._scene.sceneRect().adjusted(-60, -60, 60, 60), Qt.KeepAspectRatio)

    def flag_error(self, target: Optional[ast.AST]) -> None:
        """Highlight the node that caused an execution error."""
        for node_gui in self.nodes:
            if node_gui.ast_node is target:
                node_gui.set_error_style()
                self.centerOn(node_gui)
                logger.info("Canvas: flagged error at %s", type(target).__name__)
                return

    # ---- internals --------------------------------------------------------
    def _build(self, node: ast.AST, depth: int, index: int, parent_x: Optional[int]) -> None:
        x = index * 180 - depth * 30
        y = depth * 72

        item = ASTNodeGUI(node, x, y, self._settings)
        self._scene.addItem(item)
        self.nodes.append(item)

        if parent_x is not None:
            line = QGraphicsLineItem(parent_x + 75, (depth - 1) * 72 + ASTNodeGUI.HEIGHT, x + 75, y)
            line.setPen(QPen(QColor(60, 60, 80), 1))
            self._scene.addItem(line)

        child_idx = 0
        for _, val in ast.iter_fields(node):
            children = val if isinstance(val, list) else [val]
            for child in children:
                if isinstance(child, ast.AST):
                    self._build(child, depth + 1, child_idx, x)
                    child_idx += 1


# ===================================================================
# Main Window
# ===================================================================
class MainWindow(QMainWindow):
    """Application shell: prompt input, log, code view, env view, AST canvas."""

    def __init__(self, settings: Settings | None = None) -> None:
        super().__init__()
        self._settings = settings or Settings()
        self.setWindowTitle("Leviathan Architecture — Visual Structural Engine")
        self.setGeometry(100, 100, self._settings.window_width, self._settings.window_height)
        self.setStyleSheet(f"background-color: #1e1e1e; color: #d4d4d4;")

        self._worker: Optional[PipelineWorker] = None
        self._thread: Optional[QThread] = None
        self._init_ui()

    # ---- UI setup ---------------------------------------------------------
    def _init_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)

        # --- Left panel ---
        left = QWidget()
        left.setFixedWidth(self._settings.left_panel_width)
        left_layout = QHBoxLayout(left)
        left_layout.setContentsMargins(6, 6, 6, 6)
        col = QVBoxLayout()

        s = self._settings

        col.addWidget(QLabel("User Intent"))
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlaceholderText("e.g. Strictly prove logic and print x+10")
        self.prompt_edit.setMaximumHeight(72)
        self.prompt_edit.setFont(QFont(s.code_font_family, s.code_font_size_small))
        col.addWidget(self.prompt_edit)

        self.run_button = QPushButton("▶  EXECUTE LEVIATHAN")
        self.run_button.setStyleSheet(
            f"background-color: {s.accent_color}; font-weight: bold; "
            f"padding: 10px; font-size: 14px; border-radius: 4px;"
        )
        self.run_button.clicked.connect(self._on_run)
        col.addWidget(self.run_button)

        col.addWidget(QLabel("Pipeline Log"))
        self.state_log = QTextEdit()
        self.state_log.setReadOnly(True)
        self.state_log.setFont(QFont(s.code_font_family, s.code_font_size_small))
        col.addWidget(self.state_log)

        col.addWidget(QLabel("Generated Code"))
        self.code_view = QTextEdit()
        self.code_view.setReadOnly(True)
        self.code_view.setFont(QFont(s.code_font_family, s.code_font_size))
        col.addWidget(self.code_view)

        col.addWidget(QLabel("Environment State"))
        self.env_view = QTextEdit()
        self.env_view.setReadOnly(True)
        self.env_view.setFont(QFont(s.code_font_family, s.code_font_size_small))
        col.addWidget(self.env_view)

        left_layout.addLayout(col)

        # --- Right panel (canvas) ---
        self.canvas = NodeCanvas(self._settings)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left)
        splitter.addWidget(self.canvas)
        splitter.setSizes([self._settings.left_panel_width, self._settings.window_width - self._settings.left_panel_width])
        root.addWidget(splitter)

    # ---- button handler ---------------------------------------------------
    def _on_run(self) -> None:
        """Spin up a QThread, create a PipelineWorker, and start execution."""
        prompt = self.prompt_edit.toPlainText().strip()
        if not prompt:
            self._append_log("⚠ Please enter an intent first.")
            return

        # Disable button while running
        self.run_button.setEnabled(False)
        self.run_button.setText("⏳  RUNNING …")

        # Create thread + worker
        self._thread = QThread()
        self._worker = PipelineWorker(self._settings)
        self._worker.moveToThread(self._thread)

        # Wire signals
        self._worker.signals.state_changed.connect(self._on_state)
        self._worker.signals.ast_generated.connect(self.canvas.draw_ast)
        self._worker.signals.code_generated.connect(self.code_view.setPlainText)
        self._worker.signals.env_updated.connect(self.env_view.setPlainText)
        self._worker.signals.error_highlight.connect(self.canvas.flag_error)
        self._worker.signals.finished.connect(self._on_finished)
        self._thread.started.connect(lambda: self._worker.start(prompt))
        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.start()

    # ---- signal slots -----------------------------------------------------
    def _on_state(self, state: PipelineState, message: str) -> None:
        self._append_log(f"<b>[{state.value}]</b> {message}")

    def _on_finished(self, _result) -> None:
        self.run_button.setEnabled(True)
        self.run_button.setText("▶  EXECUTE LEVIATHAN")
        if self._thread:
            self._thread.quit()
            self._thread.wait(2000)
        logger.info("MainWindow: pipeline thread finished")

    def _append_log(self, html: str) -> None:
        self.state_log.append(html)
        # Auto-scroll to bottom
        sb = self.state_log.verticalScrollBar()
        sb.setValue(sb.maximum())
