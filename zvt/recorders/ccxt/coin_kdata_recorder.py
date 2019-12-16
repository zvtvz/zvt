# -*- coding: utf-8 -*-
import argparse

from zvdata import IntervalLevel
from zvdata.recorder import FixedCycleDataRecorder
from zvdata.utils.time_utils import to_pd_timestamp
from zvdata.utils.time_utils import to_time_str
from zvt import init_log
from zvt.accounts.ccxt_account import CCXTAccount
from zvt.api.common import generate_kdata_id, get_kdata_schema
from zvt.domain import Coin, CoinKdataCommon
from zvt.recorders.ccxt import to_ccxt_trading_level
from zvt.settings import COIN_EXCHANGES, COIN_PAIRS


class CoinKdataRecorder(FixedCycleDataRecorder):
    provider = 'ccxt'

    entity_provider = 'ccxt'
    entity_schema = Coin

    # 只是为了把recorder注册到data_schema
    data_schema = CoinKdataCommon

    def __init__(self,
                 exchanges=['binance'],
                 entity_ids=None,
                 codes=None,
                 batch_size=10,
                 force_update=True,
                 sleeping_time=10,
                 default_size=2000,
                 real_time=False,
                 fix_duplicate_way='ignore',
                 start_timestamp=None,
                 end_timestamp=None,
                 level=IntervalLevel.LEVEL_1DAY,
                 kdata_use_begin_time=True,
                 close_hour=None,
                 close_minute=None,
                 one_day_trading_minutes=24 * 60) -> None:
        self.data_schema = get_kdata_schema(entity_type='coin', level=level)
        self.ccxt_trading_level = to_ccxt_trading_level(level)

        super().__init__('coin', exchanges, entity_ids, codes, batch_size, force_update, sleeping_time,
                         default_size, real_time, fix_duplicate_way, start_timestamp, close_hour, close_minute,
                         end_timestamp, level, kdata_use_begin_time, one_day_trading_minutes)

    def generate_domain_id(self, entity, original_data):
        return generate_kdata_id(entity_id=entity.id, timestamp=original_data['timestamp'], level=self.level)

    def record(self, entity, start, end, size, timestamps):
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

            for kdata in kdatas:
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

    init_log(
        'coin_{}_{}_{}_kdata.log'.format('-'.join(exchanges), '-'.join(codes).replace('/', ''), args.level))

    CoinKdataRecorder(exchanges=exchanges, codes=codes, level=level, real_time=True).run()
