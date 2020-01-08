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
            etf_stock_df = get_etf_stocks(code=entity.code, timestamp=date, provider=self.provider)
            if pd_is_not_null(etf_stock_df):
                # etf包含的个股和比例
                etf_stock_df.set_index('stock_id', inplace=True)

                # 个股的估值数据
                stock_valuation_df = StockValuation.query_data(entity_ids=etf_stock_df.index.to_list(),
                                                               filters=[StockValuation.timestamp == date],
                                                               index='entity_id')

                if pd_is_not_null(stock_valuation_df):
                    df = pd.concat([stock_valuation_df, etf_stock_df['proportion']], axis=1, sort=False)
                    self.logger.info(f'etf:{entity.id} date:{date} stock count: {len(etf_stock_df)}')

                    df = df.dropna(subset=['proportion'])

                    self.logger.info(f'etf:{entity.id} date:{date} stock value count: {len(df)}')

                    self.logger.info(f'etf:{entity.id}  date:{date} proportion sum:{df["proportion"].sum()}')
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

                    # 加权平均
                    # df = df[['pe', 'pe_ttm', 'pb', 'ps', 'pcf']].multiply(df["proportion"], axis="index")

                    result_df = pd.DataFrame()
                    for col in ['pe', 'pe_ttm', 'pb', 'ps', 'pcf']:
                        # PE=P/E
                        positive_df = df[col][df[col] > 0].multiply(df["proportion"], axis="index").sum()
                        positive_proportion = df[df[col] > 0]['proportion'].sum()

                        negative_df = df[col][df[col] < 0].multiply(df["proportion"], axis="index").sum()
                        negative_proportion = df[df[col] < 0]['proportion'].sum()

                        # FIXME:handle negative latter
                        se = positive_df
                        if pd_is_not_null(result_df):
                            result_df[col] = se
                        else:
                            result_df = pd.DataFrame(data={col: [se]})

                    result_df['id'] = "{}_{}".format(entity.id, date)
                    result_df['entity_id'] = entity.id
                    result_df['timestamp'] = date
                    result_df['code'] = entity.code
                    result_df['name'] = entity.name

                    df_to_db(df=result_df, data_schema=self.data_schema, provider=self.provider,
                             force_update=self.force_update)

        return None


if __name__ == '__main__':
    # 上证50
    JqChinaEtfValuationRecorder(codes=['510050'], start_timestamp='2005-02-23').run()
