# -*- coding: utf-8 -*-
import pandas as pd

from zvdata.api import df_to_db
from zvdata.recorder import TimeSeriesDataRecorder
from zvdata.utils.pd_utils import pd_is_not_null
from zvdata.utils.time_utils import now_pd_timestamp
from zvt.api.common import get_etf_stocks
from zvt.domain import StockValuation, Etf, EtfValuation


class JqChinaEtfValuationRecorder(TimeSeriesDataRecorder):
    entity_provider = 'joinquant'
    entity_schema = Etf

    # 数据来自jq
    provider = 'joinquant'

    data_schema = EtfValuation

    def __init__(self, entity_type='etf', exchanges=['sh', 'sz'], entity_ids=None, codes=None, batch_size=10,
                 force_update=False, sleeping_time=5, default_size=2000, real_time=False, fix_duplicate_way='add',
                 start_timestamp=None, end_timestamp=None, close_hour=0, close_minute=0) -> None:
        super().__init__(entity_type, exchanges, entity_ids, codes, batch_size, force_update, sleeping_time,
                         default_size, real_time, fix_duplicate_way, start_timestamp, end_timestamp, close_hour,
                         close_minute)

    def record(self, entity, start, end, size, timestamps):
        if not end:
            end = now_pd_timestamp()

        date_range = pd.date_range(start=start, end=end, freq='1D').tolist()
        for date in date_range:
            # etf包含的个股和比例
            etf_stock_df = get_etf_stocks(code=entity.code, timestamp=date, provider=self.provider)

            all_pct = etf_stock_df['proportion'].sum()

            if all_pct >= 1.1 or all_pct <= 0.9:
                self.logger.info(f'etf:{entity.id}  date:{date} proportion sum:{all_pct}')

            if pd_is_not_null(etf_stock_df):
                etf_stock_df.set_index('stock_id', inplace=True)

                # 个股的估值数据
                stock_valuation_df = StockValuation.query_data(entity_ids=etf_stock_df.index.to_list(),
                                                               filters=[StockValuation.timestamp == date],
                                                               index='entity_id')

                if pd_is_not_null(stock_valuation_df):
                    # 暂时只支持 简单算术平均估值，理由：模糊的正确比精确的错误有用
                    # A股个股的市值往往相差很大，按市值权重的话，这样的估值很难反映整体
                    self.logger.info(
                        f'etf:{entity.id} date:{date} stock count: {len(etf_stock_df)},valuation count:{len(stock_valuation_df)}')

                    #     # 静态pe
                    #     pe = Column(Float)
                    #     # 动态pe
                    #     pe_ttm = Column(Float)
                    #     # 市净率
                    #     pb = Column(Float)
                    #     # 市销率
                    #     ps = Column(Float)
                    #     # 市现率
                    #     pcf = Column(Float)

                    se = pd.Series({'id': "{}_{}".format(entity.id, date),
                                    'entity_id': entity.id,
                                    'timestamp': date,
                                    'code': entity.code,
                                    'name': entity.name})
                    for col in ['pe', 'pe_ttm', 'pb', 'ps', 'pcf']:
                        # PE=P/E
                        # 这里的算法为：将其价格都设为1，算出总earning,再相除
                        positive_df = stock_valuation_df[col][stock_valuation_df[col] > 0]
                        positive_count = len(positive_df)

                        negative_df = stock_valuation_df[col][stock_valuation_df[col] < 0]
                        negative_count = len(negative_df)

                        result = (positive_count + negative_count) / (
                                positive_count / positive_df.mean() + negative_count / negative_df.mean())

                        se[col] = result
                    df = se.to_frame().T

                    self.logger.info(df)

                    df_to_db(df=df, data_schema=self.data_schema, provider=self.provider,
                             force_update=self.force_update)

        return None


__all__ = ['JqChinaEtfValuationRecorder']

if __name__ == '__main__':
    # 上证50
    JqChinaEtfValuationRecorder(codes=['510050'], start_timestamp='2005-02-23').run()
