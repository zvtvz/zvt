# -*- coding: utf-8 -*-
from zvt.domain.common import TradingLevel

from zvt.factors.technical_factor import CrossMaFactor
from zvt.selectors.selector import TargetSelector
from zvt.trader.impls import CoinTrader


# run the recoder for the data
# python zvt/recorders/ccxt/coin_kdata_recorder.py --level 1m --exchanges binance --codes EOS/USDT
class MyMaCoinTrader(CoinTrader):
    def init_selectors(self, security_list, security_type, exchanges, codes, start_timestamp, end_timestamp):
        myselector = TargetSelector(security_list=security_list, security_type=security_type, exchanges=exchanges,
                                    codes=codes, start_timestamp=start_timestamp, end_timestamp=end_timestamp,
                                    provider='ccxt', level=TradingLevel.LEVEL_1MIN)

        myselector.add_filter_factor(
            CrossMaFactor(security_list=security_list, security_type=security_type, exchanges=exchanges,
                          codes=codes, start_timestamp=start_timestamp, end_timestamp=end_timestamp, provider='ccxt',
                          level=TradingLevel.LEVEL_1MIN))

        self.selectors.append(myselector)


if __name__ == '__main__':
    MyMaCoinTrader(security_list=['coin_binance_EOS/USDT'],
                   level=TradingLevel.LEVEL_1MIN,
                   start_timestamp='2019-07-03',
                   end_timestamp='2019-07-10',
                   real_time=True).run()
