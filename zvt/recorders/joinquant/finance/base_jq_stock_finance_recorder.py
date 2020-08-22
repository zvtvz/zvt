# -*- coding: utf-8 -*-
import pandas as pd
from jqdatasdk import auth, query, indicator, get_fundamentals, logout, finance

from zvt import zvt_env
from zvt.api.quote import to_jq_report_period, get_recent_report_period
from zvt.contract import IntervalLevel
from zvt.contract.api import get_data, df_to_db
from zvt.contract.recorder import TimestampsDataRecorder
from zvt.domain import FinanceFactor

from zvt.recorders.joinquant.common import company_type_flag, get_fc, \
    call_joinquant_api, get_from_path_fields,JoinquantTimestampsDataRecorder
from zvt.recorders.joinquant.common import to_jq_entity_id
from zvt.utils.pd_utils import index_df
from zvt.utils.pd_utils import pd_is_not_null
from zvt.utils.time_utils import to_time_str, to_pd_timestamp, TIME_FORMAT_DAY
from zvt.domain import StockDetail

class BaseJqStockFinanceRecorder(JoinquantTimestampsDataRecorder):
    finance_report_type = None
    data_type = 1

    timestamps_fetching_url = 'https://emh5.eastmoney.com/api/CaiWuFenXi/GetCompanyReportDateList'
    timestamp_list_path_fields = ['CompanyReportDateList']
    timestamp_path_fields = ['ReportDate']


    entity_provider = 'joinquant'
    entity_schema = StockDetail

    provider = 'joinquant'

    def __init__(self, entity_type='stock', exchanges=['sh', 'sz'], entity_ids=None, codes=None, batch_size=10,
                 force_update=False, sleeping_time=5, default_size=2000, real_time=False,
                 fix_duplicate_way='add', start_timestamp=None, end_timestamp=None, close_hour=0,
                 close_minute=0) -> None:
        super().__init__(entity_type, exchanges, entity_ids, codes, batch_size, force_update, sleeping_time,
                         default_size, real_time, fix_duplicate_way, start_timestamp, end_timestamp, close_hour,
                         close_minute)
        try:
            auth(zvt_env['jq_username'], zvt_env['jq_password'])
            self.fetch_jq_timestamp = True
        except Exception as e:
            self.fetch_jq_timestamp = False
            self.logger.warning(
                f'joinquant account not ok,the timestamp(publish date) for finance would be not correct', e)

    def init_timestamps(self, entity):
        param = {
            "color": "w",
            "fc": get_fc(entity),
            "DataType": self.data_type
        }

        if self.finance_report_type == 'INCOME_STATEMENT' or self.finance_report_type == 'CASHFLOW_STATEMENT':
            param['ReportType'] = 1

        timestamp_json_list = call_joinquant_api(url=self.timestamps_fetching_url,
                                                 path_fields=self.timestamp_list_path_fields,
                                                 param=param)

        if self.timestamp_path_fields:
            timestamps = [get_from_path_fields(data, self.timestamp_path_fields) for data in timestamp_json_list]

        return [to_pd_timestamp(t) for t in timestamps]

    def generate_request_param(self, security_item, start, end, size, timestamps):
        if len(timestamps) <= 10:
            param = {
                "color": "w",
                "fc": get_fc(security_item),
                "corpType": company_type_flag(security_item),
                # 0 means get all types
                "reportDateType": 0,
                "endDate": '',
                "latestCount": size
            }
        else:
            param = {
                "color": "w",
                "fc": get_fc(security_item),
                "corpType": company_type_flag(security_item),
                # 0 means get all types
                "reportDateType": 0,
                "endDate": to_time_str(timestamps[10]),
                "latestCount": 10
            }

        # if self.finance_report_type == 'LiRunBiaoList' or self.finance_report_type == 'XianJinLiuLiangBiaoList':
        if self.finance_report_type == 'INCOME_STATEMENT' or self.finance_report_type == 'CASHFLOW_STATEMENT':
            param['reportType'] = 1

        return param

    def generate_path_fields(self, security_item):
        comp_type = company_type_flag(security_item)

        if comp_type in {"1", "2", "3"}:
            return 'finance.FINANCE_{}'.format(self.finance_report_type)
        elif comp_type == "4":
            return 'finance.STK_{}'.format(self.finance_report_type)

    def record(self, entity, start, end, size, timestamps):
        # different with the default timestamps handling
        param = self.generate_request_param(entity, start, end, size, timestamps)
        query_path = eval(self.generate_path_fields(entity))
        # company_type_flag(entity)
        q = query(query_path,
                  ).filter(query_path.code == to_jq_entity_id(entity),
                           query_path.end_date >= param['endDate'],
                           query_path.report_type == 0).limit(param['latestCount'])
        df = finance.run_query(q)
        # 财报时间  公告时间
        df.set_index(['report_date','pub_date'], drop=True, inplace=True)
        map_data = {value[0]: key for key, value in self.get_data_map().items()}
        df.drop([i for i in df.columns if i not in map_data.keys()], axis=1, inplace=True)
        df.rename(columns=map_data, inplace=True)
        df.reset_index(drop=False, inplace=True)

        df['report_date'] = pd.to_datetime(df['report_date'])
        df['report_period'] = df['report_date'].apply(lambda x: get_recent_report_period(x))
        df['timestamp'] = df['report_date']
        df['pub_date'] = pd.to_datetime(df['pub_date'])

        df['entity_id'] = entity.id
        df['provider'] = 'joinquant'
        df['code'] = entity.code

        def generate_finance_id(se):
            return "{}_{}".format(se['entity_id'], to_time_str(se['timestamp'], fmt=TIME_FORMAT_DAY))

        df['id'] = df[['entity_id', 'timestamp']].apply(generate_finance_id, axis=1)
        df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)
        return None

    def get_original_time_field(self):
        return 'ReportDate'


    def fill_timestamp_with_jq(self, security_item, the_data):
        # get report published date from jq
        try:
            q = query(
                indicator.pubDate
            ).filter(
                indicator.code == to_jq_entity_id(security_item),
            )

            df = get_fundamentals(q, statDate=to_jq_report_period(the_data.report_date))
            if not df.empty and pd.isna(df).empty:
                the_data.timestamp = to_pd_timestamp(df['pubDate'][0])
                self.session.commit()

        except Exception as e:
            self.logger.error(e)

    def on_finish_entity(self, entity):
        super().on_finish_entity(entity)

        if not self.fetch_jq_timestamp:
            return

        # fill the timestamp for report published date
        the_data_list = get_data(data_schema=self.data_schema,
                                 provider=self.provider,
                                 entity_id=entity.id,
                                 order=self.data_schema.timestamp.asc(),
                                 return_type='domain',
                                 session=self.session,
                                 filters=[self.data_schema.timestamp == self.data_schema.report_date,
                                          self.data_schema.timestamp >= to_pd_timestamp('2005-01-01')])
        if the_data_list:
            if self.data_schema == FinanceFactor:
                for the_data in the_data_list:
                    self.fill_timestamp_with_jq(entity, the_data)
            else:
                df = FinanceFactor.query_data(entity_id=entity.id,
                                              columns=[FinanceFactor.timestamp, FinanceFactor.report_date,
                                                       FinanceFactor.id],
                                              filters=[FinanceFactor.timestamp != FinanceFactor.report_date,
                                                       FinanceFactor.timestamp >= to_pd_timestamp('2005-01-01'),
                                                       FinanceFactor.report_date >= the_data_list[0].report_date,
                                                       FinanceFactor.report_date <= the_data_list[-1].report_date, ])

                if pd_is_not_null(df):
                    index_df(df, index='report_date', time_field='report_date')

                for the_data in the_data_list:
                    if (df is not None) and (not df.empty) and the_data.report_date in df.index:
                        the_data.timestamp = df.at[the_data.report_date, 'timestamp']
                        self.logger.info(
                            'db fill {} {} timestamp:{} for report_date:{}'.format(self.data_schema, entity.id,
                                                                                   the_data.timestamp,
                                                                                   the_data.report_date))
                        self.session.commit()
                    else:
                        # self.logger.info(
                        #     'waiting jq fill {} {} timestamp:{} for report_date:{}'.format(self.data_schema,
                        #                                                                    security_item.id,
                        #                                                                    the_data.timestamp,
                        #                                                                    the_data.report_date))

                        self.fill_timestamp_with_jq(entity, the_data)

    def on_finish(self):
        super().on_finish()
        logout()
