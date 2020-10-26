# -*- coding: utf-8 -*-
from zvt.domain import CashFlowStatement
from zvt.recorders.emquantapi.finance.base_china_stock_finance_recorder import EmBaseChinaStockFinanceRecorder
from zvt.utils.utils import add_func_to_value, first_item_to_float

cash_flow_map = {
    # 更新时间
    "pub_date": "FIRSTNOTICEDATE",
    "report_date": "REPORTDATE",
    # 经营活动产生的现金流量
    #
    # 销售商品、提供劳务收到的现金
    "cash_from_selling": "SALEGOODSSERVICEREC",

    # 收到的税费返还
    "tax_refund": "TAXRETURNREC",

    # 收到其他与经营活动有关的现金
    "cash_from_other_op": "OTHEROPERATEREC",
    # 质押贷款净增加额
    "fi_insured_pledge_loans_increase": "NIPLEDGELOAN",
    # 经营活动现金流入小计
    "total_op_cash_inflows": "SUMOPERATEFLOWIN",

    # 购买商品、接受劳务支付的现金
    "cash_to_goods_services": "BUYGOODSSERVICEPAY",

    # 支付给职工以及为职工支付的现金
    "cash_to_employees": "EMPLOYEEPAY",
    # 支付的各项税费
    "taxes_and_surcharges": "TAXPAY",
    # 支付其他与经营活动有关的现金
    "cash_to_other_related_op": "OTHEROPERATEPAY",
    # 经营活动现金流出小计
    "total_op_cash_outflows": "SUMOPERATEFLOWOUT",

    # 经营活动产生的现金流量净额
    "net_op_cash_flows": "NETOPERATECASHFLOW",
    # 处置固定资产、无形资产和其他长期资产收回的现金净额
    "cash_from_disposal_fixed_intangible_assets": "DISPFILASSETREC",
    # 投资活动产生的现金流量

    # 收回投资收到的现金
    "cash_from_disposal_of_investments": "DISPOSALINVREC",
    # 取得投资收益收到的现金
    "cash_from_returns_on_investments": "INVINCOMEREC",

    # 处置子公司及其他营业单位收到的现金净额
    "cash_from_disposal_subsidiaries": "DISPSUBSIDIARYREC",

    # 收到其他与投资活动有关的现金
    "cash_from_other_investing": "OTHERINVREC",

    # 投资活动现金流入小计
    "total_investing_cash_inflows": "SUMINVFLOWIN",

    # 购建固定资产、无形资产和其他长期资产支付的现金
    "cash_to_acquire_fixed_intangible_assets": "BUYFILASSETPAY",
    # 投资支付的现金
    "cash_to_investments": "INVPAY",

    # 取得子公司及其他营业单位支付的现金净额
    "cash_to_acquire_subsidiaries": "GETSUBSIDIARYPAY",

    # 支付其他与投资活动有关的现金
    "cash_to_other_investing": "OTHERINVPAY",

    # 投资活动现金流出小计
    "total_investing_cash_outflows": "SUMINVFLOWOUT",

    # 投资活动产生的现金流量净额
    "net_investing_cash_flows": "NETINVCASHFLOW",

    # 筹资活动产生的现金流量
    #
    # 吸收投资收到的现金
    "cash_from_accepting_investment": "ACCEPTINVREC",
    # 子公司吸收少数股东投资收到的现金
    "cash_from_subsidiaries_accepting_minority_interest": "SUBSIDIARYACCEPT",

    # 取得借款收到的现金
    "cash_from_borrowings": "LOANREC",
    # 发行债券收到的现金
    "cash_from_issuing_bonds": "ISSUEBONDREC",
    # 收到其他与筹资活动有关的现金
    "cash_from_other_financing": "OTHERFINAREC",

    # 筹资活动现金流入小计
    "total_financing_cash_inflows": "SUMFINAFLOWIN",

    # 偿还债务支付的现金
    "cash_to_repay_borrowings": "REPAYDEBTPAY",

    # 分配股利、利润或偿付利息支付的现金
    "cash_to_pay_interest_dividend": "DIVIPROFITORINTPAY",

    # 子公司支付给少数股东的股利、利润
    "cash_to_pay_subsidiaries_minority_interest": "SUBSIDIARYPAY",

    # 支付其他与筹资活动有关的现金
    "cash_to_other_financing": "OTHERFINAPAY",
    # 筹资活动现金流出小计
    "total_financing_cash_outflows": "SUMFINAFLOWOUT",

    # 筹资活动产生的现金流量净额
    "net_financing_cash_flows": "NETFINACASHFLOW",
    # 汇率变动对现金及现金等价物的影响
    "foreign_exchange_rate_effect": "EFFECTEXCHANGERATE",
    # 现金及现金等价物净增加额
    "net_cash_increase": "NICASHEQUI",
    # 加: 期初现金及现金等价物余额
    "cash_at_beginning": "CASHEQUIBEGINNING",
    # 期末现金及现金等价物余额
    "cash": "CASHEQUIENDING",
    # 客户存款和同业及其他金融机构存放款项净增加额
    # 客户存款和同业存放款项净增加额
    "fi_deposit_increase": "NIDEPOSIT",
    # 支付保单红利的现金
    "fi_cash_to_dividends": "DIVIPAY",
    # 向中央银行借款净增加额
    "fi_borrow_from_central_bank_increase": "NIBORROWFROMCBANK",
    # 向其他金融机构拆入资金净增加额
    "fi_lending_from_increase": "NIBORROWFROMFI",
    # 收到原保险合同保费取得的现金
    "fi_cash_from_premium_of_original": "PREMIUMREC",
    # 收到再保险业务现金净额
    "fi_cash_from_reinsurance": "NETRIREC",
    # 保户储金及投资款净增加额
    "fi_insured_deposit_increase": "NIINSUREDDEPOSITINV",

    # 处置交易性金融资产净增加额
    "fi_disposal_trade_asset_add": "NIDISPTRADEFASSET",
    # 客户贷款及垫款净增加额
    "fi_loan_advance_increase": "NILOANADVANCES",
    # 存放中央银行和同业款项净增加
    "fi_deposit_in_others_add": "NIDEPOSITINCBANKFI",
    # 支付原保险合同赔付款项的现金
    "fi_cash_to_insurance_claim": "INDEMNITYPAY",
    # 支付利息、手续费及佣金的现金
    "fi_cash_to_interest_commission": "INTANDCOMMPAY",
    # 收取的利息、手续费及佣金的现金 收取利息、手续费及佣金的现金
    "fi_cash_from_interest_commission": "INTANDCOMMREC",
    # 拆入资金净增加额
    "fi_borrowing_increase": "NIBORROWFUND",
    # 回购业务资金净增加额
    "fi_cash_from_repurchase_increase": "NIBUYBACKFUND",

    # 经营活动现金流入的调整项目
    # 经营活动现金流入的其他项目
    "fi_operate_flow_inother": "OPERATEFLOWINOTHER",

    # 经营活动现金流入的差错金额
    # 经营活动现金流入的平衡项目(元)
    "fi_operate_flow_in_balance": "OPERATEFLOWINBALANCE",
    # 经营活动现金流量净额的差错金额
    # 经营活动产生的现金流量净额其他项目(元)
    "fi_operate_flow_other": "OPERATEFLOWOTHER",

    # 投资活动现金流入的调整项目
    # 投资活动现金流入的其他项目(元)
    "fi_inv_flow_in_other": "INVFLOWINOTHER",
    # 投资活动现金流入的差错金额
    # 投资活动现金流入的平衡项目(元)
    "fi_inv_flow_in_balance": "INVFLOWINBALANCE",

    # 投资活动现金流出的调整项目
    # 投资活动现金流出的其他项目(元)
    "fi_inv_flow_out_other": "INVFLOWOUTOTHER",
    # 投资活动现金流出的差错金额
    # 投资活动现金流出的平衡项目(元)
    "fi_inv_flow_out_balance": "INVFLOWOUTBALANCE",

    # 投资活动现金流量净额的差错金额
    # 投资活动产生的现金流量净额其他项目(元)
    "fi_inv_flow_other": "INVFLOWOTHER",

    # 筹资活动现金流入的调整项目
    # 筹资活动现金流入的其他项目(元)
    "fi_fina_flow_in_other": "FINAFLOWINOTHER",

    # 筹资活动现金流入的差错金额
    # 筹资活动现金流入的平衡项目(元)
    "fi_fina_flow_in_balance": "FINAFLOWINBALANCE",

    # 筹资活动现金流出的调整项目
    # 其中:子公司减资支付给少数股东的现金(元)
    "fi_subsidiary_reduct_capital": "SUBSIDIARYREDUCTCAPITAL",
    # 筹资活动现金流出的差错金额
    # 筹资活动现金流出的其他项目(元)
    "fi_fina_flow_out_other": "FINAFLOWOUTOTHER",

    # 筹资活动现金流量净额的差错金额
    # 筹资活动产生的现金流量净额其他项目(元)
    "fi_fina_flow_other": "FINAFLOWOTHER",
    # 影响现金及现金等价物的调整项目		现金及现金等价物净增加额其他项目(元)
    "fi_ni_cash_equi_other": "NICASHEQUIOTHER",
    # 影响现金及现金等价物的差错金额		现金及现金等价物净增加额平衡项目(元)
    "fi_ni_cash_equi_balance": "NICASHEQUIBALANCE",
    # 影响期末现金及现金等价物余额的调整项目		期末现金及现金等价物余额其他项目(元)
    "fi_cash_equi_ending_other": "CASHEQUIENDINGOTHER",
    # 影响期末现金及现金等价物余额的差错金额		期末现金及现金等价物余额平衡项目(元)
    "fi_cash_equi_ending_balance": "CASHEQUIENDINGBALANCE",
    # 经营活动现金流出的调整项目		经营活动现金流出的其他项目(元)
    "fi_operate_flow_out_other": "OPERATEFLOWOUTOTHER",
    # 经营活动现金流出的差错金额		经营活动现金流出的平衡项目(元)
    "fi_operate_flow_out_balance": "OPERATEFLOWOUTBALANCE",

}

add_func_to_value(cash_flow_map, first_item_to_float)


class ChinaStockCashFlowRecorder(EmBaseChinaStockFinanceRecorder):
    data_schema = CashFlowStatement

    finance_report_type = 'CashFlowStatementSHSZ'
    data_type = 2

    def get_data_map(self):
        return cash_flow_map


__all__ = ['ChinaStockCashFlowRecorder']

if __name__ == '__main__':
    # init_log('cash_flow.log')
    recorder = ChinaStockCashFlowRecorder(codes=['002572'])
    recorder.run()
