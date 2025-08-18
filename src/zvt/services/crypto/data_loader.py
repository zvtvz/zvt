# -*- coding: utf-8 -*-
"""
Crypto Historical Data Loader Service
Handles batch loading of historical OHLCV and tick data from exchanges
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Callable
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

from zvt.contract import IntervalLevel
from zvt.domain.crypto import CryptoPair, CryptoPerp
from zvt.utils.time_utils import to_pd_timestamp, pd_is_not_null

logger = logging.getLogger(__name__)


class CryptoDataLoader:
    """
    Historical crypto data loading service with multi-exchange support
    
    Features:
    - Parallel data loading from multiple exchanges
    - Rate limit management and retry logic
    - Data validation and gap detection
    - Incremental updates and backfill
    - Progress tracking and error recovery
    """
    
    def __init__(
        self, 
        exchanges: List[str] = None,
        max_workers: int = 5,
        rate_limit_delay: float = 0.1,
        max_retries: int = 3,
        chunk_size: int = 1000,
        validation_enabled: bool = True
    ):
        self.exchanges = exchanges or ["binance", "okx", "bybit", "coinbase"]
        self.max_workers = max_workers
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self.chunk_size = chunk_size
        self.validation_enabled = validation_enabled
        
        # Exchange connectors will be initialized on demand
        self._connectors: Dict[str, object] = {}
        self._rate_limiters: Dict[str, float] = {}
        
        # Progress tracking
        self.progress_callback: Optional[Callable] = None
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "data_points_loaded": 0,
            "gaps_detected": 0,
            "validation_errors": 0
        }

    def load_historical_kdata(
        self,
        symbols: Union[str, List[str]],
        intervals: Union[IntervalLevel, List[IntervalLevel]],
        start_date: Union[str, datetime],
        end_date: Union[str, datetime] = None,
        exchanges: List[str] = None,
        entity_type: str = "cryptopair"
    ) -> Dict[str, pd.DataFrame]:
        """
        Load historical OHLCV data for specified symbols and intervals
        
        Args:
            symbols: Symbol or list of symbols (e.g., "BTC/USDT" or ["BTC/USDT", "ETH/USDT"])
            intervals: Interval or list of intervals to load
            start_date: Start date for historical data
            end_date: End date for historical data (default: now)
            exchanges: List of exchanges to use (default: all configured)
            entity_type: Type of entity ("cryptopair" or "cryptoperp")
            
        Returns:
            Dictionary mapping (exchange, symbol, interval) to DataFrame
        """
        logger.info(f"Starting historical data load for {symbols} on intervals {intervals}")
        
        # Normalize inputs
        if isinstance(symbols, str):
            symbols = [symbols]
        if isinstance(intervals, IntervalLevel):
            intervals = [intervals]
        if exchanges is None:
            exchanges = self.exchanges
            
        start_date = to_pd_timestamp(start_date)
        end_date = to_pd_timestamp(end_date) if end_date else pd.Timestamp.now()
        
        results = {}
        total_tasks = len(symbols) * len(intervals) * len(exchanges)
        completed_tasks = 0
        
        # Use ThreadPoolExecutor for parallel loading
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            
            for exchange in exchanges:
                for symbol in symbols:
                    for interval in intervals:
                        future = executor.submit(
                            self._load_symbol_interval,
                            exchange, symbol, interval, start_date, end_date, entity_type
                        )
                        futures.append((future, exchange, symbol, interval))
            
            # Collect results
            for future, exchange, symbol, interval in futures:
                try:
                    df = future.result()
                    if df is not None and not df.empty:
                        key = (exchange, symbol, interval.value)
                        results[key] = df
                        self.stats["data_points_loaded"] += len(df)
                        
                    completed_tasks += 1
                    if self.progress_callback:
                        self.progress_callback(completed_tasks, total_tasks)
                        
                except Exception as e:
                    logger.error(f"Failed to load {symbol} {interval.value} from {exchange}: {e}")
                    self.stats["failed_requests"] += 1
        
        logger.info(f"Historical data load completed. Loaded {len(results)} datasets")
        return results

    def _load_symbol_interval(
        self,
        exchange: str,
        symbol: str, 
        interval: IntervalLevel,
        start_date: pd.Timestamp,
        end_date: pd.Timestamp,
        entity_type: str
    ) -> Optional[pd.DataFrame]:
        """Load data for a specific symbol and interval from an exchange"""
        
        try:
            # Get exchange connector
            connector = self._get_connector(exchange)
            
            # Apply rate limiting
            self._apply_rate_limit(exchange)
            
            # Load data with retry logic
            df = None
            for attempt in range(self.max_retries + 1):
                try:
                    self.stats["total_requests"] += 1
                    
                    # Mock data loading - in real implementation, would call exchange API
                    df = self._mock_load_ohlcv(
                        connector, symbol, interval, start_date, end_date
                    )
                    
                    if df is not None and not df.empty:
                        self.stats["successful_requests"] += 1
                        break
                        
                except Exception as e:
                    if attempt < self.max_retries:
                        wait_time = (2 ** attempt) * self.rate_limit_delay
                        logger.warning(f"Attempt {attempt + 1} failed for {symbol}, retrying in {wait_time}s: {e}")
                        time.sleep(wait_time)
                    else:
                        raise e
            
            # Validate and process data
            if df is not None and not df.empty:
                df = self._validate_and_process_data(df, symbol, interval)
                
            return df
            
        except Exception as e:
            logger.error(f"Error loading {symbol} {interval.value} from {exchange}: {e}")
            return None

    def _mock_load_ohlcv(
        self,
        connector: object,
        symbol: str,
        interval: IntervalLevel,
        start_date: pd.Timestamp, 
        end_date: pd.Timestamp
    ) -> pd.DataFrame:
        """
        Mock OHLCV data loading - replace with real exchange API calls
        """
        # Generate mock data for testing
        freq_map = {
            IntervalLevel.LEVEL_1MIN: "1min",
            IntervalLevel.LEVEL_5MIN: "5min", 
            IntervalLevel.LEVEL_15MIN: "15min",
            IntervalLevel.LEVEL_30MIN: "30min",
            IntervalLevel.LEVEL_1HOUR: "1H",
            IntervalLevel.LEVEL_4HOUR: "4H",
            IntervalLevel.LEVEL_1DAY: "1D"
        }
        
        freq = freq_map.get(interval, "1H")
        timestamps = pd.date_range(start_date, end_date, freq=freq)
        
        if len(timestamps) == 0:
            return pd.DataFrame()
        
        # Generate realistic-looking crypto price data
        base_price = 45000.0 if "BTC" in symbol else 3000.0
        price_data = []
        
        current_price = base_price
        for ts in timestamps:
            # Random walk with volatility
            change = (pd.np.random.random() - 0.5) * 0.02  # ±1% moves
            current_price *= (1 + change)
            
            high = current_price * (1 + abs(change) * 0.5)
            low = current_price * (1 - abs(change) * 0.5)
            volume = pd.np.random.random() * 1000 + 100
            
            price_data.append({
                "timestamp": ts,
                "open": current_price,
                "high": high,
                "low": low, 
                "close": current_price,
                "volume": volume,
                "symbol": symbol,
                "exchange": connector.__class__.__name__.lower(),
                "interval": interval.value
            })
        
        return pd.DataFrame(price_data)

    def _validate_and_process_data(
        self,
        df: pd.DataFrame,
        symbol: str,
        interval: IntervalLevel
    ) -> pd.DataFrame:
        """Validate OHLCV data and detect gaps"""
        
        if not self.validation_enabled:
            return df
            
        original_len = len(df)
        
        # Basic OHLCV validation
        df = df[
            (df["high"] >= df[["open", "close", "low"]].max(axis=1)) &
            (df["low"] <= df[["open", "close", "high"]].min(axis=1)) &
            (df["volume"] >= 0)
        ]
        
        if len(df) < original_len:
            removed = original_len - len(df)
            self.stats["validation_errors"] += removed
            logger.warning(f"Removed {removed} invalid records from {symbol}")
        
        # Gap detection
        df = df.sort_values("timestamp")
        time_diffs = df["timestamp"].diff()
        
        # Expected interval duration
        interval_minutes = {
            IntervalLevel.LEVEL_1MIN: 1,
            IntervalLevel.LEVEL_5MIN: 5,
            IntervalLevel.LEVEL_15MIN: 15,
            IntervalLevel.LEVEL_30MIN: 30,
            IntervalLevel.LEVEL_1HOUR: 60,
            IntervalLevel.LEVEL_4HOUR: 240,
            IntervalLevel.LEVEL_1DAY: 1440
        }
        
        expected_delta = timedelta(minutes=interval_minutes.get(interval, 60))
        large_gaps = time_diffs > expected_delta * 2
        
        if large_gaps.any():
            gap_count = large_gaps.sum()
            self.stats["gaps_detected"] += gap_count
            logger.warning(f"Detected {gap_count} data gaps in {symbol}")
        
        return df

    def load_tick_data(
        self,
        symbols: Union[str, List[str]],
        start_date: Union[str, datetime],
        end_date: Union[str, datetime] = None,
        exchanges: List[str] = None,
        data_types: List[str] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Load tick-level data (trades, order book snapshots, funding rates)
        
        Args:
            symbols: Symbol or list of symbols
            start_date: Start date for tick data
            end_date: End date for tick data
            exchanges: List of exchanges to use
            data_types: Types of tick data ["trades", "orderbook", "funding"]
            
        Returns:
            Dictionary mapping (exchange, symbol, data_type) to DataFrame
        """
        logger.info(f"Loading tick data for {symbols}")
        
        if isinstance(symbols, str):
            symbols = [symbols]
        if exchanges is None:
            exchanges = self.exchanges
        if data_types is None:
            data_types = ["trades", "orderbook"]
            
        start_date = to_pd_timestamp(start_date)
        end_date = to_pd_timestamp(end_date) if end_date else pd.Timestamp.now()
        
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            
            for exchange in exchanges:
                for symbol in symbols:
                    for data_type in data_types:
                        future = executor.submit(
                            self._load_tick_data,
                            exchange, symbol, data_type, start_date, end_date
                        )
                        futures.append((future, exchange, symbol, data_type))
            
            for future, exchange, symbol, data_type in futures:
                try:
                    df = future.result()
                    if df is not None and not df.empty:
                        key = (exchange, symbol, data_type)
                        results[key] = df
                        self.stats["data_points_loaded"] += len(df)
                except Exception as e:
                    logger.error(f"Failed to load {data_type} for {symbol} from {exchange}: {e}")
        
        return results

    def _load_tick_data(
        self,
        exchange: str,
        symbol: str,
        data_type: str, 
        start_date: pd.Timestamp,
        end_date: pd.Timestamp
    ) -> Optional[pd.DataFrame]:
        """Load specific type of tick data"""
        
        connector = self._get_connector(exchange)
        self._apply_rate_limit(exchange)
        
        # Mock tick data - replace with real implementation
        if data_type == "trades":
            return self._mock_trade_data(symbol, start_date, end_date)
        elif data_type == "orderbook":
            return self._mock_orderbook_data(symbol, start_date, end_date)
        elif data_type == "funding":
            return self._mock_funding_data(symbol, start_date, end_date)
        
        return None

    def _mock_trade_data(self, symbol: str, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
        """Generate mock trade data"""
        # Generate trades every few seconds
        timestamps = pd.date_range(start, end, freq="5S")[:1000]  # Limit for demo
        
        trades = []
        price = 45000.0 if "BTC" in symbol else 3000.0
        
        for ts in timestamps:
            price *= (1 + (pd.np.random.random() - 0.5) * 0.001)  # Small price moves
            size = pd.np.random.random() * 10
            side = "buy" if pd.np.random.random() > 0.5 else "sell"
            
            trades.append({
                "timestamp": ts,
                "symbol": symbol,
                "price": price,
                "size": size,
                "side": side,
                "trade_id": f"trade_{len(trades)}"
            })
        
        return pd.DataFrame(trades)

    def _mock_orderbook_data(self, symbol: str, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
        """Generate mock order book snapshots"""
        timestamps = pd.date_range(start, end, freq="1min")[:100]  # Limit for demo
        
        snapshots = []
        mid_price = 45000.0 if "BTC" in symbol else 3000.0
        
        for ts in timestamps:
            mid_price *= (1 + (pd.np.random.random() - 0.5) * 0.001)
            
            # Generate 5 levels each side
            bids = []
            asks = []
            
            for i in range(5):
                bid_price = mid_price * (1 - (i + 1) * 0.0001)
                ask_price = mid_price * (1 + (i + 1) * 0.0001)
                size = pd.np.random.random() * 100
                
                bids.append({"price": bid_price, "size": size})
                asks.append({"price": ask_price, "size": size})
            
            snapshots.append({
                "timestamp": ts,
                "symbol": symbol,
                "bids": bids,
                "asks": asks,
                "mid_price": mid_price
            })
        
        return pd.DataFrame(snapshots)

    def _mock_funding_data(self, symbol: str, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
        """Generate mock funding rate data (for perpetuals)"""
        # Funding rates every 8 hours
        timestamps = pd.date_range(start, end, freq="8H")
        
        funding_rates = []
        for ts in timestamps:
            rate = (pd.np.random.random() - 0.5) * 0.0001  # ±0.01%
            
            funding_rates.append({
                "timestamp": ts,
                "symbol": symbol,
                "funding_rate": rate,
                "next_funding_time": ts + timedelta(hours=8)
            })
        
        return pd.DataFrame(funding_rates)

    def _get_connector(self, exchange: str) -> object:
        """Get or create exchange connector"""
        if exchange not in self._connectors:
            # Mock connector creation - replace with real exchange clients
            self._connectors[exchange] = type(f"{exchange.title()}Connector", (), {})()
        return self._connectors[exchange]

    def _apply_rate_limit(self, exchange: str):
        """Apply rate limiting per exchange"""
        now = time.time()
        if exchange in self._rate_limiters:
            elapsed = now - self._rate_limiters[exchange]
            if elapsed < self.rate_limit_delay:
                time.sleep(self.rate_limit_delay - elapsed)
        
        self._rate_limiters[exchange] = time.time()

    def set_progress_callback(self, callback: Callable[[int, int], None]):
        """Set callback function for progress updates"""
        self.progress_callback = callback

    def get_loading_stats(self) -> Dict:
        """Get loading statistics"""
        return self.stats.copy()

    def reset_stats(self):
        """Reset loading statistics"""
        for key in self.stats:
            self.stats[key] = 0

    async def load_historical_async(self, *args, **kwargs):
        """Async version of historical data loading"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.load_historical_kdata, *args, **kwargs)