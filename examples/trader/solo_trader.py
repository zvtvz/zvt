# -*- coding: utf-8 -*-

from zvt.domain import ManagerTrading
from zvt.trader.trader import StockTrader
from zvt.utils.pd_utils import pd_is_not_null


class MySoloTrader(StockTrader):
    def on_time(self, timestamp):
        # 增持5000股以上
        long_df = ManagerTrading.query_data(start_timestamp=timestamp, end_timestamp=timestamp,
                                            filters=[ManagerTrading.volume > 5000], columns=[ManagerTrading.entity_id],
                                            order=ManagerTrading.volume.desc(), limit=10)
        # 减持5000股以上
        short_df = ManagerTrading.query_data(start_timestamp=timestamp, end_timestamp=timestamp,
                                             filters=[ManagerTrading.volume < -5000],
                                             columns=[ManagerTrading.entity_id],
                                             order=ManagerTrading.volume.asc(), limit=10)
        if pd_is_not_null(long_df) or pd_is_not_null(short_df):
            try:
                self.trade_the_targets(due_timestamp=timestamp, happen_timestamp=timestamp,
                                       long_selected=set(long_df['entity_id'].to_list()),
                                       short_selected=set(short_df['entity_id'].to_list()))
            except Exception as e:
                self.logger.error(e)


if __name__ == '__main__':
    trader = MySoloTrader(start_timestamp='2015-01-01', end_timestamp='2016-01-01')
    trader.run()
