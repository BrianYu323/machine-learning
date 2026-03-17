"""
Account Summary Widget — shows Net Liquidation, P&L, open positions
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QBrush
from trading_dashboard.ui.styles import COLORS


class AccountWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        title = QLabel("ACCOUNT")
        title.setObjectName("SectionLabel")
        layout.addWidget(title)

        # ── Net Liquidation ───────────────────────────────────────
        self._net_liq_label = QLabel("$—")
        self._net_liq_label.setObjectName("AccountValue")
        self._net_liq_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self._net_liq_label)

        net_static = QLabel("Net Liquidation Value")
        net_static.setObjectName("StatLabel")
        layout.addWidget(net_static)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {COLORS['border']};")
        layout.addWidget(sep)

        # ── P&L grid ──────────────────────────────────────────────
        self._unrealized_lbl = QLabel("$—")
        self._realized_lbl   = QLabel("$—")
        self._day_trades_lbl = QLabel("—")

        pnl_pairs = [
            ("Unrealized P&L",   self._unrealized_lbl),
            ("Daily Realized P&L", self._realized_lbl),
            ("Day Trades Left",  self._day_trades_lbl),
        ]
        for stat_name, val_lbl in pnl_pairs:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(0)
            static = QLabel(stat_name)
            static.setObjectName("StatLabel")
            val_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            row_layout.addWidget(static)
            row_layout.addStretch()
            row_layout.addWidget(val_lbl)
            layout.addLayout(row_layout)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"color: {COLORS['border']};")
        layout.addWidget(sep2)

        # ── Positions table ───────────────────────────────────────
        pos_title = QLabel("OPEN POSITIONS")
        pos_title.setObjectName("SectionLabel")
        layout.addWidget(pos_title)

        self._pos_table = QTableWidget(0, 3)
        self._pos_table.setHorizontalHeaderLabels(["Symbol", "Qty", "Avg Cost"])
        self._pos_table.verticalHeader().setVisible(False)
        self._pos_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._pos_table.setShowGrid(False)
        self._pos_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._pos_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self._pos_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._pos_table.setColumnWidth(0, 60)
        self._pos_table.setColumnWidth(1, 50)
        self._pos_table.setMaximumHeight(160)
        layout.addWidget(self._pos_table)

        layout.addStretch()

    def update_account(self, summary: dict):
        """Update display from IBKR account summary dict."""
        net = summary.get("NetLiquidation", "")
        unrl = summary.get("UnrealizedPnL", "")
        real = summary.get("RealizedPnL", "")
        dtrem = summary.get("DayTradesRemaining", "")

        try:
            self._net_liq_label.setText(f"${float(net):,.2f}" if net else "$—")
        except Exception:
            self._net_liq_label.setText(net or "$—")

        def _fmt_pnl(lbl: QLabel, val_str: str):
            try:
                v = float(val_str)
                lbl.setText(f"${v:+,.2f}")
                lbl.setObjectName("PnlPositive" if v >= 0 else "PnlNegative")
                lbl.style().unpolish(lbl)
                lbl.style().polish(lbl)
            except Exception:
                lbl.setText(val_str or "—")

        _fmt_pnl(self._unrealized_lbl, unrl)
        _fmt_pnl(self._realized_lbl, real)
        self._day_trades_lbl.setText(str(dtrem) if dtrem else "—")

    def update_positions(self, positions: list[dict]):
        """Update positions table."""
        self._pos_table.setRowCount(len(positions))
        for row, pos in enumerate(positions):
            self._pos_table.setRowHeight(row, 30)
            sym = QTableWidgetItem(pos.get("symbol", ""))
            sym.setForeground(QBrush(QColor(COLORS["accent"])))
            sym.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self._pos_table.setItem(row, 0, sym)

            qty = pos.get("qty", 0)
            qty_item = QTableWidgetItem(str(qty))
            color = COLORS["green"] if qty >= 0 else COLORS["red"]
            qty_item.setForeground(QBrush(QColor(color)))
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
            self._pos_table.setItem(row, 1, qty_item)

            cost_item = QTableWidgetItem(f"{float(pos.get('avg_cost', 0)):,.2f}")
            cost_item.setForeground(QBrush(QColor(COLORS["text_primary"])))
            cost_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
            self._pos_table.setItem(row, 2, cost_item)
