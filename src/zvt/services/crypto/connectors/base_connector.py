# -*- coding: utf-8 -*-
"""
Base Crypto Exchange Connector
Defines the unified interface for all crypto exchange implementations
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Callable, Any, Union
from datetime import datetime, timedelta
import pandas as pd
import websocket
import json

from zvt.contract import IntervalLevel
from zvt.utils.time_utils import to_pd_timestamp

logger = logging.getLogger(__name__)


class BaseCryptoConnector(ABC):
    """
    Abstract base class for all crypto exchange connectors
    
    Provides unified interface for:
    - REST API operations (historical data, symbols, etc.)
    - WebSocket streaming (real-time data)
    - Rate limiting and error handling
    - Data normalization across exchanges
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        testnet: bool = True,
        rate_limit: float = 0.1
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.rate_limit = rate_limit
        
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        
        # Rate limiting
        self._last_request_time = 0
        self._request_count = 0
        
        # Connection state
        self._ws_connections: Dict[str, websocket.WebSocket] = {}
        self._is_connected = False
        
        # Statistics
        self.stats = {
            "requests_made": 0,
            "requests_failed": 0,
            "ws_messages_received": 0,
            "ws_reconnections": 0,
            "last_error": None
        }
    
    # Abstract methods that must be implemented by each exchange
    
    @abstractmethod
    def get_exchange_name(self) -> str:
        """Return the exchange name (e.g., 'binance', 'okx')"""
        pass
    
    @abstractmethod
    def get_symbols(self) -> List[Dict[str, Any]]:
        """Get all available trading symbols from the exchange"""
        pass
    
    @abstractmethod
    def get_ohlcv(
        self, 
        symbol: str, 
        interval: str, 
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> pd.DataFrame:
        """Get OHLCV data for a symbol and interval"""
        pass
    
    @abstractmethod
    def get_trades(
        self, 
        symbol: str, 
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> pd.DataFrame:
        """Get historical trades for a symbol"""
        pass
    
    @abstractmethod
    def get_orderbook(self, symbol: str, depth: int = 100) -> Dict[str, Any]:
        """Get current orderbook snapshot"""
        pass
    
    @abstractmethod
    def subscribe_ticker(self, symbols: List[str], callback: Callable):
        """Subscribe to real-time ticker updates"""
        pass
    
    @abstractmethod
    def subscribe_klines(self, symbols: List[str], intervals: List[str], callback: Callable):
        """Subscribe to real-time kline/candlestick updates"""
        pass
    
    @abstractmethod
    def subscribe_trades(self, symbols: List[str], callback: Callable):
        """Subscribe to real-time trade updates"""
        pass
    
    @abstractmethod
    def subscribe_orderbook(self, symbols: List[str], callback: Callable):
        """Subscribe to real-time orderbook updates"""
        pass
    
    # Common utility methods
    
    def _apply_rate_limit(self):
        """Apply rate limiting to prevent API throttling"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self.rate_limit:
            sleep_time = self.rate_limit - time_since_last
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
        self._request_count += 1
    
    def _handle_api_error(self, error: Exception, operation: str):
        """Handle API errors with logging and statistics"""
        self.stats["requests_failed"] += 1
        self.stats["last_error"] = str(error)
        
        self.logger.error(f"API error in {operation}: {error}")
        
        # Could implement retry logic here
        raise error
    
    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol format for this exchange"""
        # Default implementation - override in subclasses
        return symbol.upper().replace("/", "")
    
    def denormalize_symbol(self, symbol: str) -> str:
        """Convert exchange symbol back to standard format"""
        # Default implementation - override in subclasses  
        if len(symbol) >= 6:
            return f"{symbol[:-4]}/{symbol[-4:]}"
        return symbol
    
    def normalize_interval(self, interval: Union[str, IntervalLevel]) -> str:
        """Convert ZVT interval to exchange-specific format"""
        if isinstance(interval, IntervalLevel):
            interval = interval.value
            
        # Standard mapping - override in subclasses if needed
        mapping = {
            "1m": "1m", "3m": "3m", "5m": "5m", "15m": "15m", "30m": "30m",
            "1h": "1h", "2h": "2h", "4h": "4h", "6h": "6h", "8h": "8h", "12h": "12h",
            "1d": "1d", "3d": "3d", "1w": "1w", "1M": "1M"
        }
        return mapping.get(interval, interval)
    
    def parse_ohlcv(self, raw_data: List) -> pd.DataFrame:
        """Parse raw OHLCV data into standardized DataFrame"""
        # Default implementation - override in subclasses
        if not raw_data:
            return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
        
        df = pd.DataFrame(raw_data, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df[["open", "high", "low", "close", "volume"]] = df[["open", "high", "low", "close", "volume"]].astype(float)
        return df.sort_values("timestamp").reset_index(drop=True)
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status and statistics"""
        return {
            "exchange": self.get_exchange_name(),
            "is_connected": self._is_connected,
            "ws_connections": len(self._ws_connections),
            "stats": self.stats,
            "testnet": self.testnet
        }
    
    def close_connections(self):
        """Close all WebSocket connections"""
        for ws in self._ws_connections.values():
            try:
                ws.close()
            except Exception as e:
                self.logger.error(f"Error closing WebSocket: {e}")
        
        self._ws_connections.clear()
        self._is_connected = False
    
    def __del__(self):
        """Cleanup on object destruction"""
        self.close_connections()


class MockCryptoConnector(BaseCryptoConnector):
    """
    Mock connector for testing purposes
    Maintains the same interface but returns mock data
    """
    
    def __init__(self, exchange_name: str = "mock", **kwargs):
        super().__init__(**kwargs)
        self._exchange_name = exchange_name
        self._mock_symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT"]
    
    def get_exchange_name(self) -> str:
        return self._exchange_name
    
    def get_symbols(self) -> List[Dict[str, Any]]:
        return [
            {
                "symbol": symbol,
                "baseAsset": symbol[:-4],
                "quoteAsset": symbol[-4:],
                "status": "TRADING",
                "pricePrecision": 8,
                "quantityPrecision": 8
            }
            for symbol in self._mock_symbols
        ]
    
    def get_ohlcv(self, symbol: str, interval: str, start_time: Optional[datetime] = None,
                  end_time: Optional[datetime] = None, limit: int = 1000) -> pd.DataFrame:
        """Generate mock OHLCV data"""
        import numpy as np
        
        if not end_time:
            end_time = datetime.now()
        if not start_time:
            start_time = end_time - timedelta(days=1)
        
        # Generate mock data
        periods = min(limit, int((end_time - start_time).total_seconds() / 60))  # 1-minute intervals
        timestamps = pd.date_range(start=start_time, periods=periods, freq="1T")
        
        # Mock price data with some volatility
        base_price = 45000.0 if "BTC" in symbol else 3000.0
        prices = base_price + np.random.randn(periods).cumsum() * base_price * 0.001
        
        df = pd.DataFrame({
            "timestamp": timestamps,
            "open": prices,
            "high": prices * (1 + np.random.rand(periods) * 0.01),
            "low": prices * (1 - np.random.rand(periods) * 0.01),
            "close": prices + np.random.randn(periods) * base_price * 0.001,
            "volume": np.random.rand(periods) * 1000
        })
        
        return df
    
    def get_trades(self, symbol: str, start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None, limit: int = 1000) -> pd.DataFrame:
        """Generate mock trade data"""
        import numpy as np
        
        if not end_time:
            end_time = datetime.now()
        if not start_time:
            start_time = end_time - timedelta(hours=1)
        
        num_trades = min(limit, 100)
        timestamps = pd.date_range(start=start_time, end=end_time, periods=num_trades)
        base_price = 45000.0 if "BTC" in symbol else 3000.0
        
        df = pd.DataFrame({
            "timestamp": timestamps,
            "price": base_price + np.random.randn(num_trades) * base_price * 0.001,
            "quantity": np.random.rand(num_trades) * 10,
            "side": np.random.choice(["buy", "sell"], num_trades),
            "trade_id": range(num_trades)
        })
        
        return df
    
    def get_orderbook(self, symbol: str, depth: int = 100) -> Dict[str, Any]:
        """Generate mock orderbook data"""
        import numpy as np
        
        base_price = 45000.0 if "BTC" in symbol else 3000.0
        spread = base_price * 0.0001  # 0.01% spread
        
        bids = []
        asks = []
        
        for i in range(min(depth, 20)):
            bid_price = base_price - spread * (i + 1)
            ask_price = base_price + spread * (i + 1)
            quantity = np.random.rand() * 10
            
            bids.append([bid_price, quantity])
            asks.append([ask_price, quantity])
        
        return {
            "symbol": symbol,
            "bids": bids,
            "asks": asks,
            "timestamp": datetime.now().isoformat()
        }
    
    def subscribe_ticker(self, symbols: List[str], callback: Callable):
        """Mock ticker subscription"""
        self.logger.info(f"Mock subscribing to ticker for {symbols}")
        
    def subscribe_klines(self, symbols: List[str], intervals: List[str], callback: Callable):
        """Mock klines subscription"""
        self.logger.info(f"Mock subscribing to klines for {symbols} at {intervals}")
        
    def subscribe_trades(self, symbols: List[str], callback: Callable):
        """Mock trades subscription"""
        self.logger.info(f"Mock subscribing to trades for {symbols}")
        
    def subscribe_orderbook(self, symbols: List[str], callback: Callable):
        """Mock orderbook subscription"""
        self.logger.info(f"Mock subscribing to orderbook for {symbols}")