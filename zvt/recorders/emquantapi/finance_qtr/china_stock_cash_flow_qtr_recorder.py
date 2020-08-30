# -*- coding: utf-8 -*-

from zvt.utils.utils import add_func_to_value, first_item_to_float
from zvt.domain import CashFlowStatementQtr
from zvt.recorders.emquantapi.finance_qtr.base_china_stock_finance_qtr_recorder import BaseChinaStockFinanceQtrRecorder

cash_flow_qtr_map = {
    # 经营活动产生的现金流量
    # 报告时间
    "report_date": "REPORTDATE",
    # 销售商品、提供劳务收到的现金
    "cash_from_selling": "SALEGOODSSERVICEREC_S",

    # 收到的税费返还
    "tax_refund": "TAXRETURNREC_S",

    # 收到其他与经营活动有关的现金
    "cash_from_other_op": "OTHEROPERATEREC_S",

    # 经营活动现金流入小计
    "total_op_cash_inflows": "SUMOPERATEFLOWIN_S",

    # 购买商品、接受劳务支付的现金
    "cash_to_goods_services": "BUYGOODSSERVICEPAY_S",
    # 支付给职工以及为职工支付的现金
    "cash_to_employees": "EMPLOYEEPAY_S",
    # 支付的各项税费
    "taxes_and_surcharges": "TAXPAY_S",
    # 支付其他与经营活动有关的现金
    "cash_to_other_related_op": "OTHEROPERATEPAY_S",
    # 经营活动现金流出小计
    "total_op_cash_outflows": "SUMOPERATEFLOWOUT_S",

    # 经营活动产生的现金流量净额
    "net_op_cash_flows": "OPERATEFLOWOTHER_S",

    # 投资活动产生的现金流量

    # 收回投资收到的现金
    "cash_from_disposal_of_investments": "DISPOSALINVREC_S",
    # 取得投资收益收到的现金
    "cash_from_returns_on_investments": "INVINCOMEREC_S",
    # 处置固定资产、无形资产和其他长期资产收回的现金净额
    "cash_from_disposal_fixed_intangible_assets": "DISPFILASSETREC_S",
    # 处置子公司及其他营业单位收到的现金净额
    "cash_from_disposal_subsidiaries": "DISPSUBSIDIARYREC_S",

    # 收到其他与投资活动有关的现金
    "cash_from_other_investing": "OTHERINVREC_S",
    # 质押贷款净增加额
    "fi_insured_pledge_loans_increase": "NIPLEDGELOAN_S",
    # 投资活动现金流入小计
    "total_investing_cash_inflows": "SUMINVFLOWIN_S",

    # 购建固定资产、无形资产和其他长期资产支付的现金
    "cash_to_acquire_fixed_intangible_assets": "BUYFILASSETPAY_S",
    # 投资支付的现金
    "cash_to_investments": "INVPAY_S",

    # 取得子公司及其他营业单位支付的现金净额
    "cash_to_acquire_subsidiaries": "GETSUBSIDIARYPAY_S",

    # 支付其他与投资活动有关的现金
    "cash_to_other_investing": "OTHERINVPAY_S",

    # 投资活动现金流出小计
    "total_investing_cash_outflows": "SUMINVFLOWOUT_S",

    # 投资活动产生的现金流量净额
    "net_investing_cash_flows": "INVFLOWOTHER_S",
    # 支付保单红利的现金
    "fi_cash_to_dividends": "DIVIPAY_S",
    # 筹资活动产生的现金流量
    # 吸收投资收到的现金
    "cash_from_accepting_investment": "ACCEPTINVREC_S",
    # 子公司吸收少数股东投资收到的现金
    "cash_from_subsidiaries_accepting_minority_interest": "SUBSIDIARYACCEPT_S",
    # 取得借款收到的现金
    "cash_from_borrowings": "LOANREC_S",
    # 发行债券收到的现金
    "cash_from_issuing_bonds": "ISSUEBONDREC_S",
    # 收到其他与筹资活动有关的现金
    "cash_from_other_financing": "OTHERFINAREC_S",
    # 筹资活动现金流入小计
    "total_financing_cash_inflows": "SUMFINAFLOWIN_S",
    # 偿还债务支付的现金
    "cash_to_repay_borrowings": "REPAYDEBTPAY_S",
    # 分配股利、利润或偿付利息支付的现金
    "cash_to_pay_interest_dividend": "DIVIPROFITORINTPAY_S",
    # 子公司支付给少数股东的股利、利润
    "cash_to_pay_subsidiaries_minority_interest": "SUBSIDIARYPAY_S",
    # 支付其他与筹资活动有关的现金
    "cash_to_other_financing": "OTHERFINAPAY_S",
    # 筹资活动现金流出小计
    "total_financing_cash_outflows": "SUMFINAFLOWOUT_S",
    # 筹资活动产生的现金流量净额
    "net_financing_cash_flows": "FINAFLOWOTHER_S",
    # 汇率变动对现金及现金等价物的影响
    "foreign_exchange_rate_effect": "EFFECTEXCHANGERATE_S",
    # 现金及现金等价物净增加额
    "net_cash_increase": "NICASHEQUIOTHER_S",
    # 加: 期初现金及现金等价物余额
    "cash_at_beginning": "CASHEQUIBEGINNING_S",
    # 期末现金及现金等价物余额
    "cash": "CASHEQUIENDINGOTHER_S",

    # 客户存款和同业及其他金融机构存放款项净增加额
    "fi_deposit_increase": "NIDEPOSIT_S",
    # 向中央银行借款净增加额
    "fi_borrow_from_central_bank_increase": "NIBORROWFROMCBANK_S",
    # 拆入资金净增加额
    "fi_borrowing_increase": "NIBORROWFUND_S",
    # 回购业务资金净增加额
    "fi_cash_from_repurchase_increase": "NIBUYBACKFUND_S",

    # 收取利息、手续费及佣金的现金
    "fi_cash_from_interest_commission": "INTANDCOMMREC_S",

    # 保户储金及投资款净增加额
    "fi_insured_deposit_increase": "NIINSUREDDEPOSITINV_S",
    # 收到再保险业务现金净额
    "fi_cash_from_reinsurance": "NETRIREC_S",

    # 保险相关
    # 收到原保险合同保费取得的现金
    "fi_cash_from_premium_of_original": "PREMIUMREC_S",
    # 向其他金融机构拆入资金净增加额
    "fi_lending_from_increase": "NIBORROWFROMFI_S",
    # 处置交易性金融资产净增加额
    "fi_disposal_trade_asset_add": "NIDISPTRADEFASSET_S",
    # 客户贷款及垫款净增加额
    "fi_loan_advance_increase": "NILOANADVANCES_S",
    # 存放中央银行和同业款项及其他金融机构净增加额
    "fi_deposit_in_others_add": "NIDEPOSITINCBANKFI_S",
    # 支付原保险合同赔付等款项的现金
    "fi_cash_to_insurance_claim": "INDEMNITYPAY_S",
    # 支付利息、手续费及佣金的现金
    "fi_cash_to_interest_commission": "INTANDCOMMPAY_S",
    # 更新时间
    "pub_date": "FIRSTNOTICEDATE",
}
add_func_to_value(cash_flow_qtr_map, first_item_to_float)



class ChinaStockCashFlowRecorder(BaseChinaStockFinanceQtrRecorder):
    """
    合并现金流量表
    """
    data_schema = CashFlowStatementQtr

    finance_report_type = 'CashFlowStatementQSHSZ'
    data_type = 1

    def get_data_map(self):
        return cash_flow_qtr_map


__all__ = ['ChinaStockCashFlowRecorder']

if __name__ == '__main__':
    # init_log('cash_flow.log')
    recorder = ChinaStockCashFlowRecorder(codes=['002572'])
    recorder.run()
