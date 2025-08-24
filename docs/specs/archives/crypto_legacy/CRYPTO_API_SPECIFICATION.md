# Crypto API Specification for ZVT Integration

**Version**: v1.1  
**Date**: 2025-08-18  
**Status**: Enhanced with Epic 1 Implementation Details

## Overview

This document specifies the API extensions required for ZVT's crypto market integration. The API design follows ZVT's existing patterns while adding crypto-specific endpoints and parameters.

## Design Principles

1. **Backwards Compatibility**: All existing API endpoints remain unchanged
2. **Consistent Patterns**: Crypto endpoints follow existing ZVT API conventions
3. **Provider Agnostic**: Support multiple crypto exchanges through unified interface
4. **Real-time Support**: WebSocket endpoints for streaming data
5. **Security First**: Enhanced authentication and rate limiting for trading APIs

## REST API Extensions

### 1. Provider Discovery

#### GET /api/data/providers
**Enhanced to include crypto providers**

```json
{
  "stock": ["em", "qmt", "joinquant", "eastmoney"],
  "crypto": ["binance", "okx", "bybit", "coinbase", "ccxt"],
  "index": ["em", "joinquant"],
  "etf": ["em", "joinquant"]
}
```

#### GET /api/data/schemas?provider=binance
**Returns crypto schemas for specified provider**

```json
{
  "entity_schemas": [
    "CryptoAsset",
    "CryptoPair", 
    "CryptoPerp"
  ],
  "kdata_schemas": [
    "CryptoPair1mKdata",
    "CryptoPair5mKdata",
    "CryptoPair15mKdata",
    "CryptoPair30mKdata", 
    "CryptoPair1hKdata",
    "CryptoPair4hKdata",
    "CryptoPair1dKdata",
    "CryptoPerp1mKdata",
    "CryptoPerp5mKdata",
    "CryptoPerp15mKdata",
    "CryptoPerp30mKdata",
    "CryptoPerp1hKdata", 
    "CryptoPerp4hKdata",
    "CryptoPerp1dKdata"
  ],
  "tick_schemas": [
    "CryptoTrade",
    "CryptoOrderbook",
    "CryptoFunding"
  ]
}
```

### 2. Entity Endpoints

#### GET /api/data/CryptoPair
**Query crypto trading pairs**

**Parameters:**
- `provider`: Exchange name (binance, okx, bybit, coinbase)
- `codes`: Comma-separated pair codes (btcusdt,ethusdt)
- `base_symbols`: Filter by base asset (btc,eth)
- `quote_symbols`: Filter by quote asset (usdt,btc)
- `is_active`: Filter active pairs only (true/false)
- `margin_enabled`: Filter margin trading enabled (true/false)

**Example Request:**
```
GET /api/data/CryptoPair?provider=binance&base_symbols=btc,eth&quote_symbols=usdt&is_active=true
```

**Example Response:**
```json
{
  "data": [
    {
      "id": "cryptopair_binance_btcusdt",
      "entity_id": "cryptopair_binance_btcusdt", 
      "entity_type": "cryptopair",
      "exchange": "binance",
      "code": "btcusdt",
      "name": "BTC/USDT",
      "base_symbol": "btc",
      "quote_symbol": "usdt",
      "price_step": 0.01,
      "qty_step": 0.00001,
      "min_notional": 10.0,
      "maker_fee": 0.001,
      "taker_fee": 0.001,
      "is_active": true,
      "margin_enabled": true,
      "list_date": "2017-07-14T00:00:00Z"
    }
  ]
}
```

#### GET /api/data/CryptoPerp  
**Query crypto perpetual futures**

**Additional Parameters:**
- `underlying_symbols`: Filter by underlying asset
- `settlement_symbols`: Filter by settlement asset
- `max_leverage`: Filter by maximum leverage available
- `funding_interval_hours`: Filter by funding interval

### 3. Market Data Endpoints

#### GET /api/data/CryptoPair1mKdata
**Query 1-minute OHLCV data for crypto pairs**

**Parameters:**
- `provider`: Exchange name (required)
- `codes`: Pair codes (btcusdt,ethusdt)
- `entity_ids`: Full entity IDs 
- `start_timestamp`: Start time (ISO 8601)
- `end_timestamp`: End time (ISO 8601)
- `limit`: Maximum records (default 1000, max 10000)
- `columns`: Specific columns to return
- `order`: Sort order (timestamp_asc, timestamp_desc)

**Example Request:**
```
GET /api/data/CryptoPair1mKdata?provider=binance&codes=btcusdt&start_timestamp=2024-08-01T00:00:00Z&limit=1440
```

**Example Response:**
```json
{
  "data": [
    {
      "id": "cryptopair_binance_btcusdt_2024-08-01T00:00:00Z", 
      "entity_id": "cryptopair_binance_btcusdt",
      "timestamp": "2024-08-01T00:00:00Z",
      "provider": "binance",
      "code": "btcusdt",
      "name": "BTC/USDT",
      "level": "1m",
      "open": 45250.50,
      "high": 45289.99,
      "low": 45201.00,
      "close": 45275.25,
      "volume": 12.5678,
      "turnover": 568542.75,
      "volume_base": 12.5678,
      "volume_quote": 568542.75,
      "trade_count": 1842,
      "vwap": 45254.32,
      "change_pct": 0.0005,
      "turnover_rate": null
    }
  ],
  "total": 1440,
  "page": 1,
  "page_size": 1000
}
```

#### GET /api/data/CryptoTrade
**Query individual crypto trades**

**Parameters:**
- `provider`: Exchange name (required)
- `codes`: Pair codes
- `start_timestamp`: Start time
- `end_timestamp`: End time  
- `limit`: Maximum records (default 1000, max 100000)
- `side`: Filter by trade side (buy/sell)
- `min_volume`: Minimum trade volume filter

#### GET /api/data/CryptoFunding
**Query perpetual funding rates**

**Parameters:**
- `provider`: Exchange name (required)
- `codes`: Perpetual contract codes
- `start_timestamp`: Start time
- `end_timestamp`: End time
- `funding_interval_hours`: Filter by funding interval

### 4. Real-time WebSocket API

#### WebSocket Connection
**Base URL:** `wss://api.zvt.com/ws`

#### Authentication (for private streams)
```json
{
  "method": "auth",
  "params": {
    "provider": "binance",
    "api_key": "your_api_key",
    "signature": "calculated_signature", 
    "timestamp": 1692345600000
  }
}
```

#### Public Stream Subscriptions

**Subscribe to Trades:**
```json
{
  "method": "subscribe",
  "params": {
    "stream": "crypto.trades",
    "provider": "binance",
    "symbols": ["btcusdt", "ethusdt"]
  }
}
```

**Subscribe to 1m Klines:**
```json
{
  "method": "subscribe", 
  "params": {
    "stream": "crypto.klines",
    "provider": "binance", 
    "symbols": ["btcusdt"],
    "interval": "1m"
  }
}
```

**Subscribe to Order Book:**
```json
{
  "method": "subscribe",
  "params": {
    "stream": "crypto.orderbook",
    "provider": "binance",
    "symbols": ["btcusdt"],
    "depth": 20
  }
}
```

**Subscribe to Funding Rates:**
```json
{
  "method": "subscribe",
  "params": {
    "stream": "crypto.funding",
    "provider": "binance",
    "symbols": ["btcusdt-perp"]
  }
}
```

#### Private Stream Subscriptions (requires authentication)

**Subscribe to Account Updates:**
```json
{
  "method": "subscribe",
  "params": {
    "stream": "crypto.account",
    "provider": "binance"
  }
}
```

**Subscribe to Order Updates:**
```json
{
  "method": "subscribe",
  "params": {
    "stream": "crypto.orders",
    "provider": "binance"
  }
}
```

#### Stream Message Format

**Trade Message:**
```json
{
  "stream": "crypto.trades",
  "provider": "binance",
  "symbol": "btcusdt",
  "data": {
    "trade_id": "12345678",
    "price": 45250.50,
    "volume": 0.025,
    "side": "buy",
    "timestamp": "2024-08-01T12:34:56.789Z",
    "is_buyer_maker": false
  }
}
```

**Kline Message:**
```json
{
  "stream": "crypto.klines", 
  "provider": "binance",
  "symbol": "btcusdt",
  "interval": "1m",
  "data": {
    "open": 45250.50,
    "high": 45289.99, 
    "low": 45201.00,
    "close": 45275.25,
    "volume": 12.5678,
    "timestamp": "2024-08-01T12:34:00.000Z",
    "is_closed": false
  }
}
```

### 5. Trading API Extensions

#### POST /api/trading/orders
**Enhanced to support crypto orders**

**Crypto-specific Parameters:**
- `entity_type`: Must be "cryptopair" or "cryptoperp" 
- `position_side`: For perpetuals ("long", "short", "both")
- `reduce_only`: For perpetuals (true/false)
- `time_in_force`: "GTC", "IOC", "FOK"
- `leverage`: For margin/perpetual trading

**Example Crypto Order Request:**
```json
{
  "entity_id": "cryptopair_binance_btcusdt",
  "entity_type": "cryptopair",
  "provider": "binance", 
  "side": "buy",
  "type": "limit",
  "quantity": 0.01,
  "price": 45000.00,
  "time_in_force": "GTC",
  "margin_trading": false
}
```

#### GET /api/trading/positions
**Enhanced to support crypto positions**

**Crypto-specific Response Fields:**
```json
{
  "positions": [
    {
      "entity_id": "cryptoperp_binance_btcusdt",
      "entity_type": "cryptoperp", 
      "provider": "binance",
      "symbol": "btcusdt",
      "position_side": "long",
      "quantity": 0.5,
      "entry_price": 44500.00,
      "mark_price": 45250.00,
      "unrealized_pnl": 375.00,
      "leverage": 5.0,
      "margin": 4525.00,
      "margin_ratio": 0.15,
      "funding_cost": -2.50
    }
  ]
}
```

## Error Handling

### Crypto-Specific Error Codes

- `CRYPTO_PAIR_NOT_FOUND` (404): Requested crypto pair not available
- `CRYPTO_PROVIDER_UNAVAILABLE` (503): Crypto exchange temporarily unavailable
- `CRYPTO_INSUFFICIENT_BALANCE` (400): Insufficient balance for crypto trade
- `CRYPTO_MIN_NOTIONAL_NOT_MET` (400): Order below minimum notional value
- `CRYPTO_PRECISION_ERROR` (400): Price/quantity precision violation
- `CRYPTO_FUNDING_SETTLEMENT` (423): Trading locked during funding settlement

### Rate Limiting

**Crypto API Rate Limits:**
- Public data endpoints: 1000 requests/minute per IP
- Private trading endpoints: 100 requests/minute per API key
- WebSocket connections: 5 connections per IP, 200 subscriptions per connection

## Security Considerations

### API Key Management
- Support for exchange-specific API key formats
- Encrypted storage with rotation capabilities  
- Read-only keys for data access, trading-enabled keys for orders
- IP whitelisting support where available

### Signature Validation
- Support for each exchange's signature algorithm
- HMAC-SHA256 for most exchanges
- Timestamp validation with configurable windows

### Request Validation
- All crypto-specific parameter validation
- Precision checking against exchange specs
- Balance verification before order placement

## Implementation Notes

### Provider Abstraction
- Unified interface across all crypto exchanges
- Provider-specific parameter mapping
- Graceful fallback for unsupported features

### Data Consistency
- Cross-exchange price validation
- Timestamp normalization to UTC
- Symbol normalization (BTCUSDT → btcusdt)

### Performance Optimization
- Connection pooling for HTTP requests
- WebSocket connection multiplexing
- Intelligent caching with TTL

This specification provides the foundation for Epic 2 implementation and subsequent provider integrations.

## Epic 1 Implementation Enhancements

### Enhanced Provider Framework APIs

#### GET /api/crypto/providers/capabilities
**Query provider-specific capabilities**

**Example Response:**
```json
{
  "binance": {
    "spot_trading": true,
    "perpetual_trading": true,
    "margin_trading": true,
    "max_leverage": 125.0,
    "funding_intervals": [8],
    "supported_order_types": ["market", "limit", "stop_market", "stop_limit"],
    "websocket_endpoints": ["trades", "klines", "orderbook", "account"],
    "rate_limits": {
      "requests_per_minute": 1200,
      "orders_per_minute": 100,
      "websocket_connections": 5
    }
  }
}
```

#### GET /api/crypto/providers/status
**Real-time provider health status**

```json
{
  "providers": [
    {
      "name": "binance",
      "status": "operational",
      "api_latency_ms": 145,
      "websocket_connected": true,
      "last_data_timestamp": "2024-08-18T12:34:56.789Z",
      "error_rate_1h": 0.02,
      "uptime_24h": 99.8
    }
  ]
}
```

### Data Quality Validation APIs

#### POST /api/crypto/validation/price
**Validate price data across exchanges**

**Request:**
```json
{
  "symbol": "btcusdt",
  "providers": ["binance", "okx", "bybit"],
  "timestamp": "2024-08-18T12:34:56.789Z",
  "prices": {
    "binance": 45250.50,
    "okx": 45251.00,
    "bybit": 45249.75
  }
}
```

**Response:**
```json
{
  "validation_result": {
    "is_valid": true,
    "max_deviation_pct": 0.003,
    "outliers": [],
    "confidence_score": 0.998,
    "recommended_price": 45250.42
  }
}
```

#### GET /api/crypto/validation/gaps
**Check for data gaps in time series**

**Parameters:**
- `provider`: Exchange name
- `symbol`: Trading pair
- `start_timestamp`: Start time
- `end_timestamp`: End time
- `interval`: Data interval (1m, 5m, etc.)

### Configuration Management APIs

#### GET /api/crypto/config
**Retrieve crypto configuration settings**

```json
{
  "exchanges": {
    "binance": {
      "api_endpoint": "https://api.binance.com",
      "websocket_endpoint": "wss://stream.binance.com:9443",
      "rate_limits": {
        "requests_per_minute": 1200,
        "burst_limit": 100
      }
    }
  },
  "data_collection": {
    "default_backfill_days": 180,
    "max_concurrent_streams": 25,
    "data_quality_checks_enabled": true
  }
}
```

#### PUT /api/crypto/config/exchanges/{exchange_name}
**Update exchange-specific configuration**

### Monitoring and Metrics APIs

#### GET /api/crypto/metrics
**Retrieve operational metrics**

```json
{
  "websocket_metrics": {
    "total_reconnects_24h": 3,
    "average_message_lag_ms": 127,
    "messages_dropped_24h": 0
  },
  "data_quality_metrics": {
    "validation_failures_24h": 2,
    "cross_exchange_deviations": 5,
    "data_gaps_detected_24h": 0
  },
  "performance_metrics": {
    "average_query_response_ms": 85,
    "current_memory_usage_gb": 3.2,
    "active_websocket_connections": 12
  }
}
```

#### GET /api/crypto/health
**Comprehensive health check endpoint**

```json
{
  "status": "healthy",
  "checks": {
    "database_connectivity": "pass",
    "exchange_connectivity": "pass", 
    "websocket_streams": "pass",
    "data_freshness": "pass",
    "memory_usage": "pass"
  },
  "uptime_seconds": 342567,
  "last_check": "2024-08-18T12:34:56.789Z"
}
```

### Enhanced Error Handling

#### Comprehensive Error Response Format
```json
{
  "error": {
    "code": "CRYPTO_RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded for Binance API",
    "details": {
      "provider": "binance",
      "rate_limit": "1200/minute",
      "retry_after_seconds": 60,
      "current_usage": 1205
    },
    "recovery_suggestions": [
      "Wait 60 seconds before retrying",
      "Consider using different provider",
      "Implement exponential backoff"
    ],
    "timestamp": "2024-08-18T12:34:56.789Z",
    "trace_id": "abc123-def456-ghi789"
  }
}
```

#### Enhanced Error Codes from Epic 1 Framework
- `CRYPTO_WEBSOCKET_DISCONNECTED` (503): WebSocket connection lost
- `CRYPTO_DATA_QUALITY_FAILURE` (422): Data quality validation failed
- `CRYPTO_ORDERBOOK_DESYNC` (503): Order book synchronization lost
- `CRYPTO_FUNDING_RATE_MISSING` (404): Funding rate data unavailable
- `CRYPTO_EXCHANGE_MAINTENANCE` (503): Exchange under maintenance
- `CRYPTO_SYMBOL_MAPPING_ERROR` (400): Symbol normalization failed

### Security Enhancements

#### API Key Validation Endpoint
```
GET /api/crypto/auth/validate?provider=binance
Authorization: Bearer {api_key}
```

**Response:**
```json
{
  "valid": true,
  "permissions": ["spot_trading", "futures_trading", "data_access"],
  "rate_limits": {
    "remaining": 1150,
    "reset_time": "2024-08-18T12:35:00.000Z"
  },
  "expires_at": "2024-11-18T00:00:00.000Z"
}
```

### Advanced WebSocket Features

#### Connection Multiplexing Support
**Enhanced subscription with channel management:**
```json
{
  "method": "subscribe",
  "params": {
    "channel": "trades_btc",
    "streams": [
      {
        "stream": "crypto.trades",
        "provider": "binance", 
        "symbols": ["btcusdt"]
      },
      {
        "stream": "crypto.trades",
        "provider": "okx",
        "symbols": ["btc-usdt"]
      }
    ]
  }
}
```

#### Backpressure Control
**Message flow control:**
```json
{
  "method": "configure_flow",
  "params": {
    "max_messages_per_second": 100,
    "buffer_size": 1000,
    "drop_policy": "oldest"
  }
}
```

### Implementation Guidelines

#### Provider Integration Pattern
```python
# Implementation uses BaseCryptoProvider pattern from Epic 1
class BinanceAPIProvider(BaseCryptoProvider):
    def normalize_symbol(self, exchange_symbol: str) -> str:
        return exchange_symbol.lower()
    
    async def handle_rate_limit(self, context: Dict) -> bool:
        # Use CryptoErrorHandler patterns
        return await self.error_handler.handle_error(
            CryptoErrorType.RATE_LIMIT_EXCEEDED, context
        )
```

#### Data Quality Integration
```python
# Apply CryptoDataQualityValidator from Epic 1
validator = CryptoDataQualityValidator()
result = await validator.validate_kline(kline_data)
if not result.is_valid:
    # Handle validation failure with logging
    pass
```

---

**Implementation Status:** Enhanced with Epic 1 frameworks ready for Epic 2 development

**Next Steps:**
1. ✅ Epic 1 Complete: All API patterns validated
2. 🚀 Epic 2 Ready: Implement enhanced API endpoints
3. ⏳ Epic 3 Pending: Provider-specific implementations
4. ⏳ Testing: Comprehensive API testing framework