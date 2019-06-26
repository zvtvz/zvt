import json
import ccxt

from zvt.domain import COIN_EXCHANGES


class CCXTAccount(object):
    def __init__(self, exchanges=COIN_EXCHANGES) -> None:
        self.exchange_conf = {}
        self.exchanges = exchanges

        self.init_exchange_conf()

    def init_exchange_conf(self):
        for exchange in self.exchanges:
            import pkg_resources

            resource_package = 'zvt'
            resource_path = 'accounts/{}.json'.format(exchange)
            config_file = pkg_resources.resource_filename(resource_package, resource_path)

            with open(config_file) as f:
                self.exchange_conf[exchange] = json.load(f)

    def get_tick_limit(self, exchange):
        return self.exchange_conf[exchange]['tick_limit']

    def get_kdata_limit(self, exchange):
        return self.exchange_conf[exchange]['kdata_limit']

    def get_safe_sleeping_time(self, exchange):
        return self.exchange_conf[exchange]['safe_sleeping_time']

    def get_ccxt_exchange(self, exchange_str):
        exchange = eval("ccxt.{}()".format(exchange_str))
        exchange.apiKey = self.exchange_conf[exchange_str]['apiKey']
        exchange.secret = self.exchange_conf[exchange_str]['secret']
        # set to your proxies if need
        exchange.proxies = {'http': 'http://127.0.0.1:10081', 'https': 'http://127.0.0.1:10081'}
        return exchange
