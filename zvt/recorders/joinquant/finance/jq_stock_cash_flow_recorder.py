# -*- coding: utf-8 -*-
from zvt.utils.time_utils import to_pd_timestamp
from zvt.utils.utils import add_func_to_value, first_item_to_float
from zvt.api.quote import to_report_period_type
from zvt.domain import CashFlowStatement
from zvt.recorders.joinquant.finance.base_jq_stock_finance_recorder import BaseJqStockFinanceRecorder

cash_flow_map = {
    # 经营活动产生的现金流量
    #
    # 销售商品、提供劳务收到的现金
    "cash_from_selling": "goods_sale_and_service_render_cash",

    # 收到的税费返还
    "tax_refund": "tax_levy_refund",

    # 收到其他与经营活动有关的现金
    ### "cash_from_other_op": "Otheroperaterec",

    # 经营活动现金流入小计
    "total_op_cash_inflows": "subtotal_operate_cash_inflow",

    # 购买商品、接受劳务支付的现金
    "cash_to_goods_services": "goods_and_services_cash_paid",
    # 支付给职工以及为职工支付的现金
    "cash_to_employees": "staff_behalf_paid",
    # 支付的各项税费
    "taxes_and_surcharges": "tax_payments",
    # 支付其他与经营活动有关的现金
    ###"cash_to_other_related_op": "Otheroperatepay",
    # 经营活动现金流出小计
    "total_op_cash_outflows": "subtotal_operate_cash_outflow",

    # 经营活动产生的现金流量净额
    "net_op_cash_flows": "net_operate_cash_flow2",

    # 投资活动产生的现金流量

    # 收回投资收到的现金
    "cash_from_disposal_of_investments": "invest_withdrawal_cash",
    # 取得投资收益收到的现金
    "cash_from_returns_on_investments": "invest_proceeds",
    # 处置固定资产、无形资产和其他长期资产收回的现金净额
    "cash_from_disposal_fixed_intangible_assets": "fix_intan_other_asset_dispo_cash",
    # 处置子公司及其他营业单位收到的现金净额
    "cash_from_disposal_subsidiaries": "net_cash_deal_subcompany",

    # 收到其他与投资活动有关的现金
    ###"cash_from_other_investing": "Otherinvrec",

    # 投资活动现金流入小计
    "total_investing_cash_inflows": "subtotal_invest_cash_inflow",

    # 购建固定资产、无形资产和其他长期资产支付的现金
    "cash_to_acquire_fixed_intangible_assets": "fix_intan_other_asset_acqui_cash",
    # 投资支付的现金
    "cash_to_investments": "invest_cash_paid",

    # 取得子公司及其他营业单位支付的现金净额
    "cash_to_acquire_subsidiaries": "net_cash_from_sub_company",

    # 支付其他与投资活动有关的现金
    ###"cash_to_other_investing": "Otherinvpay",

    # 投资活动现金流出小计
    "total_investing_cash_outflows": "subtotal_invest_cash_outflow",

    # 投资活动现金流量净额
    "net_investing_cash_flows": "net_invest_cash_flow",

    # 筹资活动产生的现金流量
    #
    # 吸收投资收到的现金
    "cash_from_accepting_investment": "cash_from_invest",
    # 子公司吸收少数股东投资收到的现金
    "cash_from_subsidiaries_accepting_minority_interest": "cash_from_mino_s_invest_sub",

    # 取得借款收到的现金
    "cash_from_borrowings": "cash_from_borrowing",
    # 发行债券收到的现金
    "cash_from_issuing_bonds": "cash_from_bonds_issue",
    # 收到其他与筹资活动有关的现金
    ###"cash_from_other_financing": "Otherfinarec",

    # 筹资活动现金流入小计
    "total_financing_cash_inflows": "subtotal_finance_cash_inflow",

    # 偿还债务支付的现金
    "cash_to_repay_borrowings": "borrowing_repayment",

    # 分配股利、利润或偿付利息支付的现金
    "cash_to_pay_interest_dividend": "dividend_interest_payment",

    # 子公司支付给少数股东的股利、利润
    "cash_to_pay_subsidiaries_minority_interest": "proceeds_from_sub_to_mino_s",

    # 支付其他与筹资活动有关的现金
    ###"cash_to_other_financing": "Otherfinapay",
    # 筹资活动现金流出小计
    "total_financing_cash_outflows": "subtotal_finance_cash_outflow",

    # 筹资活动产生的现金流量净额
    "net_financing_cash_flows": "net_finance_cash_flow",
    # 汇率变动对现金及现金等价物的影响
    "foreign_exchange_rate_effect": "exchange_rate_change_effect",
    # 现金及现金等价物净增加额
    "net_cash_increase": "cash_equivalent_increase",
    # 加: 期初现金及现金等价物余额
    "cash_at_beginning": "cash_equivalents_at_beginning",
    # 期末现金及现金等价物余额
    "cash": "cash_and_equivalents_at_end",

    # 银行相关
    # 客户存款和同业及其他金融机构存放款项净增加额
    "fi_deposit_increase": "net_deposit_increase",
    # 向中央银行借款净增加额
    "fi_borrow_from_central_bank_increase": "net_borrowing_from_central_bank",
    # 存放中央银行和同业款项及其他金融机构净减少额
    "fi_deposit_in_others_decrease": "net_deposit_in_cb_and_ib_de",
    # 拆入资金及卖出回购金融资产款净增加额
    "fi_borrowing_and_sell_repurchase_increase": "net_increase_in_placements",
    # 其中:卖出回购金融资产款净增加额
    ###"fi_sell_repurchase_increase": "Nisellbuybackfasset",
    # 拆出资金及买入返售金融资产净减少额
    ###"fi_lending_and_buy_repurchase_decrease": "Ndlendbuysellback",
    # 其中:拆出资金净减少额
    ###"fi_lending_decrease": "Ndlendfund",
    # 买入返售金融资产净减少额
    ###"fi_buy_repurchase_decrease": "Ndbuysellbackfasset",
    # 收取的利息、手续费及佣金的现金
    "fi_cash_from_interest_commission": "interest_and_commission_cashin",
    # 客户贷款及垫款净增加额
    "fi_loan_advance_increase": "net_loan_and_advance_increase",
    # 存放中央银行和同业及其他金融机构款项净增加额
    "fi_deposit_in_others_increase": "net_deposit_in_cb_and_ib",
    # 拆出资金及买入返售金融资产净增加额
    ###"fi_lending_and_buy_repurchase_increase": "Nilendsellbuyback",
    # 其中:拆出资金净增加额
    # 向其他金融机构拆出资金净增加额
    "fi_lending_increase": "other_money_increase",
    # 拆入资金及卖出回购金融资产款净减少额
    ###"fi_borrowing_and_sell_repurchase_decrease": "Ndborrowsellbuyback",
    # 其中:拆入资金净减少额
    ###"fi_borrowing_decrease": "Ndborrowfund",
    # 卖出回购金融资产净减少额
    ###"fi_sell_repurchase_decrease": "Ndsellbuybackfasset",
    # 支付利息、手续费及佣金的现金
    "fi_cash_to_interest_commission": "handling_charges_and_commission",
    # 应收账款净增加额
    ###"fi_account_receivable_increase": "Niaccountrec",
    # 偿付债券利息支付的现金
    ###"fi_cash_to_pay_interest": "Bondintpay",

    # 保险相关
    # 收到原保险合同保费取得的现金
    "fi_cash_from_premium_of_original": "net_original_insurance_cash",
    # 保户储金及投资款净增加额
    "fi_insured_deposit_increase": "net_insurer_deposit_investment",
    # 银行及证券业务卖出回购资金净增加额
    ###"fi_bank_broker_sell_repurchase_increase": "Nisellbuyback",
    # 银行及证券业务买入返售资金净减少额
    ###"fi_bank_broker_buy_repurchase_decrease": "Ndbuysellback",
    # 支付原保险合同赔付等款项的现金
    "fi_cash_to_insurance_claim": "original_compensation_paid",
    # 支付再保险业务现金净额
    "fi_cash_to_reinsurance": "net_cash_re_insurance",
    # 银行业务及证券业务拆借资金净减少额
    ###"fi_lending_decrease": "Ndlendfund",
    # 银行业务及证券业务卖出回购资金净减少额
    ###"fi_bank_broker_sell_repurchase_decrease": "Ndsellbuyback",
    # 支付保单红利的现金
    "fi_cash_to_dividends": "policy_dividend_cash_paid",
    # 保户质押贷款净增加额
    ###"fi_insured_pledge_loans_increase": "Niinsuredpledgeloan",
    # 收购子公司及其他营业单位支付的现金净额
    ###"fi_cash_to_acquire_subsidiaries": "Buysubsidiarypay",
    # 处置子公司及其他营业单位流出的现金净额
    ###"fi_cash_to_disposal_subsidiaries": "Dispsubsidiarypay",
    # 支付卖出回购金融资产款现金净额
    ###"fi_cash_to_sell_repurchase": "Netsellbuybackfassetpay",

    # 券商相关
    # 拆入资金净增加额
    "fi_borrowing_increase": "net_increase_in_placements",
    # 代理买卖证券收到的现金净额
    ### "fi_cash_from_trading_agent": "Agenttradesecurityrec",
    # 回购业务资金净增加额
    "fi_cash_from_repurchase_increase": "net_buyback",
    # 处置交易性金融资产的净减少额
    ###"fi_disposal_trade_asset_decrease": "Nddisptradefasset",
    # 回购业务资金净减少额
    "fi_repurchase_decrease": "repurchase_decrease",
    # 代理买卖证券支付的现金净额（净减少额）
    "fi_cash_to_agent_trade": "agent_security_income",
}

add_func_to_value(cash_flow_map, first_item_to_float)
cash_flow_map["report_period"] = ("ReportDate", to_report_period_type)
cash_flow_map["report_date"] = ("ReportDate", to_pd_timestamp)
# cash_flow_map["ReportDate"] = ("report_period", to_report_period_type)
# cash_flow_map["ReportDate"] = ("report_date", to_pd_timestamp)

class JqStockCashFlowRecorder(BaseJqStockFinanceRecorder):
    data_schema = CashFlowStatement

    finance_report_type = 'CASHFLOW_STATEMENT'
    data_type = 4

    def get_data_map(self):
        return cash_flow_map


__all__ = ['JqStockCashFlowRecorder']

if __name__ == '__main__':
    # init_log('cash_flow.log')
    recorder = JqStockCashFlowRecorder(codes=['002572'])
    recorder.run()
