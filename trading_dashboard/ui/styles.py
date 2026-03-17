"""
Liquid Glass Dark Theme — QSS Stylesheet
Inspired by Stitch MCP "Trading Dashboard - Liquid Glass" design.
Color palette: deep navy bg, electric blue #0d59f2 accent, glass panels.
"""

# ─── Color Tokens ─────────────────────────────────────────────────────────────
COLORS = {
    "bg_primary":    "#0a0e1a",
    "bg_secondary":  "#0d1220",
    "bg_panel":      "#111827",
    "bg_sidebar":    "#080c17",
    "glass":         "rgba(255,255,255,0.05)",
    "glass_border":  "rgba(255,255,255,0.08)",
    "accent":        "#0d59f2",
    "accent_hover":  "#1a6aff",
    "accent_glow":   "rgba(13,89,242,0.3)",
    "green":         "#00d492",
    "red":           "#ff4560",
    "text_primary":  "#e8eaf0",
    "text_secondary":"#8892aa",
    "text_muted":    "#4a5568",
    "border":        "rgba(255,255,255,0.06)",
    "chart_bg":      "#080c14",
}

MAIN_STYLESHEET = f"""
/* ──────────────────────────────────────────────────────
   Global
────────────────────────────────────────────────────── */
* {{
    font-family: "Segoe UI", "Inter", "Space Grotesk", sans-serif;
    color: {COLORS["text_primary"]};
    outline: none;
}}

QMainWindow, QDialog {{
    background-color: {COLORS["bg_primary"]};
}}

QWidget {{
    background-color: transparent;
}}

QScrollArea {{
    border: none;
    background-color: transparent;
}}

QScrollBar:vertical {{
    background: {COLORS["bg_primary"]};
    width: 6px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {COLORS["text_muted"]};
    border-radius: 3px;
    min-height: 30px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: {COLORS["bg_primary"]};
    height: 6px;
}}
QScrollBar::handle:horizontal {{
    background: {COLORS["text_muted"]};
    border-radius: 3px;
}}

/* ──────────────────────────────────────────────────────
   Sidebar
────────────────────────────────────────────────────── */
#Sidebar {{
    background-color: {COLORS["bg_sidebar"]};
    border-right: 1px solid {COLORS["border"]};
    min-width: 64px;
    max-width: 64px;
}}

#SidebarBtn {{
    background: transparent;
    border: none;
    border-radius: 12px;
    padding: 10px;
    margin: 4px 8px;
    font-size: 22px;
    color: {COLORS["text_muted"]};
}}
#SidebarBtn:hover {{
    background: rgba(13,89,242,0.15);
    color: {COLORS["accent"]};
}}
#SidebarBtn[active="true"] {{
    background: rgba(13,89,242,0.2);
    color: {COLORS["accent"]};
    border-left: 3px solid {COLORS["accent"]};
}}

#AppTitle {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2px;
    color: {COLORS["accent"]};
    padding: 16px 8px;
}}

/* ──────────────────────────────────────────────────────
   Glass Panels
────────────────────────────────────────────────────── */
#GlassPanel {{
    background: rgba(17,24,39,0.85);
    border: 1px solid {COLORS["glass_border"]};
    border-radius: 16px;
}}

#SectionLabel {{
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1.5px;
    color: {COLORS["text_secondary"]};
    padding: 4px 0;
    text-transform: uppercase;
}}

/* ──────────────────────────────────────────────────────
   Header Bar
────────────────────────────────────────────────────── */
#HeaderBar {{
    background: rgba(8,12,23,0.95);
    border-bottom: 1px solid {COLORS["border"]};
    min-height: 52px;
    max-height: 52px;
}}
#HeaderTitle {{
    font-size: 18px;
    font-weight: 700;
    letter-spacing: 0.5px;
    color: {COLORS["text_primary"]};
}}
#ConnectionStatus {{
    font-size: 12px;
    font-weight: 600;
    padding: 4px 12px;
    border-radius: 20px;
}}
#ConnectionStatus[status="connected"] {{
    color: {COLORS["green"]};
    background: rgba(0,212,146,0.12);
    border: 1px solid rgba(0,212,146,0.25);
}}
#ConnectionStatus[status="disconnected"] {{
    color: {COLORS["red"]};
    background: rgba(255,69,96,0.12);
    border: 1px solid rgba(255,69,96,0.25);
}}

/* ──────────────────────────────────────────────────────
   Buttons
────────────────────────────────────────────────────── */
#AccentBtn {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {COLORS["accent"]}, stop:1 #1a6aff);
    border: none;
    border-radius: 10px;
    padding: 8px 20px;
    font-size: 13px;
    font-weight: 700;
    color: white;
}}
#AccentBtn:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #1a6aff, stop:1 #2a7aff);
}}
#AccentBtn:pressed {{
    background: {COLORS["accent"]};
}}

#BuyBtn {{
    background: rgba(0,212,146,0.15);
    border: 1px solid rgba(0,212,146,0.4);
    border-radius: 10px;
    padding: 10px 0;
    font-size: 14px;
    font-weight: 700;
    color: {COLORS["green"]};
}}
#BuyBtn:hover {{
    background: rgba(0,212,146,0.28);
}}
#BuyBtn:checked {{
    background: {COLORS["green"]};
    color: #001a0e;
}}

#SellBtn {{
    background: rgba(255,69,96,0.15);
    border: 1px solid rgba(255,69,96,0.4);
    border-radius: 10px;
    padding: 10px 0;
    font-size: 14px;
    font-weight: 700;
    color: {COLORS["red"]};
}}
#SellBtn:hover {{
    background: rgba(255,69,96,0.28);
}}
#SellBtn:checked {{
    background: {COLORS["red"]};
    color: white;
}}

#SubmitBtn {{
    border-radius: 10px;
    padding: 12px 0;
    font-size: 14px;
    font-weight: 700;
}}
#SubmitBtn[direction="BUY"] {{
    background: {COLORS["green"]};
    color: #001a0e;
    border: none;
}}
#SubmitBtn[direction="SELL"] {{
    background: {COLORS["red"]};
    color: white;
    border: none;
}}

/* ──────────────────────────────────────────────────────
   Inputs
────────────────────────────────────────────────────── */
QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit {{
    background: rgba(255,255,255,0.05);
    border: 1px solid {COLORS["glass_border"]};
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 13px;
    color: {COLORS["text_primary"]};
    selection-background-color: {COLORS["accent"]};
}}
QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus {{
    border: 1px solid {COLORS["accent"]};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {COLORS["text_secondary"]};
    margin-right: 6px;
}}
QComboBox QAbstractItemView {{
    background: {COLORS["bg_panel"]};
    border: 1px solid {COLORS["glass_border"]};
    border-radius: 8px;
    padding: 4px;
    selection-background-color: {COLORS["accent"]};
}}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    background: rgba(255,255,255,0.06);
    border: none;
    border-radius: 4px;
    width: 18px;
}}

/* ──────────────────────────────────────────────────────
   Tab Bar (symbol tabs)
────────────────────────────────────────────────────── */
QTabWidget::pane {{
    border: none;
    background: transparent;
}}
QTabBar::tab {{
    background: transparent;
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 6px 18px;
    margin: 2px 3px;
    font-size: 13px;
    font-weight: 600;
    color: {COLORS["text_secondary"]};
}}
QTabBar::tab:selected {{
    background: rgba(13,89,242,0.2);
    border: 1px solid rgba(13,89,242,0.5);
    color: {COLORS["accent"]};
}}
QTabBar::tab:hover:!selected {{
    background: rgba(255,255,255,0.04);
    color: {COLORS["text_primary"]};
}}

/* ──────────────────────────────────────────────────────
   Table (Watchlist / Positions)
────────────────────────────────────────────────────── */
QTableWidget {{
    background: transparent;
    border: none;
    gridline-color: {COLORS["border"]};
    font-size: 13px;
}}
QTableWidget::item {{
    padding: 6px 10px;
    border: none;
}}
QTableWidget::item:selected {{
    background: rgba(13,89,242,0.15);
    color: {COLORS["text_primary"]};
}}
QHeaderView::section {{
    background: rgba(255,255,255,0.04);
    border: none;
    border-bottom: 1px solid {COLORS["border"]};
    padding: 6px 10px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1px;
    color: {COLORS["text_muted"]};
    text-transform: uppercase;
}}

/* ──────────────────────────────────────────────────────
   Status Bar
────────────────────────────────────────────────────── */
QStatusBar {{
    background: {COLORS["bg_sidebar"]};
    border-top: 1px solid {COLORS["border"]};
    font-size: 12px;
    color: {COLORS["text_secondary"]};
}}

/* ──────────────────────────────────────────────────────
   Labels
────────────────────────────────────────────────────── */
#PriceLabel {{
    font-size: 28px;
    font-weight: 800;
    letter-spacing: -0.5px;
    color: {COLORS["text_primary"]};
}}
#ChangeLabel {{
    font-size: 14px;
    font-weight: 600;
    padding: 2px 10px;
    border-radius: 6px;
}}
#ChangeLabel[positive="true"] {{
    color: {COLORS["green"]};
    background: rgba(0,212,146,0.1);
}}
#ChangeLabel[positive="false"] {{
    color: {COLORS["red"]};
    background: rgba(255,69,96,0.1);
}}

#AccountValue {{
    font-size: 24px;
    font-weight: 800;
    color: {COLORS["text_primary"]};
}}
#PnlPositive {{
    font-size: 14px;
    font-weight: 600;
    color: {COLORS["green"]};
}}
#PnlNegative {{
    font-size: 14px;
    font-weight: 600;
    color: {COLORS["red"]};
}}

QLabel#StatLabel {{
    font-size: 11px;
    color: {COLORS["text_secondary"]};
}}

QLabel#StatValue {{
    font-size: 13px;
    font-weight: 600;
    color: {COLORS["text_primary"]};
}}

/* ──────────────────────────────────────────────────────
   Separators
────────────────────────────────────────────────────── */
QFrame[frameShape="4"], QFrame[frameShape="5"] {{
    color: {COLORS["border"]};
}}
"""
