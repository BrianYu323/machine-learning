"""
Order Entry Widget — Buy / Sell futures orders via IBKR
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QDoubleSpinBox, QButtonGroup,
    QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from trading_dashboard.ui.styles import COLORS

SYMBOLS = ["NQ", "CL", "SI", "GC"]
ORDER_TYPES = ["MKT", "LMT"]


class OrderWidget(QWidget):
    """Panel for submitting buy/sell orders through IBKR."""

    order_submitted = pyqtSignal(str, str, int, str, float)  # symbol, dir, qty, type, price

    def __init__(self, parent=None):
        super().__init__(parent)
        self._direction = "BUY"
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Title
        title = QLabel("ORDER ENTRY")
        title.setObjectName("SectionLabel")
        layout.addWidget(title)

        # ── Symbol ────────────────────────────────────────────────
        layout.addWidget(self._label("Symbol"))
        self._symbol_combo = QComboBox()
        self._symbol_combo.addItems(SYMBOLS)
        layout.addWidget(self._symbol_combo)

        # ── Buy / Sell toggle ─────────────────────────────────────
        dir_layout = QHBoxLayout()
        dir_layout.setSpacing(8)
        self._buy_btn = QPushButton("▲  BUY")
        self._buy_btn.setObjectName("BuyBtn")
        self._buy_btn.setCheckable(True)
        self._buy_btn.setChecked(True)
        self._buy_btn.clicked.connect(lambda: self._set_direction("BUY"))

        self._sell_btn = QPushButton("▼  SELL")
        self._sell_btn.setObjectName("SellBtn")
        self._sell_btn.setCheckable(True)
        self._sell_btn.clicked.connect(lambda: self._set_direction("SELL"))

        dir_layout.addWidget(self._buy_btn)
        dir_layout.addWidget(self._sell_btn)
        layout.addLayout(dir_layout)

        # ── Order Type ────────────────────────────────────────────
        layout.addWidget(self._label("Order Type"))
        self._order_type_combo = QComboBox()
        self._order_type_combo.addItems(ORDER_TYPES)
        self._order_type_combo.currentTextChanged.connect(self._on_order_type_changed)
        layout.addWidget(self._order_type_combo)

        # ── Quantity ──────────────────────────────────────────────
        layout.addWidget(self._label("Quantity (Contracts)"))
        self._qty_spin = QSpinBox()
        self._qty_spin.setMinimum(1)
        self._qty_spin.setMaximum(99)
        self._qty_spin.setValue(1)
        layout.addWidget(self._qty_spin)

        # ── Limit Price (hidden for MKT) ──────────────────────────
        self._price_label = self._label("Limit Price")
        layout.addWidget(self._price_label)
        self._price_spin = QDoubleSpinBox()
        self._price_spin.setDecimals(2)
        self._price_spin.setMaximum(999999.0)
        self._price_spin.setMinimum(0.0)
        self._price_spin.setValue(0.0)
        layout.addWidget(self._price_spin)
        self._price_label.setVisible(False)
        self._price_spin.setVisible(False)

        # ── Separator ─────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep)

        # ── Submit ────────────────────────────────────────────────
        self._submit_btn = QPushButton("PLACE BUY ORDER")
        self._submit_btn.setObjectName("SubmitBtn")
        self._submit_btn.setProperty("direction", "BUY")
        self._submit_btn.setMinimumHeight(44)
        self._submit_btn.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self._submit_btn.clicked.connect(self._on_submit)
        layout.addWidget(self._submit_btn)

        layout.addStretch()

    def _label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px; font-weight: 600; letter-spacing: 1px;")
        return lbl

    def _set_direction(self, direction: str):
        self._direction = direction
        self._buy_btn.setChecked(direction == "BUY")
        self._sell_btn.setChecked(direction == "SELL")
        self._submit_btn.setText(f"PLACE {direction} ORDER")
        self._submit_btn.setProperty("direction", direction)
        # Re-apply stylesheet to pick up new property
        self._submit_btn.style().unpolish(self._submit_btn)
        self._submit_btn.style().polish(self._submit_btn)

    def _on_order_type_changed(self, otype: str):
        is_lmt = otype == "LMT"
        self._price_label.setVisible(is_lmt)
        self._price_spin.setVisible(is_lmt)

    def _on_submit(self):
        symbol = self._symbol_combo.currentText()
        qty = self._qty_spin.value()
        otype = self._order_type_combo.currentText()
        price = self._price_spin.value() if otype == "LMT" else 0.0

        msg = (f"confirming order:\n\n"
               f"  {self._direction}  {qty} × {symbol}  @  {otype}"
               f"{f'  ${price:,.2f}' if otype == 'LMT' else ''}\n\n"
               f"Send this order to IBKR?")
        reply = QMessageBox.question(
            self, "Confirm Order", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.order_submitted.emit(symbol, self._direction, qty, otype, price)

    def set_symbol(self, symbol: str):
        idx = self._symbol_combo.findText(symbol)
        if idx >= 0:
            self._symbol_combo.setCurrentIndex(idx)
