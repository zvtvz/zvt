# -*- coding: utf-8 -*-
from zvt.domain import AuditOpinions
from zvt.recorders.emquantapi.finance.base_china_stock_finance_recorder import EmBaseChinaStockFinanceRecorder
from zvt.utils.utils import add_func_to_value, first_item_to_float

audit_opinions_map = {

    # 审计单位
    "audit_unit": "AGENCY",
    # 审计单位薪酬
    "audit_unit_pay": "AUDITPAY",
    # 审计年限(境内）
    "audit_year": "AUDITYEAR",
    # 非标意见说明
    # "non_standard_opinion_description": "INTERPRETATION",
    # 审计意见类别
    "audit_opinion_category": "CATEGORY",
    # 签字注册会计师
    "CPA": "CPA",
}

add_func_to_value(audit_opinions_map, first_item_to_float)


class ChinaStockAuditOpinionsRecorder(EmBaseChinaStockFinanceRecorder):

    data_schema = AuditOpinions

    finance_report_type = 'AuditOpinions'
    data_type = 17

    def get_data_map(self):
        return audit_opinions_map


__all__ = ['ChinaStockAuditOpinionsRecorder']

if __name__ == '__main__':
    # init_log('blance_sheet.log')
    recorder = ChinaStockAuditOpinionsRecorder(codes=['002572'])
    recorder.run()
