# Crypto Market Specification (ZVT v0.13.3+)

## Scope

Add first-class crypto market support for spot and perpetual futures across major centralized exchanges (CEX). The design mirrors existing stock/index abstractions while addressing 24/7 trading, symbol normalization, real-time streaming, and exchange-specific constraints.

## Goals

- Unified, exchange-agnostic data/query/record interfaces for crypto.
- Support top exchanges: Binance, OKX, Bybit, Coinbase (Phase 1-2).
- Historical and real-time data for OHLCV (multi-interval), trades, order book (L2 snapshots + incremental depth), and funding.
- Backtesting and live trading adapters with realistic fees, maker/taker, lot sizes, and margin modes.
- Reuse factor/trader frameworks across crypto with minimal changes.

## Non-Goals (Initial)

- On-chain DEX integration and DeFi protocols.
- Options and delivery futures beyond perpetuals.
- Cross-exchange smart order routing.

## Entities & IDs

Entity types follow `entity_type_exchange_code` pattern.

- `CryptoAsset` (base asset metadata): `crypto_{exchange}_{symbol}` e.g., `crypto_binance_btc`.
- `CryptoPair` (spot pair): `cryptopair_{exchange}_{base}{quote}` e.g., `cryptopair_binance_btcusdt`.
- `CryptoPerp` (USDT-margined perpetual): `cryptoperp_{exchange}_{base}{quote}` e.g., `cryptoperp_binance_btcusdt`.

Notes:
- Code is lowercase alnum; exchange in lowercase; keep provider-specific canonical form (e.g., `btcusdt`).
- Entity display `name` retains uppercase (e.g., `BTC/USDT`).

## Schemas

Time-series schemas mirror KData/Quote with crypto specifics.

- `CryptoPair{level}Kdata` (bfq only): OHLCV for spot pairs.
- `CryptoPerp{level}Kdata` (bfq only): OHLCV for perpetuals.
- `CryptoTrade` (tick-level trades): time, price, amount, side, trade_id.
- `CryptoOrderbook` (book snapshots/increments): bids/asks with depth N and update_id.
- `CryptoFunding` (perp): rate, next_funding_time, realized_funding.

Levels: `tick, 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 1d`.

Adjustment types: `bfq` only (no splits/dividends).

## Providers

- Historical via REST (CCXT abstraction first; native clients optional later).
- Real-time via WebSocket streams per exchange (native SDKs or lightweight clients).

Phase 1 providers:
- `binance` (spot, usdm futures)
- `okx` (spot, usdt-swap)
- `bybit` (spot, usdt-perp)
- `coinbase` (spot)

Provider keys: add to `zvt_env` and `.env`: `CRYPTO_API_KEY`, `CRYPTO_API_SECRET`, `CRYPTO_API_PASSPHRASE` (when needed), per-exchange namespaces.

## Normalization

- Symbol mapping table: provider symbol ↔ canonical `base`, `quote`, `code`.
- Timezone UTC; all timestamps stored as UTC.
- Precision/lot sizes stored per entity: `price_step`, `qty_step`, `min_notional`.
- Fees: `maker_fee`, `taker_fee` per entity/exchange.

## Data Recording

- Backfill: bounded by exchange limits; automatic pagination and rate-limit backoff.
- Incremental updates: watermarking by `end_time`/`update_id`.
- Streaming: fan-in WebSocket trades/klines/orderbook into append-only buffers; aggregate klines from trades where klines stream unavailable.

Quality:
- Gaps detection and retry; checksum/`update_id` ordering for orderbook diffs.
- Idempotent persistence (by `(entity_id, timestamp)` or `update_id`).

## Query

`query_data` mirrors existing: multi-index `(entity_id, timestamp)` with standard columns.

Examples:
- Recent 500 1m klines for BTC/USDT on Binance spot:
  - `CryptoPair1mKdata.query_data(provider="binance", code="btcusdt", limit=500)`

## Trading

Accounts:
- `CCXTAccount` (generic): API-key based spot/perp trading; order types: market/limit; tif: GTC; reduce-only for perps.
- `ExchangeAccount` (native): optional per-exchange implementation for performance and special features.

Features:
- Position mode: one-way or hedge for perps.
- Margin mode: cross or isolated; leverage per symbol.
- Risk and fee modeling: maker/taker fees, funding impacts on PnL.

Sim/Backtest:
- 24/7 calendar; trade at kline close/open; volume-aware slippage; fee modeling.
- Funding payments at 8h intervals (configurable by exchange).

## WebSocket Architecture (Updated)

### Modern WebSocket Implementation
- **Connection Multiplexing**: Single WebSocket per exchange with channel multiplexing for efficiency
- **Authentication Patterns**: Support both API-key and JWT-based auth for private streams
- **Backpressure Handling**: Implement flow control and buffer management for high-volume periods
- **Reconnection Strategy**: Exponential backoff with jitter, state reconstruction from last sequence ID
- **Private Data Streams**: Account updates, position changes, order execution reports

### Stream Management
```python
# WebSocket connection architecture
class ExchangeWebSocketManager:
    - connection_pool: Dict[str, WebSocketConnection]
    - subscription_manager: SubscriptionManager
    - message_router: MessageRouter
    - backpressure_controller: BackpressureController
```

## REST Additions/Compatibility

- Providers: expose `ccxt`, `binance`, `okx`, `bybit`, `coinbase` in `/api/data/providers`.
- Schemas: add crypto schemas via `/api/data/schemas?provider=binance`.
- Trading endpoints unchanged; accept crypto `entity_ids` and route to quote schemas for stats.
- **API Versioning**: Support for multiple API versions per exchange with graceful degradation

## Security & Compliance (Enhanced)

### API Key Management
- **Encrypted Storage**: AES-256 encryption for API keys with HSM support for production
- **Key Rotation**: Automated key rotation every 90 days with zero-downtime deployment
- **Environment Isolation**: Separate key stores for dev/staging/prod with strict access controls
- **Key Scoping**: Read-only keys for data collection, trade-enabled keys for live trading only

### Audit & Compliance
- **Audit Logging**: Complete audit trail for all API calls, key usage, and data access
- **Regulatory Compliance**: GDPR, SOX, and jurisdiction-specific compliance frameworks
- **Data Retention**: Configurable retention policies with automated archival
- **Access Controls**: Role-based access with multi-factor authentication for production keys

### Security Monitoring
- **Anomaly Detection**: ML-based detection of unusual API usage patterns
- **Rate Limit Violations**: Automated alerting and remediation for rate limit breaches
- **Key Compromise Detection**: Monitoring for signs of compromised API keys

## Telemetry

- Metrics: WS reconnects, message lag, dropped diffs, backfill rate.
- Alerts: stream staleness, funding fetch failures, order rejects.

## Acceptance Criteria (Updated - Phases 1-2)

### Phase 1: Foundation (12 weeks)
- **Data Quality**
  - Record and query 180 days of 1m OHLCV for top 50 Binance spot pairs with <0.5% gaps
  - Stream trades and aggregate 1m klines for 5 pairs concurrently with <5s end-to-end lag
  - Achieve 99.5% data completeness over 30-day continuous operation
  - Cross-validate REST vs WebSocket data with <0.1% price deviation
- **Trading (Testnet Only)**
  - Paper-trade orders with realistic fee/slippage modeling; PnL within ±0.2% vs. reference
  - Place/cancel orders on Binance testnet with <500ms average execution time
  - Support basic order types: market, limit, stop-loss
- **System Reliability**
  - Automatic WS reconnect with <30s recovery time
  - Orderbook synchronization with sequence gap detection and recovery
  - 99.0% uptime during continuous 30-day testing period

### Phase 2: Multi-Exchange (18 weeks total)
- **Extended Coverage**
  - Support 4 exchanges (Binance, OKX, Bybit, Coinbase) with unified interface
  - 100+ trading pairs across all exchanges with dynamic symbol discovery
  - Cross-exchange price consistency monitoring with alerting for >1% deviations
- **Performance & Scale**
  - Stream 25+ concurrent symbols per exchange with <3s average latency
  - Handle peak loads of 10,000+ messages/second during high volatility
  - Memory usage <4GB for full multi-exchange deployment
- **Production Readiness**
  - Comprehensive monitoring and alerting system operational
  - Security audit completed with all critical findings resolved
  - Documentation coverage >95% for public APIs and admin procedures

## Risks & Mitigations

- Rate limits: centralized throttler, exponential backoff, burst control.
- WS instability: jittered reconnect, resubscribe replay with last `update_id`.
- Symbol drift: scheduled metadata refresh, diff-based updates.
- Compliance: testnet-first by default; prod keys gated by config.

## Implementation Enhancements (Post Epic 1 Review)

### Schema Generator Integration (Critical)

**Automated Schema Generation**
Integration with ZVT's existing `gen_kdata_schema` function:

```python
# src/zvt/fill_crypto_project.py
def gen_crypto_kdata_schemas():
    """Generate all crypto kdata schemas following ZVT patterns"""
    
    # Crypto spot pairs - all intervals
    gen_kdata_schema(
        pkg="zvt",
        providers=["binance", "okx", "bybit", "coinbase", "ccxt"],
        entity_type="cryptopair", 
        levels=[
            IntervalLevel.LEVEL_1MIN,
            IntervalLevel.LEVEL_5MIN,
            IntervalLevel.LEVEL_15MIN,
            IntervalLevel.LEVEL_30MIN,
            IntervalLevel.LEVEL_1HOUR,
            IntervalLevel.LEVEL_4HOUR,
            IntervalLevel.LEVEL_1DAY
        ],
        adjust_types=[None],  # bfq only for crypto
        entity_in_submodule=True,
        kdata_module="crypto.quotes"
    )
    
    # Crypto perpetual futures - same intervals
    gen_kdata_schema(
        pkg="zvt",
        providers=["binance", "okx", "bybit", "coinbase", "ccxt"], 
        entity_type="cryptoperp",
        levels=[IntervalLevel.LEVEL_1MIN, IntervalLevel.LEVEL_5MIN, IntervalLevel.LEVEL_15MIN,
                IntervalLevel.LEVEL_30MIN, IntervalLevel.LEVEL_1HOUR, IntervalLevel.LEVEL_4HOUR, 
                IntervalLevel.LEVEL_1DAY],
        adjust_types=[None],
        entity_in_submodule=True,
        kdata_module="crypto.quotes"
    )
```

### Provider Framework Enhancement (High Priority)

**Unified Provider Base Classes**:
```python
# src/zvt/recorders/crypto/base_crypto_provider.py
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import asyncio

class BaseCryptoProvider(ABC):
    """Base class for all crypto exchange providers"""
    
    def __init__(self, api_key: str = None, api_secret: str = None, testnet: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.rate_limiter = TokenBucketRateLimiter()
        self.websocket_manager = None
        
    @abstractmethod
    async def get_symbols(self) -> List[Dict]:
        """Get all trading symbols from exchange"""
        pass
        
    @abstractmethod  
    async def get_klines(self, symbol: str, interval: str, limit: int = 1000) -> List[Dict]:
        """Get historical kline data"""
        pass
        
    @abstractmethod
    async def subscribe_trades(self, symbols: List[str], callback) -> None:
        """Subscribe to real-time trades"""
        pass
        
    @abstractmethod
    async def subscribe_orderbook(self, symbols: List[str], callback) -> None:
        """Subscribe to real-time orderbook updates"""
        pass

class BaseExchangeAdapter:
    """Adapter pattern for exchange-specific implementations"""
    
    def __init__(self, provider: BaseCryptoProvider):
        self.provider = provider
        
    def normalize_symbol(self, exchange_symbol: str) -> str:
        """Normalize exchange symbol to ZVT format"""
        return exchange_symbol.lower()
        
    def denormalize_symbol(self, zvt_symbol: str) -> str:
        """Convert ZVT symbol to exchange format"""
        return zvt_symbol.upper()
```

### Real-time Data Quality Framework (Critical)

**Data Quality Monitoring**:
```python
# src/zvt/utils/crypto/data_quality.py
class CryptoDataQualityValidator:
    """Real-time data quality validation and monitoring"""
    
    def __init__(self):
        self.validators = {
            'price_sanity': PriceSanityValidator(),
            'volume_anomaly': VolumeAnomalyDetector(), 
            'timestamp_continuity': TimestampContinuityChecker(),
            'cross_exchange_consistency': CrossExchangeValidator(),
            'orderbook_integrity': OrderbookIntegrityValidator()
        }
        
    async def validate_kline(self, kline_data: Dict) -> ValidationResult:
        """Validate incoming kline data"""
        results = []
        for name, validator in self.validators.items():
            result = await validator.validate(kline_data)
            results.append(result)
            
        return ValidationResult.aggregate(results)
        
    async def validate_trade(self, trade_data: Dict) -> ValidationResult:
        """Validate incoming trade data"""
        # Price within reasonable bounds
        # Volume consistency
        # Side validation
        # Trade ID uniqueness
        pass
        
    async def validate_orderbook(self, orderbook_data: Dict) -> ValidationResult:
        """Validate orderbook data integrity"""
        # Checksum validation
        # Sequence ID continuity
        # Price level ordering
        # Volume consistency
        pass

class ValidationResult:
    def __init__(self, is_valid: bool, warnings: List[str] = None, errors: List[str] = None):
        self.is_valid = is_valid
        self.warnings = warnings or []
        self.errors = errors or []
        
    @classmethod 
    def aggregate(cls, results: List['ValidationResult']):
        """Aggregate multiple validation results"""
        is_valid = all(r.is_valid for r in results)
        warnings = []
        errors = []
        for r in results:
            warnings.extend(r.warnings)
            errors.extend(r.errors)
        return cls(is_valid, warnings, errors)
```

### Enhanced Monitoring & Observability (24/7 Operations)

**Comprehensive Metrics Collection**:
```python
# src/zvt/monitoring/crypto_metrics.py
from prometheus_client import Counter, Histogram, Gauge, Summary

class CryptoMetrics:
    """Prometheus metrics for crypto operations"""
    
    # WebSocket metrics
    websocket_reconnects = Counter('crypto_websocket_reconnects_total', 
                                 'WebSocket reconnection count', ['exchange', 'stream_type'])
    websocket_message_lag = Histogram('crypto_websocket_message_lag_seconds',
                                    'WebSocket message processing lag', ['exchange'])
    websocket_messages_dropped = Counter('crypto_websocket_messages_dropped_total',
                                       'Dropped WebSocket messages', ['exchange', 'reason'])
    
    # Data quality metrics  
    data_validation_failures = Counter('crypto_data_validation_failures_total',
                                     'Data validation failures', ['exchange', 'validation_type'])
    price_deviation_alerts = Counter('crypto_price_deviation_alerts_total', 
                                   'Cross-exchange price deviation alerts', ['symbol'])
    data_gaps_detected = Counter('crypto_data_gaps_detected_total',
                               'Data gaps detected', ['exchange', 'symbol', 'interval'])
    
    # Performance metrics
    query_response_time = Histogram('crypto_query_response_time_seconds',
                                  'Database query response time', ['query_type'])
    backfill_rate = Gauge('crypto_backfill_rate_records_per_second', 
                         'Historical data backfill rate', ['exchange'])
    
    # Trading metrics  
    funding_rate_extreme = Gauge('crypto_funding_rate_extreme_count',
                               'Count of extreme funding rates', ['exchange'])
    order_latency = Histogram('crypto_order_latency_seconds',
                            'Order placement latency', ['exchange'])

# Enhanced alerting rules
CRYPTO_ALERT_RULES = {
    'websocket_reconnects_high': {
        'condition': 'rate(crypto_websocket_reconnects_total[5m]) > 0.1',
        'severity': 'warning',
        'message': 'High WebSocket reconnection rate for {{ $labels.exchange }}'
    },
    'data_validation_failures': {
        'condition': 'rate(crypto_data_validation_failures_total[5m]) > 0.01',
        'severity': 'critical', 
        'message': 'Data validation failures detected for {{ $labels.exchange }}'
    },
    'price_deviation_extreme': {
        'condition': 'crypto_price_deviation_alerts_total > 5',
        'severity': 'warning',
        'message': 'Extreme price deviation for {{ $labels.symbol }}'
    },
    'query_performance_degraded': {
        'condition': 'histogram_quantile(0.95, crypto_query_response_time_seconds) > 1.0',
        'severity': 'warning',
        'message': 'Crypto query performance degraded'
    }
}
```

### Configuration Management Framework

**Centralized Crypto Configuration**:
```python
# src/zvt/config/crypto_config.py
from dataclasses import dataclass
from typing import Dict, List, Optional
import os

@dataclass
class ExchangeConfig:
    """Configuration for individual crypto exchange"""
    name: str
    api_endpoint: str
    websocket_endpoint: str
    testnet_endpoint: str = None
    rate_limits: Dict[str, int] = None
    supported_intervals: List[str] = None
    max_kline_limit: int = 1000
    funding_intervals: List[int] = None
    
@dataclass
class CryptoConfig:
    """Master crypto configuration"""
    
    # Exchanges configuration
    exchanges: Dict[str, ExchangeConfig] = None
    
    # Data collection settings
    default_backfill_days: int = 180
    max_concurrent_streams: int = 25
    data_quality_checks_enabled: bool = True
    
    # Database settings
    crypto_db_path: str = "./data/crypto"
    backup_enabled: bool = True
    backup_interval_hours: int = 6
    
    # Monitoring settings
    metrics_enabled: bool = True
    prometheus_port: int = 9090
    alert_webhook_url: Optional[str] = None
    
    # Security settings
    api_key_rotation_days: int = 90
    encryption_key_env: str = "CRYPTO_ENCRYPTION_KEY"
    
    @classmethod
    def from_env(cls):
        """Load configuration from environment variables"""
        return cls(
            exchanges=cls._load_exchanges_config(),
            default_backfill_days=int(os.getenv('CRYPTO_BACKFILL_DAYS', 180)),
            max_concurrent_streams=int(os.getenv('CRYPTO_MAX_STREAMS', 25)),
            crypto_db_path=os.getenv('CRYPTO_DB_PATH', './data/crypto'),
            metrics_enabled=os.getenv('CRYPTO_METRICS_ENABLED', 'true').lower() == 'true',
            alert_webhook_url=os.getenv('CRYPTO_ALERT_WEBHOOK_URL')
        )
```

### Error Handling & Recovery Framework

**Comprehensive Error Handling**:
```python
# src/zvt/utils/crypto/error_handling.py
from enum import Enum
from typing import Optional, Callable
import asyncio

class CryptoErrorType(Enum):
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    API_KEY_INVALID = "api_key_invalid"
    WEBSOCKET_DISCONNECTED = "websocket_disconnected"
    DATA_QUALITY_FAILURE = "data_quality_failure"  
    EXCHANGE_MAINTENANCE = "exchange_maintenance"
    NETWORK_TIMEOUT = "network_timeout"
    ORDERBOOK_DESYNC = "orderbook_desync"
    FUNDING_RATE_MISSING = "funding_rate_missing"

class CryptoErrorHandler:
    """Centralized error handling for crypto operations"""
    
    def __init__(self):
        self.recovery_strategies = {
            CryptoErrorType.RATE_LIMIT_EXCEEDED: self._handle_rate_limit,
            CryptoErrorType.WEBSOCKET_DISCONNECTED: self._handle_websocket_disconnect,
            CryptoErrorType.API_KEY_INVALID: self._handle_invalid_api_key,
            CryptoErrorType.DATA_QUALITY_FAILURE: self._handle_data_quality_failure,
            CryptoErrorType.ORDERBOOK_DESYNC: self._handle_orderbook_desync
        }
        
    async def handle_error(self, error_type: CryptoErrorType, context: Dict) -> bool:
        """Handle error and return True if recovery successful"""
        if error_type in self.recovery_strategies:
            return await self.recovery_strategies[error_type](context)
        return False
        
    async def _handle_rate_limit(self, context: Dict) -> bool:
        """Handle rate limit exceeded"""
        exchange = context.get('exchange')
        wait_time = context.get('retry_after', 60)
        
        logger.warning(f"Rate limit exceeded for {exchange}, waiting {wait_time}s")
        await asyncio.sleep(wait_time)
        return True
        
    async def _handle_websocket_disconnect(self, context: Dict) -> bool:
        """Handle WebSocket disconnection with exponential backoff"""
        reconnect_attempts = context.get('reconnect_attempts', 0)
        max_attempts = context.get('max_attempts', 10)
        
        if reconnect_attempts >= max_attempts:
            logger.error("Max reconnection attempts reached")
            return False
            
        backoff_time = min(2 ** reconnect_attempts, 300)  # Max 5 minutes
        await asyncio.sleep(backoff_time)
        return True
```

## Open Questions (Updated)

- Funding compounding conventions across exchanges
- Asset precision migration path in DB schema  
- **NEW**: Cross-exchange arbitrage detection thresholds
- **NEW**: Historical data retention policies for tick data
- **NEW**: Compliance requirements for different jurisdictions
- **NEW**: Disaster recovery procedures for 24/7 operations

