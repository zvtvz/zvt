# tests/trading/test_position_management.py
"""
TDD Test Suite for Position Management Specification - RED Phase
Spec: Epic 2 Phase 2.1 - Position Management System
Methodology: Test-Driven Development (Red-Green-Refactor)

RED Phase: These tests MUST fail initially because implementation doesn't exist
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import Mock
from src.zvt.trading.position_manager import PositionManager
from src.zvt.trading.models import Position, Trade, PositionPnL, PortfolioSummary
from src.zvt.trading.exceptions import InsufficientPositionError


class TestPositionTracking:
    """
    TDD Test Suite for Position Tracking
    Spec: Epic 2 Phase 2.1 - Real-time Position Management
    
    RED Phase Requirements:
    - Multi-exchange position aggregation
    - Real-time mark-to-market with streaming prices
    - Position risk management integration
    - Position history and analytics
    """
    
    def test_create_position_from_trade(self):
        """
        RED Phase: Test position creation from trade execution
        Spec Requirement: "Position creation and tracking"
        """
        manager = PositionManager()
        
        trade = Trade(
            trade_id="trade-001",
            symbol="BTC/USDT", 
            side="buy",
            amount=Decimal("1.0"),
            price=Decimal("50000"),
            fee=Decimal("25"),
            exchange="binance",
            timestamp=datetime.now()
        )
        
        manager.process_trade(trade)
        
        position = manager.get_position("BTC/USDT")
        assert position.symbol == "BTC/USDT"
        assert position.total_quantity == Decimal("1.0")
        assert position.avg_cost == Decimal("50025")  # Including fee
        assert position.exchange_positions["binance"] == Decimal("1.0")
    
    def test_aggregate_positions_across_exchanges(self):
        """
        RED Phase: Test multi-exchange position aggregation
        Spec Requirement: "Multi-exchange position aggregation"
        """
        manager = PositionManager()
        
        # Trade on Binance
        trade1 = Trade(
            trade_id="trade-001",
            symbol="ETH/USDT",
            side="buy", 
            amount=Decimal("5.0"),
            price=Decimal("3000"),
            fee=Decimal("7.5"),
            exchange="binance"
        )
        
        # Trade on OKX
        trade2 = Trade(
            trade_id="trade-002", 
            symbol="ETH/USDT",
            side="buy",
            amount=Decimal("3.0"),
            price=Decimal("3100"),
            fee=Decimal("4.65"),
            exchange="okx"
        )
        
        manager.process_trade(trade1)
        manager.process_trade(trade2)
        
        position = manager.get_position("ETH/USDT")
        assert position.total_quantity == Decimal("8.0")
        assert position.exchange_positions["binance"] == Decimal("5.0")
        assert position.exchange_positions["okx"] == Decimal("3.0")
        
        # Weighted average cost including fees
        expected_avg_cost = (Decimal("15007.5") + Decimal("9304.65")) / Decimal("8.0")
        assert abs(position.avg_cost - expected_avg_cost) < Decimal("0.01")
    
    def test_update_position_with_opposing_trade(self):
        """
        RED Phase: Test position updates with sell trades
        Spec Requirement: "Position updates with trade reconciliation"
        """
        manager = PositionManager()
        
        # Initial buy position
        buy_trade = Trade(
            trade_id="buy-001",
            symbol="ADA/USDT",
            side="buy",
            amount=Decimal("1000"),
            price=Decimal("1.5"),
            exchange="binance"
        )
        
        # Partial sell
        sell_trade = Trade(
            trade_id="sell-001",
            symbol="ADA/USDT", 
            side="sell",
            amount=Decimal("300"),
            price=Decimal("1.8"),
            exchange="binance"
        )
        
        manager.process_trade(buy_trade)
        manager.process_trade(sell_trade)
        
        position = manager.get_position("ADA/USDT")
        assert position.total_quantity == Decimal("700")
        assert position.realized_pnl == Decimal("90")  # (1.8-1.5) * 300
    
    def test_calculate_real_time_pnl(self):
        """
        RED Phase: Test real-time PnL calculation with streaming prices
        Spec Requirement: "Real-time mark-to-market with streaming prices"
        """
        manager = PositionManager()
        
        # Create position
        trade = Trade(
            trade_id="trade-001",
            symbol="BTC/USDT",
            side="buy",
            amount=Decimal("0.5"),
            price=Decimal("45000"),
            exchange="binance"
        )
        
        manager.process_trade(trade)
        
        # Update current market price
        manager.update_market_price("BTC/USDT", Decimal("47000"))
        
        pnl = manager.calculate_position_pnl("BTC/USDT")
        assert pnl.unrealized_pnl == Decimal("1000")  # (47000-45000) * 0.5
        assert pnl.percentage_return == Decimal("0.044")  # Approximately 4.4%
        assert pnl.market_value == Decimal("23500")  # 47000 * 0.5
    
    def test_position_risk_metrics_calculation(self):
        """
        RED Phase: Test position risk metrics
        Spec Requirement: "Position risk management integration"
        """
        manager = PositionManager()
        
        # Create position with price history
        trade = Trade(
            trade_id="trade-001",
            symbol="ETH/USDT",
            side="buy",
            amount=Decimal("10"),
            price=Decimal("3000"),
            exchange="okx"
        )
        
        manager.process_trade(trade)
        
        # Add price history for volatility calculation
        price_history = [
            (datetime.now() - timedelta(days=30), Decimal("2800")),
            (datetime.now() - timedelta(days=20), Decimal("3200")),
            (datetime.now() - timedelta(days=10), Decimal("2900")),
            (datetime.now(), Decimal("3100"))
        ]
        
        manager.add_price_history("ETH/USDT", price_history)
        
        risk_metrics = manager.calculate_position_risk("ETH/USDT")
        
        assert risk_metrics.value_at_risk_95 is not None
        assert risk_metrics.volatility > 0
        assert risk_metrics.max_drawdown_pct is not None
        assert risk_metrics.beta is not None


class TestPortfolioManagement:
    """
    TDD Test Suite for Portfolio Management
    Spec: Epic 2 Phase 2.2 - Portfolio Analytics and Management
    
    RED Phase: Portfolio-level position management tests
    """
    
    def test_calculate_total_portfolio_value(self):
        """
        RED Phase: Test total portfolio valuation
        Spec Requirement: "Real-time portfolio tracking and valuation"
        """
        manager = PositionManager()
        
        # Multiple positions
        trades = [
            Trade("t1", "BTC/USDT", "buy", Decimal("1"), Decimal("50000"), exchange="binance"),
            Trade("t2", "ETH/USDT", "buy", Decimal("10"), Decimal("3000"), exchange="okx"),
            Trade("t3", "ADA/USDT", "buy", Decimal("1000"), Decimal("1.5"), exchange="bybit")
        ]
        
        for trade in trades:
            manager.process_trade(trade)
        
        # Update current prices
        manager.update_market_price("BTC/USDT", Decimal("52000"))
        manager.update_market_price("ETH/USDT", Decimal("3200")) 
        manager.update_market_price("ADA/USDT", Decimal("1.8"))
        
        portfolio_value = manager.get_total_portfolio_value()
        expected_value = Decimal("52000") + Decimal("32000") + Decimal("1800")  # 85,800
        assert portfolio_value == expected_value
    
    def test_calculate_portfolio_pnl_summary(self):
        """
        RED Phase: Test portfolio PnL summary
        Spec Requirement: "Portfolio performance analytics"
        """
        manager = PositionManager()
        
        # Create positions with known cost basis
        trades = [
            Trade("t1", "BTC/USDT", "buy", Decimal("0.5"), Decimal("48000"), exchange="binance"),
            Trade("t2", "ETH/USDT", "buy", Decimal("5"), Decimal("2800"), exchange="okx")
        ]
        
        for trade in trades:
            manager.process_trade(trade)
        
        # Update to current prices
        manager.update_market_price("BTC/USDT", Decimal("50000"))
        manager.update_market_price("ETH/USDT", Decimal("3200"))
        
        summary = manager.get_portfolio_summary()
        
        assert summary.total_cost == Decimal("38000")  # (48000*0.5) + (2800*5)
        assert summary.total_market_value == Decimal("41000")  # (50000*0.5) + (3200*5)
        assert summary.total_unrealized_pnl == Decimal("3000")  # 41000 - 38000
        assert summary.total_return_pct == Decimal("0.0789")  # Approximately 7.89%
    
    def test_portfolio_allocation_analysis(self):
        """
        RED Phase: Test portfolio allocation breakdown
        Spec Requirement: "Portfolio allocation and rebalancing analytics"
        """
        manager = PositionManager()
        
        # Create diversified portfolio
        trades = [
            Trade("t1", "BTC/USDT", "buy", Decimal("1"), Decimal("50000"), exchange="binance"),   # 50k
            Trade("t2", "ETH/USDT", "buy", Decimal("10"), Decimal("3000"), exchange="okx"),      # 30k  
            Trade("t3", "ADA/USDT", "buy", Decimal("10000"), Decimal("2"), exchange="bybit")     # 20k
        ]
        
        for trade in trades:
            manager.process_trade(trade)
        
        allocation = manager.get_portfolio_allocation()
        
        assert abs(allocation["BTC/USDT"] - Decimal("0.5")) < Decimal("0.01")     # 50%
        assert abs(allocation["ETH/USDT"] - Decimal("0.3")) < Decimal("0.01")     # 30%
        assert abs(allocation["ADA/USDT"] - Decimal("0.2")) < Decimal("0.01")     # 20%
    
    def test_multi_currency_portfolio_support(self):
        """
        RED Phase: Test multi-currency portfolio tracking
        Spec Requirement: "Multi-currency portfolio support"
        """
        manager = PositionManager(base_currency="USD")
        
        # Positions in different quote currencies
        trades = [
            Trade("t1", "BTC/USD", "buy", Decimal("1"), Decimal("50000"), exchange="coinbase"),
            Trade("t2", "ETH/EUR", "buy", Decimal("10"), Decimal("2500"), exchange="binance"),  # EUR pair
            Trade("t3", "ADA/BTC", "buy", Decimal("100000"), Decimal("0.000025"), exchange="okx") # BTC pair
        ]
        
        for trade in trades:
            manager.process_trade(trade)
        
        # Set exchange rates
        manager.set_exchange_rate("EUR", "USD", Decimal("1.1"))
        manager.set_exchange_rate("BTC", "USD", Decimal("50000"))
        
        # Get portfolio value in USD
        portfolio_value_usd = manager.get_total_portfolio_value("USD")
        
        expected_value = Decimal("50000") + (Decimal("25000") * Decimal("1.1")) + Decimal("125000")
        assert abs(portfolio_value_usd - expected_value) < Decimal("1")


class TestPositionRiskManagement:
    """
    TDD Test Suite for Position Risk Management  
    Spec: Epic 2 Phase 2.3 - Risk Management Integration
    
    RED Phase: Position-level risk management tests
    """
    
    def test_position_size_limits_enforcement(self):
        """
        RED Phase: Test position size limit enforcement
        Spec Requirement: "Position limits and validation framework"
        """
        manager = PositionManager()
        
        # Set position limit
        manager.set_position_limit("BTC/USDT", max_position=Decimal("2.0"))
        
        # Create position at limit
        trade1 = Trade("t1", "BTC/USDT", "buy", Decimal("2.0"), Decimal("50000"), exchange="binance")
        manager.process_trade(trade1)
        
        # Attempt to exceed limit
        trade2 = Trade("t2", "BTC/USDT", "buy", Decimal("0.5"), Decimal("51000"), exchange="okx")
        
        with pytest.raises(PositionLimitExceededError):
            manager.process_trade(trade2)
    
    def test_concentration_risk_monitoring(self):
        """
        RED Phase: Test portfolio concentration limits
        Spec Requirement: "Concentration risk monitoring and alerts"
        """
        manager = PositionManager()
        
        # Set concentration limit (max 60% in any single asset)
        manager.set_concentration_limit(max_allocation_pct=Decimal("0.6"))
        
        # Create concentrated position
        trades = [
            Trade("t1", "BTC/USDT", "buy", Decimal("2"), Decimal("50000"), exchange="binance"),    # 100k
            Trade("t2", "ETH/USDT", "buy", Decimal("10"), Decimal("3000"), exchange="okx")         # 30k
        ]
        
        for trade in trades:
            manager.process_trade(trade)
        
        # Try to add more BTC (would make it 70% of portfolio)
        concentrated_trade = Trade("t3", "BTC/USDT", "buy", Decimal("1"), Decimal("50000"), exchange="bybit")
        
        risk_check = manager.check_concentration_risk(concentrated_trade)
        assert risk_check.exceeds_limit == True
        assert risk_check.projected_allocation > Decimal("0.6")
    
    def test_correlation_risk_analysis(self):
        """
        RED Phase: Test correlation-based risk analysis
        Spec Requirement: "Correlation analysis and monitoring"
        """
        manager = PositionManager()
        
        # Create correlated positions
        trades = [
            Trade("t1", "BTC/USDT", "buy", Decimal("1"), Decimal("50000"), exchange="binance"),
            Trade("t2", "ETH/USDT", "buy", Decimal("10"), Decimal("3000"), exchange="okx")
        ]
        
        for trade in trades:
            manager.process_trade(trade)
        
        # Set correlation data (BTC-ETH typically highly correlated in crypto)
        manager.set_asset_correlation("BTC/USDT", "ETH/USDT", correlation=Decimal("0.85"))
        
        correlation_risk = manager.analyze_correlation_risk()
        
        assert correlation_risk.high_correlation_pairs[0]["pair"] == ("BTC/USDT", "ETH/USDT")
        assert correlation_risk.high_correlation_pairs[0]["correlation"] == Decimal("0.85")
        assert correlation_risk.portfolio_correlation_score > Decimal("0.5")
    
    def test_leverage_calculation_and_limits(self):
        """
        RED Phase: Test leverage calculation and enforcement
        Spec Requirement: "Leverage calculations and margin requirements"
        """
        manager = PositionManager()
        
        # Set account equity
        manager.set_account_equity(Decimal("100000"))
        
        # Set leverage limit
        manager.set_max_leverage(Decimal("3.0"))
        
        # Create leveraged positions
        trades = [
            Trade("t1", "BTC/USDT", "buy", Decimal("4"), Decimal("50000"), exchange="binance"),  # 200k notional
            Trade("t2", "ETH/USDT", "buy", Decimal("20"), Decimal("3000"), exchange="okx")       # 60k notional  
        ]
        
        for trade in trades:
            manager.process_trade(trade)
        
        leverage_info = manager.calculate_portfolio_leverage()
        
        assert leverage_info.current_leverage == Decimal("2.6")  # 260k / 100k
        assert leverage_info.leverage_utilization == Decimal("0.867")  # 2.6 / 3.0
        assert leverage_info.remaining_buying_power == Decimal("40000")  # (3.0 - 2.6) * 100k


class TestPositionHistory:
    """
    TDD Test Suite for Position History and Analytics
    Spec: Epic 2 Phase 2.4 - Position Analytics and Reporting
    
    RED Phase: Position history and analytics tests  
    """
    
    def test_position_history_tracking(self):
        """
        RED Phase: Test position history maintenance
        Spec Requirement: "Position history and analytics"
        """
        manager = PositionManager()
        
        # Series of trades over time
        trades = [
            Trade("t1", "BTC/USDT", "buy", Decimal("1"), Decimal("45000"), 
                 exchange="binance", timestamp=datetime(2024, 1, 1)),
            Trade("t2", "BTC/USDT", "buy", Decimal("0.5"), Decimal("48000"), 
                 exchange="okx", timestamp=datetime(2024, 1, 15)),
            Trade("t3", "BTC/USDT", "sell", Decimal("0.3"), Decimal("52000"), 
                 exchange="binance", timestamp=datetime(2024, 2, 1))
        ]
        
        for trade in trades:
            manager.process_trade(trade)
        
        history = manager.get_position_history("BTC/USDT")
        
        assert len(history.snapshots) == 3
        assert history.snapshots[0].quantity == Decimal("1.0")
        assert history.snapshots[1].quantity == Decimal("1.5")
        assert history.snapshots[2].quantity == Decimal("1.2")
        
        assert history.total_trades == 3
        assert history.total_volume == Decimal("1.8")  # 1 + 0.5 + 0.3
    
    def test_position_performance_analytics(self):
        """
        RED Phase: Test position performance metrics
        Spec Requirement: "Performance attribution and analysis"
        """
        manager = PositionManager()
        
        # Create position with realized and unrealized gains
        trades = [
            Trade("t1", "ETH/USDT", "buy", Decimal("10"), Decimal("2000"), exchange="binance"),
            Trade("t2", "ETH/USDT", "sell", Decimal("5"), Decimal("2500"), exchange="binance")
        ]
        
        for trade in trades:
            manager.process_trade(trade)
        
        # Current market price for remaining position
        manager.update_market_price("ETH/USDT", Decimal("2800"))
        
        performance = manager.get_position_performance("ETH/USDT")
        
        assert performance.realized_pnl == Decimal("2500")  # (2500-2000) * 5
        assert performance.unrealized_pnl == Decimal("4000")  # (2800-2000) * 5
        assert performance.total_return == Decimal("6500")
        assert performance.win_rate == Decimal("1.0")  # 100% winning trades
        assert performance.avg_win > 0
    
    def test_position_drawdown_analysis(self):
        """
        RED Phase: Test position drawdown tracking
        Spec Requirement: "Drawdown analysis and risk metrics"
        """
        manager = PositionManager()
        
        # Create position
        trade = Trade("t1", "BTC/USDT", "buy", Decimal("1"), Decimal("50000"), exchange="binance")
        manager.process_trade(trade)
        
        # Simulate price movements creating drawdown
        price_updates = [
            (datetime(2024, 1, 1), Decimal("52000")),   # +4%
            (datetime(2024, 1, 5), Decimal("48000")),   # -4%
            (datetime(2024, 1, 10), Decimal("45000")),  # -10%
            (datetime(2024, 1, 15), Decimal("51000"))   # +2%
        ]
        
        for timestamp, price in price_updates:
            manager.update_market_price("BTC/USDT", price, timestamp=timestamp)
        
        drawdown_analysis = manager.get_position_drawdown("BTC/USDT")
        
        assert drawdown_analysis.max_drawdown_pct == Decimal("-0.10")  # -10%
        assert drawdown_analysis.max_drawdown_amount == Decimal("-5000")
        assert drawdown_analysis.current_drawdown_pct == Decimal("0.02")  # +2%
        assert len(drawdown_analysis.drawdown_periods) >= 1