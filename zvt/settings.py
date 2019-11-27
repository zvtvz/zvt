# -*- coding: utf-8 -*-
import os
from pathlib import Path

ZVT_TEST_HOME = os.path.abspath(os.path.join(Path.home(), 'zvt-test-home'))
ZVT_TEST_DATA_PATH = os.path.join(ZVT_TEST_HOME, 'data')

DATA_SAMPLE_ZIP_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'samples', 'data.zip'))

# please change the path to your real store path
ZVT_HOME = os.path.abspath(os.path.join(Path.home(), 'zvt-home'))

HTTP_PROXY = 'http://127.0.0.1:1087'
if not HTTP_PROXY:
    HTTP_PROXY = os.environ.get('HTTP_PROXY')

HTTPS_PROXY = 'http://127.0.0.1:1087'
if not HTTPS_PROXY:
    HTTPS_PROXY = os.environ.get('HTTPS_PROXY')

# the action account settings
SMTP_HOST = 'smtpdm.aliyun.com'
SMTP_PORT = '80'

EMAIL_USERNAME = ''

if not EMAIL_USERNAME:
    EMAIL_USERNAME = os.environ.get('EMAIL_USERNAME')

EMAIL_PASSWORD = ''
if not EMAIL_PASSWORD:
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')

WECHAT_APP_ID = ""
if not WECHAT_APP_ID:
    WECHAT_APP_ID = os.environ.get("WEIXIN_APP_ID")

WECHAT_APP_SECRECT = ""
if not WECHAT_APP_SECRECT:
    WECHAT_APP_SECRECT = os.environ.get("WEIXIN_APP_SECRECT")

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
