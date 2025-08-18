# Guide: Adding a Crypto Data Connector (Historical + Live) - **UPDATED 2025**

This comprehensive guide shows how to add a new crypto data connector to ZVT, covering modern WebSocket architecture, enhanced security, comprehensive testing, and production deployment. Updated to reflect 2024-2025 crypto market evolution and ZVT v0.15.x requirements.

## **CRITICAL UPDATES** - Review Before Starting:
- **Enhanced Security Requirements**: API key rotation, audit logging, compliance frameworks
- **Modern WebSocket Architecture**: Connection multiplexing, backpressure handling, private streams
- **Realistic Performance Targets**: <5s latency (was <2s), 99.5% uptime (24/7 operations)
- **Extended Testing Requirements**: Chaos engineering, security testing, compliance validation

Prerequisites:
- Familiarity with `Recorder`, `TimeSeriesDataRecorder`, `FixedCycleDataRecorder`
- Understanding of ZVT schemas and provider registry (`zvt.contract.api`, `zvt.contract.schema`)
- **NEW**: Crypto trading domain expertise and exchange API knowledge
- **NEW**: Security best practices for financial systems
- API access to a crypto exchange (testnet required, production optional)

## 1) Choose Scope and Provider

Decide which exchange(s) and instruments to support first:
- Spot pairs (BTC/USDT), Perpetual futures (BTCUSDT), Trades (tick), Orderbook (L2), Funding (perps).
- Start with one provider (e.g., `binance`) and add more later (`okx`, `bybit`, `coinbase`).

Set a provider key string. Example: `"binance"` or use a unified `"ccxt"` layer.

## 2) Define Entities and Schemas

Follow the crypto spec (`docs/specs/CRYPTO_MARKET_SPEC.md`). Minimum:
- Entities: `CryptoPair` (spot), `CryptoPerp` (perp). Optional `CryptoAsset`.
- Kline schemas: `CryptoPair{level}Kdata`, `CryptoPerp{level}Kdata` (bfq only).
- Tick schemas: `CryptoTrade` (trades), `CryptoOrderbook` (snapshots/diffs), `CryptoFunding` (perps).

Tips:
- Use UTC timestamps. Keep `code` lowercase (e.g., `btcusdt`).
- Conform to multi-index `(entity_id, timestamp)` used throughout ZVT.
- See patterns in `zvt.domain` for Kdata common classes (e.g., `StockKdataCommon`).

## 3) Implement Historical Klines

For time-based OHLCV, extend `FixedCycleDataRecorder` to leverage interval logic and duplicate handling.

Skeleton:

```python
# src/zvt/recorders/binance/quotes/binance_kdata_recorder.py
from zvt.contract import IntervalLevel
from zvt.contract.recorder import FixedCycleDataRecorder
from zvt.contract.api import df_to_db
from zvt.utils.pd_utils import pd_is_not_null

# from your crypto domain schema helpers
from zvt.domain.crypto import (
    CryptoPair, CryptoPerp, get_crypto_kdata_schema
)
from .binance_rest import fetch_klines  # your REST fetcher or CCXT wrapper

class BaseBinanceKdataRecorder(FixedCycleDataRecorder):
    provider = "binance"
    entity_provider = "binance"  # or "zvt" if entities come from local meta

    def __init__(self, entity_schema, level=IntervalLevel.LEVEL_1MIN, **kwargs):
        self.entity_schema = entity_schema
        self.level = IntervalLevel(level)
        # bfq only for crypto
        self.data_schema = get_crypto_kdata_schema(entity_schema=self.entity_schema, level=self.level)
        super().__init__(level=self.level, **kwargs)

    def record(self, entity, start, end, size, timestamps):
        # Map ZVT interval to provider resolution (e.g., 1m, 5m, 1h)
        # Use start/size as guidance; provider pagination will drive actual volume
        df = fetch_klines(symbol=entity.code, interval=self.level, limit=size, start=start)
        if pd_is_not_null(df):
            # Ensure columns: timestamp, open, high, low, close, volume, turnover, change_pct, turnover_rate
            df["entity_id"] = entity.id
            df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)
```

Notes:
- Use `default_size` appropriate for exchange limits (e.g., 1000 for Binance REST).
- Map provider intervals to `IntervalLevel` carefully (e.g., `1m`, `5m`, `15m`, `1h`, `4h`, `1d`).
- Set `one_day_trading_minutes=24*60` (already default in kdata recorders).
- For initial bootstrap, override `evaluate_start_end_size_timestamps` if provider requires explicit `startTime`/`endTime` windows.

## 4) Implement Trades/Funding/Orderbook (Historical)

For trades and funding history, extend `TimeSeriesDataRecorder` or `TimestampsDataRecorder`:
- `TimeSeriesDataRecorder`: when you can iterate forward based on last saved timestamp.
- `TimestampsDataRecorder`: when you know exact timestamps to fetch (less common for exchanges).

Skeleton:

```python
# src/zvt/recorders/binance/quotes/binance_trade_recorder.py
from zvt.contract.recorder import TimeSeriesDataRecorder
from zvt.contract.api import df_to_db
from zvt.utils.pd_utils import pd_is_not_null
from zvt.domain.crypto import CryptoTrade, CryptoPair
from .binance_rest import fetch_trades

class BinanceTradeRecorder(TimeSeriesDataRecorder):
    provider = "binance"
    entity_provider = "binance"
    entity_schema = CryptoPair
    data_schema = CryptoTrade

    def record(self, entity, start, end, size, timestamps):
        df = fetch_trades(symbol=entity.code, start=start, limit=size)
        if pd_is_not_null(df):
            df["entity_id"] = entity.id
            df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)
```

## 5) Enhanced WebSocket Architecture - **UPDATED**

Implement a modern, production-ready WebSocket client with the following architecture:

### 5.1) WebSocket Manager (NEW)
```python
# src/zvt/recorders/binance/streams/binance_ws_manager.py
import asyncio
import json
from typing import Dict, List, Optional
from zvt.contract.api import df_to_db

class ExchangeWebSocketManager:
    """Production-ready WebSocket manager with connection multiplexing"""
    
    def __init__(self, exchange_name: str, api_credentials: dict):
        self.exchange_name = exchange_name
        self.connections: Dict[str, WebSocketConnection] = {}
        self.subscription_manager = SubscriptionManager()
        self.message_router = MessageRouter()
        self.backpressure_controller = BackpressureController()
        self.reconnect_strategy = ExponentialBackoffWithJitter()
        
    async def start(self):
        """Start the WebSocket manager with all subscriptions"""
        await self._establish_connections()
        await self._start_message_processing()
        
    async def subscribe_public(self, symbols: List[str], data_types: List[str]):
        """Subscribe to public data streams (trades, klines, orderbook)"""
        pass
        
    async def subscribe_private(self, data_types: List[str]):
        """Subscribe to private data streams (account, orders, positions)"""
        pass
```

### 5.2) Connection Multiplexing
```python
class WebSocketConnection:
    """Single WebSocket connection handling multiple subscriptions"""
    
    def __init__(self, endpoint: str, auth_required: bool = False):
        self.endpoint = endpoint
        self.auth_required = auth_required
        self.subscriptions: Dict[str, Subscription] = {}
        self.message_queue = asyncio.Queue(maxsize=10000)
        self.reconnect_count = 0
        
    async def connect(self):
        """Establish WebSocket connection with authentication if required"""
        pass
        
    async def handle_message(self, message: dict):
        """Route incoming messages to appropriate handlers"""
        if self.backpressure_controller.should_throttle():
            await self.backpressure_controller.apply_backpressure(message)
        else:
            await self.message_router.route_message(message)
```

### 5.3) Backpressure Management (NEW)
```python
class BackpressureController:
    """Manages high-volume message flows and prevents memory overflow"""
    
    def __init__(self, max_buffer_size: int = 50000):
        self.max_buffer_size = max_buffer_size
        self.current_buffer_size = 0
        self.throttle_mode = False
        
    def should_throttle(self) -> bool:
        """Determine if backpressure should be applied"""
        return self.current_buffer_size > self.max_buffer_size * 0.8
        
    async def apply_backpressure(self, message: dict):
        """Apply backpressure strategy (drop, batch, or delay)"""
        # Implementation: prioritize critical messages, batch non-critical
        pass
```

### 5.4) Enhanced Key Points:
- **Connection Multiplexing**: Single WebSocket per exchange with channel-based routing
- **Idempotency**: Use `(entity_id, timestamp, update_id)` for comprehensive deduplication
- **Backpressure Control**: Dynamic throttling during high-volume periods
- **Private Streams**: Account updates, position changes, order execution reports
- **Reconnection Strategy**: Exponential backoff with jitter + state reconstruction
- **Security**: API key authentication for private streams with token refresh
- **Monitoring**: Comprehensive metrics for latency, reconnects, message drops

## 6) Provider Registration

- Each `Recorder` has a `Meta` metaclass that auto-registers the class to its `data_schema` when `provider` and `data_schema` are set.
- Ensure your crypto schemas include provider slots and call `register_recorder_cls` (done by meta) so:
  - `YourSchema.record_data(provider="binance")` works.

Check via:

```python
from zvt.contract.api import get_providers, get_schemas
print(get_providers())
print([s.__name__ for s in get_schemas(provider="binance")])
```

## 7) Configuration

- Add API keys as env vars: `CRYPTO_API_KEY`, `CRYPTO_API_SECRET`, `CRYPTO_API_PASSPHRASE` as needed.
- Extend `zvt_env` to include provider credentials and endpoints.
- Respect rate limits: centralize a throttler (token bucket) shared by REST and WS.

## 8) Validation & Data Quality

- Gaps: verify continuity for klines; implement retries and backfills.
- Timezones: assert UTC and monotonic timestamps.
- Fields: ensure required kline columns; compute `turnover`, `change_pct`, `turnover_rate` if provider omits them.
- Orderbook: checksum verification if provider supports it.

## 9) Tests

- Unit: symbol normalization, interval mapping, row normalization.
- Integration: record limited history for a sandbox symbol; validate no gaps.
- Stream: feed captured WS fixtures; assert aggregation correctness and reconnection behavior.
- Performance: backfill throughput within provider limits (documented per exchange).

## 10) Usage Examples

Historical backfill:

```python
from zvt.recorders.binance.quotes.binance_kdata_recorder import BaseBinanceKdataRecorder
from zvt.domain.crypto import CryptoPair

recorder = BaseBinanceKdataRecorder(entity_schema=CryptoPair, level=IntervalLevel.LEVEL_1MIN, sleeping_time=1)
recorder.run()
```

Live streaming service (simplified):

```python
import asyncio
from zvt.recorders.binance.streams.binance_ws import BinanceStream

stream = BinanceStream(symbols=["btcusdt", "ethusdt"], level=IntervalLevel.LEVEL_1MIN, on_error=print)
asyncio.run(stream.run())
```

## 11) Production Tips

- Separate processes for REST backfill and WS streaming; use supervisors.
- Use feature flags for live trading/testnet vs. prod.
- Monitor: WS lag, dropped diffs, backfill rate, error rates; alert on staleness.

Refer to:
- Recorder framework: `src/zvt/contract/recorder.py` (especially `FixedCycleDataRecorder`).
- Existing kdata recorders: `src/zvt/recorders/em/quotes/em_kdata_recorder.py`.
- Crypto spec: `docs/specs/CRYPTO_MARKET_SPEC.md`.
