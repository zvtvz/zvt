# -*- coding: utf-8 -*-
from zvt.utils.time_utils import to_pd_timestamp
from zvt.utils.utils import add_func_to_value, first_item_to_float
from zvt.api.quote import to_report_period_type
from zvt.domain import BalanceSheet
from zvt.recorders.eastmoney.finance.base_china_stock_finance_recorder import BaseChinaStockFinanceRecorder

balance_sheet_map = {
    # 流动资产
    #
    # 货币资金
    "cash_and_cash_equivalents": "Monetaryfund",
    # 应收票据
    "note_receivable": "Billrec",
    # 应收账款
    "accounts_receivable": "Accountrec",
    # 预付款项
    "advances_to_suppliers": "Advancepay",
    # 其他应收款
    "other_receivables": "Otherrec",
    # 存货
    "inventories": "Inventory",
    # 一年内到期的非流动资产
    "current_portion_of_non_current_assets": "Nonlassetoneyear",
    # 其他流动资产
    "other_current_assets": "Otherlasset",
    # 流动资产合计
    "total_current_assets": "Sumlasset",
    # 非流动资产
    #
    # 可供出售金融资产
    "fi_assets_saleable": "Saleablefasset",
    # 长期应收款
    "long_term_receivables": "Ltrec",
    # 长期股权投资
    "long_term_equity_investment": "Ltequityinv",
    # 投资性房地产
    "real_estate_investment": "Estateinvest",
    # 固定资产
    "fixed_assets": "Fixedasset",
    # 在建工程
    "construction_in_process": "Constructionprogress",
    # 无形资产
    "intangible_assets": "Intangibleasset",
    # 商誉
    "goodwill": "Goodwill",
    # 长期待摊费用
    "long_term_prepaid_expenses": "Ltdeferasset",
    # 递延所得税资产
    "deferred_tax_assets": "Deferincometaxasset",
    # 其他非流动资产
    "other_non_current_assets": "Othernonlasset",
    # 非流动资产合计
    "total_non_current_assets": "Sumnonlasset",
    # 资产总计
    "total_assets": "Sumasset",
    # 流动负债
    #
    # 短期借款
    "short_term_borrowing": "Stborrow",
    # 吸收存款及同业存放
    "accept_money_deposits": "Deposit",
    # 应付账款
    "accounts_payable": "Accountpay",
    # 预收款项
    "advances_from_customers": "Advancereceive",
    # 应付职工薪酬
    "employee_benefits_payable": "Salarypay",
    # 应交税费
    "taxes_payable": "Taxpay",
    # 应付利息
    "interest_payable": "Interestpay",
    # 其他应付款
    "other_payable": "Otherpay",
    # 一年内到期的非流动负债
    "current_portion_of_non_current_liabilities": "Nonlliaboneyear",
    # 其他流动负债
    "other_current_liabilities": "Otherlliab",
    # 流动负债合计
    "total_current_liabilities": "Sumlliab",
    # 非流动负债
    #
    # 长期借款
    "long_term_borrowing": "Ltborrow",
    # 长期应付款
    "long_term_payable": "Ltaccountpay",
    # 递延收益
    "deferred_revenue": "Deferincome",
    # 递延所得税负债
    "deferred_tax_liabilities": "Deferincometaxliab",
    # 其他非流动负债
    "other_non_current_liabilities": "Othernonlliab",
    # 非流动负债合计
    "total_non_current_liabilities": "Sumnonlliab",
    # 负债合计
    "total_liabilities": "Sumliab",
    # 所有者权益(或股东权益)
    #
    # 实收资本（或股本）
    "capital": "Sharecapital",
    # 资本公积
    "capital_reserve": "Capitalreserve",
    # 专项储备
    "special_reserve": "Specialreserve",
    # 盈余公积
    "surplus_reserve": "Surplusreserve",
    # 未分配利润
    "undistributed_profits": "Retainedearning",
    # 归属于母公司股东权益合计
    "equity": "Sumparentequity",
    # 少数股东权益
    "equity_as_minority_interest": "Minorityequity",
    # 股东权益合计
    "total_equity": "Sumshequity",
    # 负债和股东权益合计
    "total_liabilities_and_equity": "Sumliabshequity",

    # 银行相关
    # 资产
    # 现金及存放中央银行款项
    "fi_cash_and_deposit_in_central_bank": "Cashanddepositcbank",
    # 存放同业款项
    "fi_deposit_in_other_fi": "Depositinfi",
    # 贵金属
    "fi_expensive_metals": "Preciousmetal",
    # 拆出资金
    "fi_lending_to_other_fi": "Lendfund",
    # 以公允价值计量且其变动计入当期损益的金融资产
    "fi_financial_assets_effect_current_income": "Fvaluefasset",
    # 衍生金融资产
    "fi_financial_derivative_asset": "Derivefasset",
    # 买入返售金融资产
    "fi_buying_sell_back_fi__asset": "Buysellbackfasset",
    # 应收账款
    #
    # 应收利息
    "fi_interest_receivable": "Interestrec",
    # 发放贷款及垫款
    "fi_disbursing_loans_and_advances": "Loanadvances",
    # 可供出售金融资产
    #
    # 持有至到期投资
    "fi_held_to_maturity_investment": "Heldmaturityinv",
    # 应收款项类投资
    "fi_account_receivable_investment": "Investrec",
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
    "fi_other_asset": "Otherasset",
    # 资产总计
    #
    # 负债
    #
    # 向中央银行借款
    "fi_borrowings_from_central_bank": "Borrowfromcbank",
    # 同业和其他金融机构存放款项
    "fi_deposit_from_other_fi": "Fideposit",
    # 拆入资金
    "fi_borrowings_from_fi": "Borrowfund",
    # 以公允价值计量且其变动计入当期损益的金融负债
    "fi_financial_liability_effect_current_income": "Fvaluefliab",
    # 衍生金融负债
    "fi_financial_derivative_liability": "Derivefliab",
    # 卖出回购金融资产款
    "fi_sell_buy_back_fi_asset": "Sellbuybackfasset",
    # 吸收存款
    "fi_savings_absorption": "Acceptdeposit",
    # 存款证及应付票据
    "fi_notes_payable": "Cdandbillrec",
    # 应付职工薪酬
    #
    # 应交税费
    #
    # 应付利息
    #
    # 预计负债
    "fi_estimated_liabilities": "Anticipateliab",
    # 应付债券
    "fi_bond_payable": "Bondpay",
    # 其他负债
    "fi_other_liability": "Otherliab",
    # 负债合计
    #
    # 所有者权益(或股东权益)
    # 股本
    "fi_capital": "Shequity",
    # 其他权益工具
    "fi_other_equity_instruments": "Otherequity",
    # 其中:优先股
    "fi_preferred_stock": "Preferredstock",
    # 资本公积
    #
    # 盈余公积
    #
    # 一般风险准备
    "fi_generic_risk_reserve": "Generalriskprepare",
    # 未分配利润
    #
    # 归属于母公司股东权益合计
    #
    # 股东权益合计
    #
    # 负债及股东权益总计

    # 券商相关
    # 资产
    #
    # 货币资金
    #
    # 其中: 客户资金存款
    "fi_client_fund": "Clientfund",
    # 结算备付金
    "fi_deposit_reservation_for_balance": "Settlementprovision",
    # 其中: 客户备付金
    "fi_client_deposit_reservation_for_balance": "Clientprovision",
    # 融出资金
    "fi_margin_out_fund": "Marginoutfund",
    # 以公允价值计量且其变动计入当期损益的金融资产
    #
    # 衍生金融资产
    #
    # 买入返售金融资产
    #
    # 应收利息
    #
    # 应收款项
    "fi_receivables": "Receivables",
    # 存出保证金
    "fi_deposit_for_recognizance": "Gdepositpay",
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
    "fi_receiving_as_agent": "Agenttradesecurity",
    # 应付账款
    #
    # 应付职工薪酬
    #
    # 应交税费
    #
    # 应付利息
    #
    # 应付短期融资款
    "fi_short_financing_payable": "Shortfinancing",
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
    "fi_trade_risk_reserve": "Traderiskprepare",
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
    "fi_premiums_receivable": "Premiumrec",
    "fi_reinsurance_premium_receivable": "Rirec",
    # 应收分保合同准备金
    "fi_reinsurance_contract_reserve": "Ricontactreserverec",
    # 保户质押贷款
    "fi_policy_pledge_loans": "Insuredpledgeloan",
    # 定期存款
    "fi_time_deposit": "Tdeposit",
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
    "fi_deposit_for_capital_recognizance": "Capitalgdepositpay",
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
    "fi_advance_from_customers": "Advancerec",
    # 预收保费
    "fi_advance_premium": "Premiumadvance",
    # 应付手续费及佣金
    "fi_fees_and_commissions_payable": "Commpay",
    # 应付分保账款
    "fi_dividend_payable_for_reinsurance": "Ripay",
    # 应付职工薪酬
    #
    # 应交税费
    #
    # 应付利息
    #
    # 预计负债
    #
    # 应付赔付款
    "fi_claims_payable": "Claimpay",
    # 应付保单红利
    "fi_policy_holder_dividend_payable": "Policydivipay",
    # 保户储金及投资款
    "fi_policy_holder_deposits_and_investment_funds": "Insureddepositinv",
    # 保险合同准备金
    "fi_contract_reserve": "Contactreserve",
    # 长期借款
    #
    # 应付债券
    #
    # 递延所得税负债
    #
    # 其他负债
    #
    # 独立账户负债
    "fi_independent_liability": "Independentliab",
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


class ChinaStockBalanceSheetRecorder(BaseChinaStockFinanceRecorder):
    data_schema = BalanceSheet

    url = 'https://emh5.eastmoney.com/api/CaiWuFenXi/GetZiChanFuZhaiBiaoList'
    finance_report_type = 'ZiChanFuZhaiBiaoList'
    data_type = 3

    def get_data_map(self):
        return balance_sheet_map


__all__ = ['ChinaStockBalanceSheetRecorder']

if __name__ == '__main__':
    # init_log('blance_sheet.log')
    recorder = ChinaStockBalanceSheetRecorder(codes=['002572'])
    recorder.run()
