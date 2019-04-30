# -*- coding: utf-8 -*-

from zvt.api.common import get_data
from zvt.domain import FinanceFactor, BalanceSheet, IncomeStatement, CashFlowStatement, SPODetail, RightsIssueDetail, \
    DividendFinancing, TopTenHolder, TopTenTradableHolder, HolderTrading, ManagerTrading


def get_finance_factor(provider='eastmoney', security_id=None, codes=None, columns=None,
                       return_type='df', session=None, start_timestamp=None, end_timestamp=None,
                       filters=None, order=None, limit=None):
    return get_data(data_schema=FinanceFactor, security_id=security_id, codes=codes, level=None, provider=provider,
                    columns=columns, return_type=return_type, start_timestamp=start_timestamp,
                    end_timestamp=end_timestamp, filters=filters, session=session, order=order, limit=limit)


def get_balance_sheet(provider='eastmoney', security_id=None, codes=None, columns=None,
                      return_type='df', session=None, start_timestamp=None, end_timestamp=None,
                      filters=None, order=None, limit=None):
    return get_data(data_schema=BalanceSheet, security_id=security_id, codes=codes, level=None, provider=provider,
                    columns=columns, return_type=return_type, start_timestamp=start_timestamp,
                    end_timestamp=end_timestamp, filters=filters, session=session, order=order, limit=limit)


def get_income_statement(provider='eastmoney', security_id=None, codes=None, columns=None,
                         return_type='df', session=None, start_timestamp=None, end_timestamp=None,
                         filters=None, order=None, limit=None):
    return get_data(data_schema=IncomeStatement, security_id=security_id, codes=codes, level=None, provider=provider,
                    columns=columns, return_type=return_type, start_timestamp=start_timestamp,
                    end_timestamp=end_timestamp, filters=filters, session=session, order=order, limit=limit)


def get_cash_flow_statement(provider='eastmoney', security_id=None, codes=None, columns=None,
                            return_type='df', session=None, start_timestamp=None, end_timestamp=None,
                            filters=None, order=None, limit=None):
    return get_data(data_schema=CashFlowStatement, security_id=security_id, codes=codes, level=None, provider=provider,
                    columns=columns, return_type=return_type, start_timestamp=start_timestamp,
                    end_timestamp=end_timestamp, filters=filters, session=session, order=order, limit=limit)


def get_spo_detail(provider='eastmoney', security_id=None, codes=None, columns=None,
                   return_type='df', session=None, start_timestamp=None, end_timestamp=None,
                   filters=None, order=None, limit=None):
    return get_data(data_schema=SPODetail, security_id=security_id, codes=codes, level=None, provider=provider,
                    columns=columns, return_type=return_type, start_timestamp=start_timestamp,
                    end_timestamp=end_timestamp, filters=filters, session=session, order=order, limit=limit)


def get_rights_issue_detail(provider='eastmoney', security_id=None, codes=None, columns=None,
                            return_type='df', session=None, start_timestamp=None, end_timestamp=None,
                            filters=None, order=None, limit=None):
    return get_data(data_schema=RightsIssueDetail, security_id=security_id, codes=codes, level=None, provider=provider,
                    columns=columns, return_type=return_type, start_timestamp=start_timestamp,
                    end_timestamp=end_timestamp, filters=filters, session=session, order=order, limit=limit)


def get_dividend_financing(provider='eastmoney', security_id=None, codes=None, columns=None,
                           return_type='df', session=None, start_timestamp=None, end_timestamp=None,
                           filters=None, order=None, limit=None):
    return get_data(data_schema=DividendFinancing, security_id=security_id, codes=codes, level=None, provider=provider,
                    columns=columns, return_type=return_type, start_timestamp=start_timestamp,
                    end_timestamp=end_timestamp, filters=filters, session=session, order=order, limit=limit)


def get_top_ten_holder(provider='eastmoney', security_id=None, codes=None, columns=None,
                       return_type='df', session=None, start_timestamp=None, end_timestamp=None,
                       filters=None, order=None, limit=None):
    return get_data(data_schema=TopTenHolder, security_id=security_id, codes=codes, level=None, provider=provider,
                    columns=columns, return_type=return_type, start_timestamp=start_timestamp,
                    end_timestamp=end_timestamp, filters=filters, session=session, order=order, limit=limit)


def get_top_ten_tradable_holder(provider='eastmoney', security_id=None, codes=None, columns=None,
                                return_type='df', session=None, start_timestamp=None, end_timestamp=None,
                                filters=None, order=None, limit=None):
    return get_data(data_schema=TopTenTradableHolder, security_id=security_id, codes=codes, level=None,
                    provider=provider,
                    columns=columns, return_type=return_type, start_timestamp=start_timestamp,
                    end_timestamp=end_timestamp, filters=filters, session=session, order=order, limit=limit)


def get_holder_trading(provider='eastmoney', security_id=None, codes=None, columns=None,
                       return_type='df', session=None, start_timestamp=None, end_timestamp=None,
                       filters=None, order=None, limit=None):
    return get_data(data_schema=HolderTrading, security_id=security_id, codes=codes, level=None,
                    provider=provider,
                    columns=columns, return_type=return_type, start_timestamp=start_timestamp,
                    end_timestamp=end_timestamp, filters=filters, session=session, order=order, limit=limit)


def get_manager_trading(provider='eastmoney', security_id=None, codes=None, columns=None,
                        return_type='df', session=None, start_timestamp=None, end_timestamp=None,
                        filters=None, order=None, limit=None):
    return get_data(data_schema=ManagerTrading, security_id=security_id, codes=codes, level=None,
                    provider=provider,
                    columns=columns, return_type=return_type, start_timestamp=start_timestamp,
                    end_timestamp=end_timestamp, filters=filters, session=session, order=order, limit=limit)
