"""
IBKR Client - Manages connection to TWS/Gateway via ib_insync
Connection method mirrors fetch_NQ_data.py
"""
import asyncio
import logging
import time
from typing import Optional, Callable
import pandas as pd

# Fix for Python 3.10+: ib_insync requires an event loop at import time
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from ib_insync import IB, Future, util, MarketOrder, LimitOrder, Contract

logger = logging.getLogger(__name__)

# ─── Contract Definitions ─────────────────────────────────────────────────────
CONTRACTS = {
    "NQ": {"exchange": "CME",   "currency": "USD"},
    "CL": {"exchange": "NYMEX", "currency": "USD"},
    "SI": {"exchange": "COMEX", "currency": "USD"},
    "GC": {"exchange": "COMEX", "currency": "USD"},
}


class IBKRClient:
    """Wraps ib_insync IB() for the trading dashboard."""

    def __init__(self, host: str = "127.0.0.1", port: int = 7497, client_id: int = 11):
        self.host = host
        self.port = port
        self.client_id = client_id
        self.ib = IB()
        self._connected = False
        self._realtime_callbacks: dict[str, Callable] = {}
        self._contract_cache: dict[str, Contract] = {}

    # ── Connection ─────────────────────────────────────────────────────────────
    def connect(self) -> bool:
        try:
            self.ib.connect(self.host, self.port, clientId=self.client_id)
            self._connected = True
            logger.info("Connected to IBKR TWS/Gateway at %s:%s", self.host, self.port)
            return True
        except Exception as e:
            logger.error("Connection failed: %s", e)
            self._connected = False
            return False

    def disconnect(self):
        if self._connected:
            self.ib.disconnect()
            self._connected = False
            logger.info("Disconnected from IBKR.")

    @property
    def is_connected(self) -> bool:
        return self._connected and self.ib.isConnected()

    # ── Contract Helper ────────────────────────────────────────────────────────
    def get_contract(self, symbol: str) -> Optional[Contract]:
        """Dynamically fetches the front-month contract from IBKR for real-time and historical data."""
        if symbol in self._contract_cache:
            return self._contract_cache[symbol]

        cfg = CONTRACTS.get(symbol)
        if not cfg:
            logger.error("Unknown symbol: %s", symbol)
            return None
        
        from ib_insync import ContFuture
        cont_contract = ContFuture(
            symbol=symbol,
            exchange=cfg["exchange"],
            currency=cfg["currency"],
        )
        try:
            # reqContractDetails on a ContFuture returns the specific front-month Future contract!
            details = self.ib.reqContractDetails(cont_contract)
            if details:
                contract = details[0].contract
                self._contract_cache[symbol] = contract
                return contract
            else:
                logger.warning("No contract details returned for %s", symbol)
                return None
        except Exception as e:
            logger.warning("Could not resolve continuous contract %s: %s", symbol, e)
            return None

    # ── Historical Data ────────────────────────────────────────────────────────
    def fetch_historical_data(
        self,
        symbol: str,
        bar_size: str = "1 hour",
        duration: str = "1 M",
    ) -> pd.DataFrame:
        """Fetch historical OHLCV bars. Returns empty DataFrame on failure."""
        if not self.is_connected:
            logger.error("Not connected to IBKR.")
            return pd.DataFrame()

        contract = self.get_contract(symbol)
        if contract is None:
            return pd.DataFrame()

        try:
            bars = self.ib.reqHistoricalData(
                contract,
                endDateTime="",
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow="TRADES",
                useRTH=False,
                formatDate=1,
            )
            if not bars:
                return pd.DataFrame()
            df = util.df(bars)
            df.drop_duplicates(subset=["date"], inplace=True)
            df.sort_values("date", inplace=True)
            df.reset_index(drop=True, inplace=True)
            # Rename to standard OHLCV for mplfinance
            df.rename(columns={
                "open": "Open", "high": "High", "low": "Low",
                "close": "Close", "volume": "Volume", "date": "Date"
            }, inplace=True)
            df["Date"] = pd.to_datetime(df["Date"])
            df.set_index("Date", inplace=True)
            return df
        except Exception as e:
            logger.error("Failed to fetch historical data for %s: %s", symbol, e)
            return pd.DataFrame()

    def fetch_multi_batch(
        self,
        symbol: str,
        bar_size: str = "1 hour",
        total_months: int = 3,
    ) -> pd.DataFrame:
        """Multi-batch historical fetch (mirrors fetch_NQ_data.py logic)."""
        if not self.is_connected:
            return pd.DataFrame()

        contract = self.get_contract(symbol)
        if contract is None:
            return pd.DataFrame()

        end_date = ""
        all_bars = []
        for i in range(total_months):
            bars = self.ib.reqHistoricalData(
                contract,
                endDateTime=end_date,
                durationStr="1 M",
                barSizeSetting=bar_size,
                whatToShow="TRADES",
                useRTH=False,
                formatDate=1,
            )
            if not bars:
                break
            all_bars.extend(bars)
            end_date = bars[0].date
            time.sleep(2)

        if not all_bars:
            return pd.DataFrame()

        df = util.df(all_bars)
        df.drop_duplicates(subset=["date"], inplace=True)
        df.sort_values("date", inplace=True)
        df.reset_index(drop=True, inplace=True)
        df.rename(columns={
            "open": "Open", "high": "High", "low": "Low",
            "close": "Close", "volume": "Volume", "date": "Date"
        }, inplace=True)
        df["Date"] = pd.to_datetime(df["Date"])
        df.set_index("Date", inplace=True)
        return df

    # ── Real-Time Ticker ───────────────────────────────────────────────────────
    def subscribe_ticker(self, symbol: str, callback: Callable):
        """Subscribe to real-time market data. callback(symbol, ticker) called on update."""
        if not self.is_connected:
            return
        contract = self.get_contract(symbol)
        if contract is None:
            return
        ticker = self.ib.reqMktData(contract, "", False, False)

        def on_pending(tickers):
            for t in tickers:
                try:
                    callback(symbol, t)
                except Exception:
                    pass

        self.ib.pendingTickersEvent += on_pending
        self._realtime_callbacks[symbol] = on_pending

    def unsubscribe_ticker(self, symbol: str):
        cb = self._realtime_callbacks.pop(symbol, None)
        if cb:
            self.ib.pendingTickersEvent -= cb

    # ── Account Summary ────────────────────────────────────────────────────────
    def get_account_summary(self) -> dict:
        """Returns dict of key account values."""
        if not self.is_connected:
            return {}
        try:
            vals = self.ib.accountValues()
            result = {}
            for v in vals:
                if v.tag in ("NetLiquidation", "UnrealizedPnL", "RealizedPnL", "DayTradesRemaining"):
                    result[v.tag] = v.value
            return result
        except Exception as e:
            logger.error("Account summary error: %s", e)
            return {}

    def get_positions(self) -> list[dict]:
        """Returns list of open positions."""
        if not self.is_connected:
            return []
        try:
            positions = self.ib.positions()
            return [
                {
                    "symbol": p.contract.symbol,
                    "qty": p.position,
                    "avg_cost": p.avgCost,
                }
                for p in positions
            ]
        except Exception:
            return []

    # ── Order Placement ────────────────────────────────────────────────────────
    def place_order(
        self,
        symbol: str,
        direction: str,
        qty: int = 1,
        order_type: str = "MKT",
        limit_price: float = 0.0,
    ) -> Optional[object]:
        """Place a buy/sell order. direction: 'BUY' or 'SELL'."""
        if not self.is_connected:
            logger.error("Cannot place order: not connected.")
            return None
        contract = self.get_contract(symbol)
        if contract is None:
            return None
        if order_type == "MKT":
            order = MarketOrder(direction.upper(), qty)
        else:
            order = LimitOrder(direction.upper(), qty, limit_price)
        try:
            trade = self.ib.placeOrder(contract, order)
            logger.info("Order placed: %s %s %s @ %s", direction, qty, symbol, order_type)
            return trade
        except Exception as e:
            logger.error("Order placement failed: %s", e)
            return None
