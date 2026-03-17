"""
Watchlist Widget — live price table for NQ, CL, SI, GC
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QBrush
from trading_dashboard.ui.styles import COLORS

SYMBOLS = ["NQ", "CL", "SI", "GC"]
SYMBOL_NAMES = {
    "NQ": "NASDAQ 100 Futures",
    "CL": "Crude Oil Futures",
    "SI": "Silver Futures",
    "GC": "Gold Futures",
}
COLUMNS = ["Symbol", "Name", "Last", "Change", "%Chg", "Volume"]


class WatchlistWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._prices: dict[str, dict] = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        title = QLabel("WATCHLIST")
        title.setObjectName("SectionLabel")
        layout.addWidget(title)

        self._table = QTableWidget(len(SYMBOLS), len(COLUMNS))
        self._table.setHorizontalHeaderLabels(COLUMNS)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setShowGrid(False)
        self._table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(0, 60)
        self._table.setColumnWidth(2, 90)
        self._table.setColumnWidth(3, 80)
        self._table.setColumnWidth(4, 70)
        self._table.setColumnWidth(5, 80)
        self._table.setAlternatingRowColors(False)
        self._table.setStyleSheet(f"QTableWidget {{ background: transparent; border: none; }}")

        # Populate initial rows
        for row, symbol in enumerate(SYMBOLS):
            self._table.setRowHeight(row, 40)
            sym_item = QTableWidgetItem(symbol)
            sym_item.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            sym_item.setForeground(QBrush(QColor(COLORS["accent"])))
            sym_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            self._table.setItem(row, 0, sym_item)

            name_item = QTableWidgetItem(SYMBOL_NAMES.get(symbol, ""))
            name_item.setForeground(QBrush(QColor(COLORS["text_secondary"])))
            name_item.setFont(QFont("Segoe UI", 10))
            self._table.setItem(row, 1, name_item)

            for col in range(2, 6):
                item = QTableWidgetItem("—")
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
                item.setForeground(QBrush(QColor(COLORS["text_muted"])))
                self._table.setItem(row, col, item)

        layout.addWidget(self._table)

    def update_price(self, symbol: str, last: float, prev_close: float = 0.0, volume: int = 0):
        """Update a symbol row with fresh price data."""
        if symbol not in SYMBOLS:
            return
        row = SYMBOLS.index(symbol)
        change = last - prev_close if prev_close else 0.0
        pct = (change / prev_close * 100) if prev_close else 0.0
        is_up = change >= 0
        color_str = COLORS["green"] if is_up else COLORS["red"]

        def _set(col, text, bold=False, color=None):
            item = self._table.item(row, col)
            if item is None:
                item = QTableWidgetItem()
                self._table.setItem(row, col, item)
            item.setText(text)
            if color:
                item.setForeground(QBrush(QColor(color)))
            if bold:
                font = QFont("Segoe UI", 11, QFont.Weight.Bold)
                item.setFont(font)
            item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        _set(2, f"{last:,.2f}",                bold=True,  color=COLORS["text_primary"])
        _set(3, f"{'+' if is_up else ''}{change:,.2f}", color=color_str)
        _set(4, f"{'+' if is_up else ''}{pct:.2f}%",    color=color_str)
        _set(5, f"{volume:,}",                           color=COLORS["text_secondary"])

    def update_from_historical(self, symbol: str, df):
        """Populate watchlist row from last bars of historical data."""
        if df is None or df.empty:
            return
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2] if len(df) > 1 else last_row
        self.update_price(
            symbol,
            last=float(last_row["Close"]),
            prev_close=float(prev_row["Close"]),
            volume=int(last_row.get("Volume", 0)),
        )
