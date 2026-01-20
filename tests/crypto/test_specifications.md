# Epic 1: Crypto Market Integration - Test Specifications

## Test Coverage Areas

### 1. Domain Layer Tests
- **Crypto Entity Tests** (`test_crypto_entity.py`)
  - Crypto asset entity creation and validation
  - Market cap calculations (total_cap, circulating_cap)
  - Trading time validation (24/7 nature)
  - Symbol normalization (BTC-USD, ETH-BTC pairs)
  
- **Crypto Detail Tests** (`test_crypto_detail.py`)
  - Token metadata (name, symbol, contract_address)
  - Market data (rank, max_supply, total_supply)
  - Network information (blockchain, consensus)
  - Price history tracking

### 2. Data Services Tests
- **Historical Data Loader Tests** (`test_data_loader.py`)
  - Multi-exchange data loading
  - Rate limiting and retry logic
  - Data validation and gap detection
  - Parallel processing and progress tracking
  - Mock and integration test modes
  
- **Stream Service Tests** (`test_stream_service.py`)
  - WebSocket connection management
  - Multi-exchange stream handling
  - Message parsing and routing
  - Connection failover and recovery
  - Buffer management and data handlers
  
- **API Ingestion Tests** (`test_api_ingestion.py`)
  - REST API endpoint validation
  - Data model validation (Pydantic)
  - Bulk ingestion processing
  - Error handling and statistics
  - FastAPI integration testing

### 3. Data Provider Integration Tests
- **Exchange API Tests** (`test_crypto_providers.py`)
  - Binance API integration
  - OKX API integration
  - Bybit API integration
  - Coinbase Pro API integration
  - Rate limiting compliance
  - Error handling and retries
  
- **Data Recording Tests** (`test_crypto_recorders.py`)
  - Real-time price feeds
  - Historical OHLCV data
  - Order book data (L2 quotes)
  - Trade tick data
  - Funding rate data

### 4. Quote Data Tests
- **Real-time Quote Tests** (`test_crypto_quotes.py`)
  - WebSocket connection handling
  - Price update frequency validation
  - Market depth data accuracy
  - Symbol subscription management
  - Cross-exchange data aggregation
  
- **Historical Data Tests** (`test_crypto_historical.py`)
  - OHLCV data completeness
  - Time interval support (1m, 5m, 15m, 30m, 1h, 4h, 1d)
  - Data gap detection and backfill
  - Historical backfill accuracy
  - Multi-timeframe data consistency

### 5. Trading Infrastructure Tests
- **Order Management Tests** (`test_crypto_orders.py`)
  - Market/limit order placement
  - Stop-loss/take-profit orders
  - Order status tracking
  - Portfolio balance updates
  
- **Risk Management Tests** (`test_crypto_risk.py`)
  - Position sizing validation
  - Leverage calculations
  - Margin requirements
  - Liquidation price calculations

### 6. REST API Integration Tests
- **API Endpoint Tests** (`test_api_endpoints.py`)
  - Asset management endpoints
  - Trading pair management
  - Data ingestion endpoints
  - Query endpoints (OHLCV, trades, orderbook)
  - Stream control endpoints
  
- **API Validation Tests** (`test_api_validation.py`)
  - Input data validation (Pydantic models)
  - Error response handling
  - Rate limiting and throttling
  - Authentication and authorization
  - CORS and security headers

### 7. Factor Analysis Tests
- **Technical Indicators Tests** (`test_crypto_factors.py`)
  - RSI, MACD, Bollinger Bands
  - Volume indicators
  - Momentum factors
  - Volatility measurements
  
- **Cross-asset Analysis Tests** (`test_crypto_correlations.py`)
  - BTC dominance factor
  - Crypto-traditional asset correlations
  - Market sentiment indicators
  - Fear & Greed index integration

### 8. Performance & Integration Tests
- **Load Tests** (`test_crypto_performance.py`)
  - High-frequency data ingestion
  - Concurrent API calls
  - WebSocket message throughput
  - Memory usage optimization
  - Database performance
  
- **Service Integration Tests** (`test_service_integration.py`)
  - Data loader + Stream service integration
  - Stream service + API ingestion integration
  - End-to-end data flow validation
  - Service failover and recovery
  
- **End-to-End Tests** (`test_crypto_e2e.py`)
  - Full trading workflow
  - Strategy execution
  - Report generation
  - UI integration

## Test Data Requirements
- Mock crypto assets (BTC, ETH, ADA, DOT, MATIC, USDT, USDC)
- Historical price data (1 year minimum, multiple intervals)
- Exchange API test credentials (sandbox environments)
- Sample order book snapshots (various depths)
- Trade execution scenarios (market conditions)
- WebSocket message samples (all data types)
- Funding rate historical data (perpetual contracts)
- Mock REST API payloads (ingestion testing)

## Service Testing Requirements
- **Data Loader Service**
  - Multi-exchange parallel loading tests
  - Rate limiting and retry mechanism validation
  - Data validation and gap detection accuracy
  - Progress tracking and statistics verification
  - Error recovery and failover testing
  
- **Stream Service Testing**
  - WebSocket connection stability tests
  - Message parsing accuracy for all exchanges
  - Connection failover and automatic reconnection
  - Real-time data buffer management
  - Cross-exchange data aggregation validation
  
- **REST API Testing**
  - All endpoint functionality and validation
  - Pydantic model validation and error handling
  - Bulk ingestion performance and accuracy
  - Stream control and monitoring endpoints
  - CORS, authentication, and security testing

## Performance Requirements
- **Data Loading Performance**
  - Historical data: >1000 records/second per exchange
  - Parallel loading: 5+ exchanges simultaneously
  - Memory usage: <2GB for 1M records
  - Error rate: <1% for network operations
  
- **Streaming Performance**
  - Message throughput: >10,000 messages/second
  - Connection stability: >99.9% uptime
  - Message latency: <50ms from exchange to processing
  - Buffer capacity: 10,000+ messages without loss
  
- **API Performance**
  - REST endpoint response: <200ms for queries
  - Bulk ingestion: >5,000 records/second
  - Concurrent requests: 100+ simultaneous users
  - Data validation: <1ms per record

## Acceptance Criteria
1. All domain entities properly inherit from TradableEntity
2. 24/7 trading time validation works correctly
3. Real-time data feeds maintain <50ms latency (improved)
4. Historical data has >99.9% completeness (improved)
5. Multi-exchange data loading works in parallel
6. WebSocket connections auto-reconnect on failures
7. REST API handles 1000+ concurrent requests
8. Data validation catches all malformed inputs
9. Order execution completes within 500ms
10. Factor calculations match reference implementations
11. Service integration works end-to-end
12. Error handling covers all network/API failures
13. Test coverage >95% for all crypto modules (improved)
14. All services support graceful shutdown and restart
15. Performance benchmarks meet requirements