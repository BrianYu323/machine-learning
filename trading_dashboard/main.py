"""
TradingPro — IBKR Trading Dashboard
Entry point: python main.py  (from inside trading_dashboard/)
Or from project root: python -m trading_dashboard.main
"""
import sys
import logging

# ── Bootstrap asyncio for ib_insync ──────────────────────────────────────────
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

from trading_dashboard.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("TradingPro")
    app.setApplicationDisplayName("TradingPro · IBKR Dashboard")

    # Default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # High-DPI support (Deprecated in PyQt6; always on by default)
    # app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
