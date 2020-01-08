# -*- coding: utf-8 -*-
import argparse

from zvdata import IntervalLevel
from zvdata.recorder import FixedCycleDataRecorder
from zvdata.utils.time_utils import to_pd_timestamp
from zvt import init_log
from zvt.accounts.ccxt_account import CCXTAccount
from zvt.api.common import get_kdata_schema, generate_kdata_id
from zvt.domain import Coin, CoinTickCommon
from zvt.settings import COIN_EXCHANGES, COIN_PAIRS


class CoinTickRecorder(FixedCycleDataRecorder):
    provider = 'ccxt'

    entity_provider = 'ccxt'
    entity_schema = Coin

    # 只是为了把recorder注册到data_schema
    data_schema = CoinTickCommon

    def __init__(self,
                 exchanges=['binance'],
                 entity_ids=None,
                 codes=None,
                 batch_size=10,
                 force_update=True,
                 sleeping_time=10,
                 default_size=2000,
                 real_time=True,
                 fix_duplicate_way='ignore',
                 start_timestamp=None,
                 end_timestamp=None,
                 kdata_use_begin_time=False,
                 close_hour=None,
                 close_minute=None,
                 level=IntervalLevel.LEVEL_TICK,
                 one_day_trading_minutes=24 * 60) -> None:

        self.data_schema = get_kdata_schema(entity_type='coin', level=level)

        super().__init__('coin', exchanges, entity_ids, codes, batch_size, force_update, sleeping_time,
                         default_size, real_time, fix_duplicate_way, start_timestamp, end_timestamp, close_hour,
                         close_minute, IntervalLevel.LEVEL_TICK, kdata_use_begin_time, one_day_trading_minutes)

    def generate_domain_id(self, entity, original_data):
        return generate_kdata_id(entity_id=entity.id, timestamp=original_data['timestamp'], level=self.level)

    def record(self, entity, start, end, size, timestamps):
        if size < 20:
            size = 20

        ccxt_exchange = CCXTAccount.get_ccxt_exchange(entity.exchange)

        if ccxt_exchange.has['fetchTrades']:
            limit = CCXTAccount.get_tick_limit(entity.exchange)

            limit = min(size, limit)

            kdata_list = []

            trades = ccxt_exchange.fetch_trades(entity.code, limit=limit)

            for trade in trades:
                kdata_json = {
                    'name': entity.name,
                    'provider': 'ccxt',
                    # 'id': trade['id'],
                    'level': 'tick',
                    'order': trade['order'],
                    'timestamp': to_pd_timestamp(trade['timestamp']),
                    'price': trade['price'],
                    'volume': trade['amount'],
                    'direction': trade['side'],
                    'order_type': trade['type'],
                    'turnover': trade['price'] * trade['amount']
                }
                kdata_list.append(kdata_json)

            return kdata_list
        else:
            self.logger.warning("exchange:{} not support fetchOHLCV".format(entity.exchange))


__all__ = ["CoinTickRecorder"]

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--exchanges', help='exchanges', default='binance', nargs='+',
                        choices=[item for item in COIN_EXCHANGES])
    parser.add_argument('--codes', help='codes', default='EOS/USDT', nargs='+',
                        choices=[item for item in COIN_PAIRS])

    args = parser.parse_args()

    init_log('coin_tick_kdata.log')

    CoinTickRecorder(codes=['EOS/USDT']).run()
