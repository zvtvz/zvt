from ..context import init_test_context

init_test_context()

from zvt.domain import FinanceFactor, BalanceSheet, IncomeStatement, CashFlowStatement
from zvt.contract.api import get_db_session
from zvt.utils.time_utils import to_time_str

session = get_db_session(provider='eastmoney', db_name='finance')  # type: sqlalchemy.orm.Session


# 银行指标
def test_000001_finance_factor():
    correct_timestamps = ['2018-09-30', '2018-06-30', '2018-03-31', '2017-12-31', '2017-09-30', '2017-06-30',
                          '2017-03-31', '2016-12-31', '2016-09-30', '2016-06-30', '2016-03-31', '2015-12-31',
                          '2015-09-30', '2015-06-30', '2015-03-31', '2014-12-31', '2014-09-30', '2014-06-30',
                          '2014-03-31', '2013-12-31', '2013-09-30', '2013-06-30', '2013-03-31', '2012-12-31',
                          '2012-09-30', '2012-06-30', '2012-03-31', '2011-12-31', '2011-09-30', '2011-06-30',
                          '2011-03-31', '2010-12-31', '2010-09-30', '2010-06-30', '2010-03-31', '2009-12-31',
                          '2009-09-30', '2009-06-30', '2009-03-31', '2008-12-31', '2008-09-30', '2008-06-30',
                          '2008-03-31', '2007-12-31', '2007-09-30', '2007-06-30', '2007-03-31', '2006-12-31',
                          '2006-09-30', '2006-06-30', '2006-03-31', '2005-12-31', '2005-09-30', '2005-06-30',
                          '2005-03-31', '2004-12-31', '2004-09-30', '2004-06-30', '2004-03-31', '2003-12-31',
                          '2003-09-30', '2003-06-30', '2003-03-31', '2002-12-31', '2002-09-30', '2002-06-30',
                          '2002-03-31', '2001-12-31', '2001-09-30', '2001-06-30', '2001-03-31', '2000-12-31',
                          '2000-06-30', '1999-12-31', '1999-06-30', '1998-12-31', '1998-06-30', '1997-12-31',
                          '1997-06-30', '1996-12-31', '1996-06-30', '1995-12-31', '1995-06-30', '1994-12-31',
                          '1994-06-30', '1993-12-31', '1993-06-30', '1992-12-31', '1991-12-31', '1990-12-31',
                          '1989-12-31']
    result = FinanceFactor.query_data(session=session, provider='eastmoney', return_type='domain',
                                      codes=['000001'], end_timestamp='2018-12-30',
                                      order=FinanceFactor.report_date.desc(), time_field='report_date')
    assert len(correct_timestamps) == len(result)
    timestamps = [to_time_str(item.report_date) for item in result]
    assert set(correct_timestamps) == set(timestamps)
    latest: FinanceFactor = result[0]
    assert latest.basic_eps == 1.14
    assert latest.deducted_eps == 1.13
    assert latest.diluted_eps == 1.14
    assert latest.bps == 12.538
    assert latest.capital_reserve_ps == 3.2886
    assert latest.undistributed_profit_ps == 5.3566
    assert latest.op_cash_flow_ps == -0.6587

    assert latest.total_op_income == 86660000000
    assert latest.net_profit == 20460000000
    assert latest.deducted_net_profit == 20350000000
    assert latest.op_income_growth_yoy == 0.0856
    assert latest.net_profit_growth_yoy == 0.068
    assert latest.deducted_net_profit_growth_yoy == 0.0636
    assert latest.op_income_growth_qoq == 0.0336
    assert latest.net_profit_growth_qoq == 0.0202
    assert latest.deducted_net_profit_growth_qoq == 0.0168

    assert latest.roe == 0.0948
    assert latest.deducted_roe == 0.0943
    assert latest.rota == 0.0062
    assert latest.net_margin == 0.2360

    assert latest.debt_asset_ratio == 0.9298
    assert latest.em == 14.25
    assert latest.equity_ratio == 13.25

    assert latest.fi_total_deposit == 2130000000000
    assert latest.fi_total_loan == 1920000000000
    assert latest.fi_loan_deposit_ratio == 0.9004
    assert latest.fi_npl_ratio == 0.0168
    assert latest.fi_npl_provision_coverage == 1.6914


# 银行资产负债表
def test_000001_balance_sheet():
    correct_timestamps = ['2018-09-30', '2018-06-30', '2018-03-31', '2017-12-31', '2017-09-30', '2017-06-30',
                          '2017-03-31', '2016-12-31', '2016-09-30', '2016-06-30', '2016-03-31', '2015-12-31',
                          '2015-09-30', '2015-06-30', '2015-03-31', '2014-12-31', '2014-09-30', '2014-06-30',
                          '2014-03-31', '2013-12-31', '2013-09-30', '2013-06-30', '2013-03-31', '2012-12-31',
                          '2012-09-30', '2012-06-30', '2012-03-31', '2011-12-31', '2011-09-30', '2011-06-30',
                          '2011-03-31', '2010-12-31', '2010-09-30', '2010-06-30', '2010-03-31', '2009-12-31',
                          '2009-09-30', '2009-06-30', '2009-03-31', '2008-12-31', '2008-09-30', '2008-06-30',
                          '2008-03-31', '2007-12-31', '2007-09-30', '2007-06-30', '2007-03-31', '2006-12-31',
                          '2006-09-30', '2006-06-30', '2006-03-31', '2005-12-31', '2005-09-30', '2005-06-30',
                          '2005-03-31', '2004-12-31', '2004-09-30', '2004-06-30', '2004-03-31', '2003-12-31',
                          '2003-09-30', '2003-06-30', '2003-03-31', '2002-12-31', '2002-09-30', '2002-06-30',
                          '2002-03-31', '2001-12-31', '2001-06-30', '2000-12-31', '2000-06-30', '1999-12-31',
                          '1999-06-30', '1998-12-31', '1998-06-30', '1997-12-31', '1997-06-30', '1996-12-31',
                          '1996-06-30', '1995-12-31', '1995-06-30', '1994-12-31', '1994-06-30', '1993-12-31',
                          '1992-12-31', '1991-12-31', '1990-12-31', '1989-12-31']
    result = BalanceSheet.query_data(session=session, provider='eastmoney', return_type='domain',
                                     codes=['000001'], end_timestamp='2018-12-30',
                                     order=BalanceSheet.report_date.desc(), time_field='report_date')
    assert len(correct_timestamps) == len(result)
    timestamps = [to_time_str(item.report_date) for item in result]
    assert set(correct_timestamps) == set(timestamps)
    latest: BalanceSheet = result[0]
    assert latest.fi_cash_and_deposit_in_central_bank == 287600000000
    assert latest.fi_deposit_in_other_fi == 95310000000
    assert latest.fi_expensive_metals == 72020000000
    assert latest.fi_lending_to_other_fi == 88100000000
    assert latest.fi_financial_assets_effect_current_income == 103500000000
    assert latest.fi_financial_derivative_asset == 25650000000

    assert latest.fi_buying_sell_back_fi__asset == 32760000000
    assert latest.accounts_receivable == 22830000000
    assert latest.fi_interest_receivable == 18310000000
    assert latest.fi_disbursing_loans_and_advances == 1870000000000
    assert latest.real_estate_investment == 194000000
    assert latest.fixed_assets == 9374000000
    assert latest.intangible_assets == 4722000000
    assert latest.goodwill == 7568000000
    assert latest.deferred_tax_assets == 28880000000
    assert latest.fi_other_asset == 15630000000
    assert latest.total_assets == 3350000000000

    assert latest.fi_borrowings_from_central_bank == 149900000000
    assert latest.fi_deposit_from_other_fi == 402300000000
    assert latest.fi_borrowings_from_fi == 17830000000
    assert latest.fi_financial_liability_effect_current_income == 9599000000
    assert latest.fi_financial_derivative_liability == 20730000000
    assert latest.fi_sell_buy_back_fi_asset == 2000000000
    assert latest.fi_savings_absorption == 2130000000000
    assert latest.fi_notes_payable == 0

    assert latest.employee_benefits_payable == 10550000000
    assert latest.taxes_payable == 7595000000
    assert latest.interest_payable == 27670000000
    assert latest.fi_estimated_liabilities == 24000000
    assert latest.fi_bond_payable == 321500000000
    assert latest.fi_other_liability == 12570000000
    assert latest.total_liabilities == 3120000000000

    assert latest.fi_capital == 17170000000
    assert latest.fi_other_equity_instruments == 19950000000
    assert latest.fi_preferred_stock == 19950000000
    assert latest.capital_reserve == 56470000000
    assert latest.surplus_reserve == 10780000000
    assert latest.fi_generic_risk_reserve == 38550000000
    assert latest.undistributed_profits == 91970000000

    assert latest.equity == 235200000000
    assert latest.total_liabilities_and_equity == 3350000000000


# 银行利润表
def test_000001_income_statement():
    correct_timestamps = ['2018-09-30', '2018-06-30', '2018-03-31', '2017-12-31', '2017-09-30',
                          '2017-06-30', '2017-03-31', '2016-12-31', '2016-09-30', '2016-06-30', '2016-03-31',
                          '2015-12-31', '2015-09-30', '2015-06-30', '2015-03-31', '2014-12-31', '2014-09-30',
                          '2014-06-30', '2014-03-31', '2013-12-31', '2013-09-30', '2013-06-30', '2013-03-31',
                          '2012-12-31', '2012-09-30', '2012-06-30', '2012-03-31', '2011-12-31', '2011-09-30',
                          '2011-06-30', '2011-03-31', '2010-12-31', '2010-09-30', '2010-06-30', '2010-03-31',
                          '2009-12-31', '2009-09-30', '2009-06-30', '2009-03-31', '2008-12-31', '2008-09-30',
                          '2008-06-30', '2008-03-31', '2007-12-31', '2007-09-30', '2007-06-30', '2007-03-31',
                          '2006-12-31', '2006-09-30', '2006-06-30', '2006-03-31', '2005-12-31', '2005-09-30',
                          '2005-06-30', '2005-03-31', '2004-12-31', '2004-09-30', '2004-06-30', '2004-03-31',
                          '2003-12-31', '2003-09-30', '2003-06-30', '2003-03-31', '2002-12-31', '2002-09-30',
                          '2002-06-30', '2002-03-31', '2001-12-31', '2001-09-30', '2001-06-30', '2001-03-31',
                          '2000-12-31', '2000-06-30', '1999-12-31', '1999-06-30', '1998-12-31', '1998-06-30',
                          '1997-12-31', '1997-06-30', '1996-12-31', '1996-06-30', '1995-12-31', '1995-06-30',
                          '1994-12-31', '1994-06-30', '1993-12-31', '1993-06-30', '1992-12-31', '1991-12-31',
                          '1990-12-31', '1989-12-31']
    result = IncomeStatement.query_data(session=session, provider='eastmoney', return_type='domain',
                                        codes=['000001'], end_timestamp='2018-12-30',
                                        order=IncomeStatement.report_date.desc(), time_field='report_date')
    assert len(correct_timestamps) == len(result)
    timestamps = [to_time_str(item.report_date) for item in result]
    assert set(correct_timestamps) == set(timestamps)
    latest: IncomeStatement = result[0]

    assert latest.operating_income == 86660000000
    assert latest.fi_net_interest_income == 54530000000
    assert latest.fi_interest_income == 121700000000
    assert latest.fi_interest_expenses == 67130000000
    assert latest.fi_net_incomes_from_fees_and_commissions == 23710000000
    assert latest.fi_incomes_from_fees_and_commissions == 28920000000
    assert latest.fi_expenses_for_fees_and_commissions == 5218000000
    assert latest.investment_income == 7099000000
    assert latest.fi_income_from_fair_value_change == 1047000000
    assert latest.fi_income_from_exchange == -40000000
    assert latest.fi_other_income == 144000000

    assert latest.operating_costs == 26430000000
    assert latest.business_taxes_and_surcharges == 847000000
    assert latest.fi_operate_and_manage_expenses == 25580000000

    assert latest.operating_profit == 26610000000
    assert latest.non_operating_income == 14000000
    assert latest.non_operating_costs == 62000000

    assert latest.total_profits == 26570000000


# 银行现金流量表
def test_000001_cash_flow_statement():
    correct_timestamps = ['2018-09-30', '2018-06-30', '2018-03-31', '2017-12-31', '2017-09-30',
                          '2017-06-30', '2017-03-31', '2016-12-31', '2016-09-30', '2016-06-30', '2016-03-31',
                          '2015-12-31', '2015-09-30', '2015-06-30', '2015-03-31', '2014-12-31', '2014-09-30',
                          '2014-06-30', '2014-03-31', '2013-12-31', '2013-09-30', '2013-06-30', '2013-03-31',
                          '2012-12-31', '2012-09-30', '2012-06-30', '2012-03-31', '2011-12-31', '2011-09-30',
                          '2011-06-30', '2011-03-31', '2010-12-31', '2010-09-30', '2010-06-30', '2010-03-31',
                          '2009-12-31', '2009-09-30', '2009-06-30', '2009-03-31', '2008-12-31', '2008-09-30',
                          '2008-06-30', '2008-03-31', '2007-12-31', '2007-09-30', '2007-06-30', '2007-03-31',
                          '2006-12-31', '2006-09-30', '2006-06-30', '2006-03-31', '2005-12-31', '2005-09-30',
                          '2005-06-30', '2005-03-31', '2004-12-31', '2004-09-30', '2004-06-30', '2004-03-31',
                          '2003-12-31', '2003-09-30', '2003-06-30', '2003-03-31', '2002-12-31', '2002-06-30',
                          '2001-12-31', '2001-06-30', '2000-12-31', '2000-06-30', '1999-12-31', '1999-06-30',
                          '1998-12-31', '1998-06-30']
    result = CashFlowStatement.query_data(session=session, provider='eastmoney', return_type='domain',
                                          codes=['000001'], end_timestamp='2018-12-30',
                                          order=CashFlowStatement.report_date.desc(), time_field='report_date')
    assert len(correct_timestamps) == len(result)
    timestamps = [to_time_str(item.report_date) for item in result]
    assert set(correct_timestamps) == set(timestamps)
    latest: CashFlowStatement = result[0]

    # 00000000
    assert latest.fi_deposit_increase == 104700000000
    assert latest.fi_borrow_from_central_bank_increase == 18960000000
    assert latest.fi_deposit_in_others_decrease == 60880000000
    assert latest.fi_lending_and_buy_repurchase_decrease == 12330000000
    assert latest.fi_lending_decrease == 12270000000
    assert latest.fi_buy_repurchase_decrease == 56000000
    assert latest.fi_cash_from_interest_commission == 133700000000
    assert latest.cash_from_other_op == 20540000000
    assert latest.total_op_cash_inflows == 381200000000
    assert latest.fi_loan_advance_increase == 250300000000
    assert latest.fi_borrowing_and_sell_repurchase_decrease == 14350000000
    assert latest.fi_borrowing_decrease == 10190000000
    assert latest.fi_sell_repurchase_decrease == 4155000000
    assert latest.fi_cash_to_interest_commission == 56760000000

    assert latest.cash_to_employees == 12930000000
    assert latest.taxes_and_surcharges == 20010000000
    assert latest.cash_to_other_related_op == 38150000000
    assert latest.total_op_cash_outflows == 392500000000
    assert latest.net_op_cash_flows == -11310000000

    assert latest.cash_from_disposal_of_investments == 348900000000
    assert latest.cash_from_returns_on_investments == 21080000000
    assert latest.cash_from_disposal_fixed_intangible_assets == 108000000
    assert latest.total_investing_cash_inflows == 370100000000
    assert latest.cash_to_investments == 294600000000
    assert latest.cash_to_acquire_fixed_intangible_assets == 1518000000
    assert latest.total_investing_cash_outflows == 296100000000
    assert latest.net_investing_cash_flows == 73960000000
    assert latest.cash_from_issuing_bonds == 581200000000
    assert latest.total_financing_cash_inflows == 581200000000
    assert latest.cash_to_repay_borrowings == 612500000000
    assert latest.fi_cash_to_pay_interest == 2511000000
    assert latest.cash_to_pay_interest_dividend == 3209000000
    assert latest.total_financing_cash_outflows == 618300000000
    assert latest.net_financing_cash_flows == -37080000000
    assert latest.foreign_exchange_rate_effect == 2018000000
    assert latest.net_cash_increase == 27590000000
    assert latest.cash_at_beginning == 137000000000
    assert latest.cash == 164600000000


# 企业指标
def test_000778_finance_factor():
    correct_timestamps = ['2018-09-30', '2018-06-30', '2018-03-31', '2017-12-31', '2017-09-30', '2017-06-30',
                          '2017-03-31', '2016-12-31', '2016-09-30', '2016-06-30', '2016-03-31', '2015-12-31',
                          '2015-09-30', '2015-06-30', '2015-03-31', '2014-12-31', '2014-09-30', '2014-06-30',
                          '2014-03-31', '2013-12-31', '2013-09-30', '2013-06-30', '2013-03-31', '2012-12-31',
                          '2012-09-30', '2012-06-30', '2012-03-31', '2011-12-31', '2011-09-30', '2011-06-30',
                          '2011-03-31', '2010-12-31', '2010-09-30', '2010-06-30', '2010-03-31', '2009-12-31',
                          '2009-09-30', '2009-06-30', '2009-03-31', '2008-12-31', '2008-09-30', '2008-06-30',
                          '2008-03-31', '2007-12-31', '2007-09-30', '2007-06-30', '2007-03-31', '2006-12-31',
                          '2006-09-30', '2006-06-30', '2006-03-31', '2005-12-31', '2005-09-30', '2005-06-30',
                          '2005-03-31', '2004-12-31', '2004-09-30', '2004-06-30', '2004-03-31', '2003-12-31',
                          '2003-09-30', '2003-06-30', '2003-03-31', '2002-12-31', '2002-09-30', '2002-06-30',
                          '2002-03-31', '2001-12-31', '2001-06-30', '2000-12-31', '2000-06-30', '1999-12-31',
                          '1999-06-30', '1998-12-31', '1998-06-30', '1997-12-31', '1997-06-30', '1996-12-31',
                          '1995-12-31', '1994-12-31']
    result = FinanceFactor.query_data(session=session, provider='eastmoney', return_type='domain',
                                      codes=['000778'], end_timestamp='2018-12-30',
                                      order=FinanceFactor.report_date.desc(), time_field='report_date')
    assert len(correct_timestamps) == len(result)
    timestamps = [to_time_str(item.report_date) for item in result]
    assert set(correct_timestamps) == set(timestamps)
    latest: FinanceFactor = result[0]

    assert latest.basic_eps == 0.4537
    assert latest.diluted_eps == 0.4537
    assert latest.bps == 5.0919
    assert latest.capital_reserve_ps == 2.1769
    assert latest.undistributed_profit_ps == 1.8132
    assert latest.op_cash_flow_ps == 1.0148
    assert latest.total_op_income == 31710000000
    assert latest.gross_profit == 5491000000
    assert latest.net_profit == 1811000000
    assert latest.deducted_net_profit == 1897000000
    assert latest.op_income_growth_yoy == -0.1024
    assert latest.net_profit_growth_yoy == 1.2404
    assert latest.deducted_net_profit_growth_yoy == 1.4813
    assert latest.op_income_growth_qoq == 0.0408
    assert latest.net_profit_growth_qoq == 0.2143
    assert latest.deducted_net_profit_growth_qoq == 0.2955

    assert latest.roe == 0.0882
    assert latest.rota == 0.0376
    assert latest.gross_profit_margin == 0.1731
    assert latest.net_margin == 0.0591

    assert latest.advance_receipts_per_op_income == 0.1
    assert latest.sales_net_cash_flow_per_op_income == 0.88
    assert latest.op_net_cash_flow_per_op_income == 0.13
    assert latest.actual_tax_rate == 0.2362

    assert latest.current_ratio == 1
    assert latest.quick_ratio == 0.84
    assert latest.cash_flow_ratio == 0.17
    assert latest.debt_asset_ratio == 0.5766
    assert latest.em == 2.36
    assert latest.equity_ratio == 1.43

    assert latest.total_assets_turnover_days == 423.91
    assert latest.inventory_turnover_days == 32.88
    assert latest.receivables_turnover_days == 52.23
    assert latest.total_assets_turnover == 0.64
    assert latest.inventory_turnover == 8.21
    assert latest.receivables_turnover == 5.17


# 企业资产负债表
def test_000778_balance_sheet():
    correct_timestamps = ['2018-09-30', '2018-06-30', '2018-03-31', '2017-12-31', '2017-09-30', '2017-06-30',
                          '2017-03-31', '2016-12-31', '2016-09-30', '2016-06-30', '2016-03-31', '2015-12-31',
                          '2015-09-30', '2015-06-30', '2015-03-31', '2014-12-31', '2014-09-30', '2014-06-30',
                          '2014-03-31', '2013-12-31', '2013-09-30', '2013-06-30', '2013-03-31', '2012-12-31',
                          '2012-09-30', '2012-06-30', '2012-03-31', '2011-12-31', '2011-09-30', '2011-06-30',
                          '2011-03-31', '2010-12-31', '2010-09-30', '2010-06-30', '2010-03-31', '2009-12-31',
                          '2009-09-30', '2009-06-30', '2009-03-31', '2008-12-31', '2008-09-30', '2008-06-30',
                          '2008-03-31', '2007-12-31', '2007-09-30', '2007-06-30', '2007-03-31', '2006-12-31',
                          '2006-09-30', '2006-06-30', '2006-03-31', '2005-12-31', '2005-09-30', '2005-06-30',
                          '2005-03-31', '2004-12-31', '2004-09-30', '2004-06-30', '2004-03-31', '2003-12-31',
                          '2003-09-30', '2003-06-30', '2003-03-31', '2002-12-31', '2002-09-30', '2002-06-30',
                          '2002-03-31', '2001-12-31', '2001-06-30', '2000-12-31', '2000-06-30', '1999-12-31',
                          '1999-06-30', '1998-12-31', '1998-06-30', '1997-12-31', '1997-06-30', '1996-12-31',
                          '1995-12-31', '1994-12-31']
    result = BalanceSheet.query_data(session=session, provider='eastmoney', return_type='domain',
                                     codes=['000778'], end_timestamp='2018-12-30',
                                     order=BalanceSheet.report_date.desc(), time_field='report_date')
    assert len(correct_timestamps) == len(result)
    timestamps = [to_time_str(item.report_date) for item in result]
    assert set(correct_timestamps) == set(timestamps)
    latest: BalanceSheet = result[0]

    assert latest.cash_and_cash_equivalents == 6381000000
    assert latest.note_receivable == 4655000000
    assert latest.accounts_receivable == 1920000000
    assert latest.advances_to_suppliers == 2112000000
    assert latest.other_receivables == 4671000000
    assert latest.inventories == 3891000000
    assert latest.current_portion_of_non_current_assets == 270000000
    assert latest.other_current_assets == 220100000
    assert latest.total_current_assets == 24120000000

    assert latest.fi_assets_saleable == 914900000
    assert latest.long_term_receivables == 1078000000
    assert latest.long_term_equity_investment == 6071000000
    assert latest.real_estate_investment == 24130000
    assert latest.fixed_assets == 15440000000
    assert latest.construction_in_process == 1196000000
    assert latest.intangible_assets == 853800000
    assert latest.goodwill == 32990000
    assert latest.long_term_prepaid_expenses == 2527000
    assert latest.deferred_tax_assets == 292300000
    assert latest.other_non_current_assets == 332800000
    assert latest.total_assets == 50350000000

    assert latest.short_term_borrowing == 9104000000
    assert latest.accept_money_deposits == 0
    assert latest.advances_from_customers == 3199000000
    assert latest.employee_benefits_payable == 207800000
    assert latest.taxes_payable == 735200000
    assert latest.other_payable == 2022000000
    assert latest.current_portion_of_non_current_liabilities == 1099000000
    assert latest.other_current_liabilities == 1000000000
    assert latest.total_current_liabilities == 24050000000

    assert latest.long_term_borrowing == 914400000
    assert latest.fi_bond_payable == 2992000000
    assert latest.long_term_payable == 636800000
    assert latest.deferred_tax_liabilities == 314800000
    assert latest.other_non_current_liabilities == 127800000
    assert latest.total_non_current_liabilities == 4986000000
    assert latest.total_liabilities == 29040000000

    assert latest.capital == 3991000000
    assert latest.capital_reserve == 8688000000
    assert latest.special_reserve == 40730000
    assert latest.surplus_reserve == 1286000000
    assert latest.undistributed_profits == 7236000000

    assert latest.equity == 20320000000
    assert latest.equity_as_minority_interest == 997400000
    assert latest.total_equity == 21320000000
    assert latest.total_liabilities_and_equity == 50350000000


# 企业利润表
def test_000778_income_statement():
    correct_timestamps = ['2018-09-30', '2018-06-30', '2018-03-31', '2017-12-31', '2017-09-30', '2017-06-30',
                          '2017-03-31', '2016-12-31', '2016-09-30', '2016-06-30', '2016-03-31', '2015-12-31',
                          '2015-09-30', '2015-06-30', '2015-03-31', '2014-12-31', '2014-09-30', '2014-06-30',
                          '2014-03-31', '2013-12-31', '2013-09-30', '2013-06-30', '2013-03-31', '2012-12-31',
                          '2012-09-30', '2012-06-30', '2012-03-31', '2011-12-31', '2011-09-30', '2011-06-30',
                          '2011-03-31', '2010-12-31', '2010-09-30', '2010-06-30', '2010-03-31', '2009-12-31',
                          '2009-09-30', '2009-06-30', '2009-03-31', '2008-12-31', '2008-09-30', '2008-06-30',
                          '2008-03-31', '2007-12-31', '2007-09-30', '2007-06-30', '2007-03-31', '2006-12-31',
                          '2006-09-30', '2006-06-30', '2006-03-31', '2005-12-31', '2005-09-30', '2005-06-30',
                          '2005-03-31', '2004-12-31', '2004-09-30', '2004-06-30', '2004-03-31', '2003-12-31',
                          '2003-09-30', '2003-06-30', '2003-03-31', '2002-12-31', '2002-09-30', '2002-06-30',
                          '2002-03-31', '2001-12-31', '2001-06-30', '2000-12-31', '2000-06-30', '1999-12-31',
                          '1999-06-30', '1998-12-31', '1998-06-30', '1997-12-31', '1997-06-30', '1996-12-31',
                          '1995-12-31', '1994-12-31']
    result = IncomeStatement.query_data(session=session, provider='eastmoney', return_type='domain',
                                        codes=['000778'], end_timestamp='2018-12-30',
                                        order=IncomeStatement.report_date.desc(), time_field='report_date')
    assert len(correct_timestamps) == len(result)
    timestamps = [to_time_str(item.report_date) for item in result]
    assert set(correct_timestamps) == set(timestamps)
    latest: IncomeStatement = result[0]

    assert latest.operating_income == 31710000000
    assert latest.total_operating_costs == 29230000000
    assert latest.operating_costs == 26220000000
    assert latest.rd_costs == 185500000
    assert latest.net_change_in_insurance_contract_reserves == 0
    assert latest.business_taxes_and_surcharges == 359700000
    assert latest.sales_costs == 771400000
    assert latest.managing_costs == 472900000
    assert latest.financing_costs == 397500000
    assert latest.assets_devaluation == 824400000
    assert latest.investment_income == 104100000
    assert latest.investment_income_from_related_enterprise == 61290000

    assert latest.operating_profit == 2637000000
    assert latest.non_operating_income == 38340000
    assert latest.non_operating_costs == 221700000

    assert latest.total_profits == 2454000000
    assert latest.tax_expense == 579600000
    assert latest.net_profit == 1874000000
    assert latest.net_profit_as_parent == 1811000000
    assert latest.net_profit_as_minority_interest == 63570000
    assert latest.deducted_net_profit == 1897000000

    assert latest.eps == 0.4537
    assert latest.diluted_eps == 0.4537

    assert latest.other_comprehensive_income == -521000000
    assert latest.other_comprehensive_income_as_parent == -522400000
    assert latest.other_comprehensive_income_as_minority_interest == 1403000
    assert latest.total_comprehensive_income == 1353000000
    assert latest.total_comprehensive_income_as_parent == 1288000000
    assert latest.total_comprehensive_income_as_minority_interest == 64980000


# 银行现金流量表
def test_000778_cash_flow_statement():
    correct_timestamps = ['2018-09-30', '2018-06-30', '2018-03-31', '2017-12-31', '2017-09-30', '2017-06-30',
                          '2017-03-31', '2016-12-31', '2016-09-30', '2016-06-30', '2016-03-31', '2015-12-31',
                          '2015-09-30', '2015-06-30', '2015-03-31', '2014-12-31', '2014-09-30', '2014-06-30',
                          '2014-03-31', '2013-12-31', '2013-09-30', '2013-06-30', '2013-03-31', '2012-12-31',
                          '2012-09-30', '2012-06-30', '2012-03-31', '2011-12-31', '2011-09-30', '2011-06-30',
                          '2011-03-31', '2010-12-31', '2010-09-30', '2010-06-30', '2010-03-31', '2009-12-31',
                          '2009-09-30', '2009-06-30', '2009-03-31', '2008-12-31', '2008-09-30', '2008-06-30',
                          '2008-03-31', '2007-12-31', '2007-09-30', '2007-06-30', '2007-03-31', '2006-12-31',
                          '2006-09-30', '2006-06-30', '2006-03-31', '2005-12-31', '2005-09-30', '2005-06-30',
                          '2005-03-31', '2004-12-31', '2004-09-30', '2004-06-30', '2004-03-31', '2003-12-31',
                          '2003-09-30', '2003-06-30', '2003-03-31', '2002-12-31', '2002-06-30', '2001-12-31',
                          '2001-06-30', '2000-12-31', '2000-06-30', '1999-12-31', '1998-12-31', '1998-06-30']
    result = CashFlowStatement.query_data(session=session, provider='eastmoney', return_type='domain',
                                          codes=['000778'], end_timestamp='2018-12-30',
                                          order=CashFlowStatement.report_date.desc(), time_field='report_date')
    assert len(correct_timestamps) == len(result)
    timestamps = [to_time_str(item.report_date) for item in result]
    assert set(correct_timestamps) == set(timestamps)
    latest: CashFlowStatement = result[0]

    assert latest.cash_from_selling == 27784000000
    assert latest.tax_refund == 60700000
    assert latest.cash_from_other_op == 1463000000
    assert latest.total_op_cash_inflows == 29310000000
    assert latest.cash_to_goods_services == 21210000000
    assert latest.cash_to_employees == 1460000000
    assert latest.taxes_and_surcharges == 2016000000
    assert latest.cash_to_other_related_op == 573700000
    assert latest.total_op_cash_outflows == 25260000000
    assert latest.net_op_cash_flows == 4050000000

    assert latest.cash_from_disposal_of_investments == 556500000
    assert latest.cash_from_returns_on_investments == 44180000
    assert latest.cash_from_disposal_fixed_intangible_assets == 457200
    assert latest.cash_from_disposal_subsidiaries == 1046000000
    assert latest.cash_from_other_investing == 553000000
    assert latest.total_investing_cash_inflows == 2201000000
    assert latest.cash_to_acquire_fixed_intangible_assets == 2521000000
    assert latest.cash_to_investments == 1808000000
    assert latest.total_investing_cash_outflows == 4329000000
    assert latest.net_investing_cash_flows == -2128000000

    assert latest.cash_from_accepting_investment == 24500000
    assert latest.cash_from_subsidiaries_accepting_minority_interest == 24500000
    assert latest.cash_from_borrowings == 10080000000
    assert latest.cash_from_issuing_bonds == 997000000
    assert latest.cash_from_other_financing == 200000000
    assert latest.total_financing_cash_inflows == 11300000000
    assert latest.cash_to_repay_borrowings == 11940000000
    assert latest.cash_to_pay_interest_dividend == 892100000
    assert latest.cash_to_other_financing == 328500000
    assert latest.total_financing_cash_outflows == 13160000000
    assert latest.net_financing_cash_flows == -1862000000

    assert latest.foreign_exchange_rate_effect == 21350000
    assert latest.net_cash_increase == 81240000
    assert latest.cash_at_beginning == 5078000000
    assert latest.cash == 5159000000
