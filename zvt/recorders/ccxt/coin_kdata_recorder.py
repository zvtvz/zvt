# -*- coding: utf-8 -*-
import argparse

from zvdata.recorder import FixedCycleDataRecorder
from zvdata.structs import IntervalLevel
from zvdata.utils.time_utils import to_pd_timestamp
from zvt.accounts.ccxt_account import CCXTAccount
from zvt.api.common import generate_kdata_id, to_ccxt_trading_level, get_kdata_schema
from zvt.domain import Coin
from zvt.settings import COIN_EXCHANGES, COIN_PAIRS
from zvt.utils.time_utils import to_time_str
from zvt.utils.utils import init_process_log


class CoinKdataRecorder(FixedCycleDataRecorder):
    provider = 'ccxt'

    entity_provider = 'ccxt'
    entity_schema = Coin

    def __init__(self, exchanges=['binance'], entity_ids=None, codes=None, batch_size=10,
                 force_update=False, sleeping_time=10, default_size=2000, one_shot=False, fix_duplicate_way='add',
                 start_timestamp=None, end_timestamp=None, contain_unfinished_data=False,
                 level=IntervalLevel.LEVEL_1DAY, kdata_use_begin_time=True, close_hour=0, close_minute=0,
                 one_day_trading_minutes=24 * 60) -> None:
        self.data_schema = get_kdata_schema(entity_type='coin', level=level)
        self.ccxt_trading_level = to_ccxt_trading_level(level)

        super().__init__('coin', exchanges, entity_ids, codes, batch_size, force_update, sleeping_time,
                         default_size, one_shot, fix_duplicate_way, start_timestamp, end_timestamp,
                         contain_unfinished_data, level, kdata_use_begin_time, close_hour, close_minute,
                         one_day_trading_minutes)

    def get_data_map(self):
        return {}

    def generate_domain_id(self, entity, original_data):
        return generate_kdata_id(entity_id=entity.id, timestamp=original_data['timestamp'], level=self.level)

    def record(self, entity, start, end, size, timestamps):
        if self.start_timestamp:
            start = max(self.start_timestamp, to_pd_timestamp(start))

        start_timestamp = to_time_str(start)

        ccxt_exchange = CCXTAccount.get_ccxt_exchange(entity.exchange)

        if ccxt_exchange.has['fetchOHLCV']:
            limit = CCXTAccount.get_kdata_limit(entity.exchange)

            limit = min(size, limit)

            kdata_list = []

            if CCXTAccount.exchange_conf[entity.exchange]['support_since']:
                kdatas = ccxt_exchange.fetch_ohlcv(entity.code,
                                                   timeframe=self.ccxt_trading_level,
                                                   since=start_timestamp)
            else:
                kdatas = ccxt_exchange.fetch_ohlcv(entity.code,
                                                   timeframe=self.ccxt_trading_level,
                                                   limit=limit)

            # always ignore the latest one,because it's not finished
            for kdata in kdatas[0:-1]:
                current_timestamp = kdata[0]
                if self.level == IntervalLevel.LEVEL_1DAY:
                    current_timestamp = to_time_str(current_timestamp)

                kdata_json = {
                    'timestamp': to_pd_timestamp(current_timestamp),
                    'open': kdata[1],
                    'high': kdata[2],
                    'low': kdata[3],
                    'close': kdata[4],
                    'volume': kdata[5],
                    'name': entity.name,
                    'provider': 'ccxt',
                    'level': self.level.value
                }
                kdata_list.append(kdata_json)

            return kdata_list
        else:
            self.logger.warning("exchange:{} not support fetchOHLCV".format(entity.exchange))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--level', help='trading level', default='1m', choices=[item.value for item in IntervalLevel])
    parser.add_argument('--exchanges', help='exchanges', default='binance', nargs='+',
                        choices=[item for item in COIN_EXCHANGES])
    parser.add_argument('--codes', help='codes', default='EOS/USDT', nargs='+',
                        choices=[item for item in COIN_PAIRS])

    args = parser.parse_args()

    level = IntervalLevel(args.level)

    exchanges = args.exchanges
    if type(exchanges) != list:
        exchanges = [exchanges]

    codes = args.codes
    if type(codes) != list:
        codes = [codes]

    init_process_log(
        'coin_{}_{}_{}_kdata.log'.format('-'.join(exchanges), '-'.join(codes).replace('/', ''), args.level))

    CoinKdataRecorder(exchanges=exchanges, codes=codes, level=level).run()
