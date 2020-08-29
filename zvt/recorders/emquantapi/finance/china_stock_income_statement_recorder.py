# -*- coding: utf-8 -*-
from zvt.utils.time_utils import to_pd_timestamp
from zvt.utils.utils import add_func_to_value, first_item_to_float
from zvt.api.quote import to_report_period_type
from zvt.domain import IncomeStatement
from zvt.recorders.eastmoney.finance.base_china_stock_finance_recorder import BaseChinaStockFinanceRecorder

income_statement_map = {
    # 更新时间
    "pub_date": "FIRSTNOTICEDATE",
    "report_date": "REPORTDATE",
    # 营业总收入
    "total_op_income": "Totalincome",
    # 营业收入
    "operating_income": "OPERATEREVE",
    # 营业总成本
    "total_operating_costs": "TOTALOPERATEEXP",
    # 营业成本
    "operating_costs": "OPERATEEXP",
    # 研发费用
    # "rd_costs": "Rdexp",
    # 提取保险合同准备金净额
    "net_change_in_insurance_contract_reserves": "NETCONTACTRESERVE",
    # 营业税金及附加
    "business_taxes_and_surcharges": "OPERATETAX",
    # 销售费用
    "sales_costs": "SALEEXP",
    # 管理费用
    "managing_costs": "MANAGEEXP",
    # 财务费用
    "financing_costs": "FINANCEEXP",
    # 资产减值损失
    "assets_devaluation": "ASSETDEVALUELOSS",
    # 其他经营收益
    #
    # 加: 投资收益
    "investment_income": "INVESTINCOME",
    # 其中: 对联营企业和合营企业的投资收益
    "investment_income_from_related_enterprise": "INVESTJOINTINCOME",
    # 营业利润
    "operating_profit": "OPERATEPROFIT",
    # 加: 营业外收入
    "non_operating_income": "NONOPERATEREVE",
    # 减: 营业外支出
    "non_operating_costs": "NONOPERATEEXP",
    # 其中: 非流动资产处置净损失
    "loss_on_disposal_non_current_asset": "NONLASSETNETLOSS",

    # 利润总额
    "total_profits": "SUMPROFIT",
    # 减: 所得税费用
    "tax_expense": "INCOMETAX",
    # 净利润
    "net_profit": "NETPROFIT",
    # 其中: 归属于母公司股东的净利润
    "net_profit_as_parent": "PARENTNETPROFIT",
    # 少数股东损益
    "net_profit_as_minority_interest": "MINORITYINCOME",

    # 每股收益
    # 基本每股收益
    "eps": "BASICEPS",
    # 稀释每股收益
    "diluted_eps": "DILUTEDEPS",
    # 其他综合收益
    "other_comprehensive_income": "OTHERCINCOME",

    # 综合收益总额
    "total_comprehensive_income": "SUMCINCOME",
    # 归属于母公司所有者的综合收益总额
    "total_comprehensive_income_as_parent": "PARENTCINCOME",
    # 归属于少数股东的综合收益总额
    "total_comprehensive_income_as_minority_interest": "MINORITYCINCOME",
    # 公允价值变动收益
    "fi_income_from_fair_value_change": "FVALUEINCOME",

    # 汇兑收益
    "fi_income_from_exchange": "EXCHANGEINCOME",
    # 其中:利息收入
    "fi_interest_income": "INTREVE",
    # 已赚保费
    "fi_net_income_from_premium": "PREMIUMEARNED",
    # 其中:手续费及佣金收入
    "fi_incomes_from_fees_and_commissions": "COMMREVE",
    # 利息支出
    "fi_interest_expenses": "INTEXP",
    # 手续费及佣金支出
    "fi_expenses_for_fees_and_commissions": "COMMEXP",
    # 退保金
    "fi_insurance_surrender_costs": "SURRENDERPREMIUM",
    # 保单红利支出
    "fi_dividend_expenses_to_insured": "POLICYDIVIEXP",
    # 分保费用
    "fi_reinsurance_expenses": "RIEXP",
    # 赔付支出净额
    "fi_net_payouts": "NETINDEMNITYEXP",
    # 资产处置收益
    "fi_asset_disposal_income": "ADISPOSALINCOME",
    # 其他收益
    "fi_other_income": "MIOTHERINCOME",
    # 持续经营净利润
    "fi_net_profit_continuing_operations": "CONTINUOUSONPROFIT",
    # 终止经营净利润
    "fi_iscontinued_operating_net_profit": "TERMINATIONONPROFIT",
}

add_func_to_value(income_statement_map, first_item_to_float)



class ChinaStockIncomeStatementRecorder(BaseChinaStockFinanceRecorder):
    data_schema = IncomeStatement

    finance_report_type = 'LiRunBiaoList'

    data_type = 2

    def get_data_map(self):
        return income_statement_map


__all__ = ['ChinaStockIncomeStatementRecorder']

if __name__ == '__main__':
    # init_log('income_statement.log')
    recorder = ChinaStockIncomeStatementRecorder(codes=['002572'])
    recorder.run()
