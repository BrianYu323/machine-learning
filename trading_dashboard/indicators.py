"""
Technical Indicators — wraps the `stock_indicators` library.
All functions accept a pandas DataFrame with OHLCV columns and return
enriched DataFrames or Series ready for plotting.
"""
import math
import pandas as pd
import numpy as np
from typing import Optional

try:
    from stock_indicators import indicators, Quote
    HAS_STOCK_IND = True
except Exception:
    # stock_indicators requires .NET runtime via pythonnet which may not be
    # compatible with all Python versions. Fall back to pure numpy/pandas.
    HAS_STOCK_IND = False


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _to_quotes(df: pd.DataFrame) -> list:
    """Convert OHLCV DataFrame to stock_indicators Quote list."""
    quotes = []
    for ts, row in df.iterrows():
        try:
            q = Quote(
                date=pd.Timestamp(ts).to_pydatetime(),
                open=float(row.get("Open", 0) or 0),
                high=float(row.get("High", 0) or 0),
                low=float(row.get("Low", 0) or 0),
                close=float(row.get("Close", 0) or 0),
                volume=float(row.get("Volume", 0) or 0),
            )
            quotes.append(q)
        except Exception:
            pass
    return quotes


def _series_from(results, field: str, index) -> pd.Series:
    vals = [getattr(r, field, None) for r in results]
    return pd.Series(vals, index=index, name=field)


# ─── Fallback calculations (pure numpy) ───────────────────────────────────────

def _ema_fallback(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def _rsi_fallback(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _macd_fallback(series: pd.Series, fast=12, slow=26, signal=9):
    ema_fast = _ema_fallback(series, fast)
    ema_slow = _ema_fallback(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = _ema_fallback(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def _bollinger_fallback(series: pd.Series, period=20, mult=2.0):
    sma = series.rolling(period).mean()
    std = series.rolling(period).std()
    upper = sma + mult * std
    lower = sma - mult * std
    return upper, sma, lower


def _atr_fallback(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)
    return tr.ewm(span=period, adjust=False).mean()


# ─── Public Indicator Functions ───────────────────────────────────────────────

def get_ema(df: pd.DataFrame, periods: list[int] = [9, 21, 50, 200]) -> dict[int, pd.Series]:
    """Return dict of {period: EMA Series}."""
    result = {}
    if HAS_STOCK_IND and len(df) > 0:
        quotes = _to_quotes(df)
        for p in periods:
            try:
                res = indicators.get_ema(quotes, p)
                result[p] = _series_from(res, "ema", df.index)
            except Exception:
                result[p] = _ema_fallback(df["Close"], p)
    else:
        for p in periods:
            result[p] = _ema_fallback(df["Close"], p)
    return result


def get_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Return RSI Series."""
    if HAS_STOCK_IND and len(df) > 0:
        try:
            quotes = _to_quotes(df)
            res = indicators.get_rsi(quotes, period)
            return _series_from(res, "rsi", df.index)
        except Exception:
            pass
    return _rsi_fallback(df["Close"], period)


def get_macd(df: pd.DataFrame, fast=12, slow=26, signal=9) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Return (macd_line, signal_line, histogram)."""
    if HAS_STOCK_IND and len(df) > 0:
        try:
            quotes = _to_quotes(df)
            res = indicators.get_macd(quotes, fast, slow, signal)
            macd = _series_from(res, "macd", df.index)
            sig = _series_from(res, "signal", df.index)
            hist = _series_from(res, "histogram", df.index)
            return macd, sig, hist
        except Exception:
            pass
    return _macd_fallback(df["Close"], fast, slow, signal)


def get_bollinger(df: pd.DataFrame, period=20, mult=2.0) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Return (upper, middle/SMA, lower) Bollinger Bands."""
    if HAS_STOCK_IND and len(df) > 0:
        try:
            quotes = _to_quotes(df)
            res = indicators.get_bollinger_bands(quotes, period, mult)
            upper = _series_from(res, "upper_band", df.index)
            middle = _series_from(res, "sma", df.index)
            lower = _series_from(res, "lower_band", df.index)
            return upper, middle, lower
        except Exception:
            pass
    return _bollinger_fallback(df["Close"], period, mult)


def get_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Return ATR Series."""
    if HAS_STOCK_IND and len(df) > 0:
        try:
            quotes = _to_quotes(df)
            res = indicators.get_atr(quotes, period)
            return _series_from(res, "atr", df.index)
        except Exception:
            pass
    return _atr_fallback(df, period)


def get_vwap(df: pd.DataFrame) -> pd.Series:
    """Return VWAP Series (daily reset)."""
    # stock_indicators VWAP resets daily — use manual for intraday
    typical = (df["High"] + df["Low"] + df["Close"]) / 3
    cum_tp_vol = (typical * df["Volume"]).cumsum()
    cum_vol = df["Volume"].cumsum()
    return cum_tp_vol / cum_vol.replace(0, np.nan)


def get_supertrend(df: pd.DataFrame, period: int = 7, mult: float = 3.0) -> pd.Series:
    """Return Supertrend direction series (1 = bullish, -1 = bearish)."""
    if HAS_STOCK_IND and len(df) > 0:
        try:
            quotes = _to_quotes(df)
            res = indicators.get_super_trend(quotes, period, mult)
            direction = pd.Series(
                [1.0 if (getattr(r, "upper_band", None) is None) else -1.0 for r in res],
                index=df.index,
                name="supertrend_dir",
            )
            return direction
        except Exception:
            pass
    # Fallback: ATR-based computation
    atr = _atr_fallback(df, period)
    hl2 = (df["High"] + df["Low"]) / 2
    upper = hl2 + mult * atr
    lower = hl2 - mult * atr
    trend = pd.Series(1.0, index=df.index)
    for i in range(1, len(df)):
        if df["Close"].iloc[i] > upper.iloc[i - 1]:
            trend.iloc[i] = 1
        elif df["Close"].iloc[i] < lower.iloc[i - 1]:
            trend.iloc[i] = -1
        else:
            trend.iloc[i] = trend.iloc[i - 1]
    return trend


def compute_all(df: pd.DataFrame) -> dict:
    """Compute all indicators and return in one dict."""
    return {
        "ema": get_ema(df),
        "rsi": get_rsi(df),
        "macd": get_macd(df),
        "bollinger": get_bollinger(df),
        "atr": get_atr(df),
        "vwap": get_vwap(df),
        "supertrend": get_supertrend(df),
    }
