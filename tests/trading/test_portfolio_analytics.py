# tests/trading/test_portfolio_analytics.py
"""
TDD Cycle 2: Portfolio Analytics Test Suite - RED Phase
Spec: Epic 2 Phase 2 - Portfolio Management System  
Methodology: Test-Driven Development (Red-Green-Refactor)

RED Phase: These tests MUST fail initially because portfolio analytics implementation doesn't exist
Building on TDD Cycle 1 success: 16/17 tests passing (94% success rate)

Epic 2 Phase 2 Requirements:
- Real-time portfolio metrics and performance tracking
- Multi-currency support with automatic conversion  
- Risk-adjusted return calculations (Sharpe, Sortino, Calmar)
- Benchmark comparison and performance attribution
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from typing import Dict, List

from src.zvt.trading.crypto_trading_engine import CryptoTradingEngine
from src.zvt.trading.models import Portfolio, Position, PortfolioSummary, BalanceInfo
from src.zvt.trading.exceptions import PortfolioError, CurrencyConversionError


class TestRealTimePortfolioTracking:
    """
    TDD Test Suite for Real-Time Portfolio Tracking
    Spec: Epic 2 Phase 2.1 - Real-time portfolio metrics and performance tracking
    
    RED Phase Requirements:
    - Real-time position aggregation across exchanges
    - Multi-currency portfolio valuation
    - PnL calculations with mark-to-market pricing
    - Performance metrics calculation
    """
    
    def test_portfolio_real_time_value_calculation(self):
        """
        RED Phase: Test fails because PortfolioAnalytics.calculate_portfolio_value() doesn't exist
        Spec Requirement: "Real-time portfolio valuation with streaming prices"
        """
        # Arrange
        engine = CryptoTradingEngine()
        portfolio_id = "test_portfolio_001"
        
        # Set up positions in portfolio
        engine.create_portfolio(portfolio_id, base_currency="USDT")
        engine.add_position_to_portfolio(portfolio_id, "BTC/USDT", quantity=Decimal("2.5"), avg_price=Decimal("45000"))
        engine.add_position_to_portfolio(portfolio_id, "ETH/USDT", quantity=Decimal("10.0"), avg_price=Decimal("3000"))
        
        # Mock real-time prices
        engine.set_real_time_price("BTC/USDT", Decimal("46000"))  # +2.22% gain
        engine.set_real_time_price("ETH/USDT", Decimal("2950"))   # -1.67% loss
        
        # Act & Assert (This MUST fail initially - RED phase)
        portfolio_value = engine.calculate_portfolio_value(portfolio_id)
        
        assert portfolio_value.total_value == Decimal("144500")  # (2.5*46000) + (10*2950)
        assert portfolio_value.total_pnl > 0  # Net positive due to BTC gains > ETH losses
        assert portfolio_value.unrealized_pnl == Decimal("2000")  # (2.5*1000) + (10*-50) = 2500-500
        assert portfolio_value.base_currency == "USDT"
        assert portfolio_value.last_update is not None
    
    def test_portfolio_multi_exchange_aggregation(self):
        """
        RED Phase: Test for position aggregation across multiple exchanges
        Spec Requirement: "Multi-exchange position aggregation"
        """
        engine = CryptoTradingEngine()
        portfolio_id = "multi_exchange_portfolio"
        
        # Create portfolio with positions across exchanges
        engine.create_portfolio(portfolio_id)
        
        # Add positions from different exchanges
        engine.add_position_to_portfolio(
            portfolio_id, "BTC/USDT", 
            quantity=Decimal("1.0"), avg_price=Decimal("45000"), 
            exchange="binance"
        )
        engine.add_position_to_portfolio(
            portfolio_id, "BTC/USDT", 
            quantity=Decimal("0.5"), avg_price=Decimal("45100"),
            exchange="okx"
        )
        
        # Set real-time prices
        engine.set_real_time_price("BTC/USDT", Decimal("46000"))
        
        # Calculate aggregated portfolio
        portfolio_summary = engine.get_portfolio_summary(portfolio_id)
        
        # Should aggregate positions across exchanges
        assert portfolio_summary.total_positions == 1  # One symbol
        assert portfolio_summary.symbols == ["BTC/USDT"]
        
        # BTC position should be aggregated (1.0 + 0.5 = 1.5 BTC)
        btc_position = portfolio_summary.get_position("BTC/USDT")
        assert btc_position.total_quantity == Decimal("1.5")
        assert btc_position.exchanges == ["binance", "okx"]
        assert btc_position.weighted_avg_price > Decimal("45000")  # Weighted average
    
    def test_portfolio_performance_metrics_calculation(self):
        """
        RED Phase: Test for performance metrics calculation
        Spec Requirement: "Performance metrics and tracking"
        """
        engine = CryptoTradingEngine()
        portfolio_id = "performance_test_portfolio"
        
        # Create portfolio with historical data
        engine.create_portfolio(portfolio_id, initial_value=Decimal("100000"))
        
        # Add some trading history to calculate returns
        yesterday = datetime.now() - timedelta(days=1)
        week_ago = datetime.now() - timedelta(days=7)
        month_ago = datetime.now() - timedelta(days=30)
        
        # Historical portfolio values
        engine.add_portfolio_snapshot(portfolio_id, week_ago, value=Decimal("100000"))
        engine.add_portfolio_snapshot(portfolio_id, yesterday, value=Decimal("105000"))
        
        # Current positions
        engine.add_position_to_portfolio(portfolio_id, "BTC/USDT", quantity=Decimal("2.0"), avg_price=Decimal("50000"))
        engine.set_real_time_price("BTC/USDT", Decimal("52500"))  # Current value: 105000
        
        # Calculate performance metrics
        performance = engine.calculate_portfolio_performance(portfolio_id)
        
        assert performance.total_return_pct == Decimal("5.0")  # 5% total return
        assert performance.daily_return_pct > 0  # Positive daily return
        assert performance.weekly_return_pct == Decimal("5.0")  # 5% weekly return
        assert performance.volatility > 0  # Should have some volatility
        assert performance.max_drawdown >= 0  # Non-negative drawdown
        assert performance.current_value == Decimal("105000")
    
    def test_portfolio_currency_conversion(self):
        """
        RED Phase: Test for multi-currency portfolio valuation
        Spec Requirement: "Multi-currency support with automatic conversion"
        """
        engine = CryptoTradingEngine()
        portfolio_id = "multi_currency_portfolio"
        
        # Create portfolio with USD base currency
        engine.create_portfolio(portfolio_id, base_currency="USD")
        
        # Add positions in different quote currencies
        engine.add_position_to_portfolio(portfolio_id, "BTC/USDT", quantity=Decimal("1.0"), avg_price=Decimal("45000"))
        engine.add_position_to_portfolio(portfolio_id, "ETH/EUR", quantity=Decimal("5.0"), avg_price=Decimal("2500"))
        
        # Mock currency conversion rates
        engine.set_currency_rate("USDT", "USD", Decimal("1.0"))
        engine.set_currency_rate("EUR", "USD", Decimal("1.1"))
        
        # Set current prices
        engine.set_real_time_price("BTC/USDT", Decimal("46000"))
        engine.set_real_time_price("ETH/EUR", Decimal("2600"))
        
        # Calculate portfolio value in base currency (USD)
        portfolio_value = engine.calculate_portfolio_value(portfolio_id, target_currency="USD")
        
        # BTC value: 46000 * 1.0 = 46000 USD
        # ETH value: (5 * 2600) * 1.1 = 14300 USD
        # Total: 60300 USD
        assert portfolio_value.total_value == Decimal("60300")
        assert portfolio_value.currency == "USD"
        assert portfolio_value.conversion_rates is not None
        assert len(portfolio_value.currency_breakdown) == 2  # USDT and EUR components
    
    def test_portfolio_position_breakdown(self):
        """
        RED Phase: Test for detailed position breakdown
        Spec Requirement: "Detailed position analysis and breakdown"
        """
        engine = CryptoTradingEngine()
        portfolio_id = "breakdown_test_portfolio"
        
        engine.create_portfolio(portfolio_id)
        
        # Add multiple positions
        positions = [
            ("BTC/USDT", Decimal("2.0"), Decimal("45000")),
            ("ETH/USDT", Decimal("10.0"), Decimal("3000")),
            ("ADA/USDT", Decimal("1000.0"), Decimal("0.5")),
            ("DOT/USDT", Decimal("50.0"), Decimal("20.0"))
        ]
        
        for symbol, quantity, avg_price in positions:
            engine.add_position_to_portfolio(portfolio_id, symbol, quantity, avg_price)
        
        # Set current prices
        engine.set_real_time_price("BTC/USDT", Decimal("46000"))
        engine.set_real_time_price("ETH/USDT", Decimal("3100"))
        engine.set_real_time_price("ADA/USDT", Decimal("0.52"))
        engine.set_real_time_price("DOT/USDT", Decimal("19.5"))
        
        # Get position breakdown
        breakdown = engine.get_portfolio_breakdown(portfolio_id)
        
        assert len(breakdown.positions) == 4
        assert breakdown.total_allocation == Decimal("1.0")  # 100%
        
        # Check BTC position (largest by value)
        btc_position = breakdown.get_position("BTC/USDT")
        assert btc_position.symbol == "BTC/USDT"
        assert btc_position.allocation_pct > Decimal("0.6")  # Should be largest allocation
        assert btc_position.unrealized_pnl == Decimal("2000")  # (46000-45000) * 2
        assert btc_position.unrealized_pnl_pct == Decimal("2.22")  # ~2.22%


class TestRiskAdjustedReturns:
    """
    TDD Test Suite for Risk-Adjusted Return Calculations  
    Spec: Epic 2 Phase 2.2 - Risk-adjusted return calculations (Sharpe, Sortino, Calmar)
    
    RED Phase Requirements:
    - Sharpe ratio calculation with risk-free rate
    - Sortino ratio focusing on downside deviation
    - Calmar ratio (CAGR / Maximum Drawdown)
    - Value at Risk (VaR) calculations
    """
    
    def test_sharpe_ratio_calculation(self):
        """
        RED Phase: Test fails because RiskAnalytics.calculate_sharpe_ratio() doesn't exist
        Spec Requirement: "Sharpe ratio calculation with configurable risk-free rate"
        """
        engine = CryptoTradingEngine()
        portfolio_id = "sharpe_test_portfolio"
        
        # Create portfolio with return history
        engine.create_portfolio(portfolio_id, initial_value=Decimal("100000"))
        
        # Add daily returns for the past month (simulated)
        daily_returns = [
            Decimal("0.02"), Decimal("-0.01"), Decimal("0.015"), Decimal("0.005"),
            Decimal("-0.008"), Decimal("0.022"), Decimal("0.01"), Decimal("-0.005"),
            Decimal("0.018"), Decimal("0.008"), Decimal("-0.012"), Decimal("0.025"),
            Decimal("0.003"), Decimal("-0.007"), Decimal("0.019"), Decimal("0.012"),
            Decimal("-0.015"), Decimal("0.028"), Decimal("0.006"), Decimal("-0.003"),
            Decimal("0.016"), Decimal("0.009"), Decimal("-0.011"), Decimal("0.021"),
            Decimal("0.004"), Decimal("-0.006"), Decimal("0.017"), Decimal("0.013"),
            Decimal("-0.009"), Decimal("0.024")
        ]
        
        for i, daily_return in enumerate(daily_returns):
            date = datetime.now() - timedelta(days=len(daily_returns)-i)
            engine.add_daily_return(portfolio_id, date, daily_return)
        
        # Calculate Sharpe ratio
        risk_free_rate = Decimal("0.02")  # 2% annual risk-free rate
        sharpe_metrics = engine.calculate_sharpe_ratio(portfolio_id, risk_free_rate=risk_free_rate)
        
        assert sharpe_metrics.sharpe_ratio > 0  # Should be positive for good performance
        assert sharpe_metrics.annualized_return > risk_free_rate  # Should beat risk-free rate
        assert sharpe_metrics.volatility > 0  # Should have some volatility
        assert sharpe_metrics.excess_return > 0  # Return above risk-free rate
        assert sharpe_metrics.risk_free_rate == risk_free_rate
    
    def test_sortino_ratio_calculation(self):
        """
        RED Phase: Test for Sortino ratio calculation
        Spec Requirement: "Sortino ratio focusing on downside deviation"
        """
        engine = CryptoTradingEngine()
        portfolio_id = "sortino_test_portfolio"
        
        # Create portfolio with mixed positive/negative returns
        engine.create_portfolio(portfolio_id)
        
        # Returns with more downside than upside volatility
        returns = [
            Decimal("0.05"), Decimal("-0.08"), Decimal("0.03"), Decimal("-0.12"),
            Decimal("0.07"), Decimal("-0.02"), Decimal("0.04"), Decimal("-0.15"),
            Decimal("0.06"), Decimal("-0.01"), Decimal("0.02"), Decimal("-0.09"),
            Decimal("0.08"), Decimal("-0.03"), Decimal("0.01"), Decimal("-0.11")
        ]
        
        for i, return_val in enumerate(returns):
            date = datetime.now() - timedelta(days=len(returns)-i)
            engine.add_daily_return(portfolio_id, date, return_val)
        
        # Calculate Sortino ratio
        target_return = Decimal("0.0")  # 0% target return
        sortino_metrics = engine.calculate_sortino_ratio(portfolio_id, target_return=target_return)
        
        assert sortino_metrics.sortino_ratio != sortino_metrics.sharpe_ratio  # Should differ from Sharpe
        assert sortino_metrics.downside_deviation > 0  # Should have downside deviation
        assert sortino_metrics.downside_deviation < sortino_metrics.total_volatility  # Less than total volatility
        assert sortino_metrics.target_return == target_return
        assert len(sortino_metrics.negative_returns) > 0  # Should have captured negative returns
    
    def test_calmar_ratio_calculation(self):
        """
        RED Phase: Test for Calmar ratio calculation  
        Spec Requirement: "Calmar ratio (CAGR / Maximum Drawdown)"
        """
        engine = CryptoTradingEngine()
        portfolio_id = "calmar_test_portfolio"
        
        # Create portfolio with drawdown scenario
        engine.create_portfolio(portfolio_id, initial_value=Decimal("100000"))
        
        # Portfolio value progression with significant drawdown
        value_progression = [
            (datetime.now() - timedelta(days=365), Decimal("100000")),  # Start
            (datetime.now() - timedelta(days=300), Decimal("120000")),  # +20%
            (datetime.now() - timedelta(days=250), Decimal("140000")),  # Peak +40%
            (datetime.now() - timedelta(days=200), Decimal("105000")),  # Drawdown -25%
            (datetime.now() - timedelta(days=150), Decimal("110000")),  # Recovery
            (datetime.now() - timedelta(days=100), Decimal("125000")),  # New high
            (datetime.now() - timedelta(days=50), Decimal("130000")),   # Growth
            (datetime.now(), Decimal("135000"))                          # Final +35%
        ]
        
        for date, value in value_progression:
            engine.add_portfolio_snapshot(portfolio_id, date, value)
        
        # Calculate Calmar ratio
        calmar_metrics = engine.calculate_calmar_ratio(portfolio_id)
        
        assert calmar_metrics.calmar_ratio > 0  # Should be positive
        assert calmar_metrics.cagr > 0  # Positive annual growth rate
        assert calmar_metrics.max_drawdown > 0  # Should have detected drawdown
        assert calmar_metrics.max_drawdown_pct == Decimal("25.0")  # 25% drawdown (140k -> 105k)
        assert calmar_metrics.time_to_recovery > 0  # Time to recover from drawdown
        assert calmar_metrics.total_return_pct == Decimal("35.0")  # 35% total return
    
    def test_value_at_risk_calculation(self):
        """
        RED Phase: Test for Value at Risk (VaR) calculation
        Spec Requirement: "Value at Risk (VaR) and Expected Shortfall calculations"
        """
        engine = CryptoTradingEngine()
        portfolio_id = "var_test_portfolio"
        
        # Create portfolio with return distribution
        engine.create_portfolio(portfolio_id, initial_value=Decimal("1000000"))  # $1M portfolio
        
        # Generate realistic crypto return distribution (higher volatility)
        returns = [
            Decimal("0.08"), Decimal("-0.12"), Decimal("0.15"), Decimal("-0.08"),
            Decimal("0.03"), Decimal("-0.18"), Decimal("0.22"), Decimal("-0.05"),
            Decimal("0.11"), Decimal("-0.09"), Decimal("0.06"), Decimal("-0.14"),
            Decimal("0.19"), Decimal("-0.07"), Decimal("0.04"), Decimal("-0.21"),
            Decimal("0.13"), Decimal("-0.06"), Decimal("0.09"), Decimal("-0.11"),
            Decimal("0.07"), Decimal("-0.16"), Decimal("0.24"), Decimal("-0.04"),
            Decimal("0.12"), Decimal("-0.13"), Decimal("0.05"), Decimal("-0.19"),
            Decimal("0.17"), Decimal("-0.08"), Decimal("0.10"), Decimal("-0.15")
        ]
        
        for i, return_val in enumerate(returns):
            date = datetime.now() - timedelta(days=len(returns)-i)
            engine.add_daily_return(portfolio_id, date, return_val)
        
        # Calculate VaR at different confidence levels
        var_95 = engine.calculate_var(portfolio_id, confidence_level=Decimal("0.95"))
        var_99 = engine.calculate_var(portfolio_id, confidence_level=Decimal("0.99"))
        
        assert var_95.var_amount > 0  # VaR should be positive (loss amount)
        assert var_99.var_amount > var_95.var_amount  # 99% VaR > 95% VaR
        assert var_95.confidence_level == Decimal("0.95")
        assert var_95.time_horizon == 1  # Daily VaR
        assert var_95.portfolio_value == Decimal("1000000")
        
        # Expected Shortfall should be higher than VaR
        assert var_95.expected_shortfall > var_95.var_amount


class TestBenchmarkComparison:
    """
    TDD Test Suite for Benchmark Comparison and Performance Attribution
    Spec: Epic 2 Phase 2.3 - Benchmark comparison and performance attribution
    
    RED Phase Requirements:
    - Benchmark comparison against crypto indices
    - Alpha and beta calculation
    - Performance attribution by asset class
    - Tracking error analysis
    """
    
    def test_benchmark_comparison_against_btc(self):
        """
        RED Phase: Test fails because BenchmarkAnalytics.compare_to_benchmark() doesn't exist
        Spec Requirement: "Benchmark comparison against major crypto indices"
        """
        engine = CryptoTradingEngine()
        portfolio_id = "benchmark_test_portfolio"
        
        # Create portfolio with performance history
        engine.create_portfolio(portfolio_id)
        
        # Portfolio returns over time
        portfolio_returns = [
            Decimal("0.05"), Decimal("0.08"), Decimal("-0.03"), Decimal("0.12"),
            Decimal("-0.07"), Decimal("0.15"), Decimal("0.02"), Decimal("0.09"),
            Decimal("-0.05"), Decimal("0.11"), Decimal("0.04"), Decimal("0.07")
        ]
        
        # BTC benchmark returns (more volatile)
        btc_benchmark_returns = [
            Decimal("0.08"), Decimal("0.12"), Decimal("-0.08"), Decimal("0.18"),
            Decimal("-0.12"), Decimal("0.22"), Decimal("-0.02"), Decimal("0.14"),
            Decimal("-0.09"), Decimal("0.16"), Decimal("0.01"), Decimal("0.10")
        ]
        
        # Add historical data
        for i, (port_ret, btc_ret) in enumerate(zip(portfolio_returns, btc_benchmark_returns)):
            date = datetime.now() - timedelta(days=len(portfolio_returns)-i)
            engine.add_daily_return(portfolio_id, date, port_ret)
            engine.add_benchmark_return("BTC", date, btc_ret)
        
        # Calculate benchmark comparison
        benchmark_analysis = engine.compare_to_benchmark(portfolio_id, benchmark="BTC")
        
        assert benchmark_analysis.alpha != 0  # Should have alpha (excess return)
        assert benchmark_analysis.beta > 0  # Should have positive beta
        assert benchmark_analysis.beta < Decimal("1.0")  # Lower volatility than BTC
        assert benchmark_analysis.tracking_error > 0  # Should have tracking error
        assert benchmark_analysis.information_ratio != 0  # Active return / tracking error
        assert benchmark_analysis.correlation > 0  # Should be correlated with BTC
        assert benchmark_analysis.r_squared >= 0  # R-squared should be non-negative
    
    def test_performance_attribution_by_asset_class(self):
        """
        RED Phase: Test for performance attribution analysis
        Spec Requirement: "Performance attribution by asset class and strategy"
        """
        engine = CryptoTradingEngine()
        portfolio_id = "attribution_test_portfolio"
        
        # Create diversified crypto portfolio
        engine.create_portfolio(portfolio_id)
        
        # Add positions across different crypto categories
        positions = [
            # Large Cap
            ("BTC/USDT", Decimal("2.0"), "large_cap"),
            ("ETH/USDT", Decimal("10.0"), "large_cap"),
            
            # Mid Cap  
            ("ADA/USDT", Decimal("1000.0"), "mid_cap"),
            ("DOT/USDT", Decimal("100.0"), "mid_cap"),
            
            # DeFi
            ("UNI/USDT", Decimal("50.0"), "defi"),
            ("AAVE/USDT", Decimal("20.0"), "defi"),
            
            # Layer 1
            ("SOL/USDT", Decimal("25.0"), "layer1"),
            ("AVAX/USDT", Decimal("30.0"), "layer1")
        ]
        
        for symbol, quantity, category in positions:
            engine.add_position_to_portfolio(portfolio_id, symbol, quantity, category=category)
        
        # Set performance by category
        category_returns = {
            "large_cap": Decimal("0.15"),  # 15% return
            "mid_cap": Decimal("0.25"),    # 25% return  
            "defi": Decimal("-0.05"),      # -5% return
            "layer1": Decimal("0.35")     # 35% return
        }
        
        for category, return_val in category_returns.items():
            engine.set_category_performance(category, return_val)
        
        # Calculate performance attribution
        attribution = engine.calculate_performance_attribution(portfolio_id)
        
        assert len(attribution.category_contributions) == 4  # Four categories
        assert attribution.total_return > 0  # Net positive return
        
        # Layer 1 should be best contributor (highest return * allocation)
        layer1_contrib = attribution.get_category_contribution("layer1")
        assert layer1_contrib.return_contribution > 0
        assert layer1_contrib.weight_allocation > 0
        assert layer1_contrib.category_return == Decimal("0.35")
        
        # DeFi should detract from performance
        defi_contrib = attribution.get_category_contribution("defi")
        assert defi_contrib.return_contribution < 0  # Negative contribution
    
    def test_tracking_error_analysis(self):
        """
        RED Phase: Test for tracking error and active risk analysis
        Spec Requirement: "Tracking error analysis and active risk management"
        """
        engine = CryptoTradingEngine()
        portfolio_id = "tracking_error_portfolio"
        
        # Create portfolio that tracks a crypto index
        engine.create_portfolio(portfolio_id)
        
        # Portfolio vs Index returns (portfolio has active bets)
        days = 30
        portfolio_returns = []
        index_returns = []
        
        for i in range(days):
            # Index return (market)
            index_ret = Decimal("0.01") + (Decimal(str(i % 5)) - Decimal("2")) * Decimal("0.005")  # Varying returns
            
            # Portfolio return (with active management)
            port_ret = index_ret + (Decimal(str(i % 3)) - Decimal("1")) * Decimal("0.003")  # Active return
            
            portfolio_returns.append(port_ret)
            index_returns.append(index_ret)
            
            date = datetime.now() - timedelta(days=days-i)
            engine.add_daily_return(portfolio_id, date, port_ret)
            engine.add_benchmark_return("CRYPTO_INDEX", date, index_ret)
        
        # Calculate tracking error analysis
        tracking_analysis = engine.calculate_tracking_error(portfolio_id, benchmark="CRYPTO_INDEX")
        
        assert tracking_analysis.tracking_error > 0  # Should have tracking error
        assert tracking_analysis.active_return != 0  # Should have active return
        assert tracking_analysis.information_ratio != 0  # IR = Active Return / Tracking Error
        assert len(tracking_analysis.return_differences) == days  # Should capture all differences
        assert tracking_analysis.annualized_tracking_error > 0  # Annualized metric
        
        # Active risk decomposition
        assert tracking_analysis.systematic_risk >= 0  # Market-related risk
        assert tracking_analysis.idiosyncratic_risk >= 0  # Stock-specific risk
        assert abs(tracking_analysis.systematic_risk + tracking_analysis.idiosyncratic_risk - tracking_analysis.total_active_risk) < Decimal("0.01")


class TestPortfolioRebalancing:
    """
    TDD Test Suite for Portfolio Rebalancing
    Spec: Epic 2 Phase 2.4 - Portfolio rebalancing and optimization
    
    RED Phase Requirements:
    - Target allocation vs current allocation analysis
    - Rebalancing trade generation
    - Transaction cost analysis for rebalancing
    - Drift monitoring and alerts
    """
    
    def test_portfolio_drift_detection(self):
        """
        RED Phase: Test fails because RebalancingEngine.detect_portfolio_drift() doesn't exist
        Spec Requirement: "Portfolio drift monitoring and rebalancing triggers"
        """
        engine = CryptoTradingEngine()
        portfolio_id = "drift_test_portfolio"
        
        # Create portfolio with target allocations
        target_allocations = {
            "BTC/USDT": Decimal("0.50"),   # 50%
            "ETH/USDT": Decimal("0.30"),   # 30%
            "ADA/USDT": Decimal("0.20")    # 20%
        }
        
        engine.create_portfolio(portfolio_id, target_allocations=target_allocations)
        
        # Set initial positions matching targets (100k portfolio)
        engine.add_position_to_portfolio(portfolio_id, "BTC/USDT", quantity=Decimal("1.0"), avg_price=Decimal("50000"))  # 50k
        engine.add_position_to_portfolio(portfolio_id, "ETH/USDT", quantity=Decimal("10.0"), avg_price=Decimal("3000"))   # 30k
        engine.add_position_to_portfolio(portfolio_id, "ADA/USDT", quantity=Decimal("40000.0"), avg_price=Decimal("0.5")) # 20k
        
        # Market moves cause drift - BTC rallies, others decline
        engine.set_real_time_price("BTC/USDT", Decimal("60000"))   # BTC up 20% -> 60k value
        engine.set_real_time_price("ETH/USDT", Decimal("2700"))    # ETH down 10% -> 27k value
        engine.set_real_time_price("ADA/USDT", Decimal("0.45"))    # ADA down 10% -> 18k value
        # Total portfolio: 105k
        
        # Detect drift
        drift_analysis = engine.detect_portfolio_drift(portfolio_id)
        
        assert drift_analysis.has_drift == True  # Should detect drift
        assert len(drift_analysis.allocation_drifts) == 3  # Three positions
        
        # BTC should be overweight (60k/105k = 57.1% vs 50% target)
        btc_drift = drift_analysis.get_allocation_drift("BTC/USDT")
        assert btc_drift.current_allocation > target_allocations["BTC/USDT"]
        assert btc_drift.drift_amount > Decimal("0.05")  # >5% drift
        assert btc_drift.requires_rebalancing == True
        
        # ETH and ADA should be underweight
        eth_drift = drift_analysis.get_allocation_drift("ETH/USDT")
        assert eth_drift.current_allocation < target_allocations["ETH/USDT"]
        assert eth_drift.drift_amount < Decimal("-0.02")  # Underweight
    
    def test_rebalancing_trade_generation(self):
        """
        RED Phase: Test for rebalancing trade generation
        Spec Requirement: "Automatic rebalancing trade generation with cost optimization"
        """
        engine = CryptoTradingEngine()
        portfolio_id = "rebalance_trades_portfolio"
        
        # Portfolio with significant drift
        target_allocations = {
            "BTC/USDT": Decimal("0.40"),   # 40% target
            "ETH/USDT": Decimal("0.35"),   # 35% target  
            "ADA/USDT": Decimal("0.25")    # 25% target
        }
        
        engine.create_portfolio(portfolio_id, target_allocations=target_allocations)
        
        # Current positions (drifted from targets)
        # Current: BTC 60%, ETH 25%, ADA 15% (total 200k)
        engine.add_position_to_portfolio(portfolio_id, "BTC/USDT", quantity=Decimal("2.4"), avg_price=Decimal("50000"))    # 120k (60%)
        engine.add_position_to_portfolio(portfolio_id, "ETH/USDT", quantity=Decimal("16.67"), avg_price=Decimal("3000"))   # 50k (25%)
        engine.add_position_to_portfolio(portfolio_id, "ADA/USDT", quantity=Decimal("60000.0"), avg_price=Decimal("0.5"))  # 30k (15%)
        
        # Generate rebalancing trades
        rebalancing_plan = engine.generate_rebalancing_trades(portfolio_id)
        
        assert rebalancing_plan.requires_rebalancing == True
        assert len(rebalancing_plan.trades) > 0  # Should generate trades
        
        # BTC should be sold (overweight: 60% -> 40%)
        btc_trade = rebalancing_plan.get_trade("BTC/USDT")
        assert btc_trade.side == "SELL"
        assert btc_trade.usd_amount == Decimal("40000")  # Sell 40k worth (200k * 20%)
        
        # ETH should be bought (underweight: 25% -> 35%)
        eth_trade = rebalancing_plan.get_trade("ETH/USDT")
        assert eth_trade.side == "BUY"
        assert eth_trade.usd_amount == Decimal("20000")  # Buy 20k worth (200k * 10%)
        
        # ADA should be bought (underweight: 15% -> 25%)
        ada_trade = rebalancing_plan.get_trade("ADA/USDT")
        assert ada_trade.side == "BUY"
        assert ada_trade.usd_amount == Decimal("20000")  # Buy 20k worth (200k * 10%)
        
        # Verify cash flows balance
        total_sells = sum(trade.usd_amount for trade in rebalancing_plan.trades if trade.side == "SELL")
        total_buys = sum(trade.usd_amount for trade in rebalancing_plan.trades if trade.side == "BUY")
        assert abs(total_sells - total_buys) < Decimal("100")  # Should roughly balance
    
    def test_rebalancing_cost_analysis(self):
        """
        RED Phase: Test for rebalancing transaction cost analysis
        Spec Requirement: "Transaction cost analysis and optimization for rebalancing"
        """
        engine = CryptoTradingEngine()
        portfolio_id = "cost_analysis_portfolio"
        
        # Create portfolio needing rebalancing
        engine.create_portfolio(portfolio_id)
        
        # Generate rebalancing plan
        trades = [
            {"symbol": "BTC/USDT", "side": "SELL", "usd_amount": Decimal("50000")},
            {"symbol": "ETH/USDT", "side": "BUY", "usd_amount": Decimal("30000")},
            {"symbol": "ADA/USDT", "side": "BUY", "usd_amount": Decimal("20000")}
        ]
        
        # Set trading costs for each exchange
        engine.set_trading_fees("binance", "BTC/USDT", maker_fee=Decimal("0.001"), taker_fee=Decimal("0.001"))
        engine.set_trading_fees("binance", "ETH/USDT", maker_fee=Decimal("0.001"), taker_fee=Decimal("0.001"))
        engine.set_trading_fees("okx", "ADA/USDT", maker_fee=Decimal("0.0008"), taker_fee=Decimal("0.0008"))
        
        # Set market impact estimates
        engine.set_market_impact("BTC/USDT", Decimal("0.0005"))  # 0.05% impact for BTC
        engine.set_market_impact("ETH/USDT", Decimal("0.0008"))  # 0.08% impact for ETH
        engine.set_market_impact("ADA/USDT", Decimal("0.0012"))  # 0.12% impact for ADA
        
        # Calculate rebalancing costs
        cost_analysis = engine.calculate_rebalancing_costs(portfolio_id, trades)
        
        assert cost_analysis.total_cost > 0  # Should have costs
        assert cost_analysis.total_cost_pct < Decimal("0.01")  # <1% of portfolio
        
        # Breakdown by cost type
        assert cost_analysis.trading_fees > 0  # Exchange fees
        assert cost_analysis.market_impact_cost > 0  # Slippage costs
        assert cost_analysis.spread_cost > 0  # Bid-ask spread costs
        
        # Cost by trade
        assert len(cost_analysis.trade_costs) == 3  # Three trades
        btc_cost = cost_analysis.get_trade_cost("BTC/USDT")
        assert btc_cost.fee_cost == Decimal("50")  # 50k * 0.001 = 50 USDT
        assert btc_cost.impact_cost == Decimal("25")  # 50k * 0.0005 = 25 USDT
        
        # Cost-benefit analysis
        assert cost_analysis.net_benefit > 0  # Rebalancing should be beneficial
        assert cost_analysis.break_even_horizon > 0  # Days to break even