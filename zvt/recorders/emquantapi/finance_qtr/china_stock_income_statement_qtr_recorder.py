# -*- coding: utf-8 -*-
from zvt.domain import IncomeStatementQtr
from zvt.recorders.emquantapi.finance_qtr.base_china_stock_finance_qtr_recorder import BaseChinaStockFinanceQtrRecorder
from zvt.utils.utils import add_func_to_value, first_item_to_float

income_statement_qtr_map = {
    # 更新时间
    "pub_date": "FIRSTNOTICEDATE",

    # 营业总收入(元)
    "total_op_income": "TOTALOPERATEREVE_S",
    # 营业收入
    "operating_income": "OPERATEREVE_S",
    # 营业总成本
    "total_operating_costs": "TOTALOPERATEEXP_S",
    # 营业成本
    "operating_costs": "OPERATEEXP_S",


    # 提取保险合同准备金净额
    "net_change_in_insurance_contract_reserves": "NETCONTACTRESERVE_S",
    # 营业税金及附加
    "business_taxes_and_surcharges": "OPERATETAX_S",
    # 销售费用
    "sales_costs": "SALEEXP_S",
    # 管理费用
    "managing_costs": "MANAGEEXP_S",
    # 财务费用
    "financing_costs": "FINANCEEXP_S",
    # 资产减值损失
    "assets_devaluation": "ASSETDEVALUELOSS_S",
    # 其他经营收益

    # 加: 投资收益
    "investment_income": "INVESTINCOME_S",
    # 其中: 对联营企业和合营企业的投资收益
    "investment_income_from_related_enterprise": "INVESTJOINTINCOME_S",
    # 营业利润
    "operating_profit": "OPERATEPROFIT_S",
    # 加: 营业外收入
    "non_operating_income": "NONOPERATEREVE_S",
    # 减: 营业外支出
    "non_operating_costs": "NONOPERATEEXP_S",
    # 其中: 非流动资产处置净损失
    "loss_on_disposal_non_current_asset": "NONLASSETNETLOSS_S",
    # 利润总额
    "total_profits": "SUMPROFIT_S",
    # 减: 所得税费用
    "tax_expense": "INCOMETAX_S",
    # 净利润
    "net_profit": "NETPROFIT_S",
    # 其中: 归属于母公司股东的净利润
    "net_profit_as_parent": "PARENTNETPROFIT_S",
    # 少数股东损益
    "net_profit_as_minority_interest": "MINORITYINCOME_S",
    # 其他综合收益
    "other_comprehensive_income": "OTHERCINCOME_S",
    # 综合收益总额
    "total_comprehensive_income": "SUMCINCOME_S",
    # 归属于母公司所有者的综合收益总额
    "total_comprehensive_income_as_parent": "PARENTCINCOME_S",
    # 归属于少数股东的综合收益总额
    "total_comprehensive_income_as_minority_interest": "MINORITYCINCOME_S",

    # 已赚保费(元)
    "fi_net_income_from_premium": "PREMIUMEARNED_S",
    # 手续费及佣金收入
    "fi_incomes_from_fees_and_commissions": "COMMREVE_S",
    #利息收入(元)
    "fi_interest_income": "INTREVE_S",
    # 利息支出(元)
    "fi_interest_expenses": "INTEXP_S",
    # 手续费及佣金支出(元)
    "fi_expenses_for_fees_and_commissions": "COMMEXP_S",
    # 退保金(元)
    "fi_insurance_surrender_costs": "SURRENDERPREMIUM_S",
    # 赔付支出净额(元)
    "fi_net_payouts": "NETINDEMNITYEXP_S",
    # 保单红利支出(元)
    "fi_dividend_expenses_to_insured": "POLICYDIVIEXP_S",
    # 分保费用
    "fi_reinsurance_expenses": "RIEXP_S",
    # 公允价值变动收益(损失以“-”号填列)
    "fi_income_from_fair_value_change": "FVALUEINCOME_S",
    # 汇兑收益(损失以“-”号填列)
    "fi_income_from_exchange": "EXCHANGEINCOME_S",
    # 资产处置收益
    "fi_asset_disposal_income": "ADISPOSALINCOME_S",
    # 其他收益
    "fi_other_income": "MIOTHERINCOME_S",
    # 持续经营净利润
    "fi_net_profit_continuing_operations": "CONTINUOUSONPROFIT_S",
    # 终止经营净利润
    "fi_iscontinued_operating_net_profit": "TERMINATIONONPROFIT_S",
}

add_func_to_value(income_statement_qtr_map, first_item_to_float)


class ChinaStockIncomeStatementQtrRecorder(BaseChinaStockFinanceQtrRecorder):

    data_schema = IncomeStatementQtr
    finance_report_type = 'IncomeStatementQSHSZ'
    data_type = 2

    def get_data_map(self):
        return income_statement_qtr_map


__all__ = ['ChinaStockIncomeStatementQtrRecorder']

if __name__ == '__main__':
    # init_log('income_statement.log')
    recorder = ChinaStockIncomeStatementQtrRecorder(codes=['002572'])
    recorder.run()
