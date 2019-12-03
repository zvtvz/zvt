# -*- coding: utf-8 -*-
import os
from pathlib import Path

# zvt home dir
ZVT_HOME = os.environ.get('ZVT_HOME')
if not ZVT_HOME:
    ZVT_HOME = os.path.abspath(os.path.join(Path.home(), 'zvt-home'))

# data for testing
ZVT_TEST_HOME = os.path.abspath(os.path.join(Path.home(), 'zvt-test-home'))
ZVT_TEST_ZIP_DATA_PATH = os.path.join(ZVT_TEST_HOME, 'data.zip')
ZVT_TEST_DATA_PATH = os.path.join(ZVT_TEST_HOME, 'data')

DATA_SAMPLE_ZIP_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'samples', 'data.zip'))

# ****** setting for crypto currency ****** #
COIN_EXCHANGES = ["binance", "huobipro", "okex"]

# COIN_BASE = ["BTC", "ETH", "XRP", "BCH", "EOS", "LTC", "XLM", "ADA", "IOTA", "TRX", "NEO", "DASH", "XMR",
#                        "BNB", "ETC", "QTUM", "ONT"]

COIN_BASE = ["BTC", "ETH", "EOS"]

COIN_PAIRS = [("{}/{}".format(item, "USDT")) for item in COIN_BASE] + \
             [("{}/{}".format(item, "USD")) for item in COIN_BASE]

# ****** setting for stocks ****** #
# 覆盖维度 银行/保险/企业/券商 创业板 中小板 主板
SAMPLE_STOCK_CODES = ['000001', '000783', '000778', '603220', '601318', '000338', '002572', '300027']
