# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, DateTime, Float, Integer
from sqlalchemy.ext.declarative import declarative_base

from zvt.contract import Mixin
from zvt.contract.register import register_schema

FinanceBase = declarative_base()

# 资产负债表
class BalanceSheet(FinanceBase, Mixin):

    @classmethod
    def important_cols(cls):
        return ['total_assets', 'total_liabilities', 'equity', 'cash_and_cash_equivalents', 'accounts_receivable',
                'inventories', 'goodwill']

    __tablename__ = 'balance_sheet'

    provider = Column(String(length=32))
    code = Column(String(length=32))

    report_period = Column(String(length=32))
    report_date = Column(DateTime)
    pub_date = Column(DateTime)

    # 流动资产
    #
    # 货币资金
    cash_and_cash_equivalents = Column(Float)
    # 应收票据
    note_receivable = Column(Float)
    # 应收账款
    accounts_receivable = Column(Float)
    # 预付款项
    advances_to_suppliers = Column(Float)
    # 其他应收款
    other_receivables = Column(Float)
    # 存货
    inventories = Column(Float)
    # 一年内到期的非流动资产
    current_portion_of_non_current_assets = Column(Float)
    # 其他流动资产
    other_current_assets = Column(Float)
    # 流动资产合计
    total_current_assets = Column(Float)
    # 非流动资产
    #
    # 可供出售金融资产
    fi_assets_saleable = Column(Float)
    # 长期应收款
    long_term_receivables = Column(Float)
    # 长期股权投资
    long_term_equity_investment = Column(Float)
    # 投资性房地产
    real_estate_investment = Column(Float)
    # 固定资产
    fixed_assets = Column(Float)
    # 在建工程
    construction_in_process = Column(Float)
    # 无形资产
    intangible_assets = Column(Float)
    # 商誉
    goodwill = Column(Float)
    # 长期待摊费用
    long_term_prepaid_expenses = Column(Float)
    # 递延所得税资产
    deferred_tax_assets = Column(Float)
    # 其他非流动资产
    other_non_current_assets = Column(Float)
    # 非流动资产合计
    total_non_current_assets = Column(Float)
    # 资产总计
    total_assets = Column(Float)
    # 流动负债
    #
    # 短期借款
    short_term_borrowing = Column(Float)
    # 吸收存款及同业存放
    accept_money_deposits = Column(Float)
    # 应付账款
    accounts_payable = Column(Float)
    # 预收款项
    advances_from_customers = Column(Float)
    # 应付职工薪酬
    employee_benefits_payable = Column(Float)
    # 应交税费
    taxes_payable = Column(Float)
    # 应付利息
    interest_payable = Column(Float)
    # 其他应付款
    other_payable = Column(Float)
    # 一年内到期的非流动负债
    current_portion_of_non_current_liabilities = Column(Float)
    # 其他流动负债
    other_current_liabilities = Column(Float)
    # 流动负债合计
    total_current_liabilities = Column(Float)
    # 非流动负债
    #
    # 长期借款
    long_term_borrowing = Column(Float)
    # 长期应付款
    long_term_payable = Column(Float)
    # 递延收益
    deferred_revenue = Column(Float)
    # 递延所得税负债
    deferred_tax_liabilities = Column(Float)
    # 其他非流动负债
    other_non_current_liabilities = Column(Float)
    # 非流动负债合计
    total_non_current_liabilities = Column(Float)
    # 负债合计
    total_liabilities = Column(Float)
    # 所有者权益(或股东权益)
    #
    # 实收资本（或股本）
    capital = Column(Float)
    # 资本公积
    capital_reserve = Column(Float)
    # 专项储备
    special_reserve = Column(Float)
    # 盈余公积
    surplus_reserve = Column(Float)
    # 未分配利润
    undistributed_profits = Column(Float)
    # 归属于母公司股东权益合计
    equity = Column(Float)
    # 少数股东权益
    equity_as_minority_interest = Column(Float)
    # 股东权益合计
    total_equity = Column(Float)
    # 负债和股东权益合计
    total_liabilities_and_equity = Column(Float)

    # 银行相关
    # 资产
    # 现金及存放中央银行款项
    fi_cash_and_deposit_in_central_bank = Column(Float)
    # 存放同业款项
    fi_deposit_in_other_fi = Column(Float)
    # 贵金属
    fi_expensive_metals = Column(Float)
    # 拆出资金
    fi_lending_to_other_fi = Column(Float)
    # 以公允价值计量且其变动计入当期损益的金融资产
    fi_financial_assets_effect_current_income = Column(Float)
    # 衍生金融资产
    fi_financial_derivative_asset = Column(Float)
    # 买入返售金融资产
    fi_buying_sell_back_fi__asset = Column(Float)
    # 应收账款
    #
    # 应收利息
    fi_interesfi_retained_earningsceivable = Column(Float)
    # 发放贷款及垫款
    fi_disbursing_loans_and_advances = Column(Float)
    # 可供出售金融资产
    #
    # 持有至到期投资
    fi_held_to_maturity_investment = Column(Float)
    # 应收款项类投资
    fi_accounfi_retained_earningsceivable_investment = Column(Float)
    # 投资性房地产
    #
    # 固定资产

    # 其他资产
    fi_other_asset = Column(Float)

    # 向中央银行借款
    fi_borrowings_from_central_bank = Column(Float)
    # 同业和其他金融机构存放款项
    fi_deposit_from_other_fi = Column(Float)
    # 拆入资金
    fi_borrowings_from_fi = Column(Float)
    # 以公允价值计量且其变动计入当期损益的金融负债
    fi_financial_liability_effect_current_income = Column(Float)
    # 衍生金融负债
    fi_financial_derivative_liability = Column(Float)
    # 卖出回购金融资产款
    fi_sell_buy_back_fi_asset = Column(Float)
    # 吸收存款
    fi_savings_absorption = Column(Float)
    # 存款证及应付票据
    fi_notes_payable = Column(Float)

    # 预计负债
    fi_estimated_liabilities = Column(Float)
    # 应付债券
    fi_bond_payable = Column(Float)
    # 其他负债
    fi_other_liability = Column(Float)

    # 所有者权益(或股东权益)
    # 股本
    fi_capital = Column(Float)
    # 其他权益工具
    fi_other_equity_instruments = Column(Float)
    # 其中:优先股
    fi_preferred_stock = Column(Float)

    # 一般风险准备
    fi_generic_risk_reserve = Column(Float)

    # 其中: 客户资金存款
    fi_client_fund = Column(Float)
    # 结算备付金
    fi_deposifi_retained_earningsservation_for_balance = Column(Float)
    # 其中: 客户备付金
    fi_client_deposifi_retained_earningsservation_for_balance = Column(Float)
    # 融出资金
    fi_margin_out_fund = Column(Float)

    # 应收款项
    fi_receivables = Column(Float)
    # 存出保证金
    fi_deposit_for_recognizance = Column(Float)


    # 代理买卖证券款
    fi_receiving_as_agent = Column(Float)
    # 应付短期融资款
    fi_short_financing_payable = Column(Float)
    # 交易风险准备
    fi_trade_risk_reserve = Column(Float)

    # 资产
    # 应收保费
    fi_premiums_receivable = Column(Float)
    # 应收分保账款
    fi_reinsurance_premium_receivable = Column(Float)
    # 应收分保合同准备金
    fi_reinsurance_contracfi_retained_earningsserve = Column(Float)
    # 保户质押贷款
    fi_policy_pledge_loans = Column(Float)
    # 发放贷款及垫款
    # 定期存款
    fi_time_deposit = Column(Float)
    # 存出资本保证金
    fi_deposit_for_capital_recognizance = Column(Float)

    # 独立账户资产
    fi_capital_in_independent_accounts = Column(Float)

    #
    # 预收账款
    fi_advance_from_customers = Column(Float)
    # 预收保费
    fi_advance_premium = Column(Float)
    # 应付手续费及佣金
    fi_fees_and_commissions_payable = Column(Float)
    # 应付分保账款
    fi_dividend_payable_for_reinsurance = Column(Float)
    # 应付职工薪酬
    #

    #
    # 应付赔付款
    fi_claims_payable = Column(Float)
    # 应付保单红利
    fi_policy_holder_dividend_payable = Column(Float)
    # 保户储金及投资款
    fi_policy_holder_deposits_and_investment_funds = Column(Float)
    # 保险合同准备金
    fi_contracfi_retained_earningsserve = Column(Float)
    # 长期借款
    #
    # 应付债券
    #
    # 递延所得税负债
    #
    # 其他负债
    #
    # 独立账户负债
    fi_independent_liability = Column(Float)
    #
    # 应收股利	其中 应收股利(元)
    fi_dividend_rec = Column(Float)
    # 股东权益合计 所有者权益(或股东权益)合计
    fi_perpetual_bond = Column(Float)
    # 减 = Column(Float)库存股
    fi_inventory_share = Column(Float)
    # 其他综合收益
    other_comprehensive_income = Column(Float)
    # 外币报表折算差额		外币报表折算差额(元)
    fi_diffconversionfc = Column(Float)
    # 归属于母公司所有者权益的调整项目	 归属于母公司股东权益其他项目(元)
    fi_parent_equity_other = Column(Float)
    # 归属于母公司所有者权益的差错金额	 归属于母公司股东权益平衡项目(元)
    fi_parent_equity_balance = Column(Float)
    # 所有者权益的调整项目  股东权益其他项目(元)
    fi_sh_equity_other = Column(Float)
    # 所有者权益的差错金额	股东权益平衡项目(元)
    fi_sh_equity_balance = Column(Float)
    # 应付债券
    # 负债和权益的调整项目	负债和股东权益其他项目(元)
    fi_liab_sh_equity_other = Column(Float)

    # 负债和权益的差错金额	负债和股东权益平衡项目(元)
    fi_liab_sh_equity_balance = Column(Float)
    # 结算备付金
    # 交易性金融资产		交易性金融资产
    fi_trade_finasset_notfvtpl = Column(Float)
    # 衍生金融资产
    # 应收保费
    # 应收分保账款
    # 应收分保合同准备金
    # 买入返售金融资产
    # 流动资产的调整项目		流动资产其他项目(元)
    fi_lasset_other = Column(Float)
    # 流动资产的差错金额		流动资产平衡项目(元)
    fi_lasset_balance = Column(Float)
    # 发放委托贷款及垫款		发放委托贷款及垫款(元)	LOANADVANCES
    fi_loan_advances = Column(Float)

    # 工程物资	工程物资(元)
    fi_construction_material = Column(Float)
    # 固定资产清理	固定资产清理(元)
    fi_liquidate_fixed_asset = Column(Float)
    # 生产性生物资产		生产性生物资产(元)
    fi_product_biology_asset = Column(Float)
    # 油气资产	油气资产(元)
    fi_oil_gas_asset = Column(Float)
    # 研发支出		开发支出(元)
    fi_develop_exp = Column(Float)
    # 非流动资产的调整项目		非流动资产其他项目(元)
    fi_nonl_asset_other = Column(Float)
    # 非流动资产的差错金额		非流动资产平衡项目(元)
    fi_nonl_asset_balance = Column(Float)
    # 资产的调整项目		资产其他项目(元)
    fi_asset_other = Column(Float)
    # 资产的差错金额		资产平衡项目(元)
    fi_asset_balance = Column(Float)
    # 向中央银行借款
    # 拆入资金
    # 交易性金融负债		交易性金融负债
    fi_trade_finliab_notfvtpl = Column(Float)
    # 衍生金融负债
    # 存款证及应付票据  应付票据
    # 卖出回购金融资产款
    # 应付手续费及佣金
    # 应付股利		其中 应付股利(元)
    fi_dividend_payable = Column(Float)
    # 代理买卖证券款
    # 代理承销证券款		代理承销证券款(元)
    fi_agentuw_security = Column(Float)
    # 流动负债的调整项目		流动负债其他项目(元)
    fi_lliab_other = Column(Float)
    # 流动负债的差错金额		流动负债平衡项目(元)
    fi_lliab_balance = Column(Float)
    # 专项应付款		专项应付款(元)
    fi_special_pay = Column(Float)
    # 非流动负债的调整项目		非流动负债其他项目(元)
    fi_non_liab_other = Column(Float)
    # 非流动负债的差错金额		非流动负债平衡项目(元)
    fi_non_liab_balance = Column(Float)
    # 负债的调整项目		负债其他项目(元)
    fi_liab_other = Column(Float)
    # 负债的差错金额		负债平衡项目(元)
    fi_liab_balance = Column(Float)

# 利润表
class IncomeStatement(FinanceBase, Mixin):

    @classmethod
    def important_cols(cls):
        return ['operating_income', 'investment_income', 'total_operating_costs', 'total_profits', 'sales_costs',
                'managing_costs', 'financing_costs']

    __tablename__ = 'income_statement'

    provider = Column(String(length=32))
    code = Column(String(length=32))

    report_period = Column(String(length=32))
    report_date = Column(DateTime)
    pub_date = Column(DateTime)
    # 营业总收入
    #
    # 营业收入
    operating_income = Column(Float)
    # 营业总成本
    total_operating_costs = Column(Float)
    # 营业成本
    operating_costs = Column(Float)
    # 研发费用
    rd_costs = Column(Float)
    # 提取保险合同准备金净额
    net_change_in_insurance_contracfi_retained_earningsserves = Column(Float)
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
    #
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
    # 扣除非经常性损益后的净利润
    deducted_net_profit = Column(Float)
    # 每股收益
    # 基本每股收益
    eps = Column(Float)
    # 稀释每股收益
    diluted_eps = Column(Float)
    # 其他综合收益
    other_comprehensive_income = Column(Float)
    # 归属于母公司股东的其他综合收益
    other_comprehensive_income_as_parent = Column(Float)
    # 归属于少数股东的其他综合收益
    other_comprehensive_income_as_minority_interest = Column(Float)
    # 综合收益总额
    total_comprehensive_income = Column(Float)
    # 归属于母公司所有者的综合收益总额
    total_comprehensive_income_as_parent = Column(Float)
    # 归属于少数股东的综合收益总额
    total_comprehensive_income_as_minority_interest = Column(Float)

    # 银行相关
    # 利息净收入
    fi_net_interest_income = Column(Float)
    # 其中:利息收入
    fi_interest_income = Column(Float)
    # 利息支出
    fi_interest_expenses = Column(Float)
    # 手续费及佣金净收入
    fi_net_incomes_from_fees_and_commissions = Column(Float)
    # 其中:手续费及佣金收入
    fi_incomes_from_fees_and_commissions = Column(Float)
    # 手续费及佣金支出
    fi_expenses_for_fees_and_commissions = Column(Float)
    # 公允价值变动收益
    fi_income_from_fair_value_change = Column(Float)
    # 汇兑收益
    fi_income_from_exchange = Column(Float)
    # 其他业务收入
    fi_other_income = Column(Float)
    # 业务及管理费
    fi_operate_and_manage_expenses = Column(Float)

    # 保险相关
    # 已赚保费
    fi_net_income_from_premium = Column(Float)
    # 其中:保险业务收入
    fi_income_from_premium = Column(Float)
    # 分保费收入
    fi_income_from_reinsurance_premium = Column(Float)
    # 减:分出保费
    fi_reinsurance_premium = Column(Float)
    # 提取未到期责任准备金
    fi_undue_duty_reserve = Column(Float)
    # 银行业务利息净收入
    fi_net_income_from_bank_interest = Column(Float)
    # 其中:银行业务利息收入
    fi_income_from_bank_interest = Column(Float)
    # 银行业务利息支出
    fi_expenses_for_bank_interest = Column(Float)
    # 非保险业务手续费及佣金净收入
    fi_net_incomes_from_fees_and_commissions_of_non_insurance = Column(Float)
    # 非保险业务手续费及佣金收入
    fi_incomes_from_fees_and_commissions_of_non_insurance = Column(Float)
    # 非保险业务手续费及佣金支出
    fi_expenses_for_fees_and_commissions_of_non_insurance = Column(Float)
    # 退保金
    fi_insurance_surrender_costs = Column(Float)
    # 赔付支出
    fi_insurance_claims_expenses = Column(Float)
    # 减:摊回赔付支出
    fi_amortized_insurance_claims_expenses = Column(Float)
    # 提取保险责任准备金
    fi_insurance_duty_reserve = Column(Float)
    # 减:摊回保险责任准备金
    fi_amortized_insurance_duty_reserve = Column(Float)
    # 保单红利支出
    fi_dividend_expenses_to_insured = Column(Float)
    # 分保费用
    fi_reinsurance_expenses = Column(Float)
    # 减:摊回分保费用
    fi_amortized_reinsurance_expenses = Column(Float)
    # 其他业务成本
    fi_other_op_expenses = Column(Float)

    # 券商相关
    # 手续费及佣金净收入
    #
    # 其中:代理买卖证券业务净收入
    fi_net_incomes_from_trading_agent = Column(Float)
    # 证券承销业务净收入
    fi_net_incomes_from_underwriting = Column(Float)
    # 受托客户资产管理业务净收入
    fi_net_incomes_from_customer_asset_management = Column(Float)
    # 手续费及佣金净收入其他项目
    fi_fees_from_other = Column(Float)
    # 公允价值变动收益
    #
    # 其中:可供出售金融资产公允价值变动损益
    fi_income_from_fair_value_change_of_fi_salable = Column(Float)

# 现金流量表
class CashFlowStatement(FinanceBase, Mixin):
    @classmethod
    def important_cols(cls):
        return ['net_op_cash_flows', 'net_investing_cash_flows', 'net_financing_cash_flows', 'cash']

    __tablename__ = 'cash_flow_statement'

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
    # 质押贷款净增加额
    fi_insured_pledge_loans_increase = Column(Float)
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
    # 处置固定资产、无形资产和其他长期资产收回的现金净额
    cash_from_disposal_fixed_intangible_assets = Column(Float)
    # 投资活动产生的现金流量

    # 收回投资收到的现金
    cash_from_disposal_of_investments = Column(Float)
    # 取得投资收益收到的现金
    cash_from_returns_on_investments = Column(Float)

    # 处置子公司及其他营业单位收到的现金净额
    cash_from_disposal_subsidiaries = Column(Float)

    # 收到其他与投资活动有关的现金
    cash_from_other_investing = Column(Float)

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

    # 筹资活动产生的现金流量
    #
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
    # 加:期初现金及现金等价物余额
    cash_at_beginning = Column(Float)
    # 期末现金及现金等价物余额
    cash = Column(Float)
    # 客户存款和同业及其他金融机构存放款项净增加额
    # 客户存款和同业存放款项净增加额
    fi_deposit_increase = Column(Float)
    # 支付保单红利的现金
    fi_cash_to_dividends = Column(Float)
    # 向中央银行借款净增加额
    fi_borrow_from_central_bank_increase = Column(Float)
    # 向其他金融机构拆入资金净增加额
    fi_lending_from_increase = Column(Float)
    # 收到原保险合同保费取得的现金
    fi_cash_from_premium_of_original = Column(Float)
    # 收到再保险业务现金净额
    fi_cash_from_reinsurance = Column(Float)
    # 保户储金及投资款净增加额
    fi_insured_deposit_increase = Column(Float)

    # 处置交易性金融资产净增加额
    fi_disposal_trade_asset_add = Column(Float)
    # 客户贷款及垫款净增加额
    fi_loan_advance_increase = Column(Float)
    # 存放中央银行和同业款项净增加
    fi_deposit_in_others_add = Column(Float)
    # 支付原保险合同赔付款项的现金
    fi_cash_to_insurance_claim = Column(Float)
    # 支付利息、手续费及佣金的现金
    fi_cash_to_interest_commission = Column(Float)
    # 收取的利息、手续费及佣金的现金 收取利息、手续费及佣金的现金
    fi_cash_from_interest_commission = Column(Float)
    # 拆入资金净增加额
    fi_borrowing_increase = Column(Float)
    # 回购业务资金净增加额
    fi_cash_from_repurchase_increase = Column(Float)

    # 经营活动现金流入的调整项目
    # 经营活动现金流入的其他项目
    fi_operate_flow_inother = Column(Float)

    # 经营活动现金流入的差错金额
    # 经营活动现金流入的平衡项目(元)
    fi_operate_flow_in_balance = Column(Float)
    # 经营活动现金流量净额的差错金额
    # 经营活动产生的现金流量净额其他项目(元)
    fi_operate_flow_other = Column(Float)

    # 投资活动现金流入的调整项目
    # 投资活动现金流入的其他项目(元)
    fi_inv_flow_in_other = Column(Float)
    # 投资活动现金流入的差错金额
    # 投资活动现金流入的平衡项目(元)
    fi_inv_flow_in_balance = Column(Float)

    # 投资活动现金流出的调整项目
    # 投资活动现金流出的其他项目(元)
    fi_inv_flow_out_other = Column(Float)
    # 投资活动现金流出的差错金额
    # 投资活动现金流出的平衡项目(元)
    fi_inv_flow_out_balance = Column(Float)

    # 投资活动现金流量净额的差错金额
    # 投资活动产生的现金流量净额其他项目(元)
    fi_inv_flow_other = Column(Float)

    # 筹资活动现金流入的调整项目
    # 筹资活动现金流入的其他项目(元)
    fi_fina_flow_in_other = Column(Float)

    # 筹资活动现金流入的差错金额
    # 筹资活动现金流入的平衡项目(元)
    fi_fina_flow_in_balance = Column(Float)

    # 筹资活动现金流出的调整项目
    # 其中= Column(Float)子公司减资支付给少数股东的现金(元)
    fi_subsidiary_reduct_capital = Column(Float)
    # 筹资活动现金流出的差错金额
    # 筹资活动现金流出的其他项目(元)
    fi_fina_flow_out_other = Column(Float)

    # 筹资活动现金流量净额的差错金额
    # 筹资活动产生的现金流量净额其他项目(元)
    fi_fina_flow_other = Column(Float)
    # 影响现金及现金等价物的调整项目		现金及现金等价物净增加额其他项目(元)
    fi_ni_cash_equi_other = Column(Float)
    # 影响现金及现金等价物的差错金额		现金及现金等价物净增加额平衡项目(元)
    fi_ni_cash_equi_balance = Column(Float)
    # 影响期末现金及现金等价物余额的调整项目		期末现金及现金等价物余额其他项目(元)
    fi_cash_equi_ending_other = Column(Float)
    # 影响期末现金及现金等价物余额的差错金额		期末现金及现金等价物余额平衡项目(元)
    fi_cash_equi_ending_balance = Column(Float)
    # 经营活动现金流出的调整项目		经营活动现金流出的其他项目(元)	OPERATEFLOWOUTOTHER
    fi_operate_flow_out_other = Column(Float)
    # 经营活动现金流出的差错金额		经营活动现金流出的平衡项目(元)	OPERATEFLOWOUTBALANCE
    fi_operate_flow_out_balance = Column(Float)

    # 银行相关
    # 存放中央银行和同业款项及其他金融机构净减少额
    fi_deposit_in_others_decrease = Column(Float)
    # 拆入资金及卖出回购金融资产款净增加额
    fi_borrowing_and_sell_repurchase_increase = Column(Float)
    # 其中:卖出回购金融资产款净增加额
    fi_sell_repurchase_increase = Column(Float)
    # 拆出资金及买入返售金融资产净减少额
    fi_lending_and_buy_repurchase_decrease = Column(Float)
    # 其中:拆出资金净减少额
    fi_lending_decrease = Column(Float)
    # 买入返售金融资产净减少额
    fi_buy_repurchase_decrease = Column(Float)
    # 存放中央银行和同业及其他金融机构款项净增加额
    fi_deposit_in_others_increase = Column(Float)
    # 拆出资金及买入返售金融资产净增加额
    fi_lending_and_buy_repurchase_increase = Column(Float)
    # 其中:拆出资金净增加额
    fi_lending_increase = Column(Float)
    # 拆入资金及卖出回购金融资产款净减少额
    fi_borrowing_and_sell_repurchase_decrease = Column(Float)
    # 其中:拆入资金净减少额
    fi_borrowing_decrease = Column(Float)
    # 卖出回购金融资产净减少额
    fi_sell_repurchase_decrease = Column(Float)
    # 应收账款净增加额
    fi_accounfi_retained_earningsceivable_increase = Column(Float)
    # 偿付债券利息支付的现金
    fi_cash_to_pay_interest = Column(Float)

    # 保险相关
    # 银行及证券业务卖出回购资金净增加额
    fi_bank_broker_sell_repurchase_increase = Column(Float)
    # 银行及证券业务买入返售资金净减少额
    fi_bank_broker_buy_repurchase_decrease = Column(Float)
    # 支付再保险业务现金净额
    fi_cash_to_reinsurance = Column(Float)
    # 银行业务及证券业务拆借资金净减少额
    # fi_lending_decrease = Column(Float)
    # 银行业务及证券业务卖出回购资金净减少额
    fi_bank_broker_sell_repurchase_decrease = Column(Float)
    # 收购子公司及其他营业单位支付的现金净额
    fi_cash_to_acquire_subsidiaries = Column(Float)
    # 处置子公司及其他营业单位流出的现金净额
    fi_cash_to_disposal_subsidiaries = Column(Float)
    # 支付卖出回购金融资产款现金净额
    fi_cash_to_sell_repurchase = Column(Float)

    # 券商相关
    # 代理买卖证券收到的现金净额
    fi_cash_from_trading_agent = Column(Float)
    # 处置交易性金融资产的净减少额
    fi_disposal_trade_asset_decrease = Column(Float)
    # 回购业务资金净减少额
    fi_repurchase_decrease = Column(Float)
    # 代理买卖证券支付的现金净额（净减少额）
    fi_cash_to_agent_trade = Column(Float)


# 主要财务指标
class FinanceFactor(FinanceBase, Mixin):
    @classmethod
    def important_cols(cls):
        return ['basic_eps', 'total_op_income', 'net_profit', 'total_op_income_growth_yoy', 'inc_net_profit_shareholders_yoy', 'roe',
                'rota', 'fi_gross_margin_margin', 'net_margin']

    __tablename__ = 'finance_factor'

    provider = Column(String(length=32))
    code = Column(String(length=32))

    report_period = Column(String(length=32))
    report_date = Column(DateTime)
    # 每股指标
    #
    # 基本每股收益(元)
    basic_eps = Column(Float)
    # 扣非每股收益(元)
    deducted_eps = Column(Float)
    # 稀释每股收益(元)
    diluted_eps = Column(Float)
    # 每股净资产(元)
    bps = Column(Float)
    # 每股资本公积(元)
    capital_reserve_ps = Column(Float)
    # 每股未分配利润(元)
    undistributed_profit_ps = Column(Float)
    # 每股经营现金流(元)
    op_cash_flow_ps = Column(Float)
    # 成长能力指标
    #
    # 营业总收入(元)
    total_op_income = Column(Float)
    # 毛利润(元)
    fi_gross_margin = Column(Float)
    # 归属净利润(元)
    net_profit = Column(Float)
    # 扣非净利润(元)
    deducted_net_profit = Column(Float)
    # 营业总收入同比增长
    total_op_income_growth_yoy = Column(Float)
    # 归属净利润同比增长
    inc_net_profit_shareholders_yoy = Column(Float)
    # 扣非净利润同比增长
    deducted_net_profit_growth_yoy = Column(Float)
    # 营业总收入滚动环比增长
    op_income_growth_qoq = Column(Float)
    # 归属净利润滚动环比增长
    net_profit_growth_qoq = Column(Float)
    # 扣非净利润滚动环比增长
    deducted_net_profit_growth_qoq = Column(Float)
    # 盈利能力指标
    #
    # 净资产收益率(加权)
    roe = Column(Float)
    # 净资产收益率(扣非/加权)
    deducted_roe = Column(Float)
    # 总资产收益率(加权)
    rota = Column(Float)
    # 毛利率
    fi_gross_margin_margin = Column(Float)
    # 净利率
    net_margin = Column(Float)
    # 收益质量指标
    #
    # 预收账款/营业收入
    advance_receipts_per_op_income = Column(Float)
    # 销售净现金流/营业收入
    sales_net_cash_flow_per_op_income = Column(Float)
    # 经营净现金流/营业收入
    op_net_cash_flow_per_op_income = Column(Float)
    # 实际税率
    actual_tax_rate = Column(Float)
    # 财务风险指标
    #
    # 流动比率
    current_ratio = Column(Float)
    # 速动比率
    quick_ratio = Column(Float)
    # 现金流量比率
    cash_flow_ratio = Column(Float)
    # 资产负债率
    debt_asset_ratio = Column(Float)
    # 权益乘数
    em = Column(Float)
    # 产权比率
    equity_ratio = Column(Float)
    # 营运能力指标(一般企业)
    #
    # 总资产周转天数(天)
    total_assets_turnover_days = Column(Integer)
    # 存货周转天数(天)
    inventory_turnover_days = Column(Integer)
    # 应收账款周转天数(天)
    receivables_turnover_days = Column(Integer)
    # 总资产周转率(次)
    total_assets_turnover = Column(Float)
    # 存货周转率(次)
    inventory_turnover = Column(Float)
    # 应收账款周转率(次)
    receivables_turnover = Column(Float)

    # 专项指标(银行)
    #
    # 存款总额
    fi_total_deposit = Column(Float)
    # 贷款总额
    fi_total_loan = Column(Float)
    # 存贷款比例
    fi_loan_deposit_ratio = Column(Float)
    # 资本充足率
    fi_capital_adequacy_ratio = Column(Float)
    # 核心资本充足率
    fi_core_capital_adequacy_ratio = Column(Float)
    # 不良贷款率
    fi_npl_ratio = Column(Float)
    # 不良贷款拨备覆盖率
    fi_npl_provision_coverage = Column(Float)
    # 资本净额
    fi_net_capital = Column(Float)
    # 专项指标(保险)
    #
    # 总投资收益率
    insurance_roi = Column(Float)
    # 净投资收益率
    insurance_net_investment_yield = Column(Float)
    # 已赚保费
    insurance_earned_premium = Column(Float)
    # 赔付支出
    insurance_payout = Column(Float)
    # 退保率
    insurance_surrender_rate = Column(Float)
    # 偿付能力充足率
    insurance_solvency_adequacy_ratio = Column(Float)
    # 专项指标(券商)
    #
    # 净资本
    broker_net_capital = Column(Float)
    # 净资产
    broker_net_assets = Column(Float)

    # 净资本/净资产
    broker_net_capital_assets_ratio = Column(Float)
    # 自营固定收益类证券规模/净资本
    broker_self_operated_fixed_income_securities_net_capital_ratio = Column(Float)


class FinanceDerivative(FinanceBase, Mixin):
    """
    财务衍生数据
    """
    @classmethod
    def important_cols(cls):
        return ['operating_income', 'investment_income', 'total_operating_costs', 'total_profits', 'sales_costs',
                'managing_costs', 'financing_costs']

    __tablename__ = 'finance_derivative'

    provider = Column(String(length=32))
    code = Column(String(length=32))

    report_period = Column(String(length=32))
    report_date = Column(DateTime)

    fi_interest_free_current_liabilities = Column(Float)  # 无息流动负债
    fi_interest_free_non_current_liabilities = Column(Float)  # 无息非流动负债

    fi_interest_bearing_debt = Column(Float)  # 带息债务
    fi_net_debt = Column(Float)  # 净债务
    fi_tangible_net_assets = Column(Float)  # 有形净资产
    fi_working_capital = Column(Float)  # 营运资本
    fi_net_working_apital = Column(Float)  # 净营运资本

    fi_retained_earnings = Column(Float)  # 留存收益
    fi_gross_margin = Column(Float)  # 毛利
    fi_operate_income = Column(Float)  # 经营活动净收益
    fi_investment_income = Column(Float)  # 价值变动净收益

    fi_ebit = Column(Float)  # 息税前利润
    fi_ebitda = Column(Float)  # 息税折旧摊销前利润

    fi_extraordinary_item = Column(Float)  # 非经常性损益
    fi_deducted_income = Column(Float)  # 扣除非经常性损益后的归属于上市公司股东的净利润
    fi_free_cash_flow_firm = Column(Float)  # 企业自由现金流量
    fi_free_cash_flow_equity = Column(Float)  # 股权自由现金流量
    fi_depreciation_amortization = Column(Float)  # 折旧与摊销
    # INT_CL = Column(Float)  # 带息流动负债
    # EBIAT = Column(Float)  # 息前税后利润
    # IC = Column(Float)  # 投入资本
    # T_FIXED_ASSETS = Column(Float)  # 固定资产合计
    # N_INT_EXP = Column(Float)  # 净利息费用



class FinancePerShare(FinanceBase, Mixin):
    """
    财务指标 每股
    """
    @classmethod
    def important_cols(cls):
        return ['operating_income', 'investment_income', 'total_operating_costs', 'total_profits', 'sales_costs',
                'managing_costs', 'financing_costs']

    __tablename__ = 'finance_derivative'

    provider = Column(String(length=32))
    code = Column(String(length=32))

    report_period = Column(String(length=32))
    report_date = Column(DateTime)

    eps_diluted_end = Column(Float)  # 每股收益(期末摊薄)
    eps = Column(Float)  # 基本每股收益
    diluted_eps = Column(Float)  # 稀释每股收益
    bps = Column(Float)  # 每股净资产
    total_operating_revenue_ps = Column(Float)  # 每股营业总收入
    operating_revenue_pee = Column(Float)  # 每股营业收入
    operating_profit_ps = Column(Float)  # 每股营业利润
    earnings_bf_interest_taxes_ps = Column(Float)  # 每股息税前利润
    capital_reserve_ps = Column(Float)  # 每股资本公积
    surplus_reserve_fund_ps = Column(Float)  # 每股盈余公积
    undistributed_profit_ps = Column(Float)  # 每股未分配利润
    retained_earnings_ps = Column(Float)  # 每股留存收益
    net_operate_cash_flow_ps = Column(Float)  # 每股经营活动产生的现金流量净额
    net_cash_flow_ps = Column(Float)  # 每股现金流量净额
    free_cash_flow_firm_ps = Column(Float)  # 每股企业自由现金流量
    free_cash_flow_equity_ps = Column(Float)  # 每股股东自由现金流量


    T_FIXED_ASSETS = Column(Float)  # 固定资产合计

class FinanceGrowthAbility(FinanceBase, Mixin):
    """
    财务指标-成长能力
    """
    @classmethod
    def important_cols(cls):
        return ['operating_income', 'investment_income', 'total_operating_costs', 'total_profits', 'sales_costs',
                'managing_costs', 'financing_costs']

    __tablename__ = 'finance_growth_ability'

    provider = Column(String(length=32))
    code = Column(String(length=32))

    report_period = Column(String(length=32))
    report_date = Column(DateTime)



    total_op_income_growth_yoy = Column(Float)  # 营业总收入同比增长率
    op_profit_growth_yoy = Column(Float)  # 营业利润同比增长率
    total_profit_growth_yoy = Column(Float)  # 利润总额同比增长率
    net_profit_growth_yoy = Column(Float)  # 净利润同比增长率
    inc_net_profit_shareholders_yoy = Column(Float)  # 归属母公司股东的净利润同比增长率
    inc_net_profit_shareholders_deducted_yoy = Column(Float)  # 归属母公司股东的净利润同比增长率(扣除非经常性损益)
    basic_eps_you = Column(Float)  # 基本每股收益同比增长率
    diluted_eps_yoy = Column(Float)  # 稀释每股收益同比增长率
    roe_liluted_yoy = Column(Float)  # 净资产收益率同比增长率(摊薄)
    net_op_cash_flows_yoy = Column(Float)  # 经营活动产生的现金流量净额同比增长率
    net_operate_cash_flow_ps_yoy = Column(Float)  # 每股经营活动中产生的现金流量净额同比增长率
    total_assets_relative_of_year = Column(Float)  # 资产总计相对年初增长率
    equity_relative_of_year = Column(Float)  # 归属母公司股东的权益相对年初增长率
    bps_relativeof_year = Column(Float)  # 每股净资产相对年初增长率

register_schema(providers=['eastmoney', 'joinquant','emquantapi'], db_name='finance', schema_base=FinanceBase)

__all__ = ['FinanceFactor', 'BalanceSheet', 'IncomeStatement', 'CashFlowStatement','FinanceDerivative','FinancePerShare','FinanceGrowthAbility']
