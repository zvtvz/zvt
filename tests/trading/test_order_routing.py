# tests/trading/test_order_routing.py
"""
TDD Test Suite for Order Routing Specification - RED Phase
Spec: Epic 2 Phase 1.1 - Order Management System
Methodology: Test-Driven Development (Red-Green-Refactor)

RED Phase: These tests MUST fail initially because implementation doesn't exist
"""
import pytest
from decimal import Decimal
from unittest.mock import Mock
from src.zvt.trading.crypto_trading_engine import CryptoTradingEngine
from src.zvt.trading.models import Order, OrderType, OrderSide, OrderResult, OrderRoutingResult
from src.zvt.trading.exceptions import NoAvailableExchangeError, InsufficientBalanceError


class TestOrderRouting:
    """
    TDD Test Suite for Order Routing Specification
    Spec: Epic 2 Phase 1.1 - Order Management System
    
    RED Phase Requirements:
    - Multi-exchange order routing based on liquidity depth
    - Smart routing based on fees and spreads  
    - Order validation and risk checks
    - Real-time order status tracking
    """
    
    def test_order_routing_selects_best_exchange_for_liquidity(self):
        """
        RED Phase: Test fails because CryptoTradingEngine.route_order() doesn't exist
        Spec Requirement: "Smart routing across exchanges based on liquidity depth"
        """
        # Arrange
        engine = CryptoTradingEngine()
        order = Order(
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            amount=Decimal("1.0"),
            order_type=OrderType.MARKET
        )
        
        # Mock exchange liquidity data
        engine.add_exchange_liquidity("binance", "BTC/USDT", bid_depth=100.0)
        engine.add_exchange_liquidity("okx", "BTC/USDT", bid_depth=50.0)
        
        # Act & Assert (This MUST fail initially - RED phase)
        result = engine.route_order(order)
        assert result.selected_exchange == "binance"  # Higher liquidity
        assert result.routing_reason == "best_liquidity"
    
    def test_order_routing_considers_fees_when_liquidity_similar(self):
        """
        RED Phase: Test for fee-based routing logic
        Spec Requirement: "Smart routing based on fees and spreads"
        """
        engine = CryptoTradingEngine()
        order = Order(
            symbol="ETH/USDT", 
            side=OrderSide.SELL, 
            amount=Decimal("5.0"),
            order_type=OrderType.MARKET
        )
        
        # Similar liquidity, different fees
        engine.add_exchange_liquidity("binance", "ETH/USDT", ask_depth=100.0, fee=0.001)
        engine.add_exchange_liquidity("coinbase", "ETH/USDT", ask_depth=95.0, fee=0.0005)
        
        result = engine.route_order(order)
        assert result.selected_exchange == "coinbase"  # Lower fees
        assert result.routing_reason == "lower_fees"
    
    def test_order_routing_validates_exchange_availability(self):
        """
        RED Phase: Test for exchange availability validation
        Spec Requirement: "Order validation and risk checks"
        """
        engine = CryptoTradingEngine()
        order = Order(
            symbol="ADA/USDT", 
            side=OrderSide.BUY, 
            amount=Decimal("1000.0"),
            order_type=OrderType.MARKET
        )
        
        # No exchanges available for this symbol
        with pytest.raises(NoAvailableExchangeError):
            engine.route_order(order)
    
    def test_order_routing_handles_multiple_order_types(self):
        """
        RED Phase: Test for different order type routing
        Spec Requirement: "Advanced order types (market, limit, stop-loss, OCO)"
        """
        engine = CryptoTradingEngine()
        
        # Test market order routing
        market_order = Order(
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            amount=Decimal("0.5"),
            order_type=OrderType.MARKET
        )
        
        # Test limit order routing  
        limit_order = Order(
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            amount=Decimal("0.5"),
            order_type=OrderType.LIMIT,
            price=Decimal("45000")
        )
        
        # Test stop-loss order routing
        stop_order = Order(
            symbol="BTC/USDT",
            side=OrderSide.SELL,
            amount=Decimal("0.5"),
            order_type=OrderType.STOP_LOSS,
            stop_price=Decimal("48000")
        )
        
        engine.add_exchange_liquidity("binance", "BTC/USDT", bid_depth=100.0, ask_depth=100.0)
        
        market_result = engine.route_order(market_order)
        limit_result = engine.route_order(limit_order)
        stop_result = engine.route_order(stop_order)
        
        assert market_result.selected_exchange == "binance"
        assert limit_result.selected_exchange == "binance"
        assert stop_result.selected_exchange == "binance"
    
    def test_order_routing_considers_slippage_impact(self):
        """
        RED Phase: Test for slippage-aware routing
        Spec Requirement: "Slippage optimization algorithms"
        """
        engine = CryptoTradingEngine()
        large_order = Order(
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            amount=Decimal("10.0"),  # Large order that might cause slippage
            order_type=OrderType.MARKET
        )
        
        # Exchange with deep book but higher fees
        engine.add_exchange_liquidity("binance", "BTC/USDT", bid_depth=500.0, fee=0.001)
        # Exchange with shallow book but lower fees  
        engine.add_exchange_liquidity("okx", "BTC/USDT", bid_depth=50.0, fee=0.0005)
        
        result = engine.route_order(large_order)
        # Should route to binance due to better liquidity for large order
        assert result.selected_exchange == "binance"
        assert result.routing_reason == "slippage_optimization"
    
    def test_order_routing_provides_execution_estimates(self):
        """
        RED Phase: Test for execution cost estimation
        Spec Requirement: "Real-time execution cost estimation"
        """
        engine = CryptoTradingEngine()
        order = Order(
            symbol="ETH/USDT",
            side=OrderSide.BUY,
            amount=Decimal("2.0"),
            order_type=OrderType.MARKET
        )
        
        engine.add_exchange_liquidity("binance", "ETH/USDT", bid_depth=100.0, fee=0.001)
        
        result = engine.route_order(order)
        
        assert result.execution_estimate is not None
        assert result.execution_estimate.estimated_cost > 0
        assert result.execution_estimate.estimated_slippage >= 0
        assert result.execution_estimate.estimated_fee > 0
    
    def test_order_routing_supports_split_orders(self):
        """
        RED Phase: Test for order splitting across exchanges  
        Spec Requirement: "Iceberg orders and smart order routing"
        """
        engine = CryptoTradingEngine()
        large_order = Order(
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            amount=Decimal("20.0"),  # Very large order
            order_type=OrderType.MARKET,
            allow_splitting=True
        )
        
        # Multiple exchanges with limited liquidity each
        engine.add_exchange_liquidity("binance", "BTC/USDT", bid_depth=100.0)
        engine.add_exchange_liquidity("okx", "BTC/USDT", bid_depth=80.0)
        engine.add_exchange_liquidity("bybit", "BTC/USDT", bid_depth=60.0)
        
        result = engine.route_order(large_order)
        
        # Should suggest splitting across multiple exchanges
        assert result.split_required == True
        assert len(result.split_orders) > 1
        assert sum(split.amount for split in result.split_orders) == large_order.amount


class TestOrderPlacement:
    """
    TDD Test Suite for Order Placement
    Spec: Epic 2 Phase 1.2 - Order Execution System
    
    RED Phase: Order placement and execution tests
    """
    
    def test_place_market_order_success(self):
        """
        RED Phase: Test market order placement
        Spec Requirement: "Market order execution with real-time fills"
        """
        engine = CryptoTradingEngine()
        order = Order(
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            amount=Decimal("0.1"),
            order_type=OrderType.MARKET
        )
        
        # Mock sufficient balance
        engine.set_balance("USDT", Decimal("5000"))
        engine.add_exchange_connector("binance", Mock())
        
        result = engine.place_order(order)
        
        assert result.success == True
        assert result.order_id is not None
        assert result.status == "pending"
        assert result.exchange == "binance"
    
    def test_place_limit_order_success(self):
        """
        RED Phase: Test limit order placement
        Spec Requirement: "Limit order management with price monitoring"
        """
        engine = CryptoTradingEngine()
        order = Order(
            symbol="ETH/USDT",
            side=OrderSide.BUY,
            amount=Decimal("1.0"),
            order_type=OrderType.LIMIT,
            price=Decimal("3000")
        )
        
        engine.set_balance("USDT", Decimal("3100"))
        engine.add_exchange_connector("okx", Mock())
        
        result = engine.place_order(order)
        
        assert result.success == True
        assert result.order_id is not None
        assert result.status == "placed"
        assert result.limit_price == Decimal("3000")
    
    def test_place_order_insufficient_balance(self):
        """
        RED Phase: Test insufficient balance validation
        Spec Requirement: "Balance validation and risk checks"
        """
        engine = CryptoTradingEngine()
        order = Order(
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            amount=Decimal("10.0"),
            order_type=OrderType.MARKET
        )
        
        # Insufficient balance
        engine.set_balance("USDT", Decimal("100"))
        
        with pytest.raises(InsufficientBalanceError):
            engine.place_order(order)
    
    def test_place_order_updates_balance(self):
        """
        RED Phase: Test balance updates after order placement
        Spec Requirement: "Real-time balance tracking and updates"
        """
        engine = CryptoTradingEngine()
        initial_balance = Decimal("5000")
        
        order = Order(
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            amount=Decimal("0.1"),
            order_type=OrderType.MARKET
        )
        
        engine.set_balance("USDT", initial_balance)
        engine.add_exchange_connector("binance", Mock())
        
        result = engine.place_order(order)
        
        # Balance should be reserved for pending order
        current_balance = engine.get_available_balance("USDT")
        assert current_balance < initial_balance
        assert result.reserved_amount > 0


class TestOrderStatusTracking:
    """
    TDD Test Suite for Order Status Tracking
    Spec: Epic 2 Phase 1.3 - Order Lifecycle Management
    
    RED Phase: Order status and lifecycle tests
    """
    
    def test_track_order_status_lifecycle(self):
        """
        RED Phase: Test complete order lifecycle tracking
        Spec Requirement: "Real-time order status tracking"
        """
        engine = CryptoTradingEngine()
        order_id = "test-order-123"
        
        # Order starts as pending
        status = engine.get_order_status(order_id)
        assert status.current_status == "pending"
        assert status.filled_amount == Decimal("0")
        
        # Simulate partial fill
        engine.update_order_status(order_id, "partially_filled", filled_amount=Decimal("0.5"))
        status = engine.get_order_status(order_id)
        assert status.current_status == "partially_filled"
        assert status.filled_amount == Decimal("0.5")
        
        # Simulate complete fill
        engine.update_order_status(order_id, "filled", filled_amount=Decimal("1.0"))
        status = engine.get_order_status(order_id)
        assert status.current_status == "filled"
        assert status.filled_amount == Decimal("1.0")
    
    def test_cancel_order_success(self):
        """
        RED Phase: Test order cancellation
        Spec Requirement: "Order cancellation and modification"
        """
        engine = CryptoTradingEngine()
        order_id = "test-order-456"
        
        # Place order first
        order = Order(
            symbol="ETH/USDT",
            side=OrderSide.BUY,
            amount=Decimal("2.0"),
            order_type=OrderType.LIMIT,
            price=Decimal("2800")
        )
        
        engine.set_balance("USDT", Decimal("6000"))
        result = engine.place_order(order)
        order_id = result.order_id
        
        # Cancel the order
        cancel_result = engine.cancel_order(order_id)
        
        assert cancel_result.success == True
        assert cancel_result.status == "cancelled"
        
        # Check that balance is released
        available_balance = engine.get_available_balance("USDT")
        assert available_balance == Decimal("6000")  # Full balance restored
    
    def test_modify_order_price(self):
        """
        RED Phase: Test order modification
        Spec Requirement: "Order modification (price/quantity updates)"
        """
        engine = CryptoTradingEngine()
        
        # Place limit order
        order = Order(
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            amount=Decimal("0.5"),
            order_type=OrderType.LIMIT,
            price=Decimal("45000")
        )
        
        engine.set_balance("USDT", Decimal("25000"))
        result = engine.place_order(order)
        order_id = result.order_id
        
        # Modify order price
        modify_result = engine.modify_order(order_id, new_price=Decimal("44000"))
        
        assert modify_result.success == True
        assert modify_result.new_price == Decimal("44000")
        
        # Verify order details updated
        order_details = engine.get_order_details(order_id)
        assert order_details.price == Decimal("44000")


class TestOrderValidation:
    """
    TDD Test Suite for Order Validation
    Spec: Epic 2 Phase 1.4 - Risk Management Integration
    
    RED Phase: Order validation and risk management tests
    """
    
    def test_validate_order_minimum_size(self):
        """
        RED Phase: Test minimum order size validation
        Spec Requirement: "Position limits and validation framework"
        """
        engine = CryptoTradingEngine()
        
        # Order below minimum size
        small_order = Order(
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            amount=Decimal("0.00001"),  # Very small amount
            order_type=OrderType.MARKET
        )
        
        validation_result = engine.validate_order(small_order)
        assert validation_result.is_valid == False
        assert "minimum_size" in validation_result.errors
    
    def test_validate_order_maximum_position_size(self):
        """
        RED Phase: Test maximum position size limits
        Spec Requirement: "Position risk limits and validation"
        """
        engine = CryptoTradingEngine()
        
        # Set position limits
        engine.set_position_limit("BTC/USDT", max_position=Decimal("5.0"))
        
        # Current position
        engine.set_current_position("BTC/USDT", Decimal("4.5"))
        
        # Order that would exceed limit
        large_order = Order(
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            amount=Decimal("1.0"),  # Would make total position 5.5
            order_type=OrderType.MARKET
        )
        
        validation_result = engine.validate_order(large_order)
        assert validation_result.is_valid == False
        assert "position_limit_exceeded" in validation_result.errors
    
    def test_validate_order_symbol_permissions(self):
        """
        RED Phase: Test symbol trading permissions
        Spec Requirement: "Trading permissions and compliance"
        """
        engine = CryptoTradingEngine()
        
        # Restricted symbol
        restricted_order = Order(
            symbol="RESTRICTED/USDT",
            side=OrderSide.BUY,
            amount=Decimal("100"),
            order_type=OrderType.MARKET
        )
        
        # Set symbol as restricted
        engine.set_symbol_restriction("RESTRICTED/USDT", allowed=False)
        
        validation_result = engine.validate_order(restricted_order)
        assert validation_result.is_valid == False
        assert "symbol_not_allowed" in validation_result.errors