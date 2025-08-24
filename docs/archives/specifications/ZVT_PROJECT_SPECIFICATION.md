# ZVT Project Specification v0.13.3

## Project Overview

**ZVT (Zero Vector Trading)** is a unified, modular quantitative trading framework designed for human beings, providing comprehensive market data collection, factor analysis, strategy backtesting, and automated trading capabilities across multiple global markets.

### Mission Statement
To democratize quantitative trading by providing a production-ready, extensible platform that bridges the gap between financial data and actionable trading strategies through modern software engineering practices.

## System Architecture

### Core Design Principles

#### 1. Domain-Driven Design
- **TradableEntity**: Core abstraction for any tradable instrument (stocks, ETFs, futures, etc.)
- **EntityEvent**: Time-series events occurring on entities (quotes, financial reports, news)
- **ActorEntity**: Market participants (funds, institutions, individuals)

#### 2. Schema-Centric Data Model
- Unified data structure with pandas multi-index (entity_id, timestamp)
- Multiple provider support for data resilience
- Incremental data updates with local persistence

#### 3. Factor-Based Analysis
- **Transformer**: Stateless computations on input data
- **Accumulator**: Stateful computations depending on historical results
- **TargetSelector**: Factor-based security selection engine

## Technical Specifications

### Technology Stack
- **Language**: Python 3.9+
- **Database**: SQLite (default), MySQL (production)
- **Data Processing**: Pandas 2.2.3, NumPy 2.1.3
- **Web Framework**: FastAPI 0.110.0
- **UI Framework**: Dash 2.18.2, Plotly 5.13.0
- **ML Framework**: scikit-learn 1.5.2
- **Task Scheduling**: APScheduler 3.10.4

### Data Layer Architecture

#### Supported Markets
- **China A-Shares**: Shanghai/Shenzhen Stock Exchanges
- **Hong Kong**: SEHK (Stock Exchange of Hong Kong)
- **United States**: NYSE, NASDAQ
- **Indices**: Major global indices
- **ETFs**: Exchange-traded funds
- **Futures**: Commodity and financial futures
- **Crypto (Planned)**: Spot and perpetual futures across major CEXs (see Crypto Market Specification)

#### Data Providers
- **Primary**: EastMoney (eastmoney), EM API, QMT
- **Secondary**: JoinQuant, Sina Finance
- **Backup**: Exchange official APIs
- **Crypto**: CCXT abstraction; native exchange APIs (Binance, OKX, Bybit, Coinbase)

#### Data Types
- **Meta Data**: Security basic information, corporate actions
- **Market Data**: OHLCV data at multiple frequencies (1m to 1mon)
- **Fundamental Data**: Financial statements, ratios, valuations
- **Alternative Data**: News sentiment, institutional holdings, money flow

### Computing Engine

#### Factor Framework
```python
{entity_schema}{level}{adjust_type}Kdata
```
- **entity_schema**: Stock, Stockus, Stockhk, etc.
- **level**: tick, 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1wk, 1mon
- **adjust_type**: qfq (pre-adjusted), hfq (post-adjusted), bfq (unadjusted)

#### Adjustment Types
- **QFQ (前复权)**: Pre-adjustment for dividend/split analysis
- **HFQ (后复权)**: Post-adjustment for return calculation
- **BFQ (不复权)**: Raw prices for technical analysis (only for crypto)

### API Architecture

#### REST API Design
- **Base URL**: `http://localhost:8090`
- **Authentication**: Token-based (configurable)
- **Rate Limiting**: Per-endpoint throttling
- **Response Format**: JSON with standardized error codes

#### Key Endpoints
- `/data/*`: Data query and retrieval
- `/factor/*`: Factor computation and results
- `/trading/*`: Portfolio management and trading
- `/misc/*`: Utility functions and system status

### Trading Engine

#### Account Management
- **SimAccount**: Backtesting with realistic slippage/commission
- **QMTAccount**: Real trading through QMT broker interface
- **Portfolio Tracking**: Real-time P&L, positions, risk metrics

#### Strategy Framework
- **Free Style**: Custom logic for timestamp-based trading
- **Factor-Based**: Systematic strategies using TargetSelector
- **ML-Driven**: Machine learning predictions with MaStockMLMachine

### Data Quality & Reliability

#### Multi-Provider Redundancy
Each data type supports multiple providers to ensure reliability:
```python
Stock.provider_map_recorder = {
    'em': EMStockRecorder,
    'eastmoney': EastmoneyChinaStockListRecorder,
    'joinquant': JqChinaStockRecorder,
    'exchange': ExchangeStockMetaRecorder
}
```

#### Incremental Updates
- Automatic detection of missing data periods
- Intelligent retry mechanisms for failed requests
- Data validation and consistency checks

## Feature Specifications

### 1. Data Management System

#### Real-time Data Collection
- **Quote Streaming**: 1-minute interval updates during trading hours
- **Event Processing**: Corporate actions, news, analyst reports
- **Quality Assurance**: Automated data validation and cleansing

#### Historical Data Management
- **Storage Optimization**: Compressed time-series storage
- **Query Performance**: Indexed multi-dimensional data access
- **Data Lineage**: Full audit trail of data sources and transformations

### 2. Factor Analysis Engine

#### Technical Factors
- **Moving Averages**: SMA, EMA, MACD with configurable periods
- **Momentum**: RSI, Stochastic, Rate of Change
- **Volatility**: Bollinger Bands, ATR, VIX-style indicators
- **Volume**: OBV, Volume Price Trend, Accumulation/Distribution

#### Fundamental Factors
- **Financial Ratios**: ROE, ROA, P/E, P/B, Debt/Equity
- **Growth Metrics**: Revenue growth, earnings growth, margin trends
- **Quality Scores**: Piotroski Score, Altman Z-Score
- **Valuation Models**: DCF components, relative valuation

#### Alternative Factors
- **Sentiment Analysis**: News sentiment, social media buzz
- **Institutional Flow**: Fund holdings changes, smart money tracking
- **Market Microstructure**: Bid-ask spreads, order flow imbalance

### 3. Machine Learning Integration

#### MaStockMLMachine Capabilities
- **Feature Engineering**: Automatic factor transformation and selection
- **Model Selection**: Ensemble methods, time-series specific algorithms
- **Backtesting**: Walk-forward analysis with realistic trading costs
- **Prediction**: Multi-horizon forecasting with confidence intervals

#### Supported Algorithms
- **Traditional ML**: Random Forest, SVM, Gradient Boosting
- **Time Series**: ARIMA, LSTM, Prophet
- **Ensemble**: Stacking, Blending, Dynamic weighting

### 4. Tag System

#### Dynamic Classification
- **Main Tags**: Primary industry/sector classification
- **Sub Tags**: Granular thematic categorization
- **Hidden Tags**: Private research classifications
- **AI Suggestions**: Automated tag recommendations

#### Use Cases
- **Sector Rotation**: Industry momentum strategies
- **Thematic Investing**: ESG, Technology trends, Demographics
- **Risk Management**: Concentration limits, correlation analysis

### 5. Trading Automation

#### Strategy Development
- **Backtesting Engine**: Realistic simulation with market impact; 24/7 calendar for crypto
- **Performance Analytics**: Sharpe ratio, maximum drawdown, factor attribution
- **Risk Controls**: Position sizing, stop-loss, correlation limits; funding/fee modeling for crypto

#### Execution Management
- **Order Types**: Market, limit, stop, iceberg orders
- **Slippage Modeling**: Volume-based impact estimation
- **Transaction Costs**: Realistic commission and fee calculation

### 6. User Interface

#### Dash Web Application
- **Interactive Charts**: Plotly-based technical analysis
- **Portfolio Dashboard**: Real-time performance monitoring
- **Strategy Builder**: Visual strategy construction and testing

#### REST API
- **Data Access**: Programmatic data retrieval
- **Strategy Management**: Automated strategy deployment
- **System Monitoring**: Health checks and performance metrics

## Integration Specifications

### Broker Integration

#### QMT (Quantitative Trading Platform)
- **Market Data**: Real-time quotes and level-2 data
- **Order Management**: Direct trading execution
- **Risk Management**: Pre-trade compliance checks
- **Account Management**: Multi-account support

### External Services

#### Notification Systems
- **WeChat Integration**: QiyeWechatBot for alerts and reports
- **Email Alerts**: SMTP-based notifications
- **Webhook Support**: Custom integrations

#### Data Sources
- **Financial APIs**: Integration-ready for Bloomberg, Reuters
- **News Services**: Automated news ingestion and processing
- **Economic Data**: Macro indicators and central bank announcements

## Performance Requirements

### Latency Specifications
- **Market Data**: < 1 second from source to application
- **Factor Calculation**: < 5 seconds for daily updates
- **Strategy Signals**: < 10 seconds from trigger to execution
- **API Response**: < 100ms for cached data, < 5s for complex queries

### Scalability Targets
- **Concurrent Users**: 100+ simultaneous web interface users
- **Data Volume**: 10M+ daily price records, 1M+ factor calculations
- **Strategy Capacity**: 1000+ simultaneous strategy executions
- **Historical Data**: 20+ years of daily data, 5+ years of intraday

### Reliability Standards
- **Uptime**: 99.9% during market hours
- **Data Accuracy**: > 99.99% for price data
- **Recovery Time**: < 5 minutes for service restoration
- **Backup Frequency**: Real-time data replication

## Security & Compliance

### Data Security
- **Access Control**: Role-based permissions for data and trading
- **Encryption**: AES-256 for sensitive data at rest
- **Audit Logging**: Complete trail of data access and modifications
- **API Security**: JWT tokens with expiration and refresh

### Trading Compliance
- **Risk Limits**: Configurable position and loss limits
- **Audit Trail**: Complete trade history with timestamps
- **Regulatory Reporting**: Extensible framework for compliance requirements
- **Access Controls**: Multi-level approval for trading operations

## Quality Assurance

### Testing Strategy
- **Unit Tests**: 90%+ code coverage for core modules
- **Integration Tests**: End-to-end data flow validation
- **Performance Tests**: Load testing for peak market conditions
- **Regression Tests**: Automated testing of strategy performance

### Code Quality
- **Type Hints**: Full typing for all public APIs
- **Documentation**: Comprehensive docstrings and examples
- **Code Style**: Black formatting, flake8 linting
- **Dependency Management**: Pinned versions for reproducibility

## Deployment Architecture

### Local Development
- **SQLite Database**: Single-file database for development
- **Built-in Server**: Development server with auto-reload
- **Sample Data**: Pre-loaded datasets for testing

### Production Deployment
- **Database**: MySQL/PostgreSQL with read replicas
- **Web Server**: Gunicorn with nginx reverse proxy
- **Task Queue**: Celery with Redis for background processing
- **Monitoring**: Prometheus metrics with Grafana dashboards

### Cloud Architecture
- **Container Support**: Docker images for consistent deployment
- **Kubernetes**: Helm charts for orchestration
- **Auto-scaling**: CPU/memory-based horizontal scaling
- **Data Pipeline**: Airflow for ETL orchestration

## Version Compatibility

### Current Version: 0.13.3
- **Python**: 3.9, 3.10, 3.11, 3.12
- **Pandas**: 2.2.x
- **SQLAlchemy**: 2.0.x
- **FastAPI**: 0.110.x

### Backward Compatibility
- **Data Formats**: Migration tools for older data formats
- **API Versioning**: /v1, /v2 endpoint versioning
- **Configuration**: Automatic config migration utilities

### Future Compatibility
- **Python 3.13**: Planned support in v0.14.x
- **Pandas 3.0**: Compatibility testing underway
- **SQLAlchemy 2.1**: Migration plan in development

## Extension Points

### Plugin Architecture
- **Custom Factors**: Plugin interface for proprietary factors
- **Data Providers**: Framework for adding new data sources
- **Brokers**: Extensible trading backend integration
- **Notification Channels**: Custom alert and reporting systems

### API Extensions
- **GraphQL**: Planned addition for flexible data queries
- **WebSocket**: Real-time streaming data interface
- **gRPC**: High-performance inter-service communication
- **OpenAPI**: Comprehensive API documentation and client generation

This specification serves as the definitive technical reference for ZVT v0.13.3 and provides the foundation for future development planning and architectural decisions.
