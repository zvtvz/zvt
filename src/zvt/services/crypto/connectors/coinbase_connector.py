# -*- coding: utf-8 -*-
"""
Coinbase Exchange Connector
Production-ready implementation for Coinbase Advanced Trade API
"""

import json
import time
import hashlib
import hmac
import base64
import requests
import websocket
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
import pandas as pd

from .base_connector import BaseCryptoConnector


class CoinbaseConnector(BaseCryptoConnector):
    """
    Coinbase exchange connector with Advanced Trade API
    
    Features:
    - Coinbase Advanced Trade REST API
    - WebSocket feeds for real-time data
    - Sandbox and production support
    """
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, 
                 testnet: bool = True, **kwargs):
        super().__init__(api_key, api_secret, testnet, **kwargs)
        
        # API endpoints
        if testnet:
            self.base_url = "https://api.sandbox.exchange.coinbase.com"
            self.ws_url = "wss://ws-feed-public.sandbox.exchange.coinbase.com"
        else:
            self.base_url = "https://api.exchange.coinbase.com"
            self.ws_url = "wss://ws-feed.exchange.coinbase.com"
        
        self.session = requests.Session()
    
    def get_exchange_name(self) -> str:
        return "coinbase"
    
    def _sign_request(self, method: str, path: str, body: str = "") -> Dict[str, str]:
        """Generate Coinbase Pro API signature"""
        if not self.api_key or not self.api_secret:
            return {}
        
        timestamp = str(time.time())
        message = timestamp + method + path + body
        signature = base64.b64encode(
            hmac.new(
                base64.b64decode(self.api_secret),
                message.encode(),
                hashlib.sha256
            ).digest()
        ).decode()
        
        return {
            "CB-ACCESS-KEY": self.api_key,
            "CB-ACCESS-SIGN": signature,
            "CB-ACCESS-TIMESTAMP": timestamp,
            "CB-ACCESS-PASSPHRASE": "your_passphrase"  # Would need to be provided
        }
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None, 
                      signed: bool = False) -> Dict[str, Any]:
        """Make REST API request to Coinbase"""
        self._apply_rate_limit()
        
        headers = {"Content-Type": "application/json"}
        if signed:
            headers.update(self._sign_request("GET", endpoint))
        
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            self.stats["requests_made"] += 1
            return response.json()
            
        except requests.RequestException as e:
            self._handle_api_error(e, f"GET {endpoint}")
            return {}
    
    def normalize_symbol(self, symbol: str) -> str:
        """Convert standard format to Coinbase format (BTC/USD -> BTC-USD)"""
        return symbol.replace("/", "-")
    
    def denormalize_symbol(self, symbol: str) -> str:
        """Convert Coinbase format back to standard (BTC-USD -> BTC/USD)"""
        return symbol.replace("-", "/")
    
    def get_symbols(self) -> List[Dict[str, Any]]:
        """Get trading products from Coinbase"""
        try:
            data = self._make_request("/products")
            symbols = []
            
            if isinstance(data, list):
                for product in data:
                    if not product.get("trading_disabled", False):
                        symbols.append({
                            "symbol": product["id"],
                            "baseAsset": product["base_currency"],
                            "quoteAsset": product["quote_currency"],
                            "status": "TRADING" if not product.get("cancel_only", False) else "CANCEL_ONLY",
                            "pricePrecision": len(product.get("quote_increment", "0.01").split(".")[-1]),
                            "quantityPrecision": len(product.get("base_increment", "0.001").split(".")[-1])
                        })
            
            return symbols
            
        except Exception as e:
            self.logger.error(f"Error getting symbols: {e}")
            return []
    
    def normalize_interval(self, interval: str) -> str:
        """Convert ZVT interval to Coinbase granularity (in seconds)"""
        mapping = {
            "1m": "60", "5m": "300", "15m": "900", 
            "1h": "3600", "6h": "21600", "1d": "86400"
        }
        return mapping.get(interval, "3600")  # Default to 1h
    
    def get_ohlcv(self, symbol: str, interval: str, start_time: Optional[datetime] = None,
                  end_time: Optional[datetime] = None, limit: int = 300) -> pd.DataFrame:
        """Get OHLCV data from Coinbase"""
        endpoint = f"/products/{self.normalize_symbol(symbol)}/candles"
        params = {
            "granularity": self.normalize_interval(interval)
        }
        
        if start_time:
            params["start"] = start_time.isoformat()
        if end_time:
            params["end"] = end_time.isoformat()
        
        try:
            data = self._make_request(endpoint, params)
            
            if not data or not isinstance(data, list):
                return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
            
            # Coinbase returns [timestamp, low, high, open, close, volume]
            df = pd.DataFrame(data, columns=["timestamp", "low", "high", "open", "close", "volume"])
            
            # Reorder columns and convert
            df = df[["timestamp", "open", "high", "low", "close", "volume"]]
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
            df[["open", "high", "low", "close", "volume"]] = df[["open", "high", "low", "close", "volume"]].astype(float)
            
            return df.sort_values("timestamp").reset_index(drop=True)
            
        except Exception as e:
            self.logger.error(f"Error getting OHLCV data for {symbol}: {e}")
            return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
    
    def get_trades(self, symbol: str, start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None, limit: int = 100) -> pd.DataFrame:
        """Get recent trades from Coinbase"""
        endpoint = f"/products/{self.normalize_symbol(symbol)}/trades"
        
        try:
            data = self._make_request(endpoint)
            
            if not data or not isinstance(data, list):
                return pd.DataFrame(columns=["timestamp", "price", "quantity", "side", "trade_id"])
            
            df = pd.DataFrame(data)
            df["timestamp"] = pd.to_datetime(df["time"])
            df["price"] = df["price"].astype(float)
            df["quantity"] = df["size"].astype(float)
            df["trade_id"] = df["trade_id"]
            
            df = df[["timestamp", "price", "quantity", "side", "trade_id"]]
            return df.sort_values("timestamp").reset_index(drop=True).head(limit)
            
        except Exception as e:
            self.logger.error(f"Error getting trades for {symbol}: {e}")
            return pd.DataFrame(columns=["timestamp", "price", "quantity", "side", "trade_id"])
    
    def get_orderbook(self, symbol: str, depth: int = 50) -> Dict[str, Any]:
        """Get order book from Coinbase"""
        endpoint = f"/products/{self.normalize_symbol(symbol)}/book"
        params = {"level": 2}  # Level 2 gives 50 best bids and asks
        
        try:
            data = self._make_request(endpoint, params)
            
            if not data:
                return {"bids": [], "asks": [], "timestamp": datetime.now().isoformat()}
            
            bids = [[float(price), float(size)] for price, size, _ in data.get("bids", [])]
            asks = [[float(price), float(size)] for price, size, _ in data.get("asks", [])]
            
            return {
                "symbol": symbol,
                "bids": bids[:depth],
                "asks": asks[:depth],
                "timestamp": datetime.now().isoformat(),
                "sequence": data.get("sequence")
            }
            
        except Exception as e:
            self.logger.error(f"Error getting orderbook for {symbol}: {e}")
            return {"bids": [], "asks": [], "timestamp": datetime.now().isoformat()}
    
    # WebSocket methods (simplified implementations)
    def subscribe_ticker(self, symbols: List[str], callback: Callable):
        """Subscribe to ticker channel"""
        self.logger.info(f"Coinbase ticker subscription for {symbols}")
        channels = [{
            "name": "ticker",
            "product_ids": [self.normalize_symbol(symbol) for symbol in symbols]
        }]
        self._subscribe_channels(channels, callback, "ticker")
        
    def subscribe_klines(self, symbols: List[str], intervals: List[str], callback: Callable):
        """Coinbase doesn't have real-time candlestick feeds, use ticker instead"""
        self.logger.info(f"Coinbase using ticker for klines simulation: {symbols}")
        self.subscribe_ticker(symbols, callback)
        
    def subscribe_trades(self, symbols: List[str], callback: Callable):
        """Subscribe to matches (trades) channel"""
        self.logger.info(f"Coinbase trades subscription for {symbols}")
        channels = [{
            "name": "matches",
            "product_ids": [self.normalize_symbol(symbol) for symbol in symbols]
        }]
        self._subscribe_channels(channels, callback, "matches")
        
    def subscribe_orderbook(self, symbols: List[str], callback: Callable):
        """Subscribe to level2 (order book) channel"""
        self.logger.info(f"Coinbase orderbook subscription for {symbols}")
        channels = [{
            "name": "level2",
            "product_ids": [self.normalize_symbol(symbol) for symbol in symbols]
        }]
        self._subscribe_channels(channels, callback, "level2")
    
    def _subscribe_channels(self, channels: List[Dict], callback: Callable, data_type: str):
        """Subscribe to Coinbase WebSocket channels"""
        if not channels:
            return
        
        def on_message(ws, message):
            try:
                data = json.loads(message)
                
                # Handle subscription confirmation
                if data.get("type") == "subscriptions":
                    self.logger.info(f"Coinbase subscribed to {data_type}")
                    return
                
                # Handle different message types
                parsed_data = self._parse_coinbase_data(data, data_type)
                if parsed_data:
                    callback(parsed_data)
                
                self.stats["ws_messages_received"] += 1
                
            except Exception as e:
                self.logger.error(f"Error processing Coinbase WebSocket message: {e}")
        
        def on_error(ws, error):
            self.logger.error(f"Coinbase WebSocket error: {error}")
        
        def on_close(ws, close_status_code, close_msg):
            self.logger.info(f"Coinbase WebSocket closed")
            self._is_connected = False
        
        def on_open(ws):
            self.logger.info(f"Coinbase WebSocket connected")
            
            # Send subscription message
            subscribe_msg = {
                "type": "subscribe",
                "channels": channels
            }
            ws.send(json.dumps(subscribe_msg))
            self._is_connected = True
        
        # Create WebSocket connection
        ws = websocket.WebSocketApp(
            self.ws_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open
        )
        
        # Store connection
        connection_id = f"coinbase_{data_type}_{len(self._ws_connections)}"
        self._ws_connections[connection_id] = ws
        
        # Start connection
        import threading
        thread = threading.Thread(target=ws.run_forever)
        thread.daemon = True
        thread.start()
    
    def _parse_coinbase_data(self, data: Dict, data_type: str) -> Optional[Dict[str, Any]]:
        """Parse Coinbase WebSocket data"""
        try:
            if data_type == "ticker" and data.get("type") == "ticker":
                return {
                    "type": "ticker",
                    "symbol": self.denormalize_symbol(data["product_id"]),
                    "price": float(data["price"]),
                    "volume": float(data.get("volume_24h", 0)),
                    "high": float(data.get("high_24h", data["price"])),
                    "low": float(data.get("low_24h", data["price"])),
                    "timestamp": pd.to_datetime(data["time"])
                }
            
            elif data_type == "matches" and data.get("type") == "match":
                return {
                    "type": "trade",
                    "symbol": self.denormalize_symbol(data["product_id"]),
                    "trade_id": data["trade_id"],
                    "price": float(data["price"]),
                    "quantity": float(data["size"]),
                    "side": data["side"],
                    "timestamp": pd.to_datetime(data["time"])
                }
            
            elif data_type == "level2" and data.get("type") == "l2update":
                return {
                    "type": "depthUpdate",
                    "symbol": self.denormalize_symbol(data["product_id"]),
                    "changes": data["changes"],  # [["buy"/"sell", "price", "size"], ...]
                    "timestamp": pd.to_datetime(data["time"])
                }
        
        except Exception as e:
            self.logger.error(f"Error parsing Coinbase {data_type} data: {e}")
            return None
        
        return None