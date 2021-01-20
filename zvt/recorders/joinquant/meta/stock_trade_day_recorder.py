# -*- coding: utf-8 -*-
import pandas as pd
from jqdatapy.api import get_trade_days

from zvt.contract.api import df_to_db
from zvt.contract.recorder import TimeSeriesDataRecorder
from zvt.domain import StockTradeDay, Stock
from zvt.utils.time_utils import to_time_str


class StockTradeDayRecorder(TimeSeriesDataRecorder):
    entity_provider = 'joinquant'
    entity_schema = Stock

    provider = 'joinquant'
    data_schema = StockTradeDay

    def __init__(self, entity_type='stock', exchanges=['sh', 'sz'], entity_ids=None, codes=None, day_data=False, batch_size=10,
                 force_update=False, sleeping_time=5, default_size=2000, real_time=False, fix_duplicate_way='add',
                 start_timestamp=None, end_timestamp=None, close_hour=0, close_minute=0) -> None:
        super().__init__(entity_type, exchanges, entity_ids, ['000001'], batch_size, force_update, sleeping_time,
                         default_size, real_time, fix_duplicate_way, start_timestamp, end_timestamp, close_hour,
                         close_minute)

    def record(self, entity, start, end, size, timestamps):
        df = pd.DataFrame()
        dates = get_trade_days(date=to_time_str(start))
        dates = dates.iloc[:, 0]
        self.logger.info(f'add dates:{dates}')
        df['timestamp'] = pd.to_datetime(dates)
        df['id'] = [to_time_str(date) for date in dates]
        df['entity_id'] = 'stock_sz_000001'

        df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)


if __name__ == '__main__':
    r = StockTradeDayRecorder()
    r.run()
# the __all__ is generated
__all__ = ['StockTradeDayRecorder']