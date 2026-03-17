"""
Chart Widget — Candlestick chart with technical indicators
Embeds a matplotlib/mplfinance figure in a PyQt6 widget.
"""
import sys
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import mplfinance as mpf
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QComboBox, QLabel, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from trading_dashboard.ui.styles import COLORS

CHART_STYLE = {
    "axes.facecolor":    COLORS["chart_bg"],        # hex: #080c14
    "figure.facecolor":  COLORS["chart_bg"],
    "axes.edgecolor":    "#1e2535",                 # mpl-compat (was rgba border)
    "xtick.color":       COLORS["text_muted"],
    "ytick.color":       COLORS["text_muted"],
    "grid.color":        "#1e2535",                 # mpl-compat (was rgba border)
    "grid.alpha":        0.5,
    "text.color":        COLORS["text_secondary"],
    "axes.labelcolor":   COLORS["text_secondary"],
}

TIMEFRAME_DURATIONS = {
    "1 hour":  ("1 hour",  "2 M"),
    "2 hours": ("2 hours", "4 M"),
    "4 hours": ("4 hours", "6 M"),
    "1 day":   ("1 day",   "1 Y"),
}

INDICATOR_CHOICES = ["EMA", "Bollinger Bands", "VWAP", "None"]


class ChartWidget(QWidget):
    """Candlestick chart area with indicator overlays and sub-charts."""

    # Emitted when timeframe or indicator changes so parent can re-fetch data
    timeframe_changed = pyqtSignal(str, str)   # bar_size, duration
    indicator_changed = pyqtSignal(str)

    def __init__(self, symbol: str = "NQ", parent=None):
        super().__init__(parent)
        self.symbol = symbol
        self._df: pd.DataFrame = pd.DataFrame()
        self._indicators: dict = {}
        self._current_overlay = "EMA"
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        # ── Toolbar ──────────────────────────────────────────────
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)

        sym_label = QLabel(self.symbol)
        sym_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        sym_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        toolbar.addWidget(sym_label)

        toolbar.addStretch()

        # Timeframe combo
        tf_label = QLabel("Timeframe:")
        tf_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size:12px;")
        toolbar.addWidget(tf_label)
        
        self._tf_combo = QComboBox()
        self._tf_combo.addItems(list(TIMEFRAME_DURATIONS.keys()))
        self._tf_combo.setCurrentText("1 hour")
        self._tf_combo.setFixedWidth(100)
        self._tf_combo.currentTextChanged.connect(self._on_tf_changed)
        toolbar.addWidget(self._tf_combo)

        # Overlay selector
        toolbar.addSpacing(12)
        overlay_label = QLabel("Overlay:")
        overlay_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size:12px;")
        toolbar.addWidget(overlay_label)

        self._overlay_combo = QComboBox()
        self._overlay_combo.addItems(INDICATOR_CHOICES)
        self._overlay_combo.setFixedWidth(140)
        self._overlay_combo.currentTextChanged.connect(self._on_overlay_changed)
        toolbar.addWidget(self._overlay_combo)

        layout.addLayout(toolbar)

        # ── Matplotlib Canvas ─────────────────────────────────────
        self._figure = Figure(figsize=(10, 7), facecolor=COLORS["chart_bg"])
        self._canvas = FigureCanvasQTAgg(self._figure)
        self._canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self._canvas)

        self._draw_empty()

    def _on_tf_changed(self, tf: str):
        bar_size, duration = TIMEFRAME_DURATIONS[tf]
        self.timeframe_changed.emit(bar_size, duration)

    def _on_overlay_changed(self, text: str):
        self._current_overlay = text
        if not self._df.empty:
            self._draw_chart()
        self.indicator_changed.emit(text)

    def _draw_empty(self):
        self._figure.clear()
        ax = self._figure.add_subplot(111)
        ax.set_facecolor(COLORS["chart_bg"])
        ax.text(0.5, 0.5, "Connect to IBKR to load chart data",
                ha="center", va="center", fontsize=13,
                color=COLORS["text_muted"], transform=ax.transAxes)
        ax.set_xticks([]); ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_color("#1e2535")
        self._canvas.draw_idle()

    def update_data(self, df: pd.DataFrame, indicators: dict):
        """Called by parent to refresh chart with new OHLCV + indicator data."""
        self._df = df
        self._indicators = indicators
        if df.empty:
            self._draw_empty()
            return
        self._draw_chart()

    def _draw_chart(self):
        df = self._df.copy()
        if df.empty or len(df) < 2:
            return

        plt.rcParams.update(CHART_STYLE)
        self._figure.clear()

        # Create 3-panel grid: candles (4), RSI (1.5), MACD (1.5)
        gs = gridspec.GridSpec(3, 1, figure=self._figure,
                               height_ratios=[4, 1.5, 1.5],
                               hspace=0.04)
        ax_candle = self._figure.add_subplot(gs[0])
        ax_rsi    = self._figure.add_subplot(gs[1], sharex=ax_candle)
        ax_macd   = self._figure.add_subplot(gs[2], sharex=ax_candle)

        for ax in (ax_candle, ax_rsi, ax_macd):
            ax.set_facecolor(COLORS["chart_bg"])
            ax.tick_params(colors=COLORS["text_muted"], labelsize=9)
            for spine in ax.spines.values():
                spine.set_color("#1e2535")
            ax.grid(True, alpha=0.25, color="#1e2535")

        # ── Candlestick (manual) ──────────────────────────────────
        x = np.arange(len(df))
        w = 0.5
        for i, (idx, row) in enumerate(df.iterrows()):
            color = COLORS["green"] if row["Close"] >= row["Open"] else COLORS["red"]
            # Body
            ax_candle.add_patch(plt.Rectangle(
                (i - w/2, min(row["Open"], row["Close"])),
                w, abs(row["Close"] - row["Open"]),
                color=color, zorder=3
            ))
            # Wick
            ax_candle.plot([i, i], [row["Low"], row["High"]],
                           color=color, linewidth=0.8, zorder=2)

        ax_candle.set_xlim(-1, len(df))
        ax_candle.set_ylim(df["Low"].min() * 0.999, df["High"].max() * 1.001)

        # X tick labels (every N bars)
        step = max(1, len(df) // 8)
        tick_pos = x[::step]
        tick_lbl = [str(df.index[i])[:16] for i in tick_pos if i < len(df)]
        ax_macd.set_xticks(tick_pos)
        ax_macd.set_xticklabels(tick_lbl, rotation=30, ha="right", fontsize=8)
        plt.setp(ax_candle.get_xticklabels(), visible=False)
        plt.setp(ax_rsi.get_xticklabels(), visible=False)

        ax_candle.set_ylabel("Price", color=COLORS["text_secondary"], fontsize=9)
        ax_candle.set_title(f"{self.symbol}", color=COLORS["text_primary"],
                             fontsize=11, fontweight="bold", pad=6)

        # ── Overlays ──────────────────────────────────────────────
        if self._indicators:
            ema_colors = {9: "#f59e0b", 21: "#a78bfa", 50: "#60a5fa", 200: "#f472b6"}
            if self._current_overlay == "EMA":
                for period, color in ema_colors.items():
                    s = self._indicators.get("ema", {}).get(period)
                    if s is not None and not s.dropna().empty:
                        ax_candle.plot(x, s.values, color=color,
                                       linewidth=1.2, label=f"EMA{period}", zorder=4, alpha=0.85)
                ax_candle.legend(loc="upper left", fontsize=8,
                                 facecolor=COLORS["bg_panel"],
                                 labelcolor=COLORS["text_secondary"],
                                 edgecolor=COLORS["border"])

            elif self._current_overlay == "Bollinger Bands":
                bb = self._indicators.get("bollinger")
                if bb:
                    upper, mid, lower = bb
                    ax_candle.plot(x, upper.values, color="#a78bfa", linewidth=1, linestyle="--", alpha=0.7)
                    ax_candle.plot(x, mid.values,   color="#60a5fa", linewidth=1, alpha=0.7)
                    ax_candle.plot(x, lower.values, color="#a78bfa", linewidth=1, linestyle="--", alpha=0.7)
                    ax_candle.fill_between(x, lower.values, upper.values, alpha=0.05, color="#a78bfa")

            elif self._current_overlay == "VWAP":
                vwap = self._indicators.get("vwap")
                if vwap is not None and not vwap.dropna().empty:
                    ax_candle.plot(x, vwap.values, color="#f59e0b",
                                   linewidth=1.5, linestyle="--", label="VWAP", alpha=0.85)
                    ax_candle.legend(loc="upper left", fontsize=8,
                                     facecolor=COLORS["bg_panel"],
                                     labelcolor=COLORS["text_secondary"],
                                     edgecolor=COLORS["border"])

            # ── RSI ──────────────────────────────────────────────
            rsi = self._indicators.get("rsi")
            if rsi is not None and not rsi.dropna().empty:
                ax_rsi.plot(x, rsi.values, color=COLORS["accent"], linewidth=1.2)
                ax_rsi.axhline(70, color=COLORS["red"],   linewidth=0.7, linestyle="--", alpha=0.6)
                ax_rsi.axhline(30, color=COLORS["green"], linewidth=0.7, linestyle="--", alpha=0.6)
                ax_rsi.fill_between(x, rsi.values, 70, where=(rsi.values >= 70),
                                    color=COLORS["red"], alpha=0.15, interpolate=True)
                ax_rsi.fill_between(x, rsi.values, 30, where=(rsi.values <= 30),
                                    color=COLORS["green"], alpha=0.15, interpolate=True)
                ax_rsi.set_ylim(0, 100)
                ax_rsi.set_ylabel("RSI", color=COLORS["text_secondary"], fontsize=8)
                ax_rsi.yaxis.set_label_position("right")
                ax_rsi.yaxis.tick_right()

            # ── MACD ─────────────────────────────────────────────
            macd_data = self._indicators.get("macd")
            if macd_data:
                macd_line, sig_line, hist = macd_data
                hist_vals = hist.values
                colors_hist = [COLORS["green"] if v >= 0 else COLORS["red"]
                               for v in hist_vals]
                ax_macd.bar(x, hist_vals, color=colors_hist, alpha=0.6, width=0.6)
                ax_macd.plot(x, macd_line.values, color="#60a5fa", linewidth=1)
                ax_macd.plot(x, sig_line.values,  color="#f59e0b", linewidth=1)
                ax_macd.axhline(0, color=COLORS["text_muted"], linewidth=0.5, alpha=0.5)
                ax_macd.set_ylabel("MACD", color=COLORS["text_secondary"], fontsize=8)
                ax_macd.yaxis.set_label_position("right")
                ax_macd.yaxis.tick_right()

        self._figure.tight_layout(pad=0.5)
        self._canvas.draw_idle()
