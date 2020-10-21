# -*- coding: utf-8 -*-
from zvt.domain import FinanceDebtpayingAbility
from zvt.recorders.emquantapi.finance.base_china_stock_finance_recorder import EmBaseChinaStockFinanceRecorder
from zvt.utils.utils import add_func_to_value, first_item_to_float

financial_debtpayingability_map = {
    # 更新时间
    "report_date": "REPORTDATE",
    'debt_asset_ratio': 'LIBILITYTOASSET',  # 资产负债率
    'conservative_quick_ratio': 'CONSERVQUICKRATIO',  # 保守速动比率
    'equity_ratio': 'LIBILITYTOEQUITY',  # 产权比率
    'equity_to_interest_libility': 'EQUITYTOINTERESTLIBILITY',  # 归属母公司股东的权益与带息债务之比
    'equity_to_libility': 'EQUITYTOLIBILITY',  # 归属母公司股东的权益与负债合计之比
    # 'cash_to_current_libility': 'CASHTOCL',  # 货币资金与流动负债之比
    'cfo_to_interest_libility': 'CFOTOINTERESTLIBILITY',  # 经营活动产生的现金流量净额与带息债务之比
    'cfo_to_libility': 'CFOTOLIBILITY',  # 经营活动产生的现金流量净额与负债合计之比
    'cfo_to_net_libility': 'CFOTONETLIBILITY',  # 经营活动产生的现金流量净额与净债务之比
    'cfo_to_cl': 'CFOTOSHORTLIBILITY',  # 经营活动产生的现金流量净额与流动负债之比
    'current_ratio': 'CURRENTTATIO',  # 流动比率
    'quick_ratio': 'QUICKTATIO',  # 速动比率
    # 'ebitda_to_int_libility': 'EBITDATOINTLIBILITY',  # 息税折旧摊销前利润与带息债务之比
    'ebitda_to_libility': 'EBITDATOLIBILITY',  # 息税折旧摊销前利润与负债合计之比
    # 'op_to_libility': 'OPTOLIBILITY',  # 营业利润与负债合计之比
    # 'op_to_cl': 'OPTOCL',  # 营业利润与流动负债之比
    'tangible_asset_to_interest_libility': 'TANGIBLEASSETTOINTERESTLIBILITY',  # 有形资产与带息债务之比
    'tangible_asset_to_libility': 'TANGIBLEASSETTOLIBILITY',  # 有形资产与负债合计之比
    'tangible_asset_to_net_libility': 'TANGIBLEASSETTONETLIBILITY',  # 有形资产与净债务之比
    # 'times_inte_cf': '',  # 现金流量利息保障倍数
    # 'n_cf_opa_ncl': '',  # 经营活动现金流量净额与非流动负债之比
    # 'cash_icl': '',  # 货币资金与带息流动负债之比
    # 'tl_teap': '',  # 负债合计与归属于母公司的股东权益之比
    # 'ncl_wc': '',  # 非流动负债与营运资金比率之比
    # 'n_cf_nfa_cl': '',  # 非筹资性现金流量净额与流动负债之比
    # 'n_cf_nfa_liab': '',  # 非筹资性现金流量净额与负债总额之比
    # 'times_inte_ebit': '',  # EBIT利息保障倍数
    # 'times_inte_ebitda': '',  # EBITDA利息保障倍数
}
add_func_to_value(financial_debtpayingability_map, first_item_to_float)


class ChinaStockFinanceDebtpayingAbilityRecorder(EmBaseChinaStockFinanceRecorder):
    """
    财务指标-偿债能力
    """
    data_schema = FinanceDebtpayingAbility

    finance_report_type = 'FinanceDebtpayingAbility'

    data_type = 5

    def get_data_map(self):
        return financial_debtpayingability_map


__all__ = ['ChinaStockFinanceDebtpayingAbilityRecorder']

if __name__ == '__main__':
    # init_log('income_statement.log')
    recorder = ChinaStockFinanceDebtpayingAbilityRecorder(codes=['002572'])
    recorder.run()
