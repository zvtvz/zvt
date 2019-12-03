# -*- coding: utf-8 -*-
import json

import ccxt

from zvt import zvt_env
from zvt.settings import COIN_EXCHANGES


class CCXTAccount(object):
    exchanges = COIN_EXCHANGES
    exchange_conf = {}

    @classmethod
    def init(cls):
        for exchange in cls.exchanges:
            import pkg_resources

            resource_package = 'zvt'
            resource_path = 'accounts/{}.json'.format(exchange)
            config_file = pkg_resources.resource_filename(resource_package, resource_path)

            with open(config_file) as f:
                cls.exchange_conf[exchange] = json.load(f)

    @classmethod
    def get_tick_limit(cls, exchange):
        return cls.exchange_conf[exchange]['tick_limit']

    @classmethod
    def get_kdata_limit(cls, exchange):
        return cls.exchange_conf[exchange]['kdata_limit']

    @classmethod
    def get_safe_sleeping_time(cls, exchange):
        return cls.exchange_conf[exchange]['safe_sleeping_time']

    @classmethod
    def get_ccxt_exchange(cls, exchange_str) -> ccxt.Exchange:
        exchange = eval("ccxt.{}()".format(exchange_str))
        exchange.apiKey = cls.exchange_conf[exchange_str]['apiKey']
        exchange.secret = cls.exchange_conf[exchange_str]['secret']
        # set to your proxies if need
        exchange.proxies = {'http': zvt_env['http_proxy'], 'https': zvt_env['https_proxy']}
        return exchange
