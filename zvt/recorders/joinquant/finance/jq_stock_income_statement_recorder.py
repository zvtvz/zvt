# -*- coding: utf-8 -*-
from zvt.utils.time_utils import to_pd_timestamp
from zvt.utils.utils import add_func_to_value, first_item_to_float
from zvt.api.quote import to_report_period_type
from zvt.domain import IncomeStatement
from zvt.recorders.joinquant.finance.base_jq_stock_finance_recorder import BaseJqStockFinanceRecorder


income_statement_map = {
    # 营业总收入
    #
    # 营业收入
    "operating_income": "operating_revenue",
    # 营业总成本
    "total_operating_costs": "total_operating_cost",
    # 营业成本
    "operating_costs": "operating_cost",
    # 研发费用
    # "rd_costs": "rd_expenses",
    # 提取保险合同准备金净额
    "net_change_in_insurance_contract_reserves": "withdraw_insurance_contract_reserve",
    # 营业税金及附加
    "business_taxes_and_surcharges": "operating_tax_surcharges",
    # 销售费用
    "sales_costs": "sale_expense",
    # 管理费用
    "managing_costs": "administration_expense",
    # 财务费用
    "financing_costs": "financial_expense",
    # 资产减值损失
    "assets_devaluation": "asset_impairment_loss",
    # 其他经营收益
    #
    # 加: 投资收益
    "investment_income": "investment_income",
    # 其中: 对联营企业和合营企业的投资收益
    "investment_income_from_related_enterprise": "invest_income_associates",
    # 营业利润
    "operating_profit": "operating_profit",
    # 加: 营业外收入
    "non_operating_income": "non_operating_revenue",
    # 减: 营业外支出
    "non_operating_costs": "non_operating_expense",
    # 其中: 非流动资产处置净损失
    "loss_on_disposal_non_current_asset": "disposal_loss_non_current_liability",

    # 利润总额
    "total_profits": "total_profit",
    # 减: 所得税费用
    "tax_expense": "income_tax_expense",
    # 净利润
    "net_profit": "net_profit",
    # 其中: 归属于母公司股东的净利润
    "net_profit_as_parent": "np_parent_company_owners",
    # 少数股东损益
    "net_profit_as_minority_interest": "minority_profit",
    # 扣除非经常性损益后的净利润
    # "deducted_net_profit": "adjusted_profit",
    # 每股收益
    "eps": "eps",

    # 稀释每股收益
    "diluted_eps": "diluted_eps",
    # 其他综合收益
    "other_comprehensive_income": "other_comprehensive_income",

    # 综合收益总额
    "total_comprehensive_income": "total_composite_income",
    # 归属于母公司所有者的综合收益总额
    "total_comprehensive_income_as_parent": "ci_parent_company_owners",
    # 归属于少数股东的综合收益总额
    "total_comprehensive_income_as_minority_interest": "ci_minority_owners",

    # 银行相关

    # 其中:利息收入
    "fi_interest_income": "interest_income",
    # 利息支出
    "fi_interest_expenses": "interest_expense",
    # 手续费及佣金净收入
    # "fi_net_incomes_from_fees_and_commissions": "commission_net_income",
    # 其中:手续费及佣金收入
    "fi_incomes_from_fees_and_commissions": "commission_income",
    # 手续费及佣金支出
    "fi_expenses_for_fees_and_commissions": "commission_expense",
    # 公允价值变动收益
    "fi_income_from_fair_value_change": "fair_value_variable_income",
    # 汇兑收益
    "fi_income_from_exchange": "exchange_income",
    # 其他业务收入
    "fi_other_income": "other_income",
    # 保险相关
    # 已赚保费
    "fi_net_income_from_premium": "premiums_earned",

    # 退保金
    "fi_insurance_surrender_costs": "refunded_premiums",

    # 保单红利支出
    "fi_dividend_expenses_to_insured": "policy_dividend_payout",
    # 分保费用
    "fi_reinsurance_expenses": "reinsurance_cost",

}


add_func_to_value(income_statement_map, first_item_to_float)
income_statement_map["report_period"] = ("ReportDate", to_report_period_type)
income_statement_map["report_date"] = ("ReportDate", to_pd_timestamp)

class JqStockIncomeStatementRecorder(BaseJqStockFinanceRecorder):
    data_schema = IncomeStatement
    finance_report_type = 'INCOME_STATEMENT'

    data_type = 2

    def get_data_map(self):
        return income_statement_map


__all__ = ['JqStockIncomeStatementRecorder']

if __name__ == '__main__':
    # init_log('income_statement.log')
    recorder = JqStockIncomeStatementRecorder(codes=['002572'])
    recorder.run()
