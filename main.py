"""
main.py — Leviathan application entry point.

Bootstraps logging, loads settings, and launches the PySide6 event loop.
All configuration is centralised in config.Settings.
"""

from __future__ import annotations

import sys

from config import Settings, _setup_logging
from gui import MainWindow
from models import PipelineState

# Bootstrap logging BEFORE anything else touches the logger
_settings = Settings.from_env()
_setup_logging(_settings.log_level)


def main() -> int:
    """Create the QApplication and show the main window."""
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QFont

    app = QApplication(sys.argv)
    app.setFont(QFont(_settings.font_family, _settings.font_size))

    window = MainWindow(_settings)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
