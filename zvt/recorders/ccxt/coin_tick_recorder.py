# -*- coding: utf-8 -*-
import argparse
import logging

from zvdata.recorder import FixedCycleDataRecorder
from zvdata.structs import IntervalLevel
from zvdata.utils.time_utils import to_pd_timestamp
from zvt.accounts.ccxt_account import CCXTAccount
from zvt.api.common import get_kdata_schema, generate_kdata_id
from zvt.domain import Coin
from zvt.settings import COIN_EXCHANGES, COIN_PAIRS
from zvt.utils.utils import init_process_log

logger = logging.getLogger(__name__)


class CoinKdataRecorder(FixedCycleDataRecorder):
    provider = 'ccxt'

    entity_provider = 'ccxt'
    entity_schema = Coin

    def __init__(self, exchanges=['binance'], entity_ids=None, codes=None, batch_size=10,
                 force_update=False, sleeping_time=10, default_size=2000, one_shot=False, fix_duplicate_way='add',
                 start_timestamp=None, end_timestamp=None, contain_unfinished_data=False,
                 kdata_use_begin_time=True, close_hour=0, close_minute=0,
                 one_day_trading_minutes=24 * 60) -> None:

        self.data_schema = get_kdata_schema(entity_type='coin', level=IntervalLevel.LEVEL_TICK)

        super().__init__('coin', exchanges, entity_ids, codes, batch_size, force_update, sleeping_time,
                         default_size, one_shot, fix_duplicate_way, start_timestamp, end_timestamp,
                         contain_unfinished_data, IntervalLevel.LEVEL_TICK, kdata_use_begin_time, close_hour,
                         close_minute,
                         one_day_trading_minutes)

    def get_data_map(self):
        return {}

    def generate_domain_id(self, entity, original_data):
        return generate_kdata_id(entity_id=entity.id, timestamp=original_data['timestamp'], level=self.level)

    def record(self, entity, start, end, size, timestamps):
        if size < 20:
            size = 20

        entity = entity

        ccxt_exchange = CCXTAccount.get_ccxt_exchange(entity.exchange)

        if ccxt_exchange.has['fetchTrades']:
            limit = CCXTAccount.get_tick_limit(entity.exchange)

            limit = min(size, limit)

            kdata_list = []

            try:
                trades = ccxt_exchange.fetch_trades(entity.code, limit=limit)

                # always ignore the latest one,because it's not finished
                for trade in trades[0:-1]:
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
                        'orderType': trade['type'],
                        'turnover': trade['price'] * trade['amount']
                    }
                    kdata_list.append(kdata_json)

                return kdata_list
            except Exception as e:
                logger.exception("record_kdata for security:{} failed".format(entity.id))
        else:
            logger.warning("exchange:{} not support fetchOHLCV".format(entity.exchange))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--exchanges', help='exchanges', default='binance', nargs='+',
                        choices=[item for item in COIN_EXCHANGES])
    parser.add_argument('--codes', help='codes', default='EOS/USDT', nargs='+',
                        choices=[item for item in COIN_PAIRS])

    args = parser.parse_args()

    init_process_log('coin_tick_kdata.log')

    CoinKdataRecorder(codes=['EOS/USDT']).run()
