# -*- coding: utf-8 -*-
from zvdata import IntervalLevel
from zvt.factors.ma.ma_factor import CrossMaFactor
from zvt.factors.target_selector import TargetSelector

# run the recoder for the data
# python zvt/recorders/ccxt/coin_kdata_recorder.py --level 1m --exchanges binance --codes EOS/USDT
from zvt.trader.trader import CoinTrader


class MyMaCoinTrader(CoinTrader):

    def init_selectors(self, entity_ids, entity_type, exchanges, codes, start_timestamp, end_timestamp):
        myselector = TargetSelector(entity_ids=entity_ids, entity_type=entity_type, exchanges=exchanges,
                                    codes=codes, start_timestamp=start_timestamp, end_timestamp=end_timestamp,
                                    provider='ccxt', level=IntervalLevel.LEVEL_1MIN)

        myselector.add_filter_factor(
            CrossMaFactor(entity_ids=entity_ids, entity_type=entity_type, exchanges=exchanges,
                          codes=codes, start_timestamp=start_timestamp, end_timestamp=end_timestamp, provider='ccxt',
                          level=IntervalLevel.LEVEL_1MIN))

        self.selectors.append(myselector)


if __name__ == '__main__':
    MyMaCoinTrader(entity_ids=['coin_binance_EOS/USDT'],
                   level=IntervalLevel.LEVEL_1MIN,
                   start_timestamp='2019-07-03',
                   end_timestamp='2019-07-10',
                   real_time=True).run()
