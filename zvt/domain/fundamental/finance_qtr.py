# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base

from zvt.contract import Mixin
from zvt.contract.register import register_schema

FinanceQtrBase = declarative_base()


class IncomeStatementQtr(FinanceQtrBase, Mixin):

    @classmethod
    def important_cols(cls):
        return ['operating_income', 'investment_income', 'total_operating_costs', 'total_profits', 'sales_costs',
                'managing_costs', 'financing_costs']

    __tablename__ = 'income_statement_qtr'

    provider = Column(String(length=32))
    code = Column(String(length=32))

    report_period = Column(String(length=32))
    # 报告时间
    report_date = Column(DateTime)
    # 更新时间
    pub_date = Column(DateTime)

    # 营业总收入(元)
    total_op_income = Column(Float)
    # 营业收入
    operating_income = Column(Float)
    # 营业总成本
    total_operating_costs = Column(Float)
    # 营业成本
    operating_costs = Column(Float)

    # 提取保险合同准备金净额
    net_change_in_insurance_contract_reserves = Column(Float)
    # 营业税金及附加
    business_taxes_and_surcharges = Column(Float)
    # 销售费用
    sales_costs = Column(Float)
    # 管理费用
    managing_costs = Column(Float)
    # 财务费用
    financing_costs = Column(Float)
    # 资产减值损失
    assets_devaluation = Column(Float)
    # 其他经营收益

    # 加: 投资收益
    investment_income = Column(Float)
    # 其中: 对联营企业和合营企业的投资收益
    investment_income_from_related_enterprise = Column(Float)
    # 营业利润
    operating_profit = Column(Float)
    # 加: 营业外收入
    non_operating_income = Column(Float)
    # 减: 营业外支出
    non_operating_costs = Column(Float)
    # 其中: 非流动资产处置净损失
    loss_on_disposal_non_current_asset = Column(Float)
    # 利润总额
    total_profits = Column(Float)
    # 减: 所得税费用
    tax_expense = Column(Float)
    # 净利润
    net_profit = Column(Float)
    # 其中: 归属于母公司股东的净利润
    net_profit_as_parent = Column(Float)
    # 少数股东损益
    net_profit_as_minority_interest = Column(Float)
    # 其他综合收益
    other_comprehensive_income = Column(Float)
    # 综合收益总额
    total_comprehensive_income = Column(Float)
    # 归属于母公司所有者的综合收益总额
    total_comprehensive_income_as_parent = Column(Float)
    # 归属于少数股东的综合收益总额
    total_comprehensive_income_as_minority_interest = Column(Float)

    # 已赚保费(元)
    fi_net_income_from_premium = Column(Float)
    # 手续费及佣金收入
    fi_incomes_from_fees_and_commissions = Column(Float)
    # 利息收入(元)
    fi_interest_income = Column(Float)
    # 利息支出(元)
    fi_interest_expenses = Column(Float)
    # 手续费及佣金支出(元)
    fi_expenses_for_fees_and_commissions = Column(Float)
    # 退保金(元)
    fi_insurance_surrender_costs = Column(Float)
    # 赔付支出净额(元)
    fi_net_payouts = Column(Float)
    # 保单红利支出(元)
    fi_dividend_expenses_to_insured = Column(Float)
    # 分保费用
    fi_reinsurance_expenses = Column(Float)
    # 公允价值变动收益(损失以“-”号填列)
    fi_income_from_fair_value_change = Column(Float)
    # 汇兑收益(损失以“-”号填列)
    fi_income_from_exchange = Column(Float)
    # 资产处置收益
    fi_asset_disposal_income = Column(Float)
    # 其他收益
    fi_other_income = Column(Float)
    # 持续经营净利润
    fi_net_profit_continuing_operations = Column(Float)
    # 终止经营净利润
    fi_iscontinued_operating_net_profit = Column(Float)


class CashFlowStatementQtr(FinanceQtrBase, Mixin):
    """
    单季度_现金流量表
    """
    @classmethod
    def important_cols(cls):
        return []

    __tablename__ = 'cash_flow_statement_qtr'

    provider = Column(String(length=32))
    code = Column(String(length=32))

    report_period = Column(String(length=32))
    report_date = Column(DateTime)
    pub_date = Column(DateTime)
    # 经营活动产生的现金流量
    #
    # 销售商品、提供劳务收到的现金
    cash_from_selling = Column(Float)

    # 收到的税费返还
    tax_refund = Column(Float)

    # 收到其他与经营活动有关的现金
    cash_from_other_op = Column(Float)

    # 经营活动现金流入小计
    total_op_cash_inflows = Column(Float)

    # 购买商品、接受劳务支付的现金
    cash_to_goods_services = Column(Float)
    # 支付给职工以及为职工支付的现金
    cash_to_employees = Column(Float)
    # 支付的各项税费
    taxes_and_surcharges = Column(Float)
    # 支付其他与经营活动有关的现金
    cash_to_other_related_op = Column(Float)
    # 经营活动现金流出小计
    total_op_cash_outflows = Column(Float)

    # 经营活动产生的现金流量净额
    net_op_cash_flows = Column(Float)

    # 投资活动产生的现金流量

    # 收回投资收到的现金
    cash_from_disposal_of_investments = Column(Float)
    # 取得投资收益收到的现金
    cash_from_returns_on_investments = Column(Float)
    # 处置固定资产、无形资产和其他长期资产收回的现金净额
    cash_from_disposal_fixed_intangible_assets = Column(Float)
    # 处置子公司及其他营业单位收到的现金净额
    cash_from_disposal_subsidiaries = Column(Float)

    # 收到其他与投资活动有关的现金
    cash_from_other_investing = Column(Float)
    # 质押贷款净增加额
    fi_insured_pledge_loans_increase = Column(Float)
    # 投资活动现金流入小计
    total_investing_cash_inflows = Column(Float)

    # 购建固定资产、无形资产和其他长期资产支付的现金
    cash_to_acquire_fixed_intangible_assets = Column(Float)
    # 投资支付的现金
    cash_to_investments = Column(Float)

    # 取得子公司及其他营业单位支付的现金净额
    cash_to_acquire_subsidiaries = Column(Float)

    # 支付其他与投资活动有关的现金
    cash_to_other_investing = Column(Float)

    # 投资活动现金流出小计
    total_investing_cash_outflows = Column(Float)

    # 投资活动产生的现金流量净额
    net_investing_cash_flows = Column(Float)
    # 支付保单红利的现金
    fi_cash_to_dividends = Column(Float)
    # 筹资活动产生的现金流量
    # 吸收投资收到的现金
    cash_from_accepting_investment = Column(Float)
    # 子公司吸收少数股东投资收到的现金
    cash_from_subsidiaries_accepting_minority_interest = Column(Float)
    # 取得借款收到的现金
    cash_from_borrowings = Column(Float)
    # 发行债券收到的现金
    cash_from_issuing_bonds = Column(Float)
    # 收到其他与筹资活动有关的现金
    cash_from_other_financing = Column(Float)
    # 筹资活动现金流入小计
    total_financing_cash_inflows = Column(Float)
    # 偿还债务支付的现金
    cash_to_repay_borrowings = Column(Float)
    # 分配股利、利润或偿付利息支付的现金
    cash_to_pay_interest_dividend = Column(Float)
    # 子公司支付给少数股东的股利、利润
    cash_to_pay_subsidiaries_minority_interest = Column(Float)
    # 支付其他与筹资活动有关的现金
    cash_to_other_financing = Column(Float)
    # 筹资活动现金流出小计
    total_financing_cash_outflows = Column(Float)
    # 筹资活动产生的现金流量净额
    net_financing_cash_flows = Column(Float)
    # 汇率变动对现金及现金等价物的影响
    foreign_exchange_rate_effect = Column(Float)
    # 现金及现金等价物净增加额
    net_cash_increase = Column(Float)
    # 加: 期初现金及现金等价物余额
    cash_at_beginning = Column(Float)
    # 期末现金及现金等价物余额
    cash = Column(Float)

    # 客户存款和同业及其他金融机构存放款项净增加额
    fi_deposit_increase = Column(Float)
    # 向中央银行借款净增加额
    fi_borrow_from_central_bank_increase = Column(Float)
    # 拆入资金净增加额
    fi_borrowing_increase = Column(Float)
    # 回购业务资金净增加额
    fi_cash_from_repurchase_increase = Column(Float)

    # 收取利息、手续费及佣金的现金
    fi_cash_from_interest_commission = Column(Float)

    # 保户储金及投资款净增加额
    fi_insured_deposit_increase = Column(Float)
    # 收到再保险业务现金净额
    fi_cash_from_reinsurance = Column(Float)

    # 保险相关
    # 收到原保险合同保费取得的现金
    fi_cash_from_premium_of_original = Column(Float)
    # 向其他金融机构拆入资金净增加额
    fi_lending_from_increase = Column(Float)
    # 处置交易性金融资产净增加额
    fi_disposal_trade_asset_add = Column(Float)
    # 客户贷款及垫款净增加额
    fi_loan_advance_increase = Column(Float)
    # 存放中央银行和同业款项及其他金融机构净增加额
    fi_deposit_in_others_add = Column(Float)
    # 支付原保险合同赔付等款项的现金
    fi_cash_to_insurance_claim = Column(Float)
    # 支付利息、手续费及佣金的现金
    fi_cash_to_interest_commission = Column(Float)


register_schema(providers=['emquantapi','joinquant'], db_name='finance_qtr', schema_base=FinanceQtrBase)

__all__ = ['IncomeStatementQtr', 'CashFlowStatementQtr']
