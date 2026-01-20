# -*- coding: utf-8 -*-
"""
Crypto REST API Data Ingestion Service
Provides REST endpoints for external data ingestion and management
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from fastapi import FastAPI, HTTPException, Depends, Query, Path, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import pandas as pd
from sqlalchemy.orm import Session

from zvt.contract import IntervalLevel
from zvt.contract.api import get_db_session
from zvt.domain.crypto import CryptoPair, CryptoPerp, CryptoAsset
from zvt.services.crypto.data_loader import CryptoDataLoader
from zvt.services.crypto.stream_service import CryptoStreamService
from zvt.utils.time_utils import to_pd_timestamp

logger = logging.getLogger(__name__)


# Pydantic models for API requests/responses
class CryptoAssetModel(BaseModel):
    """Crypto asset data model"""
    symbol: str = Field(..., description="Asset symbol (e.g., BTC, ETH)")
    full_name: str = Field(..., description="Full asset name")
    max_supply: Optional[float] = Field(None, description="Maximum supply")
    circulating_supply: Optional[float] = Field(None, description="Circulating supply")
    total_supply: Optional[float] = Field(None, description="Total supply")
    market_cap: Optional[float] = Field(None, description="Market capitalization")
    is_stablecoin: bool = Field(False, description="Is this a stablecoin")
    consensus_mechanism: Optional[str] = Field(None, description="Consensus mechanism")


class CryptoPairModel(BaseModel):
    """Crypto trading pair data model"""
    symbol: str = Field(..., description="Trading pair symbol (e.g., BTC/USDT)")
    base_symbol: str = Field(..., description="Base asset symbol")
    quote_symbol: str = Field(..., description="Quote asset symbol")
    exchange: str = Field(..., description="Exchange name")
    price_step: Optional[float] = Field(None, description="Minimum price increment")
    qty_step: Optional[float] = Field(None, description="Minimum quantity increment")
    min_notional: Optional[float] = Field(None, description="Minimum notional value")
    maker_fee: Optional[float] = Field(None, description="Maker fee rate")
    taker_fee: Optional[float] = Field(None, description="Taker fee rate")
    is_active: bool = Field(True, description="Is trading active")


class OHLCVDataModel(BaseModel):
    """OHLCV candlestick data model"""
    timestamp: datetime = Field(..., description="Candle timestamp")
    open: float = Field(..., description="Opening price")
    high: float = Field(..., description="Highest price")
    low: float = Field(..., description="Lowest price")
    close: float = Field(..., description="Closing price")
    volume: float = Field(..., description="Trading volume")
    
    @validator('high')
    def validate_high(cls, v, values):
        if 'open' in values and 'close' in values and 'low' in values:
            if v < max(values['open'], values['close']) or v < values['low']:
                raise ValueError('High must be >= max(open, close) and >= low')
        return v
    
    @validator('low')
    def validate_low(cls, v, values):
        if 'open' in values and 'close' in values and 'high' in values:
            if v > min(values['open'], values['close']) or v > values['high']:
                raise ValueError('Low must be <= min(open, close) and <= high')
        return v


class TradeDataModel(BaseModel):
    """Trade execution data model"""
    timestamp: datetime = Field(..., description="Trade execution timestamp")
    price: float = Field(..., description="Trade price")
    quantity: float = Field(..., description="Trade quantity")
    side: str = Field(..., description="Trade side (buy/sell)")
    trade_id: Optional[str] = Field(None, description="Trade ID")
    
    @validator('side')
    def validate_side(cls, v):
        if v.lower() not in ['buy', 'sell']:
            raise ValueError('Side must be "buy" or "sell"')
        return v.lower()


class OrderBookDataModel(BaseModel):
    """Order book data model"""
    timestamp: datetime = Field(..., description="Order book timestamp")
    bids: List[List[float]] = Field(..., description="Bid prices and quantities")
    asks: List[List[float]] = Field(..., description="Ask prices and quantities")
    
    @validator('bids', 'asks')
    def validate_orders(cls, v):
        for order in v:
            if len(order) != 2 or order[0] <= 0 or order[1] <= 0:
                raise ValueError('Orders must be [price, quantity] with positive values')
        return v


class DataIngestionRequest(BaseModel):
    """Bulk data ingestion request"""
    exchange: str = Field(..., description="Exchange name")
    symbol: str = Field(..., description="Trading symbol")
    data_type: str = Field(..., description="Data type (ohlcv, trades, orderbook)")
    interval: Optional[str] = Field(None, description="Data interval for OHLCV")
    data: List[Dict[str, Any]] = Field(..., description="Data records")
    
    @validator('data_type')
    def validate_data_type(cls, v):
        valid_types = ['ohlcv', 'trades', 'orderbook', 'funding']
        if v not in valid_types:
            raise ValueError(f'Data type must be one of {valid_types}')
        return v


class DataQueryParams(BaseModel):
    """Parameters for data queries"""
    symbols: Optional[List[str]] = Field(None, description="Symbol filter")
    exchanges: Optional[List[str]] = Field(None, description="Exchange filter")
    start_time: Optional[datetime] = Field(None, description="Start time filter")
    end_time: Optional[datetime] = Field(None, description="End time filter")
    limit: Optional[int] = Field(1000, description="Result limit")
    interval: Optional[str] = Field(None, description="Data interval")


class CryptoAPIIngestion:
    """
    REST API service for crypto data ingestion and management
    
    Features:
    - Data ingestion endpoints (OHLCV, trades, order book)
    - Asset and pair metadata management
    - Historical data queries
    - Stream control and monitoring
    - Validation and error handling
    """
    
    def __init__(
        self,
        data_loader: CryptoDataLoader = None,
        stream_service: CryptoStreamService = None,
        enable_cors: bool = True,
        api_prefix: str = "/api/v1/crypto"
    ):
        self.app = FastAPI(
            title="ZVT Crypto Data Ingestion API",
            description="REST API for cryptocurrency data ingestion and management",
            version="1.0.0"
        )
        
        self.data_loader = data_loader or CryptoDataLoader()
        self.stream_service = stream_service or CryptoStreamService()
        self.api_prefix = api_prefix
        
        # Enable CORS for web applications
        if enable_cors:
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
        
        self._setup_routes()
        
        # Request statistics
        self.stats = {
            "requests_total": 0,
            "requests_by_endpoint": {},
            "ingestion_records": 0,
            "validation_errors": 0,
            "start_time": datetime.now()
        }

    def _setup_routes(self):
        """Setup all API routes"""
        
        # Asset management endpoints
        @self.app.post(f"{self.api_prefix}/assets", response_model=Dict[str, str])
        async def create_asset(asset: CryptoAssetModel):
            """Create or update crypto asset"""
            return await self._create_asset(asset)
        
        @self.app.get(f"{self.api_prefix}/assets")
        async def get_assets(
            symbols: Optional[List[str]] = Query(None),
            limit: int = Query(100, le=1000)
        ):
            """Get crypto assets"""
            return await self._get_assets(symbols, limit)
        
        # Trading pair management
        @self.app.post(f"{self.api_prefix}/pairs", response_model=Dict[str, str])
        async def create_pair(pair: CryptoPairModel):
            """Create or update trading pair"""
            return await self._create_pair(pair)
        
        @self.app.get(f"{self.api_prefix}/pairs")
        async def get_pairs(
            symbols: Optional[List[str]] = Query(None),
            exchanges: Optional[List[str]] = Query(None),
            limit: int = Query(100, le=1000)
        ):
            """Get trading pairs"""
            return await self._get_pairs(symbols, exchanges, limit)
        
        # Data ingestion endpoints
        @self.app.post(f"{self.api_prefix}/ingest/ohlcv")
        async def ingest_ohlcv(
            exchange: str,
            symbol: str,
            interval: str,
            data: List[OHLCVDataModel]
        ):
            """Ingest OHLCV candlestick data"""
            return await self._ingest_ohlcv(exchange, symbol, interval, data)
        
        @self.app.post(f"{self.api_prefix}/ingest/trades")
        async def ingest_trades(
            exchange: str,
            symbol: str,
            data: List[TradeDataModel]
        ):
            """Ingest trade execution data"""
            return await self._ingest_trades(exchange, symbol, data)
        
        @self.app.post(f"{self.api_prefix}/ingest/orderbook")
        async def ingest_orderbook(
            exchange: str,
            symbol: str,
            data: List[OrderBookDataModel]
        ):
            """Ingest order book snapshots"""
            return await self._ingest_orderbook(exchange, symbol, data)
        
        @self.app.post(f"{self.api_prefix}/ingest/bulk")
        async def bulk_ingest(request: DataIngestionRequest):
            """Bulk data ingestion endpoint"""
            return await self._bulk_ingest(request)
        
        # Data query endpoints
        @self.app.get(f"{self.api_prefix}/data/ohlcv")
        async def query_ohlcv(
            symbol: str = Query(...),
            exchange: str = Query(...),
            interval: str = Query("1h"),
            start_time: Optional[datetime] = Query(None),
            end_time: Optional[datetime] = Query(None),
            limit: int = Query(1000, le=10000)
        ):
            """Query OHLCV data"""
            return await self._query_ohlcv(symbol, exchange, interval, start_time, end_time, limit)
        
        @self.app.get(f"{self.api_prefix}/data/trades")
        async def query_trades(
            symbol: str = Query(...),
            exchange: str = Query(...),
            start_time: Optional[datetime] = Query(None),
            end_time: Optional[datetime] = Query(None),
            limit: int = Query(1000, le=10000)
        ):
            """Query trade data"""
            return await self._query_trades(symbol, exchange, start_time, end_time, limit)
        
        # Stream management endpoints  
        @self.app.post(f"{self.api_prefix}/stream/start")
        async def start_streams():
            """Start data streaming services"""
            return await self._start_streams()
        
        @self.app.post(f"{self.api_prefix}/stream/stop")
        async def stop_streams():
            """Stop data streaming services"""
            return await self._stop_streams()
        
        @self.app.post(f"{self.api_prefix}/stream/subscribe")
        async def subscribe_streams(
            data_type: str,
            symbols: List[str],
            exchanges: Optional[List[str]] = None
        ):
            """Subscribe to data streams"""
            return await self._subscribe_streams(data_type, symbols, exchanges)
        
        @self.app.get(f"{self.api_prefix}/stream/status")
        async def stream_status():
            """Get streaming service status"""
            return await self._get_stream_status()
        
        # Historical data loading
        @self.app.post(f"{self.api_prefix}/load/historical")
        async def load_historical(
            symbols: List[str],
            intervals: List[str],
            start_date: datetime,
            end_date: Optional[datetime] = None,
            exchanges: Optional[List[str]] = None
        ):
            """Load historical data"""
            return await self._load_historical(symbols, intervals, start_date, end_date, exchanges)
        
        # Statistics and monitoring
        @self.app.get(f"{self.api_prefix}/stats")
        async def get_stats():
            """Get API and service statistics"""
            return await self._get_stats()
        
        @self.app.get(f"{self.api_prefix}/health")
        async def health_check():
            """Health check endpoint"""
            return {"status": "healthy", "timestamp": datetime.now()}

    # Implementation methods
    async def _create_asset(self, asset: CryptoAssetModel) -> Dict[str, str]:
        """Create or update crypto asset"""
        try:
            self._update_stats("create_asset")
            
            with get_db_session() as session:
                # Check if asset exists
                existing = session.query(CryptoAsset).filter(
                    CryptoAsset.symbol == asset.symbol
                ).first()
                
                if existing:
                    # Update existing asset
                    for field, value in asset.dict(exclude_unset=True).items():
                        setattr(existing, field, value)
                    session.commit()
                    return {"status": "updated", "symbol": asset.symbol}
                else:
                    # Create new asset
                    new_asset = CryptoAsset(
                        id=f"crypto_asset_{asset.symbol.lower()}",
                        entity_id=f"crypto_asset_{asset.symbol.lower()}",
                        entity_type="crypto",
                        exchange="meta",
                        code=asset.symbol,
                        name=asset.full_name,
                        timestamp=datetime.now(),
                        **asset.dict(exclude={'symbol', 'full_name'})
                    )
                    session.add(new_asset)
                    session.commit()
                    return {"status": "created", "symbol": asset.symbol}
                    
        except Exception as e:
            logger.error(f"Error creating asset {asset.symbol}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def _get_assets(self, symbols: Optional[List[str]], limit: int) -> Dict:
        """Get crypto assets"""
        try:
            self._update_stats("get_assets")
            
            with get_db_session() as session:
                query = session.query(CryptoAsset)
                
                if symbols:
                    query = query.filter(CryptoAsset.symbol.in_(symbols))
                
                assets = query.limit(limit).all()
                
                result = []
                for asset in assets:
                    result.append({
                        "symbol": asset.symbol,
                        "full_name": asset.name,
                        "market_cap": asset.market_cap,
                        "circulating_supply": asset.circulating_supply,
                        "is_stablecoin": asset.is_stablecoin,
                        "consensus_mechanism": asset.consensus_mechanism
                    })
                
                return {"assets": result, "count": len(result)}
                
        except Exception as e:
            logger.error(f"Error getting assets: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def _create_pair(self, pair: CryptoPairModel) -> Dict[str, str]:
        """Create or update trading pair"""
        try:
            self._update_stats("create_pair")
            
            with get_db_session() as session:
                # Check if pair exists
                existing = session.query(CryptoPair).filter(
                    CryptoPair.code == pair.symbol,
                    CryptoPair.exchange == pair.exchange
                ).first()
                
                if existing:
                    # Update existing pair
                    for field, value in pair.dict(exclude_unset=True).items():
                        if hasattr(existing, field):
                            setattr(existing, field, value)
                    session.commit()
                    return {"status": "updated", "symbol": pair.symbol}
                else:
                    # Create new pair
                    new_pair = CryptoPair(
                        id=f"cryptopair_{pair.exchange}_{pair.symbol.replace('/', '')}",
                        entity_id=f"cryptopair_{pair.exchange}_{pair.symbol.replace('/', '')}",
                        entity_type="cryptopair",
                        exchange=pair.exchange,
                        code=pair.symbol,
                        name=f"{pair.base_symbol}/{pair.quote_symbol}",
                        timestamp=datetime.now(),
                        **pair.dict(exclude={'symbol', 'exchange'})
                    )
                    session.add(new_pair)
                    session.commit()
                    return {"status": "created", "symbol": pair.symbol}
                    
        except Exception as e:
            logger.error(f"Error creating pair {pair.symbol}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def _ingest_ohlcv(
        self,
        exchange: str,
        symbol: str,
        interval: str,
        data: List[OHLCVDataModel]
    ) -> Dict:
        """Ingest OHLCV candlestick data"""
        try:
            self._update_stats("ingest_ohlcv")
            
            # Convert to DataFrame for processing
            df = pd.DataFrame([item.dict() for item in data])
            
            # Validate data
            if df.empty:
                raise ValueError("No data provided")
            
            # Sort by timestamp
            df = df.sort_values('timestamp')
            
            # Basic validation
            invalid_records = df[
                (df['high'] < df[['open', 'close', 'low']].max(axis=1)) |
                (df['low'] > df[['open', 'close', 'high']].min(axis=1)) |
                (df['volume'] < 0)
            ]
            
            if not invalid_records.empty:
                self.stats["validation_errors"] += len(invalid_records)
                logger.warning(f"Removed {len(invalid_records)} invalid OHLCV records")
                df = df[~df.index.isin(invalid_records.index)]
            
            # Store data (mock implementation - replace with actual storage)
            self.stats["ingestion_records"] += len(df)
            
            logger.info(f"Ingested {len(df)} OHLCV records for {symbol} on {exchange}")
            
            return {
                "status": "success",
                "records_ingested": len(df),
                "records_rejected": len(invalid_records),
                "symbol": symbol,
                "exchange": exchange,
                "interval": interval
            }
            
        except Exception as e:
            logger.error(f"Error ingesting OHLCV data: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    async def _ingest_trades(
        self,
        exchange: str,
        symbol: str,
        data: List[TradeDataModel]
    ) -> Dict:
        """Ingest trade execution data"""
        try:
            self._update_stats("ingest_trades")
            
            df = pd.DataFrame([item.dict() for item in data])
            
            if df.empty:
                raise ValueError("No trade data provided")
            
            # Basic validation
            invalid_records = df[
                (df['price'] <= 0) | (df['quantity'] <= 0)
            ]
            
            if not invalid_records.empty:
                self.stats["validation_errors"] += len(invalid_records)
                df = df[~df.index.isin(invalid_records.index)]
            
            self.stats["ingestion_records"] += len(df)
            
            return {
                "status": "success",
                "records_ingested": len(df),
                "records_rejected": len(invalid_records),
                "symbol": symbol,
                "exchange": exchange
            }
            
        except Exception as e:
            logger.error(f"Error ingesting trade data: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    async def _ingest_orderbook(
        self,
        exchange: str,
        symbol: str,
        data: List[OrderBookDataModel]
    ) -> Dict:
        """Ingest order book snapshots"""
        try:
            self._update_stats("ingest_orderbook")
            
            if not data:
                raise ValueError("No order book data provided")
            
            processed_count = 0
            for snapshot in data:
                # Validate bid/ask ordering
                bids = sorted(snapshot.bids, key=lambda x: x[0], reverse=True)
                asks = sorted(snapshot.asks, key=lambda x: x[0])
                
                # Check for crossed market
                if bids and asks and bids[0][0] >= asks[0][0]:
                    self.stats["validation_errors"] += 1
                    continue
                
                processed_count += 1
            
            self.stats["ingestion_records"] += processed_count
            
            return {
                "status": "success",
                "records_ingested": processed_count,
                "records_rejected": len(data) - processed_count,
                "symbol": symbol,
                "exchange": exchange
            }
            
        except Exception as e:
            logger.error(f"Error ingesting order book data: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    async def _bulk_ingest(self, request: DataIngestionRequest) -> Dict:
        """Handle bulk data ingestion"""
        try:
            self._update_stats("bulk_ingest")
            
            data_type = request.data_type
            
            if data_type == "ohlcv":
                ohlcv_data = [OHLCVDataModel(**item) for item in request.data]
                return await self._ingest_ohlcv(
                    request.exchange, request.symbol, request.interval, ohlcv_data
                )
            elif data_type == "trades":
                trade_data = [TradeDataModel(**item) for item in request.data]
                return await self._ingest_trades(request.exchange, request.symbol, trade_data)
            elif data_type == "orderbook":
                ob_data = [OrderBookDataModel(**item) for item in request.data]
                return await self._ingest_orderbook(request.exchange, request.symbol, ob_data)
            else:
                raise ValueError(f"Unsupported data type: {data_type}")
                
        except Exception as e:
            logger.error(f"Error in bulk ingestion: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    async def _start_streams(self) -> Dict:
        """Start data streaming services"""
        try:
            if not self.stream_service.is_running:
                self.stream_service.start()
                return {"status": "started", "message": "Data streams started successfully"}
            else:
                return {"status": "already_running", "message": "Data streams are already running"}
        except Exception as e:
            logger.error(f"Error starting streams: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def _stop_streams(self) -> Dict:
        """Stop data streaming services"""
        try:
            if self.stream_service.is_running:
                self.stream_service.stop()
                return {"status": "stopped", "message": "Data streams stopped successfully"}
            else:
                return {"status": "not_running", "message": "Data streams are not running"}
        except Exception as e:
            logger.error(f"Error stopping streams: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def _subscribe_streams(
        self,
        data_type: str,
        symbols: List[str],
        exchanges: Optional[List[str]]
    ) -> Dict:
        """Subscribe to data streams"""
        try:
            if not self.stream_service.is_running:
                raise ValueError("Stream service is not running")
            
            if data_type == "ticker":
                self.stream_service.subscribe_ticker(symbols, exchanges)
            elif data_type == "klines":
                self.stream_service.subscribe_klines(symbols, ["1m"], exchanges)
            elif data_type == "trades":
                self.stream_service.subscribe_trades(symbols, exchanges)
            elif data_type == "orderbook":
                self.stream_service.subscribe_orderbook(symbols, 20, exchanges)
            else:
                raise ValueError(f"Unsupported stream type: {data_type}")
            
            return {
                "status": "subscribed",
                "data_type": data_type,
                "symbols": symbols,
                "exchanges": exchanges or self.stream_service.exchanges
            }
            
        except Exception as e:
            logger.error(f"Error subscribing to streams: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    async def _get_stream_status(self) -> Dict:
        """Get streaming service status"""
        try:
            stats = self.stream_service.get_stream_stats()
            return {
                "is_running": self.stream_service.is_running,
                "statistics": stats
            }
        except Exception as e:
            logger.error(f"Error getting stream status: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def _load_historical(
        self,
        symbols: List[str],
        intervals: List[str],
        start_date: datetime,
        end_date: Optional[datetime],
        exchanges: Optional[List[str]]
    ) -> Dict:
        """Load historical data"""
        try:
            self._update_stats("load_historical")
            
            # Convert intervals to IntervalLevel
            interval_levels = []
            interval_map = {
                "1m": IntervalLevel.LEVEL_1MIN,
                "5m": IntervalLevel.LEVEL_5MIN,
                "15m": IntervalLevel.LEVEL_15MIN,
                "30m": IntervalLevel.LEVEL_30MIN,
                "1h": IntervalLevel.LEVEL_1HOUR,
                "4h": IntervalLevel.LEVEL_4HOUR,
                "1d": IntervalLevel.LEVEL_1DAY
            }
            
            for interval in intervals:
                if interval in interval_map:
                    interval_levels.append(interval_map[interval])
                else:
                    raise ValueError(f"Unsupported interval: {interval}")
            
            # Load data
            results = self.data_loader.load_historical_kdata(
                symbols=symbols,
                intervals=interval_levels,
                start_date=start_date,
                end_date=end_date,
                exchanges=exchanges
            )
            
            return {
                "status": "completed",
                "datasets_loaded": len(results),
                "symbols": symbols,
                "intervals": intervals,
                "start_date": start_date,
                "end_date": end_date,
                "loading_stats": self.data_loader.get_loading_stats()
            }
            
        except Exception as e:
            logger.error(f"Error loading historical data: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    async def _get_stats(self) -> Dict:
        """Get comprehensive API statistics"""
        uptime = datetime.now() - self.stats["start_time"]
        
        stats = {
            "api_stats": {
                **self.stats,
                "uptime_seconds": uptime.total_seconds()
            },
            "data_loader_stats": self.data_loader.get_loading_stats(),
        }
        
        if self.stream_service:
            stats["stream_stats"] = self.stream_service.get_stream_stats()
        
        return stats

    def _update_stats(self, endpoint: str):
        """Update request statistics"""
        self.stats["requests_total"] += 1
        if endpoint not in self.stats["requests_by_endpoint"]:
            self.stats["requests_by_endpoint"][endpoint] = 0
        self.stats["requests_by_endpoint"][endpoint] += 1

    def get_app(self) -> FastAPI:
        """Get FastAPI application instance"""
        return self.app

# Convenience function to create and configure the API
def create_crypto_api(
    data_loader: CryptoDataLoader = None,
    stream_service: CryptoStreamService = None,
    **kwargs
) -> FastAPI:
    """Create and configure crypto API ingestion service"""
    service = CryptoAPIIngestion(
        data_loader=data_loader,
        stream_service=stream_service,
        **kwargs
    )
    return service.get_app()