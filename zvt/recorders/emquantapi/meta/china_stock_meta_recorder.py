# -*- coding: utf-8 -*-
import pandas as pd
from jqdatasdk import auth, get_all_securities, logout, query, finance,normalize_code,get_query_count,get_concept,get_security_info
from EmQuantAPI import *
from zvt.recorders.emquantapi.common import mainCallback, to_em_entity_id
from zvt.contract.api import df_to_db, get_entity_exchange, get_entity_code, get_entities,get_data
from zvt.contract.recorder import Recorder, TimeSeriesDataRecorder
from zvt.recorders.tonglian.common import to_jq_entity_id
from zvt.utils.pd_utils import pd_is_not_null
from zvt import zvt_env
from zvt.api.quote import china_stock_code_to_id, portfolio_relate_stock
from zvt.domain import EtfStock, Stock, Etf, StockDetail,Fund,FundDetail,FundStock
from zvt.recorders.joinquant.common import to_entity_id, jq_to_report_period
from zvt.utils.time_utils import to_pd_timestamp
from zvt.utils.utils import to_float, pct_to_float


class BaseEmChinaMetaRecorder(Recorder):
    provider = 'emquantapi'

    def __init__(self, batch_size=10, force_update=True, sleeping_time=10) -> None:
        super().__init__(batch_size, force_update, sleeping_time)
        # 调用登录函数（激活后使用，不需要用户名密码）
        loginResult = c.start("ForceLogin=1", '', mainCallback)
        if (loginResult.ErrorCode != 0):
            print("login in fail")
            exit()

    def to_zvt_entity(self, df, entity_type, category=None):
        df.index.name = 'entity_id'
        df = df.reset_index()
        # 上市日期
        df.rename(columns={'start_date': 'timestamp'}, inplace=True)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['list_date'] = df['timestamp']
        df['end_date'] = pd.to_datetime(df['end_date'])
        df['entity_id'] = df['entity_id'].apply(lambda x: x.lower())
        df['entity_id'] = df['entity_id'].apply(lambda x: to_entity_id(entity_type=entity_type, jq_code=x))
        df['id'] = df['entity_id']
        df['entity_type'] = entity_type
        df['exchange'] = df['entity_id'].apply(lambda x: get_entity_exchange(x))
        df['code'] = df['entity_id'].apply(lambda x: get_entity_code(x))
        df['end_date'].fillna(pd.to_datetime("22000101"),inplace=True)
        if category:
            df['category'] = category

        return df


class EmChinaStockRecorder(BaseEmChinaMetaRecorder):
    data_schema = Stock

    def run(self):
        # 抓取股票列表 001004 全部A股
        # cn_stock_market  = c.sector("001004", "2021-01-17")
        hk_stock_market = c.sector("401001", "2021-01-17")
        import pandas as pd
        # cn_stock_market_df = pd.DataFrame(cn_stock_market.Data, columns=['code'])
        hk_stock_market_df = pd.DataFrame(hk_stock_market.Data, columns=['code'])
        # em_data = pd.concat([cn_stock_market_df,hk_stock_market_df],axis=0)
        # try:
        df_res = pd.DataFrame()
        for code in hk_stock_market_df.code:
            if '.SH' in code or '.SZ' in code:
                data_css = c.css(code, "NAME,CODE,LISTDATE,LISTMKT,DELISTDATE", "ispandas=1")
            elif '.HK' in code:
                # 港、美股和A股的字段不同
                try:
                    self.logger.info(f"开始获取{code}的数据!")
                    data_css = c.css(code, "NAME,CODE,IPOLISTDATE,DELISTDATE", "ispandas=1")
                except:
                    self.logger.info(f"获取{code}的数据失败,跳过!")
                    continue
            else:
                continue
            df_res = df_res.append(data_css)
            self.logger.info(f"{code}的数据获取成功!")
        df_res.rename(columns = {
            "NAME":"name",
            "LISTDATE":"start_date",
            "IPOLISTDATE":"start_date",
            "DELISTDATE":"end_date",
        },inplace=True)
        # except:
        #     print()
        df_stock = self.to_zvt_entity(df_res, entity_type='stock')
        # df_stock = self.to_zvt_entity(get_all_securities(['stock']), entity_type='stock')
        df_to_db(df_stock, data_schema=Stock, provider=self.provider, force_update=self.force_update)
        # persist StockDetail too
        # df_to_db(df=df_stock, data_schema=StockDetail, provider=self.provider, force_update=self.force_update)

        # self.logger.info(df_stock)
        self.logger.info("persist stock list success")




class EmChinaStockDetailRecorder(Recorder):
    provider = 'emquantapi'
    data_schema = StockDetail

    def __init__(self, batch_size=10, force_update=False, sleeping_time=5, codes=None) -> None:
        super().__init__(batch_size, force_update, sleeping_time)

        loginResult = c.start("ForceLogin=1", '', mainCallback)
        if (loginResult.ErrorCode != 0):
            print("login in fail")
            exit()
        self.codes = codes
        if not self.force_update:
            self.entities = get_entities(session=self.session,
                                         entity_type='stock_detail',
                                         exchanges=['hk'],
                                         codes=self.codes,
                                         # filters=[StockDetail.profile.is_(None)],
                                         return_type='domain',
                                         provider=self.provider)

    def run(self):
        for security_item in self.entities:
            assert isinstance(security_item, StockDetail)
            security = to_jq_entity_id(security_item)

            # 基本资料
            data = c.css(security, "COMPANYPROFILE,FOUNDDATE,AREA,CAPITAL,IPOSHARESVOL,IPOPRICE,IPONETCOLLECTION,IPOPE,HKSE,IPOPLANISSUEVOL",
                         "CurType=1,ClassiFication=4,ispandas=1")
            security_item.profile = data.COMPANYPROFILE[0]
            security_item.date_of_establishment = to_pd_timestamp(data.FOUNDDATE.values[0])
            # 关联行业
            security_item.industries = data.HKSE.values[0]
            # 关联概念
            # security_item.concept_indices = [i['concept_name'] for i in concept_dict["000001.XSHE"]['jq_concept']]
            # 关联地区
            security_item.area_indices = data.AREA.values[0]

            # 发行相关
            security_item.price = data.IPOPRICE.values[0]
            security_item.issues = data.IPOPLANISSUEVOL.values[0]
            security_item.raising_fund = data.IPONETCOLLECTION.values[0]
            try:
                security_item.register_capital = to_float(data.CAPITAL.values[0].split(' ')[0])/10000
            except AttributeError:
                pass
            self.session.commit()
            self.logger.info('finish recording stock meta for:{}'.format(security_item.code))
            self.sleep()



class EmChinaEtfRecorder(BaseEmChinaMetaRecorder):
    data_schema = Etf

    def run(self):
        # 抓取etf列表
        df_index = self.to_zvt_entity(get_all_securities(['etf']), entity_type='etf', category='etf')
        df_to_db(df_index, data_schema=Etf, provider=self.provider, force_update=self.force_update)

        # self.logger.info(df_index)
        self.logger.info("persist etf list success")
        logout()

class EmChinaFundDetailRecorder(BaseEmChinaMetaRecorder):
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

        df['entity_id'] = df.main_code.apply(lambda x:normalize_code(x))
        df['entity_id'] = df['entity_id'].apply(lambda x: to_entity_id(entity_type='fund', jq_code=x))

        df['id'] = df['entity_id']
        df['entity_type'] = 'fund'
        df['exchange'] = df['entity_id'].apply(lambda x: get_entity_exchange(x))
        df['code'] = df['entity_id'].apply(lambda x: get_entity_code(x))

        df['category'] = 'fund'

        df_to_db(df, data_schema=FundDetail, provider=self.provider, force_update=self.force_update)

        # self.logger.info(df_index)
        self.logger.info("persist etf list success")
        logout()

class JqChinaFundRecorder(BaseEmChinaMetaRecorder):
    data_schema = Fund

    def run(self):
        # 抓取基金列表
        df_index = self.to_zvt_entity(get_all_securities(['fund']), entity_type='fund', category='fund')
        df_to_db(df_index, data_schema=Fund, provider=self.provider, force_update=self.force_update)

        # self.logger.info(df_index)
        self.logger.info("persist etf list success")
        logout()


class EmChinaStockEtfPortfolioRecorder(TimeSeriesDataRecorder):
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




__all__ = ['EmChinaStockDetailRecorder','EmChinaStockRecorder', 'EmChinaEtfRecorder', 'EmChinaStockEtfPortfolioRecorder','EmChinaFundDetailRecorder']

if __name__ == '__main__':
    # EmChinaStockRecorder().run()
    EmChinaStockEtfPortfolioRecorder(codes=['510050']).run()
