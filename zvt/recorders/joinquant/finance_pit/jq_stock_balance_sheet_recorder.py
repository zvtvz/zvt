# -*- coding: utf-8 -*-
from zvt.utils.time_utils import to_pd_timestamp
from zvt.utils.utils import add_func_to_value, first_item_to_float
from zvt.api.quote import to_report_period_type
from zvt.domain import BalanceSheet
from zvt.recorders.joinquant.finance.base_jq_stock_finance_recorder import BaseJqStockFinanceRecorder

balance_sheet_map = {
    # 流动资产
    #
    # 货币资金
    "cash_and_cash_equivalents": "cash_equivalents",
    # 应收票据
    "note_receivable": "bill_receivable",
    # 应收账款
    "accounts_receivable": "account_receivable",
    # 预付款项
    "advances_to_suppliers": "advance_payment",
    # 其他应收款
    "other_receivables": "other_receivable",
    # 存货
    "inventories": "inventories",
    # 一年内到期的非流动资产
    "current_portion_of_non_current_assets": "non_current_asset_in_one_year",
    # 其他流动资产
    ###"other_current_assets": "Otherlasset",
    # 流动资产合计
    "total_current_assets": "total_current_assets",
    # 非流动资产
    #
    # 可供出售金融资产
    "fi_assets_saleable": "hold_for_sale_assets",
    # 长期应收款
    "long_term_receivables": "longterm_receivable_account",
    # 长期股权投资
    "long_term_equity_investment": "longterm_equity_invest",
    # 投资性房地产
    "real_estate_investment": "investment_property",
    # 固定资产
    "fixed_assets": "fixed_assets",
    # 在建工程
    "construction_in_process": "constru_in_process",
    # 无形资产
    "intangible_assets": "intangible_assets",
    # 商誉
    "goodwill": "good_will",
    # 长期待摊费用
    "long_term_prepaid_expenses": "long_deferred_expense",
    # 递延所得税资产
    "deferred_tax_assets": "deferred_tax_assets",
    # 其他非流动资产
    "other_non_current_assets": "Othernonlasset",
    # 非流动资产合计
    "total_non_current_assets": "total_non_current_assets",
    # 资产总计
    "total_assets": "total_assets",
    # 流动负债
    #
    # 短期借款
    "short_term_borrowing": "shortterm_loan",
    # 吸收存款及同业存放
    "accept_money_deposits": "deposit_in_interbank",
    # 应付账款
    "accounts_payable": "accounts_payable",
    # 预收款项
    "advances_from_customers": "advance_peceipts",
    # 应付职工薪酬
    "employee_benefits_payable": "salaries_payable",
    # 应交税费
    "taxes_payable": "taxs_payable",
    # 应付利息
    "interest_payable": "interest_payable",
    # 其他应付款
    "other_payable": "other_payable",
    # 一年内到期的非流动负债
    "current_portion_of_non_current_liabilities": "non_current_liability_in_one_year",
    # 其他流动负债
    ### "other_current_liabilities": "Otherlliab",
    # 流动负债合计
    "total_current_liabilities": "total_current_liability",
    # 非流动负债
    #
    # 长期借款
    "long_term_borrowing": "longterm_loan",
    # 长期应付款
    "long_term_payable": "longterm_account_payable",
    # 递延收益-非流动负债
    "deferred_revenue": "deferred_earning",
    # 递延所得税负债
    "deferred_tax_liabilities": "deferred_tax_liability",
    # 其他非流动负债
    ### "other_non_current_liabilities": "Othernonlliab",
    # 非流动负债合计
    "total_non_current_liabilities": "total_non_current_liability",
    # 负债合计
    "total_liabilities": "total_liability",
    # 所有者权益(或股东权益)
    #
    # 实收资本（或股本）
    "capital": "paidin_capital",
    # 资本公积
    "capital_reserve": "capital_reserve_fund",
    # 专项储备
    "special_reserve": "specific_reserves",
    # 盈余公积
    "surplus_reserve": "surplus_reserve_fund",
    # 未分配利润
    "undistributed_profits": "retained_profit",
    # 归属于母公司股东权益合计
    "equity": "equities_parent_company_owners",
    # 少数股东权益
    "equity_as_minority_interest": "minority_interests",
    # 股东权益合计
    "total_equity": "total_owner_equities",
    # 负债和股东权益合计
    "total_liabilities_and_equity": "total_sheet_owner_equities",

    # 银行相关
    # 资产
    # 现金及存放中央银行款项
    "fi_cash_and_deposit_in_central_bank": "cash_in_cb",
    # 存放同业款项
    "fi_deposit_in_other_fi": "deposit_in_ib",
    # 贵金属
    "fi_expensive_metals": "metal",
    # 拆出资金
    "fi_lending_to_other_fi": "lend_capital",
    # 以公允价值计量且其变动计入当期损益的金融资产(	交易性金融资产)
    "fi_financial_assets_effect_current_income": "fairvalue_fianancial_asset",
    # 衍生金融资产
    "fi_financial_derivative_asset": "derivative_financial_asset",
    # 买入返售金融资产
    "fi_buying_sell_back_fi__asset": "bought_sellback_assets",
    # 应收账款
    #
    # 应收利息
    "fi_interest_receivable": "interest_receivable",
    # 发放贷款及垫款
    "fi_disbursing_loans_and_advances": "loan_and_advance",
    # 可供出售金融资产
    #
    # 持有至到期投资
    "fi_held_to_maturity_investment": "hold_to_maturity_investments",
    # 应收款项类投资
    "fi_account_receivable_investment": "investment_reveiable",
    # 投资性房地产
    #
    # 固定资产
    #
    # 无形资产
    #
    # 商誉
    #
    # 递延所得税资产
    #
    # 其他资产
    "fi_other_asset": "other_asset",
    # 资产总计
    #
    # 负债
    #
    # 向中央银行借款
    "fi_borrowings_from_central_bank": "borrowing_from_centralbank",
    # 同业和其他金融机构存放款项
    "fi_deposit_from_other_fi": "deposit_in_ib_and_other",
    # 拆入资金
    "fi_borrowings_from_fi": "borrowing_capital",
    # 以公允价值计量且其变动计入当期损益的金融负债
    "fi_financial_liability_effect_current_income": "fairvalue_financial_liability",
    # 衍生金融负债
    "fi_financial_derivative_liability": "derivative_financial_liability",
    # 卖出回购金融资产款
    "fi_sell_buy_back_fi_asset": "sold_buyback_secu_proceeds",
    # 吸收存款
    "fi_savings_absorption": "deposit_absorb",
    # 存款证及应付票据
    "fi_notes_payable": "notes_payable",
    # 应付职工薪酬
    #
    # 应交税费
    #
    # 应付利息
    #
    # 预计负债
    "fi_estimated_liabilities": "estimate_liability",
    # 应付债券
    "fi_bond_payable": "bonds_payable",
    # 其他负债
    "fi_other_liability": "other_liability",
    # 负债合计
    #
    # 所有者权益(或股东权益)
    # 股本
    "fi_capital": "Shequity",
    # 其他权益工具
    "fi_other_equity_instruments": "other_equity_tools",
    # 其中:优先股
    "fi_preferred_stock": "preferred_shares_equity",
    # 资本公积
    #
    # 盈余公积
    #
    # 一般风险准备
    ###"fi_generic_risk_reserve": "Generalriskprepare",
    # 未分配利润
    #
    # 归属于母公司股东权益合计
    #
    # 股东权益合计
    #
    # 负债及股东权益总计
    "fi_total_liability_equity": "total_liability_equity",
    # 券商相关
    # 资产
    #
    # 货币资金
    #
    # 其中: 客户资金存款
    "fi_client_fund": "deposit_client",
    # 结算备付金
    "fi_deposit_reservation_for_balance": "settlement_provi",
    # 其中: 客户备付金
    "fi_client_deposit_reservation_for_balance": "settlement_provi_client",
    # 融出资金
    "fi_margin_out_fund": "finance_out",
    # 以公允价值计量且其变动计入当期损益的金融资产
    #
    # 衍生金融资产
    #
    # 买入返售金融资产
    #
    # 应收利息
    #
    # 应收款项类投资
    "fi_receivables": "investment_reveiable",
    # 存出保证金
    "fi_deposit_for_recognizance": "margin_out",
    # 可供出售金融资产
    #
    # 持有至到期投资
    #
    # 长期股权投资
    #
    # 固定资产
    #
    # 在建工程
    #
    # 无形资产
    #
    # 商誉
    #
    # 递延所得税资产
    #
    # 其他资产
    #
    # 资产总计
    #
    # 负债
    #
    # 短期借款
    #
    # 拆入资金
    #
    # 以公允价值计量且其变动计入当期损益的金融负债
    #
    # 衍生金融负债
    #
    # 卖出回购金融资产款
    #
    # 代理买卖证券款
    "fi_receiving_as_agent": "proxy_secu_proceeds",
    # 应付账款
    #
    # 应付职工薪酬
    #
    # 应交税费
    #
    # 应付利息
    #
    # 应付短期融资款
    "fi_short_financing_payable": "shortterm_loan_payable",
    # 预计负债
    #
    # 应付债券
    #
    # 递延所得税负债
    #
    # 其他负债
    #
    # 负债合计
    #
    # 所有者权益(或股东权益)
    #
    # 股本
    #
    # 资本公积
    #
    # 其他权益工具
    #
    # 盈余公积
    #
    # 一般风险准备
    #
    # 交易风险准备
    ###"fi_trade_risk_reserve": "Traderiskprepare",
    # 未分配利润
    #
    # 归属于母公司股东权益合计
    #
    # 少数股东权益
    #
    # 股东权益合计
    #
    # 负债和股东权益总计

    # 保险相关
    # 应收保费
    "fi_premiums_receivable": "insurance_receivables",
    # 应收分保账款
    "fi_reinsurance_premium_receivable": "reinsurance_receivables",
    # 应收分保合同准备金
    "fi_reinsurance_contract_reserve": "reinsurance_contract_reserves_receivable",
    # 保户质押贷款
    "fi_policy_pledge_loans": "margin_loan",
    # 定期存款
    "fi_time_deposit": "deposit_period",
    # 可供出售金融资产
    #
    # 持有至到期投资
    #
    # 应收款项类投资
    #
    # 应收账款
    #
    # 长期股权投资
    #
    # 存出资本保证金
    "fi_deposit_for_capital_recognizance": "capital_margin_out",
    # 投资性房地产
    #
    # 固定资产
    #
    # 无形资产
    #
    # 商誉
    #
    # 递延所得税资产
    #
    # 其他资产
    #
    # 独立账户资产
    "fi_capital_in_independent_accounts": "Independentasset",
    # 资产总计
    #
    # 负债
    #
    # 短期借款
    #
    # 同业及其他金融机构存放款项
    #
    # 拆入资金
    #
    # 以公允价值计量且其变动计入当期损益的金融负债
    #
    # 衍生金融负债
    #
    # 卖出回购金融资产款
    #
    # 吸收存款
    #
    # 代理买卖证券款
    #
    # 应付账款
    #
    # 预收账款
    "fi_advance_from_customers": "advance_peceipts",
    # 预收保费
    "fi_advance_premium": "insurance_receive_early",
    # 应付手续费及佣金
    "fi_fees_and_commissions_payable": "commission_payable",
    # 应付分保账款
    "fi_dividend_payable_for_reinsurance": "reinsurance_payables",
    # 应付职工薪酬
    #
    # 应交税费
    #
    # 应付利息
    #
    # 预计负债
    #
    # 应付赔付款
    "fi_claims_payable": "compensation_payable",
    # 应付保单红利
    "fi_policy_holder_dividend_payable": "interest_insurance_payable",
    # 保户储金及投资款
    "fi_policy_holder_deposits_and_investment_funds": "investment_money",
    # 保险合同准备金
    "fi_contract_reserve": "insurance_contract_reserves",
    # 长期借款
    #
    # 应付债券
    #
    # 递延所得税负债
    #
    # 其他负债
    #
    # 独立账户负债
    ###"fi_independent_liability": "Independentliab",
    # 负债合计
    #
    # 所有者权益(或股东权益)
    #
    # 股本
    #
    # 资本公积
    #
    # 盈余公积
    #
    # 一般风险准备
    #
    # 未分配利润
    #
    # 归属于母公司股东权益总计
    #
    # 少数股东权益
    #
    # 股东权益合计
    #
    # 负债和股东权益总计

}

add_func_to_value(balance_sheet_map, first_item_to_float)
balance_sheet_map["report_period"] = ("ReportDate", to_report_period_type)
balance_sheet_map["report_date"] = ("ReportDate", to_pd_timestamp)

# balance_sheet_map["ReportDate"] = ("report_period", to_report_period_type)
# balance_sheet_map["ReportDate"] = ("report_date", to_pd_timestamp)


class JqStockBalanceSheetRecorder(BaseJqStockFinanceRecorder):
    # url = 'https://emh5.eastmoney.com/api/CaiWuFenXi/GetZiChanFuZhaiBiaoList'
    data_schema = BalanceSheet
    # 合并资产负债表
    # STK_BALANCE_SHEET
    finance_report_type = 'BALANCE_SHEET'
    data_type = 3
    def get_data_map(self):
        return balance_sheet_map


__all__ = ['JqStockBalanceSheetRecorder']

if __name__ == '__main__':
    # init_log('blance_sheet.log')
    recorder = JqStockBalanceSheetRecorder(codes=['002572'])
    recorder.run()
