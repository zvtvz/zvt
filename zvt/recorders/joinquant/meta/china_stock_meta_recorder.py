# -*- coding: utf-8 -*-
import pandas as pd
from EmQuantAPI import *
from jqdatasdk import auth, get_all_securities, logout, query, finance, normalize_code, get_query_count, get_concept, \
    get_index_stocks

from zvt.contract.api import df_to_db, get_entity_exchange, get_entity_code, get_entities
from zvt.contract.recorder import Recorder, TimeSeriesDataRecorder
from zvt.recorders.tonglian.common import to_jq_entity_id
from zvt.utils.pd_utils import pd_is_not_null
from zvt import zvt_env
from zvt.api.quote import china_stock_code_to_id, portfolio_relate_stock
from zvt.domain import EtfStock, Stock, Etf, StockDetail, Fund, FundDetail, FundStock, Index, IndexStockNew, \
    StockDetailNew
from zvt.recorders.joinquant.common import to_entity_id, jq_to_report_period
from zvt.utils.time_utils import to_pd_timestamp, to_time_str, now_pd_timestamp
from zvt.utils.utils import to_float, pct_to_float


class BaseJqChinaMetaRecorder(Recorder):
    provider = 'joinquant'

    def __init__(self, batch_size=10, force_update=True, sleeping_time=10) -> None:
        super().__init__(batch_size, force_update, sleeping_time)

        auth(zvt_env['jq_username'], zvt_env['jq_password'])
        print(f"剩余{get_query_count()['spare'] / 10000}万")

    def to_zvt_entity(self, df, entity_type, category=None):
        df.index.name = 'entity_id'
        df = df.reset_index()
        # 上市日期
        df.rename(columns={'start_date': 'timestamp'}, inplace=True)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['list_date'] = df['timestamp']
        df['end_date'] = pd.to_datetime(df['end_date'])

        df['entity_id'] = df['entity_id'].apply(lambda x: to_entity_id(entity_type=entity_type, jq_code=x))
        df['id'] = df['entity_id']
        df['entity_type'] = entity_type
        df['exchange'] = df['entity_id'].apply(lambda x: get_entity_exchange(x))
        df['code'] = df['entity_id'].apply(lambda x: get_entity_code(x))
        df['name'] = df['display_name']
        if entity_type == 'etf':
            # ETF  查询标的指数
            df['choice_code'] = df.apply(lambda x: x.code + '.' + x.exchange.upper(), axis=1)
            loginResult = c.start("ForceLogin=1", '')
            df['underlying_index_code'] = df.apply(lambda x: c.css(x.choice_code, "BMINDEXCODE", "Rank=1").Data, axis=1)
            df['index_codes'] = df['underlying_index_code'].apply(lambda x: [i for i in x.values()][0][0])
            df['index_exchange'] = df['index_codes'].apply(lambda x: str(x).split('.'))
            df['index_code'] = df['index_codes'].apply(lambda x: str(x).split('.')[0])
            df['index_exchange'] = df['index_exchange'].apply(
                lambda x: x[1] if isinstance(x, list) and len(x) > 1 else None)
            df['underlying_index_code'] = df.apply(
                lambda x: 'index_' + x.index_exchange.lower() + '_' + x.index_code if x.index_exchange else None,
                axis=1)
            loginResult = c.stop()
        if category:
            df['category'] = category

        return df


class JqChinaStockRecorder(BaseJqChinaMetaRecorder):
    data_schema = Stock

    def run(self):
        # 抓取股票列表
        df_stock = self.to_zvt_entity(get_all_securities(['stock']), entity_type='stock')
        df_to_db(df_stock, data_schema=Stock, provider=self.provider, force_update=self.force_update)
        # persist StockDetail too
        df_to_db(df=df_stock, data_schema=StockDetail, provider=self.provider, force_update=self.force_update)

        self.logger.info(df_stock)
        self.logger.info("persist stock list success")

        logout()


class JqChinaStockDetailNewRecorder(Recorder):
    provider = 'joinquant'
    data_schema = StockDetail

    def __init__(self, batch_size=10, force_update=False, sleeping_time=5, codes=None) -> None:
        super().__init__(batch_size, force_update, sleeping_time)

        # get list at first
        # JqChinaStockRecorder().run()

        auth(zvt_env['jq_username'], zvt_env['jq_password'])
        print(f"剩余{get_query_count()['spare'] / 10000}万")
        self.codes = codes
        if not self.force_update:
            self.entities = get_entities(session=self.session,
                                         entity_type='stock_detail',
                                         exchanges=['sh', 'sz'],
                                         codes=self.codes,
                                         filters=[StockDetail.profile.is_(None)],
                                         return_type='domain',
                                         provider=self.provider)

    def run(self):
        for security_item in self.entities:
            assert isinstance(security_item, StockDetail)
            security = to_jq_entity_id(security_item)
            # 基本资料
            df = finance.run_query(query(finance.STK_COMPANY_INFO).filter(finance.STK_COMPANY_INFO.code == security))

            concept_dict = get_concept(security, date=security_item.timestamp)
            security_df = pd.DataFrame(index=[0])
            security_df['profile'] = df.description.values[0]
            security_df['main_business'] = df.main_business.values[0]
            security_df['date_of_establishment'] = to_pd_timestamp(df.establish_date.values[0])
            security_df['register_capital'] = df.register_capital.values[0]
            security_df['industries'] = ''
            security_df['industries'] = security_df['industries'].apply(lambda x:'、'.join(df[['industry_1', 'industry_2']].values.tolist()[0]))
            security_df['concept_indices'] = ''


            security_df['concept_indices'] = security_df['industries'].apply(
                lambda x: '、'.join([i['concept_name'] for i in concept_dict[security]['jq_concept']]))
            security_df['area_indices'] = df.province.values[0]

            df_stk = finance.run_query(query(finance.STK_LIST).filter(finance.STK_LIST.code == security))
            security_df['price'] = df_stk.book_price.values[0]
            security_df['issues'] = df_stk.ipo_shares.values[0]
            security_df['raising_fund'] = df_stk.ipo_shares.values[0] * df_stk.book_price.values[0]
            security_df['timestamp'] =security_item.timestamp
            security_df['id'] =security_item.id
            security_df['entity_id'] =security_item.entity_id
            security_df['code'] =security_item.code
            security_df['entity_type'] =security_item.entity_type
            security_df['exchange'] =security_item.exchange
            security_df['name'] =security_item.name
            security_df['list_date'] =security_item.list_date
            security_df['end_date'] =security_item.end_date
            df_to_db(df=security_df, data_schema=self.data_schema, provider=self.provider, force_update=True)
            # security_item.profile = df.description[0]
            # security_item.main_business = df.main_business.values[0]
            # security_item.date_of_establishment = to_pd_timestamp(df.establish_date.values[0])
            # security_item.register_capital = df.register_capital.values[0]
            # security_item.date_of_establishment = security_item.date_of_establishment.to_pydatetime()
            # security_item.date_of_establishment = security_item.date_of_establishment.strftime('%Y-%m-%d %H:%M:%S')
            # 关联行业to_pd_timestamp
            # security_item.industries = df[['industry_1', 'industry_2']].values.tolist()[0]
            # 关联概念
            # security_item.concept_indices = [i['concept_name'] for i in concept_dict[security]['jq_concept']]
            # 关联地区
            # security_item.area_indices = df.province.values[0]

            self.sleep()

            # 发行相关
            # df_stk = finance.run_query(query(finance.STK_LIST).filter(finance.STK_LIST.code == security))
            # security_item.issue_pe = to_float("--")
            # security_item.price = to_float(str(df_stk.book_price.values[0]))
            # security_item.issues = to_float(str(df_stk.ipo_shares.values[0]))
            # security_item.raising_fund = to_float(str(df_stk.ipo_shares.values[0] * df_stk.book_price.values[0]))
            # security_item.net_winning_rate = pct_to_float("--")

            # self.session.commit()
            self.logger.info('finish recording stock meta for:{}'.format(security_item.code))
            self.sleep()

        logout()


class JqChinaEtfRecorder(BaseJqChinaMetaRecorder):
    data_schema = Etf

    def run(self):
        # 抓取etf列表
        df_index = self.to_zvt_entity(get_all_securities(['etf']), entity_type='etf', category='etf')
        df_to_db(df_index, data_schema=Etf, provider=self.provider, force_update=self.force_update)

        # self.logger.info(df_index)
        self.logger.info("persist etf list success")
        logout()


class JqChinaFundDetailRecorder(BaseJqChinaMetaRecorder):
    data_schema = FundDetail

    def run(self):
        # 抓取fund列表
        df = finance.run_query(query(finance.FUND_MAIN_INFO))
        df.index.name = 'entity_id'
        df = df.reset_index()
        # 上市日期
        df.rename(columns={'start_date': 'timestamp'}, inplace=True)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['list_date'] = df['timestamp']
        df['end_date'] = pd.to_datetime(df['end_date'])

        df['entity_id'] = df.main_code.apply(lambda x: normalize_code(x))
        df['entity_id'] = df['entity_id'].apply(lambda x: to_entity_id(entity_type='fund', jq_code=x))

        df['id'] = df['entity_id']
        df['entity_type'] = 'fund'
        df['exchange'] = df['entity_id'].apply(lambda x: get_entity_exchange(x))
        df['code'] = df['entity_id'].apply(lambda x: get_entity_code(x))
        df['category'] = 'fund'
        # df['choice_code'] = df.apply(lambda x:x.main_code+'.'+x.exchange.upper(),axis=1)
        # loginResult = c.start("ForceLogin=1", '')
        # df['underlying_index_code'] = df.apply(lambda x:c.css(x.choice_code, "BMINDEXCODE", "Rank=1").Data if x.operate_mode == 'ETF' else None,axis=1)
        # df['underlying_index_code'] = df['underlying_index_code'].apply(lambda x:[i for i in x.values()][0][0].lower().replace(".","_") if x else None)
        # c.stop()
        df_to_db(df, data_schema=FundDetail, provider=self.provider, force_update=self.force_update)

        # self.logger.info(df_index)
        self.logger.info("persist etf list success")
        logout()


class JqChinaFundRecorder(BaseJqChinaMetaRecorder):
    data_schema = Fund

    def run(self):
        # 抓取基金列表
        df_index = self.to_zvt_entity(get_all_securities(['fund']), entity_type='fund', category='fund')
        df_to_db(df_index, data_schema=Fund, provider=self.provider, force_update=self.force_update)

        # self.logger.info(df_index)
        self.logger.info("persist etf list success")
        logout()


class JqChinaStockEtfPortfolioRecorder(TimeSeriesDataRecorder):
    entity_provider = 'joinquant'
    entity_schema = Etf

    # 数据来自jq
    provider = 'joinquant'

    data_schema = EtfStock

    def __init__(self, entity_type='etf', exchanges=['sh', 'sz'], entity_ids=None, codes=None, batch_size=10,
                 force_update=False, sleeping_time=5, default_size=2000, real_time=False, fix_duplicate_way='add',
                 start_timestamp=None, end_timestamp=None, close_hour=0, close_minute=0) -> None:
        super().__init__(entity_type, exchanges, entity_ids, codes, batch_size, force_update, sleeping_time,
                         default_size, real_time, fix_duplicate_way, start_timestamp, end_timestamp, close_hour,
                         close_minute)
        auth(zvt_env['jq_username'], zvt_env['jq_password'])

    def on_finish(self):
        super().on_finish()
        logout()

    def record(self, entity, start, end, size, timestamps):
        q = query(finance.FUND_PORTFOLIO_STOCK).filter(finance.FUND_PORTFOLIO_STOCK.pub_date >= start).filter(
            finance.FUND_PORTFOLIO_STOCK.code == entity.code)
        df = finance.run_query(q)
        if pd_is_not_null(df):
            #          id    code period_start  period_end    pub_date  report_type_id report_type  rank  symbol  name      shares    market_cap  proportion
            # 0   8640569  159919   2018-07-01  2018-09-30  2018-10-26          403003        第三季度     1  601318  中国平安  19869239.0  1.361043e+09        7.09
            # 1   8640570  159919   2018-07-01  2018-09-30  2018-10-26          403003        第三季度     2  600519  贵州茅台    921670.0  6.728191e+08        3.50
            # 2   8640571  159919   2018-07-01  2018-09-30  2018-10-26          403003        第三季度     3  600036  招商银行  18918815.0  5.806184e+08        3.02
            # 3   8640572  159919   2018-07-01  2018-09-30  2018-10-26          403003        第三季度     4  601166  兴业银行  22862332.0  3.646542e+08        1.90
            df['timestamp'] = pd.to_datetime(df['pub_date'])

            df.rename(columns={'symbol': 'stock_code', 'name': 'stock_name'}, inplace=True)
            df['proportion'] = df['proportion'] * 0.01

            df = portfolio_relate_stock(df, entity)

            df['stock_id'] = df['stock_code'].apply(lambda x: china_stock_code_to_id(x))
            df['id'] = df[['entity_id', 'stock_id', 'pub_date', 'id']].apply(lambda x: '_'.join(x.astype(str)), axis=1)
            df['report_date'] = pd.to_datetime(df['period_end'])
            df['report_period'] = df['report_type'].apply(lambda x: jq_to_report_period(x))

            df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)

            # self.logger.info(df.tail())
            self.logger.info(f"persist etf {entity.code} portfolio success")

        return None


class JqChinaFundEtfPortfolioRecorder(TimeSeriesDataRecorder):
    entity_provider = 'joinquant'
    entity_schema = Fund

    # 数据来自jq
    provider = 'joinquant'

    data_schema = FundStock

    def __init__(self, entity_type='fund', exchanges=['sh', 'sz'], entity_ids=None, codes=None, batch_size=10,
                 force_update=False, sleeping_time=5, default_size=2000, real_time=False, fix_duplicate_way='add',
                 start_timestamp=None, end_timestamp=None, close_hour=0, close_minute=0) -> None:
        super().__init__(entity_type, exchanges, entity_ids, codes, batch_size, force_update, sleeping_time,
                         default_size, real_time, fix_duplicate_way, start_timestamp, end_timestamp, close_hour,
                         close_minute)
        auth(zvt_env['jq_username'], zvt_env['jq_password'])

    def on_finish(self):
        super().on_finish()
        logout()

    def record(self, entity, start, end, size, timestamps):
        q = query(finance.FUND_PORTFOLIO_STOCK).filter(finance.FUND_PORTFOLIO_STOCK.pub_date >= start).filter(
            finance.FUND_PORTFOLIO_STOCK.code == entity.code)
        df = finance.run_query(q)
        if pd_is_not_null(df):
            #          id    code period_start  period_end    pub_date  report_type_id report_type  rank  symbol  name      shares    market_cap  proportion
            # 0   8640569  159919   2018-07-01  2018-09-30  2018-10-26          403003        第三季度     1  601318  中国平安  19869239.0  1.361043e+09        7.09
            # 1   8640570  159919   2018-07-01  2018-09-30  2018-10-26          403003        第三季度     2  600519  贵州茅台    921670.0  6.728191e+08        3.50
            # 2   8640571  159919   2018-07-01  2018-09-30  2018-10-26          403003        第三季度     3  600036  招商银行  18918815.0  5.806184e+08        3.02
            # 3   8640572  159919   2018-07-01  2018-09-30  2018-10-26          403003        第三季度     4  601166  兴业银行  22862332.0  3.646542e+08        1.90
            df['timestamp'] = pd.to_datetime(df['pub_date'])

            df.rename(columns={'symbol': 'stock_code', 'name': 'stock_name'}, inplace=True)
            df['proportion'] = df['proportion'] * 0.01

            df = portfolio_relate_stock(df, entity)

            df['stock_id'] = df['stock_code'].apply(lambda x: china_stock_code_to_id(x))
            df['id'] = df[['entity_id', 'stock_id', 'pub_date', 'id']].apply(lambda x: '_'.join(x.astype(str)), axis=1)
            df['report_date'] = pd.to_datetime(df['period_end'])
            df['report_period'] = df['report_type'].apply(lambda x: jq_to_report_period(x))

            df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)

            # self.logger.info(df.tail())
            self.logger.info(f"persist etf {entity.code} portfolio success")

        return None


class JqChinaIndexListSpiderNewRecorder(TimeSeriesDataRecorder):
    entity_provider = 'joinquant'
    entity_schema = Index

    # 数据来自jq
    provider = 'joinquant'

    data_schema = IndexStockNew

    def __init__(self, entity_type='index', exchanges=['sh', 'sz'], entity_ids=None, codes=None, batch_size=10,
                 force_update=True, sleeping_time=5, default_size=2000, real_time=False, fix_duplicate_way='add',
                 start_timestamp=None, end_timestamp=None, close_hour=0, close_minute=0) -> None:
        super().__init__(entity_type, exchanges, entity_ids, codes, batch_size, force_update, sleeping_time,
                         default_size, real_time, fix_duplicate_way, start_timestamp, end_timestamp, close_hour,
                         close_minute)
        auth(zvt_env['jq_username'], zvt_env['jq_password'])

    def on_finish(self):
        super().on_finish()
        logout()

    def record(self, entity, start, end, size, timestamps):
        if start < to_pd_timestamp("2008-01-01"):
            start = to_pd_timestamp("2008-01-01")
        # 获取数据库中已有数据
        data_schema_df = self.data_schema.query_data(entity_id=entity.id)
        if not data_schema_df.empty and data_schema_df.timestamp.max() <= start:
            from datetime import timedelta
            bdate_range_date = pd.bdate_range(start, start + timedelta(weeks=1))
            if bdate_range_date[bdate_range_date > start][-1] > now_pd_timestamp():
                start = to_time_str(now_pd_timestamp())
            else:
                start = to_time_str(bdate_range_date[bdate_range_date > start][-1])

        data = get_index_stocks(to_jq_entity_id(entity), date=start)

        df = pd.DataFrame(data, columns=['code'])
        if pd_is_not_null(df):
            df['stock_code'] = df['code'].apply(lambda x: str(x).split('.')[0])
            df['stock_exchange'] = df['code'].apply(lambda x: str(x).split('.')[1])
            df['stock_exchange'] = df['stock_exchange'].replace('XSHG', 'sh').replace('XSHE', 'sz')
            df['stock_id'] = df['stock_code'].apply(lambda x: china_stock_code_to_id(x))
            df_old = df[df.stock_id.isin(data_schema_df.stock_id)].copy()
            df_new = df[~df.stock_id.isin(data_schema_df.stock_id)].copy()
            out_data = data_schema_df[~data_schema_df.stock_id.isin(df.stock_id)].copy()
            if df_new.empty and out_data.empty:
                # 没有调入的股票  没有调出的股票
                data_schema_df['timestamp'] = pd.to_datetime(start)
                data_schema_df['pub_date'] = data_schema_df['timestamp']
                df_to_db(df=data_schema_df, data_schema=self.data_schema, provider=self.provider,
                         force_update=self.force_update)
                return None
            elif df_new.empty and not out_data.empty:
                # 没有调入,有调出
                data_schema_df['timestamp'] = pd.to_datetime(start)
                data_schema_df['pub_date'] = data_schema_df['timestamp']
                df2 = pd.DataFrame()
                for index, data_old in data_schema_df.iterrows():
                    schema_details = out_data.query("id == @data_old.id").copy()
                    if not schema_details.empty:
                        data_schema_df['timestamp'] = pd.to_datetime(start)
                        # 更新调出时间
                        schema_details['out_date'] = pd.to_datetime(start)
                        data_schema_df['pub_date'] = pd.to_datetime(start)
                        df2 = df2.append(schema_details)
                    else:
                        df2 = df2.append(data_old)
                df_to_db(df=df2, data_schema=self.data_schema, provider=self.provider,
                         force_update=self.force_update)
                return None
            elif not df_new.empty and not out_data.empty:
                # 有调入,有调出
                data_schema_df['timestamp'] = pd.to_datetime(start)
                data_schema_df['pub_date'] = data_schema_df['timestamp']
                df2 = pd.DataFrame()
                # 处理调出
                for index, data_old in data_schema_df.iterrows():
                    schema_details = out_data.query("id == @data_old.id").copy()
                    if not schema_details.empty:
                        # 更新调出时间
                        schema_details['out_date'] = pd.to_datetime(start)
                        schema_details['pub_date'] = pd.to_datetime(start)
                        df2 = df2.append(schema_details)
                    else:
                        # 无调出的不变
                        df2 = df2.append(data_old)
                # 处理调入,新增
                df_new['timestamp'] = pd.to_datetime(start)
                df_new['pub_date'] = df_new['timestamp']
                df_new['into_date'] = start
                df_new['out_date'] = pd.to_datetime("2200-01-01")
                df_new['pub_date2'] = df_new['timestamp'].apply(lambda x: to_time_str(x))
                df_new['stock_code'] = df_new['code'].apply(lambda x: str(x).split('.')[0])
                df_new['entity_id'] = entity.id
                df_new['id'] = df_new[['entity_id', 'stock_id']].apply(lambda x: '_'.join(x.astype(str)), axis=1)
                df_new['code'] = entity.code
                df_new['entity_type'] = entity.entity_type
                df_new['exchange'] = entity.exchange
                df_new['name'] = entity.name
                df2 = df2.append(df_new)
                df_to_db(df=df2, data_schema=self.data_schema, provider=self.provider,
                         force_update=self.force_update)
                return None
            elif not df_new.empty and out_data.empty:
                # 处理调入,新增
                df_new['timestamp'] = pd.to_datetime(start)
                df_new['pub_date'] = df_new['timestamp']
                df_new['into_date'] = start
                df_new['out_date'] = pd.to_datetime("2200-01-01")
                df_new['pub_date2'] = df_new['timestamp'].apply(lambda x: to_time_str(x))
                df_new['stock_code'] = df_new['code'].apply(lambda x: str(x).split('.')[0])
                df_new['entity_id'] = entity.id
                df_new['id'] = df_new[['entity_id', 'stock_id']].apply(lambda x: '_'.join(x.astype(str)), axis=1)
                df_new['code'] = entity.code
                df_new['entity_type'] = entity.entity_type
                df_new['exchange'] = entity.exchange
                df_new['name'] = entity.name
                df_to_db(df=df_new, data_schema=self.data_schema, provider=self.provider,
                         force_update=self.force_update)
                return None
            else:
                print('1')

            # self.logger.info(df.tail())
            self.logger.info(f"persist etf {entity.code} portfolio success")

        return None


__all__ = ['JqChinaStockDetailNewRecorder', 'JqChinaStockRecorder', 'JqChinaEtfRecorder',
           'JqChinaStockEtfPortfolioRecorder', 'JqChinaFundDetailRecorder']

if __name__ == '__main__':
    # JqChinaStockRecorder().run()
    JqChinaStockEtfPortfolioRecorder(codes=['510050']).run()
