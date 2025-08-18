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

### 2. Data Provider Integration Tests
- **Exchange API Tests** (`test_crypto_providers.py`)
  - Binance API integration
  - Coinbase Pro API integration
  - Rate limiting compliance
  - Error handling and retries
  
- **Data Recording Tests** (`test_crypto_recorders.py`)
  - Real-time price feeds
  - Historical OHLCV data
  - Order book data (L2 quotes)
  - Trade tick data

### 3. Quote Data Tests
- **Real-time Quote Tests** (`test_crypto_quotes.py`)
  - WebSocket connection handling
  - Price update frequency validation
  - Market depth data accuracy
  - Symbol subscription management
  
- **Historical Data Tests** (`test_crypto_historical.py`)
  - OHLCV data completeness
  - Time interval support (1m, 5m, 1h, 1d)
  - Data gap detection
  - Historical backfill accuracy

### 4. Trading Infrastructure Tests
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

### 5. Factor Analysis Tests
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

### 6. Performance & Integration Tests
- **Load Tests** (`test_crypto_performance.py`)
  - High-frequency data ingestion
  - Concurrent API calls
  - Memory usage optimization
  - Database performance
  
- **End-to-End Tests** (`test_crypto_e2e.py`)
  - Full trading workflow
  - Strategy execution
  - Report generation
  - UI integration

## Test Data Requirements
- Mock crypto assets (BTC, ETH, ADA, DOT, MATIC)
- Historical price data (1 year minimum)
- Exchange API test credentials
- Sample order book snapshots
- Trade execution scenarios

## Acceptance Criteria
1. All domain entities properly inherit from TradableEntity
2. 24/7 trading time validation works correctly
3. Real-time data feeds maintain <100ms latency
4. Historical data has >99% completeness
5. Order execution completes within 500ms
6. Factor calculations match reference implementations
7. Error handling covers all network/API failures
8. Test coverage >90% for all crypto modules