# -*- coding: utf-8 -*-
import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from datetime import datetime, timedelta
from zvt.recorders.crypto.binance_recorder import BinanceRecorder
from zvt.recorders.crypto.coinbase_recorder import CoinbaseRecorder


class TestCryptoDataProviders:
    """Test crypto exchange API integrations and data providers"""

    @patch('requests.get')
    def test_binance_api_connection(self, mock_get):
        """Test Binance API connection and response handling"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "symbols": [
                {
                    "symbol": "BTCUSD",
                    "status": "TRADING",
                    "baseAsset": "BTC",
                    "quoteAsset": "USD",
                    "filters": []
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Test API connection
        recorder = BinanceRecorder()
        symbols = recorder.get_trading_symbols()
        
        assert len(symbols) > 0
        assert "BTCUSD" in [s["symbol"] for s in symbols]
        mock_get.assert_called_once()

    @patch('requests.get')
    def test_binance_rate_limiting(self, mock_get):
        """Test Binance API rate limiting handling"""
        # Mock rate limit exceeded response
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {'Retry-After': '60'}
        mock_response.json.return_value = {
            "code": -1003,
            "msg": "Rate limit exceeded"
        }
        mock_get.return_value = mock_response
        
        recorder = BinanceRecorder()
        
        # Should handle rate limit gracefully
        with pytest.raises(Exception) as exc_info:
            recorder.fetch_kline_data("BTCUSD", "1d", limit=100)
        
        assert "rate limit" in str(exc_info.value).lower()

    @patch('requests.get')
    def test_coinbase_api_connection(self, mock_get):
        """Test Coinbase Pro API connection"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": "BTC-USD",
                "base_currency": "BTC", 
                "quote_currency": "USD",
                "status": "online",
                "trading_disabled": False
            }
        ]
        mock_get.return_value = mock_response
        
        recorder = CoinbaseRecorder()
        products = recorder.get_products()
        
        assert len(products) > 0
        assert "BTC-USD" in [p["id"] for p in products]

    def test_exchange_api_error_handling(self):
        """Test API error handling for various scenarios"""
        recorder = BinanceRecorder()
        
        # Test network timeout
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout()
            
            with pytest.raises(requests.exceptions.Timeout):
                recorder.fetch_ticker_data("BTCUSD")
        
        # Test connection error
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError()
            
            with pytest.raises(requests.exceptions.ConnectionError):
                recorder.fetch_ticker_data("BTCUSD")

    @patch('requests.get')
    def test_historical_data_fetching(self, mock_get):
        """Test fetching historical OHLCV data"""
        # Mock historical kline data response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            [
                1704067200000,  # Open time
                "45000.00",     # Open
                "45100.00",     # High
                "44900.00",     # Low 
                "45050.00",     # Close
                "1250.50",      # Volume
                1704153600000,  # Close time
                "56256225.00",  # Quote asset volume
                8563,           # Number of trades
                "625.25",       # Taker buy base volume
                "28128112.50",  # Taker buy quote volume
                "0"             # Ignore
            ]
        ]
        mock_get.return_value = mock_response
        
        recorder = BinanceRecorder()
        klines = recorder.fetch_kline_data("BTCUSD", "1d", limit=1)
        
        assert len(klines) == 1
        kline = klines[0]
        assert float(kline[1]) == 45000.00  # Open
        assert float(kline[4]) == 45050.00  # Close

    def test_websocket_connection_handling(self):
        """Test WebSocket connection management"""
        with patch('websocket.WebSocketApp') as mock_ws:
            mock_ws_instance = Mock()
            mock_ws.return_value = mock_ws_instance
            
            recorder = BinanceRecorder()
            recorder.start_websocket_stream(["btcusd@ticker"])
            
            # Verify WebSocket was created and started
            mock_ws.assert_called_once()
            mock_ws_instance.run_forever.assert_called_once()

    def test_websocket_message_processing(self):
        """Test processing of WebSocket messages"""
        recorder = BinanceRecorder()
        
        # Sample ticker message
        message = """{
            "e": "24hrTicker",
            "E": 123456789,
            "s": "BTCUSD",
            "p": "0.0015",
            "P": "250.00",
            "w": "0.0018",
            "x": "0.0009",
            "c": "45250.75",
            "Q": "10",
            "b": "45249.50",
            "B": "10",
            "a": "45250.25",
            "A": "20",
            "o": "45100.00",
            "h": "45350.00",
            "l": "44950.00",
            "v": "1250.50",
            "q": "56256225.00",
            "O": 123456785,
            "C": 123456789,
            "F": 123456788,
            "L": 123456795,
            "n": 1000
        }"""
        
        # Process message
        data = recorder.process_ticker_message(message)
        
        assert data["symbol"] == "BTCUSD"
        assert float(data["price"]) == 45250.75
        assert float(data["volume"]) == 1250.50

    @patch('time.sleep')
    def test_api_retry_mechanism(self, mock_sleep):
        """Test API retry mechanism with exponential backoff"""
        with patch('requests.get') as mock_get:
            # First two calls fail, third succeeds
            mock_get.side_effect = [
                requests.exceptions.RequestException("Temporary failure"),
                requests.exceptions.RequestException("Temporary failure"), 
                Mock(status_code=200, json=lambda: {"result": "success"})
            ]
            
            recorder = BinanceRecorder()
            result = recorder.fetch_with_retry("https://api.binance.com/test", max_retries=3)
            
            assert result["result"] == "success"
            assert mock_get.call_count == 3
            assert mock_sleep.call_count == 2  # Sleep called between retries

    def test_data_validation_and_cleaning(self):
        """Test data validation and cleaning processes"""
        recorder = BinanceRecorder()
        
        # Test invalid price data
        invalid_kline = [
            1704067200000,  # Open time
            "0.00",         # Invalid: zero open price
            "45100.00",     # High
            "44900.00",     # Low
            "45050.00",     # Close
            "1250.50",      # Volume
        ]
        
        is_valid = recorder.validate_kline_data(invalid_kline)
        assert is_valid is False
        
        # Test valid data
        valid_kline = [
            1704067200000,
            "45000.00",
            "45100.00", 
            "44900.00",
            "45050.00",
            "1250.50",
        ]
        
        is_valid = recorder.validate_kline_data(valid_kline)
        assert is_valid is True

    def test_exchange_status_monitoring(self):
        """Test exchange status and maintenance monitoring"""
        with patch('requests.get') as mock_get:
            # Mock exchange status response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": 0,  # 0: normal, 1: maintenance
                "msg": "normal"
            }
            mock_get.return_value = mock_response
            
            recorder = BinanceRecorder()
            status = recorder.get_exchange_status()
            
            assert status["status"] == 0
            assert status["msg"] == "normal"

    def test_symbol_mapping_and_normalization(self):
        """Test symbol mapping between different exchanges"""
        recorder = BinanceRecorder()
        
        # Test symbol normalization
        binance_symbols = ["BTCUSD", "ETHUSD", "ADAUSD"]
        normalized = [recorder.normalize_symbol(s) for s in binance_symbols]
        
        expected = ["BTC-USD", "ETH-USD", "ADA-USD"]
        assert normalized == expected
        
        # Test reverse mapping
        coinbase_symbols = ["BTC-USD", "ETH-USD", "ADA-USD"] 
        coinbase_recorder = CoinbaseRecorder()
        binance_format = [coinbase_recorder.to_binance_symbol(s) for s in coinbase_symbols]
        
        assert binance_format == ["BTCUSD", "ETHUSD", "ADAUSD"]

    def test_data_persistence_integration(self):
        """Test integration with database persistence layer"""
        with patch('zvt.contract.recorder.TimestampDataRecorder.persist') as mock_persist:
            recorder = BinanceRecorder()
            
            # Sample kline data to persist
            kline_data = {
                "entity_id": "crypto_binance_BTC",
                "timestamp": datetime(2024, 1, 1),
                "open": 45000.00,
                "high": 45100.00,
                "low": 44900.00,
                "close": 45050.00,
                "volume": 1250.50
            }
            
            recorder.persist_kline_data([kline_data])
            
            # Verify persistence was called
            mock_persist.assert_called_once()

    def test_multi_exchange_data_aggregation(self):
        """Test aggregating data from multiple exchanges"""
        binance_price = 45250.75
        coinbase_price = 45252.25
        
        # Calculate weighted average based on volume
        binance_volume = 1000.0
        coinbase_volume = 800.0
        total_volume = binance_volume + coinbase_volume
        
        weighted_price = (
            (binance_price * binance_volume + coinbase_price * coinbase_volume) 
            / total_volume
        )
        
        expected_price = 45251.42
        assert abs(weighted_price - expected_price) < 0.01
        
        # Test price deviation detection
        price_diff = abs(binance_price - coinbase_price)
        max_deviation = 50.0  # $50 max deviation
        
        assert price_diff < max_deviation  # Should not trigger arbitrage alert