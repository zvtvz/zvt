# -*- coding: utf-8 -*-

from typing import List

from zvt.api.utils import get_recent_report_date
from zvt.contract import PortfolioStockHistory
from zvt.contract.api import get_schema_by_name
from zvt.domain import ReportPeriod, Fund, Etf
from zvt.utils.time_utils import to_pd_timestamp, now_pd_timestamp


def portfolio_relate_stock(df, portfolio):
    df['entity_id'] = portfolio.entity_id
    df['entity_type'] = portfolio.entity_type
    df['exchange'] = portfolio.exchange
    df['code'] = portfolio.code
    df['name'] = portfolio.name

    return df


# 季报只有前十大持仓，半年报和年报才有全量的持仓信息，故根据离timestamp最近的报表(年报 or 半年报)来确定持仓
def get_portfolio_stocks(portfolio_entity=Fund, code=None, codes=None, ids=None, timestamp=now_pd_timestamp(),
                         provider=None):
    portfolio_stock = f'{portfolio_entity.__name__}Stock'
    data_schema: PortfolioStockHistory = get_schema_by_name(portfolio_stock)
    latests: List[PortfolioStockHistory] = data_schema.query_data(provider=provider, code=code, end_timestamp=timestamp,
                                                                  order=data_schema.timestamp.desc(), limit=1,
                                                                  return_type='domain')
    if latests:
        latest_record = latests[0]
        # 获取最新的报表
        df = data_schema.query_data(provider=provider, code=code, codes=codes, ids=ids, end_timestamp=timestamp,
                                    filters=[data_schema.report_date == latest_record.report_date])
        # 最新的为年报或者半年报
        if latest_record.report_period == ReportPeriod.year or latest_record.report_period == ReportPeriod.half_year:
            return df
        # 季报，需要结合 年报或半年报 来算持仓
        else:
            step = 0
            while step <= 20:
                report_date = get_recent_report_date(latest_record.report_date, step=step)

                pre_df = data_schema.query_data(provider=provider, code=code, codes=codes, ids=ids,
                                                end_timestamp=timestamp,
                                                filters=[data_schema.report_date == to_pd_timestamp(report_date)])
                df = df.append(pre_df)

                # 半年报和年报
                if (ReportPeriod.half_year.value in pre_df['report_period'].tolist()) or (
                        ReportPeriod.year.value in pre_df['report_period'].tolist()):
                    # 保留最新的持仓
                    df = df.drop_duplicates(subset=['stock_code'], keep='first')
                    return df
                step = step + 1


def get_etf_stocks(code=None, codes=None, ids=None, timestamp=now_pd_timestamp(), provider=None):
    return get_portfolio_stocks(portfolio_entity=Etf, code=code, codes=codes, ids=ids, timestamp=timestamp,
                                provider=provider)


def get_fund_stocks(code=None, codes=None, ids=None, timestamp=now_pd_timestamp(), provider=None):
    return get_portfolio_stocks(portfolio_entity=Fund, code=code, codes=codes, ids=ids, timestamp=timestamp,
                                provider=provider)
# the __all__ is generated
__all__ = ['portfolio_relate_stock', 'get_portfolio_stocks', 'get_etf_stocks', 'get_fund_stocks']