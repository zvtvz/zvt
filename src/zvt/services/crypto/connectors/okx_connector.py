# -*- coding: utf-8 -*-
"""
OKX Exchange Connector
Production-ready implementation for OKX REST and WebSocket APIs
"""

import json
import time
import requests
import websocket
import hashlib
import hmac
import base64
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
import pandas as pd

from .base_connector import BaseCryptoConnector


class OKXConnector(BaseCryptoConnector):
    """
    OKX exchange connector with REST and WebSocket support
    
    Features:
    - OKX REST API v5 integration
    - WebSocket streams for real-time data
    - Authentication and rate limiting
    - Demo and live trading support
    """
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, 
                 passphrase: Optional[str] = None, testnet: bool = True, **kwargs):
        super().__init__(api_key, api_secret, testnet, **kwargs)
        self.passphrase = passphrase
        
        # API endpoints
        if testnet:
            self.base_url = "https://www.okx.com/api/v5"  # OKX uses same URL with demo flag
            self.ws_public_url = "wss://ws.okx.com:8443/ws/v5/public"
            self.ws_private_url = "wss://ws.okx.com:8443/ws/v5/private"
        else:
            self.base_url = "https://www.okx.com/api/v5"
            self.ws_public_url = "wss://ws.okx.com:8443/ws/v5/public"
            self.ws_private_url = "wss://ws.okx.com:8443/ws/v5/private"
        
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "OK-ACCESS-TIMESTAMP": "",
            "OK-ACCESS-SIGN": "",
            "OK-ACCESS-PASSPHRASE": ""
        })
        
        if testnet:
            self.session.headers.update({"x-simulated-trading": "1"})
    
    def get_exchange_name(self) -> str:
        return "okx"
    
    def _sign_request(self, method: str, endpoint: str, body: str = "") -> Dict[str, str]:
        """Generate OKX API signature"""
        if not all([self.api_key, self.api_secret, self.passphrase]):
            return {}
        
        timestamp = str(time.time())
        message = timestamp + method.upper() + endpoint + body
        signature = base64.b64encode(
            hmac.new(
                self.api_secret.encode(),
                message.encode(),
                hashlib.sha256
            ).digest()
        ).decode()
        
        return {
            "OK-ACCESS-KEY": self.api_key,
            "OK-ACCESS-SIGN": signature,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": self.passphrase
        }
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None, 
                      method: str = "GET", signed: bool = False) -> Dict[str, Any]:
        """Make REST API request to OKX"""
        self._apply_rate_limit()
        
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        if signed:
            body = ""
            if method == "POST" and params:
                body = json.dumps(params)
                headers.update(self._sign_request(method, endpoint, body))
            else:
                headers.update(self._sign_request(method, endpoint))
        
        try:
            if method == "GET":
                response = self.session.get(url, params=params, headers=headers)
            else:
                response = self.session.post(url, data=body if 'body' in locals() else None, headers=headers)
            
            response.raise_for_status()
            data = response.json()
            
            self.stats["requests_made"] += 1
            
            # OKX wraps responses in {"code": "0", "data": [...]}
            if data.get("code") == "0":
                return data.get("data", [])
            else:
                self.logger.error(f"OKX API error: {data.get('msg', 'Unknown error')}")
                return []
                
        except requests.RequestException as e:
            self._handle_api_error(e, f"{method} {endpoint}")
            return []
    
    def normalize_symbol(self, symbol: str) -> str:
        """Convert standard symbol format to OKX format (BTC/USDT -> BTC-USDT)"""
        return symbol.replace("/", "-")
    
    def denormalize_symbol(self, symbol: str) -> str:
        """Convert OKX symbol back to standard format (BTC-USDT -> BTC/USDT)"""
        return symbol.replace("-", "/")
    
    def get_symbols(self) -> List[Dict[str, Any]]:
        """Get all trading instruments from OKX"""
        try:
            data = self._make_request("/public/instruments", {"instType": "SPOT"})
            symbols = []
            
            for instrument in data:
                if instrument.get("state") == "live":
                    symbols.append({
                        "symbol": instrument["instId"],
                        "baseAsset": instrument["baseCcy"],
                        "quoteAsset": instrument["quoteCcy"],
                        "status": "TRADING",
                        "pricePrecision": len(instrument.get("tickSz", "0.01").split(".")[-1]),
                        "quantityPrecision": len(instrument.get("lotSz", "0.001").split(".")[-1]),
                        "tickSize": float(instrument.get("tickSz", "0.01")),
                        "lotSize": float(instrument.get("lotSz", "0.001")),
                        "minSize": float(instrument.get("minSz", "0.001"))
                    })
            
            return symbols
            
        except Exception as e:
            self.logger.error(f"Error getting symbols: {e}")
            return []
    
    def normalize_interval(self, interval: str) -> str:
        """Convert ZVT interval to OKX format"""
        mapping = {
            "1m": "1m", "3m": "3m", "5m": "5m", "15m": "15m", "30m": "30m",
            "1h": "1H", "2h": "2H", "4h": "4H", "6h": "6H", "12h": "12H",
            "1d": "1D", "1w": "1W", "1M": "1M"
        }
        return mapping.get(interval, interval)
    
    def get_ohlcv(self, symbol: str, interval: str, start_time: Optional[datetime] = None,
                  end_time: Optional[datetime] = None, limit: int = 100) -> pd.DataFrame:
        """Get OHLCV data from OKX"""
        params = {
            "instId": self.normalize_symbol(symbol),
            "bar": self.normalize_interval(interval),
            "limit": str(min(limit, 100))  # OKX max is 100
        }
        
        if start_time:
            params["after"] = str(int(start_time.timestamp() * 1000))
        if end_time:
            params["before"] = str(int(end_time.timestamp() * 1000))
        
        try:
            data = self._make_request("/market/candles", params)
            
            if not data:
                return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
            
            # OKX returns [timestamp, open, high, low, close, volume, vol_ccy]
            df = pd.DataFrame(data, columns=[
                "timestamp", "open", "high", "low", "close", "volume", "vol_ccy"
            ])
            
            # Convert and format data
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df[["open", "high", "low", "close", "volume"]] = df[["open", "high", "low", "close", "volume"]].astype(float)
            
            # Keep only required columns and sort by timestamp
            df = df[["timestamp", "open", "high", "low", "close", "volume"]]
            return df.sort_values("timestamp").reset_index(drop=True)
            
        except Exception as e:
            self.logger.error(f"Error getting OHLCV data for {symbol}: {e}")
            return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
    
    def get_trades(self, symbol: str, start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None, limit: int = 100) -> pd.DataFrame:
        """Get recent trades from OKX"""
        params = {
            "instId": self.normalize_symbol(symbol),
            "limit": str(min(limit, 100))
        }
        
        try:
            data = self._make_request("/market/trades", params)
            
            if not data:
                return pd.DataFrame(columns=["timestamp", "price", "quantity", "side", "trade_id"])
            
            df = pd.DataFrame(data)
            df["timestamp"] = pd.to_datetime(df["ts"], unit="ms")
            df["price"] = df["px"].astype(float)
            df["quantity"] = df["sz"].astype(float)
            df["trade_id"] = df["tradeId"]
            # OKX side: "buy" or "sell"
            df = df[["timestamp", "price", "quantity", "side", "trade_id"]]
            
            return df.sort_values("timestamp").reset_index(drop=True)
            
        except Exception as e:
            self.logger.error(f"Error getting trades for {symbol}: {e}")
            return pd.DataFrame(columns=["timestamp", "price", "quantity", "side", "trade_id"])
    
    def get_orderbook(self, symbol: str, depth: int = 20) -> Dict[str, Any]:
        """Get order book from OKX"""
        params = {
            "instId": self.normalize_symbol(symbol),
            "sz": str(min(depth, 400))  # Max 400
        }
        
        try:
            data = self._make_request("/market/books", params)
            
            if not data or not data[0]:
                return {"bids": [], "asks": [], "timestamp": datetime.now().isoformat()}
            
            book_data = data[0]
            
            # Convert to float
            bids = [[float(price), float(qty)] for price, qty, _, _ in book_data.get("bids", [])]
            asks = [[float(price), float(qty)] for price, qty, _, _ in book_data.get("asks", [])]
            
            return {
                "symbol": symbol,
                "bids": bids,
                "asks": asks,
                "timestamp": pd.to_datetime(book_data["ts"], unit="ms").isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting orderbook for {symbol}: {e}")
            return {"bids": [], "asks": [], "timestamp": datetime.now().isoformat()}
    
    def subscribe_ticker(self, symbols: List[str], callback: Callable):
        """Subscribe to ticker data"""
        channels = [{"channel": "tickers", "instId": self.normalize_symbol(symbol)} for symbol in symbols]
        self._subscribe_channels(channels, callback, "ticker")
    
    def subscribe_klines(self, symbols: List[str], intervals: List[str], callback: Callable):
        """Subscribe to candlestick data"""
        channels = []
        for symbol in symbols:
            for interval in intervals:
                channels.append({
                    "channel": f"candle{self.normalize_interval(interval)}",
                    "instId": self.normalize_symbol(symbol)
                })
        self._subscribe_channels(channels, callback, "candle")
    
    def subscribe_trades(self, symbols: List[str], callback: Callable):
        """Subscribe to trade data"""
        channels = [{"channel": "trades", "instId": self.normalize_symbol(symbol)} for symbol in symbols]
        self._subscribe_channels(channels, callback, "trades")
    
    def subscribe_orderbook(self, symbols: List[str], callback: Callable):
        """Subscribe to order book data"""
        channels = [{"channel": "books", "instId": self.normalize_symbol(symbol)} for symbol in symbols]
        self._subscribe_channels(channels, callback, "books")
    
    def _subscribe_channels(self, channels: List[Dict], callback: Callable, data_type: str):
        """Subscribe to OKX WebSocket channels"""
        if not channels:
            return
        
        def on_message(ws, message):
            try:
                data = json.loads(message)
                
                # Handle subscription confirmation
                if data.get("event") == "subscribe":
                    self.logger.info(f"Subscribed to {data_type}: {data}")
                    return
                
                # Handle data messages
                if "data" in data and data["data"]:
                    for item in data["data"]:
                        parsed_data = self._parse_okx_data(item, data.get("arg", {}), data_type)
                        if parsed_data:
                            callback(parsed_data)
                
                self.stats["ws_messages_received"] += 1
                
            except Exception as e:
                self.logger.error(f"Error processing OKX WebSocket message: {e}")
        
        def on_error(ws, error):
            self.logger.error(f"OKX WebSocket error: {error}")
        
        def on_close(ws, close_status_code, close_msg):
            self.logger.info(f"OKX WebSocket closed: {close_status_code}")
            self._is_connected = False
        
        def on_open(ws):
            self.logger.info(f"OKX WebSocket connected, subscribing to {len(channels)} channels")
            
            # Send subscription message
            subscribe_msg = {
                "op": "subscribe",
                "args": channels
            }
            ws.send(json.dumps(subscribe_msg))
            self._is_connected = True
        
        # Create WebSocket connection
        ws = websocket.WebSocketApp(
            self.ws_public_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open
        )
        
        # Store connection
        connection_id = f"okx_{data_type}_{len(self._ws_connections)}"
        self._ws_connections[connection_id] = ws
        
        # Start connection
        import threading
        thread = threading.Thread(target=ws.run_forever)
        thread.daemon = True
        thread.start()
    
    def _parse_okx_data(self, data: Dict, channel_info: Dict, data_type: str) -> Optional[Dict[str, Any]]:
        """Parse OKX WebSocket data"""
        try:
            symbol = self.denormalize_symbol(channel_info.get("instId", ""))
            
            if data_type == "ticker":
                return {
                    "type": "ticker",
                    "symbol": symbol,
                    "price": float(data["last"]),
                    "change": float(data["chgUtc8"]),
                    "volume": float(data["vol24h"]),
                    "high": float(data["high24h"]),
                    "low": float(data["low24h"]),
                    "timestamp": pd.to_datetime(data["ts"], unit="ms")
                }
            
            elif data_type == "candle":
                return {
                    "type": "kline",
                    "symbol": symbol,
                    "interval": channel_info.get("channel", "").replace("candle", ""),
                    "open": float(data[1]),
                    "high": float(data[2]),
                    "low": float(data[3]),
                    "close": float(data[4]),
                    "volume": float(data[5]),
                    "timestamp": pd.to_datetime(data[0], unit="ms")
                }
            
            elif data_type == "trades":
                return {
                    "type": "trade",
                    "symbol": symbol,
                    "trade_id": data["tradeId"],
                    "price": float(data["px"]),
                    "quantity": float(data["sz"]),
                    "side": data["side"],
                    "timestamp": pd.to_datetime(data["ts"], unit="ms")
                }
            
            elif data_type == "books":
                return {
                    "type": "depthUpdate",
                    "symbol": symbol,
                    "bids": [[float(price), float(qty)] for price, qty, _, _ in data.get("bids", [])],
                    "asks": [[float(price), float(qty)] for price, qty, _, _ in data.get("asks", [])],
                    "timestamp": pd.to_datetime(data["ts"], unit="ms")
                }
        
        except Exception as e:
            self.logger.error(f"Error parsing OKX {data_type} data: {e}")
            return None
        
        return None