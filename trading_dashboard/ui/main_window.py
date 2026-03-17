"""
Main Window — TradingPro Liquid Glass Edition
Full desktop trading dashboard with sidebar, chart tabs, watchlist, order panel & account.
"""
import sys
import os
import glob
import logging
import pandas as pd
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QTabWidget, QScrollArea,
    QSplitter, QStatusBar, QFrame, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QFont, QIcon, QColor

from trading_dashboard.ui.styles import MAIN_STYLESHEET, COLORS
from trading_dashboard.ui.chart_widget import ChartWidget
from trading_dashboard.ui.watchlist_widget import WatchlistWidget
from trading_dashboard.ui.order_widget import OrderWidget
from trading_dashboard.ui.account_widget import AccountWidget
from trading_dashboard.ibkr_client import IBKRClient
from trading_dashboard import indicators as ind

logger = logging.getLogger(__name__)

SYMBOLS = ["NQ", "CL", "SI", "GC"]

# ─── Data Fetching ────────────────────────────────────────────────────────────
# ─── Sidebar Button ──────────────────────────────────────────────────────────

class SidebarButton(QPushButton):
    def __init__(self, emoji: str, tooltip: str, parent=None):
        super().__init__(emoji, parent)
        self.setObjectName("SidebarBtn")
        self.setToolTip(tooltip)
        self.setCheckable(True)
        self.setFixedSize(48, 48)
        self.setFont(QFont("Segoe UI Emoji", 18))


# ─── Glass Panel ─────────────────────────────────────────────────────────────

class GlassPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("GlassPanel")


# ─── Main Window ─────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TradingPro · Liquid Glass Edition")
        self.resize(1600, 960)
        self.setMinimumSize(1200, 700)

        self._client = IBKRClient()
        self._symbol_dfs: dict[str, object] = {}
        self._current_tf: dict[str, tuple[str, str]] = {s: ("1 hour", "2 M") for s in SYMBOLS}

        self.setStyleSheet(MAIN_STYLESHEET)
        self._build_ui()
        self._setup_statusbar()
        self._start_account_timer()

    # ── UI Construction ───────────────────────────────────────────────────────
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar
        sidebar = self._build_sidebar()
        root.addWidget(sidebar)

        # Main content
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        header = self._build_header()
        content_layout.addWidget(header)

        # Body splitter: charts | right pane
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(2)
        splitter.setStyleSheet(f"QSplitter::handle {{ background: {COLORS['border']}; }}")

        charts_area = self._build_charts_area()
        right_panel  = self._build_right_panel()

        splitter.addWidget(charts_area)
        splitter.addWidget(right_panel)
        splitter.setSizes([1100, 420])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)

        content_layout.addWidget(splitter, stretch=1)

        content_widget = QWidget()
        content_widget.setLayout(content_layout)
        root.addWidget(content_widget, stretch=1)

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(64)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        logo = QLabel("TP")
        logo.setObjectName("AppTitle")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        layout.addWidget(logo)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {COLORS['border']}; margin: 4px 8px;")
        layout.addWidget(sep)

        self._nav_btns: dict[str, SidebarButton] = {}
        nav_items = [
            ("📊", "Dashboard"),
            ("📈", "Markets"),
            ("🕐", "History"),
            ("👤", "Account"),
            ("⚙️", "Settings"),
        ]
        for emoji, name in nav_items:
            btn = SidebarButton(emoji, name)
            btn.clicked.connect(lambda _, n=name: self._on_nav(n))
            layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignHCenter)
            self._nav_btns[name] = btn

        self._nav_btns["Dashboard"].setChecked(True)
        layout.addStretch()
        return sidebar

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("HeaderBar")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(20, 0, 20, 0)

        title = QLabel("TradingPro · IBKR Dashboard")
        title.setObjectName("HeaderTitle")
        hl.addWidget(title)
        hl.addStretch()

        self._conn_status = QLabel("⬤  Disconnected")
        self._conn_status.setObjectName("ConnectionStatus")
        self._conn_status.setProperty("status", "disconnected")
        hl.addWidget(self._conn_status)

        self._connect_btn = QPushButton("Connect to IBKR")
        self._connect_btn.setObjectName("AccentBtn")
        self._connect_btn.setFixedHeight(32)
        self._connect_btn.clicked.connect(self._on_connect_toggle)
        hl.addWidget(self._connect_btn)

        return header

    def _build_charts_area(self) -> QWidget:
        area = QWidget()
        area.setStyleSheet(f"background: {COLORS['bg_primary']};")
        layout = QVBoxLayout(area)
        layout.setContentsMargins(12, 12, 6, 12)
        layout.setSpacing(0)

        self._tabs = QTabWidget()
        self._chart_widgets: dict[str, ChartWidget] = {}

        for symbol in SYMBOLS:
            cw = ChartWidget(symbol)
            cw.timeframe_changed.connect(
                lambda bs, dur, s=symbol: self._on_timeframe_changed(s, bs, dur)
            )
            self._chart_widgets[symbol] = cw
            self._tabs.addTab(cw, symbol)
            
        self._tabs.currentChanged.connect(self._on_tab_changed)

        layout.addWidget(self._tabs)
        return area

    def _build_right_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet(f"background: {COLORS['bg_secondary']};")
        panel.setFixedWidth(400)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # ── Watchlist ─────────────────────────────────────────────
        watch_panel = GlassPanel()
        wl = QVBoxLayout(watch_panel)
        wl.setContentsMargins(14, 12, 14, 12)
        self._watchlist = WatchlistWidget()
        wl.addWidget(self._watchlist)
        layout.addWidget(watch_panel)

        # ── Order Entry ───────────────────────────────────────────
        order_panel = GlassPanel()
        ol = QVBoxLayout(order_panel)
        ol.setContentsMargins(14, 12, 14, 12)
        self._order_widget = OrderWidget()
        self._order_widget.order_submitted.connect(self._on_order_submitted)
        ol.addWidget(self._order_widget)
        layout.addWidget(order_panel)

        # ── Account ───────────────────────────────────────────────
        account_panel = GlassPanel()
        al = QVBoxLayout(account_panel)
        al.setContentsMargins(14, 12, 14, 12)
        self._account_widget = AccountWidget()
        al.addWidget(self._account_widget)
        layout.addWidget(account_panel)

        return panel

    def _setup_statusbar(self):
        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)
        self._statusbar.showMessage("Ready  ·  Not connected to IBKR TWS")

    def _start_account_timer(self):
        self._acc_timer = QTimer(self)
        self._acc_timer.timeout.connect(self._refresh_account)
        self._acc_timer.start(15000)  # every 15s

    # ── Connection ────────────────────────────────────────────────────────────
    def _on_connect_toggle(self):
        if self._client.is_connected:
            self._client.disconnect()
            self._set_disconnected()
        else:
            self._connect_btn.setEnabled(False)
            self._connect_btn.setText("Connecting…")
            ok = self._client.connect()
            if ok:
                self._set_connected()
                self._load_active_symbol()
            else:
                self._set_disconnected()
                self._statusbar.showMessage("⚠️  Connection failed — is IBKR TWS running on port 7497?")
            self._connect_btn.setEnabled(True)

    def _set_connected(self):
        self._conn_status.setText("⬤  Connected")
        self._conn_status.setProperty("status", "connected")
        self._conn_status.style().unpolish(self._conn_status)
        self._conn_status.style().polish(self._conn_status)
        self._connect_btn.setText("Disconnect")
        self._statusbar.showMessage("✅ Connected to IBKR TWS  ·  Fetching data…")

    def _set_disconnected(self):
        self._conn_status.setText("⬤  Disconnected")
        self._conn_status.setProperty("status", "disconnected")
        self._conn_status.style().unpolish(self._conn_status)
        self._conn_status.style().polish(self._conn_status)
        self._connect_btn.setText("Connect to IBKR")
        self._statusbar.showMessage("Disconnected from IBKR")

    # ── Data Loading ──────────────────────────────────────────────────────────
    def _load_active_symbol(self):
        idx = self._tabs.currentIndex()
        if idx >= 0:
            symbol = SYMBOLS[idx]
            bs, dur = self._current_tf[symbol]
            self._fetch_symbol(symbol, bs, dur)
            QApplication.processEvents()

    def _on_tab_changed(self, index: int):
        if self._client.is_connected and index >= 0:
            symbol = SYMBOLS[index]
            # Only fetch if we haven't already for this session, or if you want it to refresh every time:
            if symbol not in self._symbol_dfs or self._symbol_dfs[symbol].empty:
                bs, dur = self._current_tf[symbol]
                self._fetch_symbol(symbol, bs, dur)

    def _fetch_symbol(self, symbol: str, bar_size: str, duration: str):
        if not self._client.is_connected:
            # Fallback constraint for offline CSV
            import os, glob, pandas as pd
            from trading_dashboard import indicators as ind
            try:
                # Look for matching offline CSV in the symbol's directory
                cwd = os.getcwd() # c:\Users\brian\Desktop\machine learning
                bs_clean = bar_size.replace(" ", "")
                pattern = os.path.join(cwd, symbol, f"{symbol}_*_{bs_clean}_historical.csv")
                matches = glob.glob(pattern)
                if not matches:
                    pattern_any = os.path.join(cwd, symbol, f"{symbol}_*_historical.csv")
                    matches = glob.glob(pattern_any)

                if matches:
                    df = pd.read_csv(matches[0])
                    # standardizing column names
                    cols = {c: c.capitalize() for c in df.columns if c.lower() in ("open", "high", "low", "close", "volume", "date")}
                    df.rename(columns=cols, inplace=True)
                    if "Date" in df.columns:
                        df["Date"] = pd.to_datetime(df["Date"])
                        df.set_index("Date", inplace=True)
                    
                    indic = ind.compute_all(df)
                    self._on_data_ready(symbol, df, indic)
                    self._statusbar.showMessage(f"Offline Mode: Loaded {symbol} from {os.path.basename(matches[0])}")
            except Exception as e:
                # Assuming 'logger' is defined elsewhere or will be handled by the user
                # For this response, I'll include it as provided in the instruction.
                logger.error(f"Failed to load offline data for {symbol}: {e}")
            return

        self._statusbar.showMessage(f"Fetching {symbol} data ({bar_size}, {duration})…")
        QApplication.processEvents()
        
        try:
            df = self._client.fetch_historical_data(symbol, bar_size, duration)
            if df.empty:
                self._on_data_error(symbol, "No data returned from IBKR.")
                return
            
            # Ensure proper typing for Matplotlib candlestick chart
            for col in ["Open", "High", "Low", "Close", "Volume"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            df.dropna(subset=["Close"], inplace=True)

            indic = ind.compute_all(df)
            self._on_data_ready(symbol, df, indic)
        except Exception as e:
            self._on_data_error(symbol, str(e))

    def _on_data_ready(self, symbol: str, df, indicator_dict: dict):
        self._symbol_dfs[symbol] = df
        cw = self._chart_widgets.get(symbol)
        if cw:
            cw.update_data(df, indicator_dict)
        self._watchlist.update_from_historical(symbol, df)
        self._statusbar.showMessage(f"✅  {symbol}: {len(df)} bars loaded")

    def _on_data_error(self, symbol: str, message: str):
        self._statusbar.showMessage(f"⚠️  {symbol} error: {message}")

    def _on_timeframe_changed(self, symbol: str, bar_size: str, duration: str):
        self._current_tf[symbol] = (bar_size, duration)
        self._fetch_symbol(symbol, bar_size, duration)

    # ── Account Refresh ───────────────────────────────────────────────────────
    def _refresh_account(self):
        if not self._client.is_connected:
            return
        summary   = self._client.get_account_summary()
        positions = self._client.get_positions()
        self._account_widget.update_account(summary)
        self._account_widget.update_positions(positions)

    # ── Order Submission ──────────────────────────────────────────────────────
    def _on_order_submitted(self, symbol: str, direction: str, qty: int, otype: str, price: float):
        trade = self._client.place_order(symbol, direction, qty, otype, price)
        if trade:
            self._statusbar.showMessage(
                f"📤 Order sent: {direction} {qty}×{symbol} @{otype}"
            )
        else:
            self._statusbar.showMessage("❌ Order failed — check connection.")

    # ── Navigation ────────────────────────────────────────────────────────────
    def _on_nav(self, name: str):
        for n, btn in self._nav_btns.items():
            btn.setChecked(n == name)
            btn.setProperty("active", "true" if n == name else "false")
            btn.style().unpolish(btn); btn.style().polish(btn)

    # ── Cleanup ───────────────────────────────────────────────────────────────
    def closeEvent(self, event):
        self._acc_timer.stop()
        self._client.disconnect()
        event.accept()
