# -*- coding: utf-8 -*-
"""
Binance Exchange Connector
Production-ready implementation for Binance REST and WebSocket APIs
"""

import hashlib
import hmac
import json
import time
import requests
import websocket
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
import pandas as pd
from urllib.parse import urlencode

from .base_connector import BaseCryptoConnector


class BinanceConnector(BaseCryptoConnector):
    """
    Binance exchange connector with full REST and WebSocket support
    
    Features:
    - Binance REST API v3 integration
    - WebSocket streams for real-time data
    - Proper authentication and rate limiting
    - Testnet and mainnet support
    """
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, 
                 testnet: bool = True, **kwargs):
        super().__init__(api_key, api_secret, testnet, **kwargs)
        
        # API endpoints
        if testnet:
            self.base_url = "https://testnet.binance.vision/api/v3"
            self.ws_base_url = "wss://testnet.binance.vision/ws"
            self.ws_stream_url = "wss://testnet.binance.vision/stream"
        else:
            self.base_url = "https://api.binance.com/api/v3"
            self.ws_base_url = "wss://stream.binance.com:9443/ws"
            self.ws_stream_url = "wss://stream.binance.com:9443/stream"
        
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({"X-MBX-APIKEY": api_key})
    
    def get_exchange_name(self) -> str:
        return "binance"
    
    def _sign_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add signature to request parameters"""
        if not self.api_secret:
            return params
        
        params["timestamp"] = int(time.time() * 1000)
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        params["signature"] = signature
        return params
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None, 
                      signed: bool = False) -> Dict[str, Any]:
        """Make authenticated REST API request"""
        self._apply_rate_limit()
        
        if params is None:
            params = {}
        
        if signed:
            params = self._sign_request(params)
        
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            self.stats["requests_made"] += 1
            return response.json()
            
        except requests.RequestException as e:
            self._handle_api_error(e, f"GET {endpoint}")
            return {}
    
    def get_symbols(self) -> List[Dict[str, Any]]:
        """Get all trading symbols from Binance"""
        try:
            data = self._make_request("/exchangeInfo")
            symbols = []
            
            for symbol_info in data.get("symbols", []):
                if symbol_info.get("status") == "TRADING":
                    symbols.append({
                        "symbol": symbol_info["symbol"],
                        "baseAsset": symbol_info["baseAsset"],
                        "quoteAsset": symbol_info["quoteAsset"],
                        "status": symbol_info["status"],
                        "pricePrecision": symbol_info.get("quotePrecision", 8),
                        "quantityPrecision": symbol_info.get("baseAssetPrecision", 8),
                        "minPrice": self._get_filter_value(symbol_info["filters"], "PRICE_FILTER", "minPrice"),
                        "maxPrice": self._get_filter_value(symbol_info["filters"], "PRICE_FILTER", "maxPrice"),
                        "tickSize": self._get_filter_value(symbol_info["filters"], "PRICE_FILTER", "tickSize"),
                        "minQty": self._get_filter_value(symbol_info["filters"], "LOT_SIZE", "minQty"),
                        "maxQty": self._get_filter_value(symbol_info["filters"], "LOT_SIZE", "maxQty"),
                        "stepSize": self._get_filter_value(symbol_info["filters"], "LOT_SIZE", "stepSize")
                    })
            
            return symbols
            
        except Exception as e:
            self.logger.error(f"Error getting symbols: {e}")
            return []
    
    def _get_filter_value(self, filters: List[Dict], filter_type: str, key: str) -> Optional[float]:
        """Extract filter values from symbol info"""
        for filter_info in filters:
            if filter_info.get("filterType") == filter_type:
                value = filter_info.get(key)
                return float(value) if value else None
        return None
    
    def normalize_interval(self, interval: str) -> str:
        """Convert ZVT interval to Binance format"""
        mapping = {
            "1m": "1m", "3m": "3m", "5m": "5m", "15m": "15m", "30m": "30m",
            "1h": "1h", "2h": "2h", "4h": "4h", "6h": "6h", "8h": "8h", "12h": "12h",
            "1d": "1d", "3d": "3d", "1w": "1w", "1M": "1M"
        }
        return mapping.get(interval, interval)
    
    def get_ohlcv(self, symbol: str, interval: str, start_time: Optional[datetime] = None,
                  end_time: Optional[datetime] = None, limit: int = 1000) -> pd.DataFrame:
        """Get OHLCV data from Binance"""
        params = {
            "symbol": self.normalize_symbol(symbol),
            "interval": self.normalize_interval(interval),
            "limit": min(limit, 1000)  # Binance max is 1000
        }
        
        if start_time:
            params["startTime"] = int(start_time.timestamp() * 1000)
        if end_time:
            params["endTime"] = int(end_time.timestamp() * 1000)
        
        try:
            data = self._make_request("/klines", params)
            
            if not data:
                return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
            
            df = pd.DataFrame(data, columns=[
                "timestamp", "open", "high", "low", "close", "volume",
                "close_time", "quote_asset_volume", "number_of_trades",
                "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
            ])
            
            # Convert and format data
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df[["open", "high", "low", "close", "volume"]] = df[["open", "high", "low", "close", "volume"]].astype(float)
            
            # Keep only required columns
            df = df[["timestamp", "open", "high", "low", "close", "volume"]]
            
            return df.sort_values("timestamp").reset_index(drop=True)
            
        except Exception as e:
            self.logger.error(f"Error getting OHLCV data for {symbol}: {e}")
            return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
    
    def get_trades(self, symbol: str, start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None, limit: int = 1000) -> pd.DataFrame:
        """Get historical trades from Binance"""
        params = {
            "symbol": self.normalize_symbol(symbol),
            "limit": min(limit, 1000)
        }
        
        try:
            # Note: Historical trades require different endpoint and may need special permissions
            data = self._make_request("/trades", params)
            
            if not data:
                return pd.DataFrame(columns=["timestamp", "price", "quantity", "side", "trade_id"])
            
            df = pd.DataFrame(data)
            df["timestamp"] = pd.to_datetime(df["time"], unit="ms")
            df["price"] = df["price"].astype(float)
            df["quantity"] = df["qty"].astype(float)
            df["side"] = df["isBuyerMaker"].apply(lambda x: "sell" if x else "buy")
            df["trade_id"] = df["id"]
            
            df = df[["timestamp", "price", "quantity", "side", "trade_id"]]
            
            return df.sort_values("timestamp").reset_index(drop=True)
            
        except Exception as e:
            self.logger.error(f"Error getting trades for {symbol}: {e}")
            return pd.DataFrame(columns=["timestamp", "price", "quantity", "side", "trade_id"])
    
    def get_orderbook(self, symbol: str, depth: int = 100) -> Dict[str, Any]:
        """Get current orderbook snapshot"""
        params = {
            "symbol": self.normalize_symbol(symbol),
            "limit": min(depth, 5000)  # Binance supports up to 5000
        }
        
        try:
            data = self._make_request("/depth", params)
            
            if not data:
                return {"bids": [], "asks": [], "timestamp": datetime.now().isoformat()}
            
            # Convert to float and sort
            bids = [[float(price), float(qty)] for price, qty in data.get("bids", [])]
            asks = [[float(price), float(qty)] for price, qty in data.get("asks", [])]
            
            return {
                "symbol": symbol,
                "bids": bids,
                "asks": asks,
                "timestamp": datetime.now().isoformat(),
                "lastUpdateId": data.get("lastUpdateId")
            }
            
        except Exception as e:
            self.logger.error(f"Error getting orderbook for {symbol}: {e}")
            return {"bids": [], "asks": [], "timestamp": datetime.now().isoformat()}
    
    def subscribe_ticker(self, symbols: List[str], callback: Callable):
        """Subscribe to 24hr ticker statistics"""
        streams = [f"{self.normalize_symbol(symbol).lower()}@ticker" for symbol in symbols]
        self._subscribe_to_streams(streams, callback, "ticker")
    
    def subscribe_klines(self, symbols: List[str], intervals: List[str], callback: Callable):
        """Subscribe to kline/candlestick streams"""
        streams = []
        for symbol in symbols:
            for interval in intervals:
                stream = f"{self.normalize_symbol(symbol).lower()}@kline_{self.normalize_interval(interval)}"
                streams.append(stream)
        
        self._subscribe_to_streams(streams, callback, "kline")
    
    def subscribe_trades(self, symbols: List[str], callback: Callable):
        """Subscribe to trade streams"""
        streams = [f"{self.normalize_symbol(symbol).lower()}@trade" for symbol in symbols]
        self._subscribe_to_streams(streams, callback, "trade")
    
    def subscribe_orderbook(self, symbols: List[str], callback: Callable):
        """Subscribe to partial book depth streams"""
        streams = [f"{self.normalize_symbol(symbol).lower()}@depth20@100ms" for symbol in symbols]
        self._subscribe_to_streams(streams, callback, "depthUpdate")
    
    def _subscribe_to_streams(self, streams: List[str], callback: Callable, stream_type: str):
        """Generic method to subscribe to multiple streams"""
        if not streams:
            return
        
        # Create combined stream URL
        stream_names = "/".join(streams)
        ws_url = f"{self.ws_stream_url}?streams={stream_names}"
        
        def on_message(ws, message):
            try:
                data = json.loads(message)
                
                # Handle combined stream format
                if "stream" in data and "data" in data:
                    stream_data = data["data"]
                    stream_name = data["stream"]
                    
                    # Parse the data based on stream type
                    parsed_data = self._parse_stream_data(stream_data, stream_type)
                    if parsed_data:
                        callback(parsed_data)
                else:
                    # Handle single stream format
                    parsed_data = self._parse_stream_data(data, stream_type)
                    if parsed_data:
                        callback(parsed_data)
                
                self.stats["ws_messages_received"] += 1
                
            except Exception as e:
                self.logger.error(f"Error processing WebSocket message: {e}")
        
        def on_error(ws, error):
            self.logger.error(f"WebSocket error: {error}")
            self.stats["requests_failed"] += 1
        
        def on_close(ws, close_status_code, close_msg):
            self.logger.info(f"WebSocket connection closed: {close_status_code} - {close_msg}")
            self._is_connected = False
        
        def on_open(ws):
            self.logger.info(f"WebSocket connected to {len(streams)} streams")
            self._is_connected = True
        
        # Create WebSocket connection
        ws = websocket.WebSocketApp(
            ws_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open
        )
        
        # Store connection
        connection_id = f"{stream_type}_{len(self._ws_connections)}"
        self._ws_connections[connection_id] = ws
        
        # Start connection in a separate thread
        import threading
        thread = threading.Thread(target=ws.run_forever)
        thread.daemon = True
        thread.start()
    
    def _parse_stream_data(self, data: Dict[str, Any], stream_type: str) -> Optional[Dict[str, Any]]:
        """Parse WebSocket stream data into standardized format"""
        try:
            if stream_type == "ticker":
                return {
                    "type": "ticker",
                    "symbol": self.denormalize_symbol(data["s"]),
                    "price": float(data["c"]),
                    "change": float(data["P"]),
                    "volume": float(data["v"]),
                    "high": float(data["h"]),
                    "low": float(data["l"]),
                    "timestamp": pd.to_datetime(data["E"], unit="ms")
                }
            
            elif stream_type == "kline":
                kline_data = data["k"]
                return {
                    "type": "kline",
                    "symbol": self.denormalize_symbol(kline_data["s"]),
                    "interval": kline_data["i"],
                    "open": float(kline_data["o"]),
                    "high": float(kline_data["h"]),
                    "low": float(kline_data["l"]),
                    "close": float(kline_data["c"]),
                    "volume": float(kline_data["v"]),
                    "is_closed": kline_data["x"],
                    "timestamp": pd.to_datetime(kline_data["t"], unit="ms")
                }
            
            elif stream_type == "trade":
                return {
                    "type": "trade",
                    "symbol": self.denormalize_symbol(data["s"]),
                    "trade_id": data["t"],
                    "price": float(data["p"]),
                    "quantity": float(data["q"]),
                    "side": "sell" if data["m"] else "buy",
                    "timestamp": pd.to_datetime(data["T"], unit="ms")
                }
            
            elif stream_type == "depthUpdate":
                return {
                    "type": "depthUpdate",
                    "symbol": self.denormalize_symbol(data["s"]),
                    "bids": [[float(price), float(qty)] for price, qty in data["b"]],
                    "asks": [[float(price), float(qty)] for price, qty in data["a"]],
                    "timestamp": pd.to_datetime(data["E"], unit="ms"),
                    "lastUpdateId": data["u"]
                }
            
        except Exception as e:
            self.logger.error(f"Error parsing {stream_type} data: {e}")
            return None
        
        return None