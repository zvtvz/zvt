# -*- coding: utf-8 -*-
from zvt.domain import TradingLevel, SecurityType
from zvt.selectors.zvt_selector import TechnicalSelector
from zvt.trader.trader import Trader


class MultipleLevelTrader(Trader):
    def init_selectors(self, security_list, security_type, exchanges, codes, start_timestamp, end_timestamp):
        self.selectors = []

        ma_1d_selector = TechnicalSelector(security_list=security_list, security_type=security_type,
                                           exchanges=exchanges, codes=codes,
                                           start_timestamp=start_timestamp,
                                           end_timestamp=end_timestamp, level=TradingLevel.LEVEL_15MIN,
                                           provider='ccxt')
        ma_1d_selector.run()

        ma_1h_selector = TechnicalSelector(security_list=security_list, security_type=security_type,
                                           exchanges=exchanges, codes=codes,
                                           start_timestamp=start_timestamp,
                                           end_timestamp=end_timestamp, level=TradingLevel.LEVEL_5MIN,
                                           provider='ccxt')
        ma_1h_selector.run()

        # finance_selector = FundamentalSelector(security_type=security_type, exchanges=exchanges, codes=codes,
        #                                        start_timestamp=start_timestamp, end_timestamp=end_timestamp)
        # finance_selector.run()

        self.selectors.append(ma_1d_selector)
        self.selectors.append(ma_1h_selector)
        # self.selectors.append(finance_selector)

        print(ma_1d_selector.get_df())
        print(ma_1h_selector.get_df())


if __name__ == '__main__':
    MultipleLevelTrader(provider='ccxt',
                        start_timestamp='2019-06-01',
                        end_timestamp='2019-10-10', trading_level=TradingLevel.LEVEL_5MIN,
                        security_type=SecurityType.coin,
                        security_list=['coin_binance_EOS/USDT'],
                        real_time=True,
                        kdata_use_begin_time=True).run()
