# -*- coding: utf-8 -*-
import os

DATA_SAMPLE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'datasample'))
DATA_SAMPLE_ZIP_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'datasample.zip'))

# please change the path to your real store path
DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'datasample'))

UI_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ui'))

LOG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logs'))

if not DATA_PATH:
    DATA_PATH = os.environ.get('ZVT_DATA_PATH')

if not LOG_PATH:
    LOG_PATH = os.environ.get('LOG_PATH')

JQ_ACCOUNT = ''
if not JQ_ACCOUNT:
    JQ_ACCOUNT = os.environ.get('JQ_ACCOUNT')

JQ_PASSWD = ''
if not JQ_PASSWD:
    JQ_PASSWD = os.environ.get('JQ_PASSWD')

HTTP_PROXY = 'http://127.0.0.1:10080'
if not HTTP_PROXY:
    HTTP_PROXY = os.environ.get('HTTP_PROXY')

HTTPS_PROXY = 'http://127.0.0.1:10080'
if not HTTPS_PROXY:
    HTTPS_PROXY = os.environ.get('HTTPS_PROXY')

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
