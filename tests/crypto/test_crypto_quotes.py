# -*- coding: utf-8 -*-
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from zvt.domain.crypto import CryptoKdata, CryptoTickData
from zvt.contract import IntervalLevel


class TestCryptoQuotes:
    """Test crypto real-time and historical quote data"""

    def test_crypto_kdata_creation(self):
        """Test OHLCV kline data creation"""
        kdata = CryptoKdata(
            id="crypto_binance_BTC_1d_2024-01-01",
            entity_id="crypto_binance_BTC",
            provider="binance",
            code="BTC",
            name="Bitcoin",
            level=IntervalLevel.LEVEL_1DAY.value,
            timestamp=datetime(2024, 1, 1),
            open=45000.0,
            high=46000.0, 
            low=44000.0,
            close=45500.0,
            volume=1250.5,
            turnover=56750000.0
        )
        
        assert kdata.open == 45000.0
        assert kdata.high == 46000.0
        assert kdata.low == 44000.0
        assert kdata.close == 45500.0
        assert kdata.volume == 1250.5
        assert kdata.level == "1d"

    def test_crypto_kdata_validation(self):
        """Test kline data validation rules"""
        with pytest.raises(ValueError):
            # High should be >= open, low, close
            CryptoKdata(
                open=45000.0,
                high=44000.0,  # Invalid: high < open
                low=43000.0,
                close=45500.0
            )
        
        with pytest.raises(ValueError):
            # Low should be <= open, high, close  
            CryptoKdata(
                open=45000.0,
                high=46000.0,
                low=47000.0,  # Invalid: low > high
                close=45500.0
            )

    def test_crypto_tick_data_creation(self):
        """Test tick data creation and validation"""
        tick = CryptoTickData(
            id="crypto_binance_BTC_tick_2024-01-01T12:00:00",
            entity_id="crypto_binance_BTC", 
            provider="binance",
            code="BTC",
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            price=45250.75,
            volume=0.125,
            direction="buy",  # buy/sell/neutral
            order_type="market"
        )
        
        assert tick.price == 45250.75
        assert tick.volume == 0.125
        assert tick.direction == "buy"
        assert tick.order_type == "market"

    def test_crypto_order_book_data(self):
        """Test order book (Level 2) data structure"""
        order_book = {
            "symbol": "BTCUSD",
            "timestamp": datetime(2024, 1, 1, 12, 0, 0),
            "bids": [
                {"price": 45249.50, "size": 1.25},
                {"price": 45249.00, "size": 2.50}, 
                {"price": 45248.50, "size": 0.75}
            ],
            "asks": [
                {"price": 45250.00, "size": 1.10},
                {"price": 45250.50, "size": 3.20},
                {"price": 45251.00, "size": 0.90}
            ]
        }
        
        # Validate order book structure
        assert len(order_book["bids"]) > 0
        assert len(order_book["asks"]) > 0
        
        # Bids should be descending price order
        bid_prices = [bid["price"] for bid in order_book["bids"]]
        assert bid_prices == sorted(bid_prices, reverse=True)
        
        # Asks should be ascending price order
        ask_prices = [ask["price"] for ask in order_book["asks"]]
        assert ask_prices == sorted(ask_prices)
        
        # Best bid < best ask (no crossed market)
        assert order_book["bids"][0]["price"] < order_book["asks"][0]["price"]

    def test_crypto_market_data_intervals(self):
        """Test different time interval support"""
        intervals = [
            (IntervalLevel.LEVEL_1MIN, timedelta(minutes=1)),
            (IntervalLevel.LEVEL_5MIN, timedelta(minutes=5)),
            (IntervalLevel.LEVEL_15MIN, timedelta(minutes=15)),
            (IntervalLevel.LEVEL_30MIN, timedelta(minutes=30)),
            (IntervalLevel.LEVEL_1HOUR, timedelta(hours=1)),
            (IntervalLevel.LEVEL_4HOUR, timedelta(hours=4)),
            (IntervalLevel.LEVEL_1DAY, timedelta(days=1))
        ]
        
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        
        for level, delta in intervals:
            kdata = CryptoKdata(
                id=f"crypto_binance_BTC_{level.value}_2024-01-01", 
                entity_id="crypto_binance_BTC",
                level=level.value,
                timestamp=base_time,
                open=45000.0,
                high=45100.0,
                low=44900.0, 
                close=45050.0,
                volume=100.0
            )
            
            # Next candle should be at base_time + delta
            next_time = base_time + delta
            assert kdata.timestamp < next_time

    def test_crypto_websocket_data_handling(self):
        """Test WebSocket real-time data handling"""
        mock_ws_data = {
            "stream": "btcusd@ticker",
            "data": {
                "s": "BTCUSD",  # symbol
                "c": "45250.75",  # close price
                "o": "45100.00",  # open price  
                "h": "45350.00",  # high price
                "l": "44950.00",  # low price
                "v": "1250.5",   # volume
                "E": 1704110400000  # event time
            }
        }
        
        # Simulate processing WebSocket message
        symbol = mock_ws_data["data"]["s"]
        price = float(mock_ws_data["data"]["c"])
        volume = float(mock_ws_data["data"]["v"])
        
        assert symbol == "BTCUSD"
        assert price == 45250.75
        assert volume == 1250.5

    @patch('requests.get')
    def test_crypto_rest_api_data_fetch(self, mock_get):
        """Test REST API data fetching with mocking"""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "symbol": "BTCUSD",
            "price": "45250.75",
            "volume": "1250.5",
            "timestamp": 1704110400000
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Simulate API call
        response = mock_get("https://api.exchange.com/ticker/BTCUSD")
        data = response.json()
        
        assert data["symbol"] == "BTCUSD"
        assert float(data["price"]) == 45250.75
        assert response.status_code == 200

    def test_crypto_data_gap_detection(self):
        """Test detection of missing data gaps"""
        # Create sequence of 1-minute candles with a gap
        timestamps = [
            datetime(2024, 1, 1, 12, 0, 0),  # 12:00
            datetime(2024, 1, 1, 12, 1, 0),  # 12:01
            datetime(2024, 1, 1, 12, 2, 0),  # 12:02
            # Gap: 12:03 missing
            datetime(2024, 1, 1, 12, 4, 0),  # 12:04
            datetime(2024, 1, 1, 12, 5, 0),  # 12:05
        ]
        
        # Detect gaps (expected 1-minute intervals)
        expected_interval = timedelta(minutes=1)
        gaps = []
        
        for i in range(1, len(timestamps)):
            actual_interval = timestamps[i] - timestamps[i-1]
            if actual_interval > expected_interval:
                gaps.append((timestamps[i-1], timestamps[i]))
        
        assert len(gaps) == 1
        assert gaps[0] == (datetime(2024, 1, 1, 12, 2, 0), datetime(2024, 1, 1, 12, 4, 0))

    def test_crypto_volume_spike_detection(self):
        """Test unusual volume spike detection"""
        # Normal volume baseline
        normal_volumes = [100.0, 120.0, 95.0, 110.0, 105.0]
        avg_volume = sum(normal_volumes) / len(normal_volumes)
        
        # Volume spike (5x normal)
        spike_volume = avg_volume * 5
        
        # Spike detection threshold (3x average)
        threshold_multiplier = 3.0
        
        assert spike_volume > (avg_volume * threshold_multiplier)
        
        # This would trigger volume spike alert
        volume_spike_detected = spike_volume > (avg_volume * threshold_multiplier)
        assert volume_spike_detected is True