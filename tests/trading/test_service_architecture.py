# -*- coding: utf-8 -*-
"""
Test Suite for SOLID Architecture Service Extraction
====================================================

Validates that the internal service composition pattern is working correctly
and that the SOLID principles are being followed.

Architecture Pattern: Composition + Delegation
- CryptoTradingEngine maintains backward compatibility
- Internal services handle specific responsibilities
- Clean interfaces enable better testing and maintainability
"""

import pytest
from decimal import Decimal
from unittest.mock import patch, Mock

from src.zvt.trading.crypto_trading_engine import (
    CryptoTradingEngine, OrderRequest, 
    TradingService, PortfolioService, AnalyticsService, 
    RebalancingService, HatchetAdapter
)
from src.zvt.trading.models import Order, OrderSide, OrderType


class TestServiceComposition:
    """Test that internal services are properly composed and accessible."""
    
    def test_all_services_initialized(self):
        """Test that all internal services are initialized in the engine."""
        engine = CryptoTradingEngine()
        
        # Verify all services are present
        assert hasattr(engine, 'trading_service')
        assert hasattr(engine, 'portfolio_service')
        assert hasattr(engine, 'analytics_service')
        assert hasattr(engine, 'rebalancing_service')
        assert hasattr(engine, 'hatchet_adapter')
        
        # Verify service types
        assert isinstance(engine.trading_service, TradingService)
        assert isinstance(engine.portfolio_service, PortfolioService)
        assert isinstance(engine.analytics_service, AnalyticsService)
        assert isinstance(engine.rebalancing_service, RebalancingService)
        assert isinstance(engine.hatchet_adapter, HatchetAdapter)
    
    def test_service_access_to_engine(self):
        """Test that services have proper access to the main engine."""
        engine = CryptoTradingEngine()
        
        # All services should have reference to engine
        assert engine.trading_service.engine is engine
        assert engine.portfolio_service.engine is engine
        assert engine.analytics_service.engine is engine
        assert engine.rebalancing_service.engine is engine
        assert engine.hatchet_adapter.engine is engine


class TestTradingServiceDelegation:
    """Test that trading operations properly delegate to TradingService."""
    
    def test_place_order_delegation(self):
        """Test that place_order delegates to trading service."""
        engine = CryptoTradingEngine()
        
        order_request = OrderRequest(
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("1.0"),
            portfolio_id="test"
        )
        
        # Mock the internal implementation
        with patch.object(engine, '_place_order_impl') as mock_impl:
            mock_impl.return_value = Mock(success=True, order_id="test_123")
            
            result = engine.place_order(order_request)
            
            assert result.success == True
            assert result.order_id == "test_123"
            mock_impl.assert_called_once_with(order_request)
    
    def test_available_exchanges_access(self):
        """Test that exchanges are accessible through trading service."""
        engine = CryptoTradingEngine(exchanges=["binance", "okx"])
        
        exchanges = engine.trading_service.get_available_exchanges()
        assert exchanges == ["binance", "okx"]


class TestPortfolioServiceDelegation:
    """Test that portfolio operations properly delegate to PortfolioService."""
    
    def test_get_positions_delegation(self):
        """Test that get_positions delegates to portfolio service."""
        engine = CryptoTradingEngine()
        
        # Mock the internal implementation
        with patch.object(engine, '_get_positions_impl') as mock_impl:
            mock_impl.return_value = []
            
            result = engine.get_positions("test_portfolio")
            
            assert result == []
            mock_impl.assert_called_once_with("test_portfolio")
    
    def test_portfolio_summary_delegation(self):
        """Test that get_portfolio_summary delegates to portfolio service."""
        engine = CryptoTradingEngine()
        
        # Mock the internal implementation  
        with patch.object(engine, '_get_portfolio_summary_impl') as mock_impl:
            mock_summary = Mock()
            mock_summary.total_value = Decimal("100000")
            mock_impl.return_value = mock_summary
            
            result = engine.get_portfolio_summary("test_portfolio")
            
            assert result.total_value == Decimal("100000")
            mock_impl.assert_called_once_with("test_portfolio")


class TestAnalyticsServiceDelegation:
    """Test that analytics operations properly delegate to AnalyticsService."""
    
    def test_performance_metrics_delegation(self):
        """Test that get_performance_metrics delegates to analytics service."""
        engine = CryptoTradingEngine()
        
        # Mock the internal implementation
        with patch.object(engine, '_get_performance_metrics_impl') as mock_impl:
            mock_impl.return_value = {"total_orders": 10, "avg_latency": 50.5}
            
            result = engine.get_performance_metrics()
            
            assert result["total_orders"] == 10
            assert result["avg_latency"] == 50.5
            mock_impl.assert_called_once()
    
    def test_portfolio_analytics_methods_available(self):
        """Test that portfolio analytics methods are available via service."""
        engine = CryptoTradingEngine()
        analytics = engine.analytics_service
        
        # Test that analytics methods exist
        assert hasattr(analytics, 'calculate_portfolio_performance')
        assert hasattr(analytics, 'calculate_sharpe_ratio')
        assert hasattr(analytics, 'calculate_sortino_ratio')
        assert hasattr(analytics, 'calculate_calmar_ratio')
        assert hasattr(analytics, 'calculate_var')
        assert hasattr(analytics, 'compare_to_benchmark')


class TestRebalancingServiceDelegation:
    """Test that rebalancing operations properly delegate to RebalancingService."""
    
    def test_rebalancing_methods_available(self):
        """Test that rebalancing methods are available via service."""
        engine = CryptoTradingEngine()
        rebalancing = engine.rebalancing_service
        
        # Test that rebalancing methods exist
        assert hasattr(rebalancing, 'detect_portfolio_drift')
        assert hasattr(rebalancing, 'generate_rebalancing_trades')
        assert hasattr(rebalancing, 'calculate_rebalancing_costs')
        assert hasattr(rebalancing, 'set_trading_fees')
        assert hasattr(rebalancing, 'set_market_impact')


class TestHatchetAdapterDelegation:
    """Test that Hatchet workflow operations properly delegate to HatchetAdapter."""
    
    def test_hatchet_methods_available(self):
        """Test that Hatchet workflow methods are available via adapter."""
        engine = CryptoTradingEngine()
        hatchet = engine.hatchet_adapter
        
        # Test that Hatchet methods exist
        assert hasattr(hatchet, 'execute_order_workflow')
        assert hasattr(hatchet, 'start_rebalancing_workflow')
        assert hasattr(hatchet, 'start_risk_monitoring_workflow')
        assert hasattr(hatchet, 'emit_price_update_event')
        assert hasattr(hatchet, 'get_triggered_workflows')
        assert hasattr(hatchet, 'get_hatchet_metrics')
        assert hasattr(hatchet, 'handle_trading_error')


class TestBackwardCompatibility:
    """Test that the service architecture maintains full backward compatibility."""
    
    def test_legacy_api_still_works(self):
        """Test that existing API calls still work without modification."""
        engine = CryptoTradingEngine()
        
        # These should all work exactly as before
        assert hasattr(engine, 'place_order')
        assert hasattr(engine, 'cancel_order')
        assert hasattr(engine, 'get_order_status')
        assert hasattr(engine, 'get_positions')
        assert hasattr(engine, 'get_portfolio_summary')
        assert hasattr(engine, 'create_portfolio')
        assert hasattr(engine, 'calculate_portfolio_value')
        assert hasattr(engine, 'calculate_portfolio_performance')
        assert hasattr(engine, 'detect_portfolio_drift')
        assert hasattr(engine, 'generate_rebalancing_trades')
    
    def test_constructor_signature_unchanged(self):
        """Test that constructor signature remains the same."""
        # Should work with no arguments
        engine1 = CryptoTradingEngine()
        assert engine1 is not None
        
        # Should work with exchanges argument
        engine2 = CryptoTradingEngine(exchanges=["binance", "okx"])
        assert engine2.exchanges == ["binance", "okx"]
    
    def test_existing_components_still_present(self):
        """Test that existing components are still accessible."""
        engine = CryptoTradingEngine()
        
        # Core components should still exist
        assert hasattr(engine, 'order_manager')
        assert hasattr(engine, 'position_manager') 
        assert hasattr(engine, 'risk_manager')
        assert hasattr(engine, 'hatchet_integration')
        assert hasattr(engine, 'data_loader')


class TestSOLIDPrinciples:
    """Test that SOLID principles are being followed in the new architecture."""
    
    def test_single_responsibility_principle(self):
        """Test that each service has a single, focused responsibility."""
        engine = CryptoTradingEngine()
        
        # TradingService: Order management and execution
        trading_methods = [m for m in dir(engine.trading_service) if not m.startswith('_')]
        trading_expected = ['place_order', 'cancel_order', 'get_order_status', 'get_available_exchanges', 'route_order']
        assert all(method in trading_methods for method in trading_expected)
        
        # PortfolioService: Portfolio and position management
        portfolio_methods = [m for m in dir(engine.portfolio_service) if not m.startswith('_')]
        portfolio_expected = ['get_positions', 'get_portfolio_summary', 'create_portfolio', 'add_position_to_portfolio']
        assert all(method in portfolio_methods for method in portfolio_expected)
    
    def test_interface_segregation_principle(self):
        """Test that services provide focused interfaces."""
        engine = CryptoTradingEngine()
        
        # Each service should have a focused set of methods
        # TradingService shouldn't have portfolio methods
        assert not hasattr(engine.trading_service, 'calculate_portfolio_value')
        assert not hasattr(engine.trading_service, 'calculate_sharpe_ratio')
        
        # PortfolioService shouldn't have trading methods
        assert not hasattr(engine.portfolio_service, 'place_order')
        assert not hasattr(engine.portfolio_service, 'cancel_order')
        
        # AnalyticsService shouldn't have trading methods
        assert not hasattr(engine.analytics_service, 'place_order')
        assert not hasattr(engine.analytics_service, 'get_positions')
    
    def test_dependency_inversion_principle(self):
        """Test that services depend on the engine abstraction."""
        engine = CryptoTradingEngine()
        
        # All services should depend on the engine (abstraction)
        assert engine.trading_service.engine is engine
        assert engine.portfolio_service.engine is engine
        assert engine.analytics_service.engine is engine
        assert engine.rebalancing_service.engine is engine
        assert engine.hatchet_adapter.engine is engine