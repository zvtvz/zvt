# -*- coding: utf-8 -*-
from zvt.domain import BalanceSheet
from zvt.recorders.emquantapi.finance.base_china_stock_finance_recorder import EmBaseChinaStockFinanceRecorder
from zvt.utils.utils import add_func_to_value, first_item_to_float

balance_sheet_map = {
    # 更新时间
    "pub_date": "FIRSTNOTICEDATE",
    "report_date": "REPORTDATE",
    # 流动资产
    #CASHTOCL
    # 货币资金
    "cash_and_cash_equivalents": "MONETARYFUND",
    # 应收票据
    "note_receivable": "BILLREC",
    # 应收账款
    "accounts_receivable": "ACCOUNTREC",
    # 预付款项
    "advances_to_suppliers": "ADVANCEPAY",
    # 其他应收款
    "other_receivables": "OTHERREC",
    # 存货
    "inventories": "INVENTORY",
    # 一年内到期的非流动资产
    "current_portion_of_non_current_assets": "NONLASSETONEYEAR",
    # 其他流动资产
    "other_current_assets": "OTHERLASSET",
    # 流动资产合计
    "total_current_assets": "SUMLASSET",
    # 非流动资产
    #
    # 可供出售金融资产
    "fi_assets_saleable": "SALEABLEFASSET",
    # 长期应收款
    "long_term_receivables": "LTREC",
    # 长期股权投资
    "long_term_equity_investment": "LTEQUITYINV",
    # 投资性房地产
    "real_estate_investment": "ESTATEINVEST",
    # 固定资产
    "fixed_assets": "FIXEDASSET",
    # 在建工程
    "construction_in_process": "CONSTRUCTIONPROGRESS",
    # 无形资产
    "intangible_assets": "INTANGIBLEASSET",
    # 商誉
    "goodwill": "GOODWILL",
    # 长期待摊费用
    "long_term_prepaid_expenses": "LTDEFERASSET",
    # 递延所得税资产
    "deferred_tax_assets": "DEFERINCOMETAXASSET",
    # 其他非流动资产
    "other_non_current_assets": "OTHERNONLASSET",
    # 非流动资产合计
    "total_non_current_assets": "SUMNONLASSET",
    # 资产总计
    "total_assets": "SUMASSET",
    # 流动负债
    #
    # 短期借款
    "short_term_borrowing": "STBORROW",
    # 吸收存款及同业存放
    "accept_money_deposits": "DEPOSIT",
    # 应付账款
    "accounts_payable": "ACCOUNTPAY",
    # 预收款项
    "advances_from_customers": "ADVANCERECEIVE",
    # 应付职工薪酬
    "employee_benefits_payable": "SALARYPAY",
    # 应交税费
    "taxes_payable": "TAXPAY",
    # 应付利息
    "interest_payable": "INTERESTPAY",
    # 其他应付款
    "other_payable": "OTHERPAY",
    # 一年内到期的非流动负债
    "current_portion_of_non_current_liabilities": "DEFERINCOMEONEYEAR",
    # 其他流动负债
    "other_current_liabilities": "OTHERLLIAB",
    # 流动负债合计
    "total_current_liabilities": "SUMLLIAB",
    # 一般风险准备
    "fi_generic_risk_reserve": "GENERALRISKPREPARE",
    # 非流动负债
    #
    # 长期借款
    "long_term_borrowing": "LTBORROW",
    # 长期应付款
    "long_term_payable": "LTACCOUNTPAY",
    # 递延收益
    "deferred_revenue": "DEFERINCOME",
    # 递延所得税负债
    "deferred_tax_liabilities": "DEFERINCOMETAXLIAB",
    # 其他非流动负债
    "other_non_current_liabilities": "OTHERNONLLIAB",
    # 非流动负债合计
    "total_non_current_liabilities": "SUMNONLLIAB",
    # 负债合计
    "total_liabilities": "SUMLIAB",
    # 所有者权益(或股东权益)
    #
    # 实收资本（或股本）
    "capital": "SHARECAPITAL",
    # 资本公积
    "capital_reserve": "CAPITALRESERVE",
    # 专项储备
    "special_reserve": "SPECIALRESERVE",
    # 盈余公积
    "surplus_reserve": "SURPLUSRESERVE",
    # 未分配利润
    "undistributed_profits": "RETAINEDEARNING",
    # 归属于母公司股东权益合计
    "equity": "SUMPARENTEQUITY",
    # 少数股东权益
    "equity_as_minority_interest": "MINORITYEQUITY",
    # 应收利息
    "fi_interest_receivable": "INTERESTREC",
    # 应收股利	其中:应收股利(元)	DIVIDENDREC
    "fi_dividend_rec": "DIVIDENDREC",
    # 股东权益合计 所有者权益(或股东权益)合计
    "total_equity": "SUMSHEQUITY",
    # 负债和股东权益合计
    "total_liabilities_and_equity": "SUMLIABSHEQUITY",
    # 其中:优先股
    "fi_preferred_stock": "YXGQY",
    # 拆出资金
    "fi_lending_to_other_fi": "LENDFUND",
    # 其他权益工具
    "fi_other_equity_instruments": "QTQYGJ",
    # 永续债
    "fi_perpetual_bond": "YXZQY",
    # 减:库存股
    "fi_inventory_share": "INVENTORYSHARE",
    # 其他综合收益
    "other_comprehensive_income": "OTHERCINCOME",
    # 外币报表折算差额		外币报表折算差额(元)
    "fi_diffconversionfc": "DIFFCONVERSIONFC",
    # 归属于母公司所有者权益的调整项目	 归属于母公司股东权益其他项目(元)
    "fi_parent_equity_other": "PARENTEQUITYOTHER",
    # 归属于母公司所有者权益的差错金额	 归属于母公司股东权益平衡项目(元)
    "fi_parent_equity_balance": "PARENTEQUITYBALANCE",
    # 所有者权益的调整项目  股东权益其他项目(元)
    "fi_sh_equity_other": "SHEQUITYOTHER",
    # 所有者权益的差错金额	股东权益平衡项目(元)
    "fi_sh_equity_balance": "SHEQUITYBALANCE",
    # 应付债券
    "fi_bond_payable": "BONDPAY",
    # 负债和权益的调整项目	负债和股东权益其他项目(元)
    "fi_liab_sh_equity_other": "LIABSHEQUITYOTHER",

    # 负债和权益的差错金额	负债和股东权益平衡项目(元)
    "fi_liab_sh_equity_balance": "LIABSHEQUITYBALANCE",
    # 结算备付金
    "fi_deposit_reservation_for_balance": "SETTLEMENTPROVISION",
    # 交易性金融资产		交易性金融资产	TRADE_FINASSET_NOTFVTPL
    "fi_trade_finasset_notfvtpl": "TRADE_FINASSET_NOTFVTPL",
    # 衍生金融资产
    "fi_financial_derivative_asset": "DERIVEFASSET",
    # 应收保费
    "fi_premiums_receivable": "PREMIUMREC",
    # 应收分保账款
    "fi_reinsurance_premium_receivable": "RIREC",
    # 应收分保合同准备金
    "fi_reinsurance_contract_reserve": "RICONTACTRESERVEREC",
    # 买入返售金融资产
    "fi_buying_sell_back_fi__asset": "BUYSELLBACKFASSET",
    # 流动资产的调整项目		流动资产其他项目(元)
    "fi_lasset_other": "LASSETOTHER",
    # 流动资产的差错金额		流动资产平衡项目(元)
    "fi_lasset_balance": "LASSETBALANCE",
    # 发放委托贷款及垫款		发放委托贷款及垫款(元)	LOANADVANCES
    "fi_loan_advances": "LOANADVANCES",
    # 保险合同准备金
    "fi_contract_reserve": "CONTACTRESERVE",
    # 持有至到期投资
    "fi_held_to_maturity_investment": "HELDMATURITYINV",

    # 工程物资	工程物资(元)
    "fi_construction_material": "CONSTRUCTIONMATERIAL",
    # 固定资产清理	固定资产清理(元)
    "fi_liquidate_fixed_asset": "LIQUIDATEFIXEDASSET",
    # 生产性生物资产		生产性生物资产(元)
    "fi_product_biology_asset": "PRODUCTBIOLOGYASSET",
    # 油气资产	油气资产(元)
    "fi_oil_gas_asset": "OILGASASSET",
    # 研发支出		开发支出(元)	DEVELOPEXP
    "fi_develop_exp": "DEVELOPEXP",
    # 非流动资产的调整项目		非流动资产其他项目(元)	NONLASSETOTHER
    "fi_nonl_asset_other": "NONLASSETOTHER",
    # 非流动资产的差错金额		非流动资产平衡项目(元)	NONLASSETBALANCE
    "fi_nonl_asset_balance": "NONLASSETBALANCE",
    # 资产的调整项目		资产其他项目(元)	ASSETOTHER
    "fi_asset_other": "ASSETOTHER",
    # 资产的差错金额		资产平衡项目(元)	ASSETBALANCE
    "fi_asset_balance": "ASSETBALANCE",
    # 向中央银行借款
    "fi_borrowings_from_central_bank": "BORROWFROMCBANK",
    # 拆入资金
    "fi_borrowings_from_fi": "BORROWFUND",
    # 交易性金融负债		交易性金融负债	TRADE_FINLIAB_NOTFVTPL
    "fi_trade_finliab_notfvtpl": "TRADE_FINLIAB_NOTFVTPL",
    # 衍生金融负债
    "fi_financial_derivative_liability": "DERIVEFLIAB",
    # 存款证及应付票据  应付票据
    "fi_notes_payable": "BILLPAY",
    # 卖出回购金融资产款
    "fi_sell_buy_back_fi_asset": "SELLBUYBACKFASSET",
    # 应付手续费及佣金
    "fi_fees_and_commissions_payable": "COMMPAY",
    # 应付股利		其中:应付股利(元)
    "fi_dividend_payable": "DIVIDENDPAY",
    # 代理买卖证券款
    "fi_receiving_as_agent": "AGENTTRADESECURITY",
    # 代理承销证券款		代理承销证券款(元)
    "fi_agentuw_security": "AGENTUWSECURITY",
    # 流动负债的调整项目		流动负债其他项目(元)
    "fi_lliab_other": "LLIABOTHER",
    # 流动负债的差错金额		流动负债平衡项目(元)
    "fi_lliab_balance": "LLIABBALANCE",
    # 专项应付款		专项应付款(元)	SPECIALPAY
    "fi_special_pay": "SPECIALPAY",
    # 预计负债
    "fi_estimated_liabilities": "ANTICIPATELIAB",
    # 非流动负债的调整项目		非流动负债其他项目(元)
    "fi_non_liab_other": "NONLLIABOTHER",
    # 非流动负债的差错金额		非流动负债平衡项目(元)
    "fi_non_liab_balance": "NONLLIABBALANCE",
    # 负债的调整项目		负债其他项目(元)	LIABOTHER
    "fi_liab_other": "LIABOTHER",
    # 负债的差错金额		负债平衡项目(元)	LIABBALANCE
    "fi_liab_balance": "LIABBALANCE",
    # 应付分保账款
    "fi_dividend_payable_for_reinsurance": "RIPAY",
}

add_func_to_value(balance_sheet_map, first_item_to_float)


class ChinaStockBalanceSheetRecorder(EmBaseChinaStockFinanceRecorder):
    data_schema = BalanceSheet

    finance_report_type = 'BalanceStatementSHSZ'
    data_type = 1

    def get_data_map(self):
        return balance_sheet_map


__all__ = ['ChinaStockBalanceSheetRecorder']

if __name__ == '__main__':
    # init_log('blance_sheet.log')
    recorder = ChinaStockBalanceSheetRecorder(codes=['002572'])
    recorder.run()
