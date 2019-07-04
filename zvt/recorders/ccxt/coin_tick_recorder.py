# -*- coding: utf-8 -*-
import argparse
import logging

from zvt.accounts.ccxt_account import CCXTAccount
from zvt.api.common import get_kdata_schema, generate_kdata_id
from zvt.domain import SecurityType, TradingLevel, Provider, to_pd_timestamp, Coin, COIN_EXCHANGES, COIN_PAIRS
from zvt.recorders.recorder import FixedCycleDataRecorder, TimeSeriesFetchingStyle, ApiWrapper
from zvt.utils.time_utils import to_time_str
from zvt.utils.utils import init_process_log

logger = logging.getLogger(__name__)


class MyApiWrapper(ApiWrapper):
    def request(self, url=None, method='get', param=None, path_fields=None):
        security_item = param['security_item']
        size = param['size']

        ccxt_exchange = CCXTAccount.get_ccxt_exchange(security_item.exchange)

        if ccxt_exchange.has['fetchTrades']:
            limit = CCXTAccount.get_tick_limit(security_item.exchange)

            limit = min(size, limit)

            kdata_list = []

            try:
                trades = ccxt_exchange.fetch_trades(security_item.code, limit=limit)

                # always ignore the latest one,because it's not finished
                for trade in trades[0:-1]:
                    kdata_json = {
                        'securityId': security_item.id,
                        'name': security_item.name,
                        'provider': 'ccxt',
                        # 'id': trade['id'],
                        'level': 'tick',
                        'order': trade['order'],
                        'timestamp': to_pd_timestamp(trade['timestamp']),
                        'price': trade['price'],
                        'volume': trade['amount'],
                        'direction': trade['side'],
                        'orderType': trade['type'],
                        'turnover': trade['price'] * trade['amount']
                    }
                    kdata_list.append(kdata_json)

                return kdata_list
            except Exception as e:
                logger.exception("record_kdata for security:{} failed".format(security_item.id))
        else:
            logger.warning("exchange:{} not support fetchOHLCV".format(security_item.exchange))


class CoinKdataRecorder(FixedCycleDataRecorder):
    provider = Provider.CCXT

    meta_provider = Provider.CCXT
    meta_schema = Coin

    api_wrapper = MyApiWrapper()

    def __init__(self, security_type=SecurityType.coin, exchanges=['binance'], codes=None, batch_size=10,
                 force_update=False, sleeping_time=5, fetching_style=TimeSeriesFetchingStyle.end_size,
                 default_size=2000, contain_unfinished_data=False,
                 one_shot=False, start_timestamp=None) -> None:
        self.data_schema = get_kdata_schema(security_type=security_type, level=TradingLevel.LEVEL_TICK)

        self.start_timestamp = to_pd_timestamp(start_timestamp)

        super().__init__(security_type, exchanges, codes, batch_size, force_update, sleeping_time, fetching_style,
                         default_size, contain_unfinished_data, TradingLevel.LEVEL_TICK, one_shot,
                         kdata_use_begin_time=True)

    def get_data_map(self):
        return {}

    def generate_domain_id(self, security_item, original_data):
        return generate_kdata_id(security_id=security_item.id, timestamp=original_data['timestamp'], level=self.level)

    def generate_request_param(self, security_item, start, end, size, timestamp):
        if self.start_timestamp:
            start = max(self.start_timestamp, to_pd_timestamp(start))
        if size < 20:
            size = 20

        return {
            'security_item': security_item,
            'start_timestamp': to_time_str(start),
            'size': size
        }


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--exchanges', help='exchanges', default='binance', nargs='+',
                        choices=[item for item in COIN_EXCHANGES])
    parser.add_argument('--codes', help='codes', default='EOS/USDT', nargs='+',
                        choices=[item for item in COIN_PAIRS])

    args = parser.parse_args()

    init_process_log('coin_tick_kdata.log')

    CoinKdataRecorder(codes=['EOS/USDT']).run()
