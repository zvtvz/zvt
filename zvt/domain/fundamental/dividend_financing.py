# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base

from zvt.contract import Mixin
from zvt.contract.register import register_schema

DividendFinancingBase = declarative_base()


class DividendFinancing(DividendFinancingBase, Mixin):
    __tablename__ = 'dividend_financing'

    provider = Column(String(length=32))
    code = Column(String(length=32))

    # 分红总额
    dividend_money = Column(Float)

    # 新股
    ipo_issues = Column(Float)
    ipo_raising_fund = Column(Float)

    # 增发
    spo_issues = Column(Float)
    spo_raising_fund = Column(Float)
    # 配股
    rights_issues = Column(Float)
    rights_raising_fund = Column(Float)


dividenddetail_map = {
    "DIVAGMANNCDATE": "announcement_date_general_meeting",  # 股东大会公告日
    "DIVEXDATE": "dividend_date",  # 除权除息日
    "DIVRECORDDATE": "record_date",  # 股权登记日
    "DIVIMPLANNCDATE": "announce_date_dividend_implementation",  # 分红实施公告日
    "DIVLASTTRDDATESHAREB": "last_trading_day_b_shares",  # B股最后交易日
    "DIVCASHPSAFTAX": "dividend_per_share_after_tax",  # 每股股利(税后)
    "DIVCASHPSBFTAX": "dividend_per_share_before_tax",  # 每股股利(税前)
    "DIVPROGRESS": "dividend_plan_progress",  # 分红方案进度
    "DIVPAYDATE": "dividend_pay_date",  # 派息日
    "DIVSTOCKPS": "share_bonus_per_share",  # 每股送股比例
    "DIVCAPITALIZATIONPS": "per_share_conversion_ratio",  # 每股转增比例
    "DIVCASHANDSTOCKPS": "dividend",  # 分红送转方案
}


funddividenddetail_map = {
    "pub_date": "announce_date",  # 除权除息日
    "ex_date": "dividend_date",  # 除权除息日
    "record_date": "record_date",  # 股权登记日
    "pay_date": "dividend_pay_date",  # 派息日
    "dividend_implement_date": "announce_date_dividend_implementation",  # 分红实施公告日

    "proportion": "dividend_per_share_after_tax",  # 每股股利(税后)

    "split_ratio": "split_ratio",  # 分拆（合并、赠送）比例
    "process": "dividend_plan_progress",  # 分红方案进度
}


class FundDividendDetail(DividendFinancingBase, Mixin):
    """
    基金拆分、分红明细
    """
    __tablename__ = "fund_dividend_detail"

    def get_data_map(self):
        return funddividenddetail_map

    provider = Column(String(length=32))
    code = Column(String(length=32))

    announce_date = Column(DateTime)  # 公告日  DIVRECORDDATE  pub_date  公告日
    record_date = Column(DateTime)  # 股权登记日
    dividend_date = Column(DateTime)  # 除权除息日 DIVEXDATE 除权除息日  #ex_date 除息日 date  fund_paid_date	基金红利派发日
    announce_date_dividend_implementation = Column(DateTime)   # 分红实施公告日  #dividend_implement_date 分红实施公告日
    # 派息日
    dividend_pay_date = Column(DateTime)
    # 每股股利(税后)
    dividend_per_share_after_tax = Column(Float)
    # 分拆（合并、赠送）比例
    split_ratio = Column(Float)
    # 分红方案进度
    dividend_plan_progress = Column(String(length=128))




class DividendDetail(DividendFinancingBase, Mixin):
    """
    分红明细
    """
    __tablename__ = "dividend_detail"

    def get_data_map(self):
        return dividenddetail_map

    provider = Column(String(length=32))
    code = Column(String(length=32))

    report_date = Column(DateTime)    # 报告时间
    announce_date = Column(DateTime)  # 公告日  DIVRECORDDATE
    record_date = Column(DateTime)  # 股权登记日
    dividend_date = Column(DateTime)  # 除权除息日 DIVEXDATE 除权除息日
    dividend = Column(String(length=128))    #方案
    announce_date_general_meeting = Column(DateTime)   # 股东大会公告日
    announce_date_dividend_implementation = Column(DateTime)   # 分红实施公告日
    # B股最后交易日
    last_trading_day_b_shares = Column(DateTime)
    # 每股股利(税后)
    dividend_per_share_after_tax = Column(Float)
    # 每股股利(税前)
    dividend_per_share_before_tax = Column(Float)
    # 分红方案进度
    dividend_plan_progress = Column(String(length=128))
    # 派息日
    dividend_pay_date = Column(DateTime)
    # 每股送股比例
    share_bonus_per_share = Column(Float)
    # 每股转增比例
    per_share_conversion_ratio = Column(Float)


class SpoDetail(DividendFinancingBase, Mixin):
    __tablename__ = "spo_detail"

    provider = Column(String(length=32))
    code = Column(String(length=32))

    spo_issues = Column(Float)
    spo_price = Column(Float)
    spo_raising_fund = Column(Float)


rightsissuedetail_map = {
    "RTISSANNCDATE": "rtiss_announcement_date",  # 配股公告日
    "RTISSREGISTDATE": "record_date",  # 股权登记日
    "RTISSEXDIVDATE": "rtiss_date",  # 配股除权日
    "RTISSLISTDATE": "rtiss_listing_date",  # 配股上市日
    "RTISSPAYSDATE": "rtiss_pays_date",  # 缴款起始日
    "RTISSPAYEDATE": "rtiss_paye_date",  # 缴款终止日
    "RTISSPERTISSHARE": "rtiss_per_share",  # 每股配股数
    "RTISSBASESHARES": "rtiss_base_shares",  # 基准股本
    "RTISSPLANNEDVOL": "rtiss_plan_number",  # 计划配股数
    "RTISSACTVOL": "rights_issues",  # 实际配股
    "RTISSPRICE": "rights_issue_price",  # 配股价格
    "RTISSCOLLECTION": "rights_raising_fund",  # 实际募集资金
    "RTISSNETCOLLECTION": "rtiss_net_proceeds",  # 配股募集资金净额
    "RTISSEXPENSE": "rtiss_tax",  # 配股费用

}


class RightsIssueDetail(DividendFinancingBase, Mixin):
    """
    配股
    """
    __tablename__ = "rights_issue_detail"

    def get_data_map(self):
        return rightsissuedetail_map

    provider = Column(String(length=32))
    code = Column(String(length=32))

    rights_issues = Column(Float)  # 实际配股
    rights_issue_price = Column(Float)  # 配股价格
    rights_raising_fund = Column(Float)  # 实际募集资金
    # 配股公告日
    rtiss_announcement_date = Column(DateTime)
    # 股权登记日
    record_date = Column(DateTime)
    # 配股除权日
    rtiss_date = Column(DateTime)

    rtiss_listing_date = Column(DateTime)   # 配股上市日
    rtiss_pays_date = Column(DateTime)  # 缴款起始日
    rtiss_paye_date = Column(DateTime) # 缴款终止日
    rtiss_per_share = Column(Float)  # 每股配股数
    # 基准股本
    rtiss_base_shares = Column(Float)
    # 计划配股数
    rtiss_plan_number = Column(Float)
    # 配股募集资金
    rtiss_raise_funds = Column(Float)
    # 配股募集资金净额
    rtiss_net_proceeds = Column(Float)
    # 配股费用
    rtiss_tax = Column(Float)


# class StkXrXd(DividendFinancingBase, Mixin):
#     """
#     上市公司分红送股（除权除息）数据
#     """
#     __tablename__ = 'stk_xr_xd'
#     provider = Column(String(length=32))
#     code = Column(String(length=32))
#
#     report_date = Column(DateTime)  # 实施方案公告日期
#     pub_date = Column(DateTime)  # 股东大会预案公告日期
#
#     bonus_type = Column(String(length=32))  # 分红类型
#     board_plan_bonusnote = Column(String(length=32))  # 董事会预案分红说明
#     distributed_share_base_board = Column(Float)  # 分配股本基数（董事会）
#     shareholders_plan_bonusnote = Column(String(length=32))  # 股东大会预案分红说明
#     distributed_share_base_shareholders = Column(Float)  # 分配股本基数（股东大会）
#
#     implementation_bonusnote = Column(String(length=32))  # 实施方案分红说明
#     distributed_share_base_implement = Column(Float)  # 分配股本基数（实施）
#     dividend_ratio = Column(Float)  # 送股比例
#     transfer_ratio = Column(Float)  # 转增比例
#     bonus_ratio_rmb = Column(Float)  # 派息比例(人民币)
#     bonus_ratio_usd = Column(Float)  # 派息比例（美元）
#     bonus_ratio_hkd = Column(Float)  # 派息比例（港币）
#     at_bonus_ratio_rmb = Column(Float)  # 税后派息比例（人民币）
#     exchange_rate = Column(Float)  # 汇率
#     dividend_number = Column(Float)  # 送股数量
#     transfer_number = Column(Float)  # 转增数量
#     bonus_amount_rmb = Column(Float)  # 派息金额(人民币)
#     a_registration_date = Column(DateTime)  # A股股权登记日
#     b_registration_date = Column(DateTime)  # B股股权登记日
#     a_xr_date = Column(DateTime)  # A股除权日
#     b_xr_baseday = Column(DateTime)  # B股除权基准日
#     b_final_trade_date = Column(DateTime)  # B股最后交易日
#     a_bonus_date = Column(DateTime)  # 派息日(A)
#     b_bonus_date = Column(DateTime)  # 派息日(B)
#     dividend_arrival_date = Column(DateTime)  # 红股到帐日
#     a_increment_listing_date = Column(DateTime)  # A股新增股份上市日
#     b_increment_listing_date = Column(DateTime)  # B股新增股份上市日
#     total_capital_before_transfer = Column(Float)  # 送转前总股本
#     total_capital_after_transfer = Column(Float)  # 送转后总股本
#     float_capital_before_transfer = Column(Float)  # 送转前流通股本
#     float_capital_after_transfer = Column(Float)  # 送转后流通股本
#     a_transfer_arrival_date = Column(DateTime)  # A股转增股份到帐日
#     b_transfer_arrival_date = Column(DateTime)  # B股转增股份到帐日
#     b_dividend_arrival_date = Column(DateTime)  # B股送红股到帐日
#     note_of_no_dividend = Column(String(length=32))  # 有关不分配的说明
#     plan_progress_code = Column(Float)  # 方案进度编码
#     plan_progress = Column(String(length=32))  # 方案进度
#     bonus_cancel_pub_date = Column(DateTime)  # 取消分红公告日期

# shareschange_map={
#     "SHARECHANGEDATE":"change_date" ,  # 变动日期
#     "SHARECHANGREPORTDATE":"pub_date" ,  # 公告日期
#     # "":"change_reason_id" ,  # 变动原因编码
#     "LOCKAMNT":"share_non_trade" ,  # 未流通股份
#     # "": "share_start",  # 发起人股份
#     "RTDSTATE": "share_nation",  # 国家持股
#     "SHARECHANGECAUSE":"change_reason" ,  # 变动原因
#     "TOTALSHARE":"share_total" ,  # 总股本
#     "LIQASHARE":"" ,  # 流通A股
#     "RESTRICTEDASHARE":"" ,  # 限售A股
#     "LIQBSHARE":"" ,  # 流通B股
#
#
#     "RTDSTATEJUR":"share_nation_legal" ,  # 国有法人持股
#     "RTDDOMESJUR":"share_instate_legal" ,  # 境内法人持股
#     "RTDFRGNJUR":"share_outstate_legal" ,  # 境外法人持股
#     # "":"share_natural" ,  # 自然人持股
#     # "":"share_raised" ,  # 募集法人股
#     # "":"share_inside" ,  # 内部职工股
#     # '':'share_convert',  # 转配股
#     '':'share_perferred',  # 优先股
#     '':'share_other_nontrade',  # 其他未流通股
#     '':'share_limited',  # 流通受限股份
#     '':'share_legal_issue',  # 配售法人股
#     '':'share_strategic_investor',  # 战略投资者持股
#     '':'share_fund',  # 证券投资基金持股
#     '':'share_normal_legal',  # 一般法人持股
#     '':'share_other_limited',  # 其他流通受限股份
#     '':'share_nation_limited',  # 国家持股（受限）
#     '':'share_nation_legal_limited',  # 国有法人持股（受限）
#     '':'other_instate_limited',  # 其他内资持股（受限）
#     '':'legal_of_other_instate_limited',  # 其他内资持股（受限）中的境内法人持股
#     '':'natural_of_other_instate_limited',  # 其他内资持股（受限）中的境内自然人持股
#     '':'outstate_limited',  # 外资持股（受限）
#     '':'legal_of_outstate_limited',  # 外资持股（受限）中的境外法人持股
#     '':'natural_of_outstate_limited',  # 外资持股（受限）境外自然人持股
#     '':'share_trade_total',  # 已流通股份（自由流通股）
#     '':'share_rmb',  # 人民币普通股
#     '':'share_b',  # 境内上市外资股（B股）
#     '':'share_b_limited',  # 限售B股
#     '':'share_h',  # 境外上市外资股（H股）
#     '':'share_h_limited',  # 限售H股
#     '':'share_management',  # 高管股
#     '':'share_management_limited',  # 限售高管股
#     '':'share_other_trade',  # 其他流通股
#     '':'control_shareholder_limited',  # 控股股东、实际控制人(受限)
#     '':'core_employee_limited',  # 核心员工(受限)
#     '':'individual_fund_limited',  # 个人或基金(受限)
#     '':'other_legal_limited',  # 其他法人(受限)
#     '':'other_limited',  # 其他(受限)
#
# }

class SharesChange(DividendFinancingBase, Mixin):
    __tablename__ = 'shares_change'
    # def get_data_map(self):
    #     return shareschange_map
    provider = Column(String(length=32))
    code = Column(String(length=32))

    change_date = Column(DateTime)  # 变动日期
    pub_date = Column(DateTime)  # 公告日期
    change_reason_id = Column(Float)  # 变动原因编码
    change_reason = Column(String(length=32))  # 变动原因
    share_total = Column(Float)  # 总股本
    share_non_trade = Column(Float)  # 未流通股份
    share_start = Column(Float)  # 发起人股份
    share_nation = Column(Float)  # 国家持股
    share_nation_legal = Column(Float)  # 国有法人持股
    share_instate_legal = Column(Float)  # 境内法人持股
    share_outstate_legal = Column(Float)  # 境外法人持股
    share_natural = Column(Float)  # 自然人持股
    share_raised = Column(Float)  # 募集法人股
    share_inside = Column(Float)  # 内部职工股
    share_convert = Column(Float)  # 转配股
    share_perferred = Column(Float)  # 优先股
    share_other_nontrade = Column(Float)  # 其他未流通股
    share_limited = Column(Float)  # 流通受限股份
    share_legal_issue = Column(Float)  # 配售法人股
    share_strategic_investor = Column(Float)  # 战略投资者持股
    share_fund = Column(Float)  # 证券投资基金持股
    share_normal_legal = Column(Float)  # 一般法人持股
    share_other_limited = Column(Float)  # 其他流通受限股份
    share_nation_limited = Column(Float)  # 国家持股（受限）
    share_nation_legal_limited = Column(Float)  # 国有法人持股（受限）
    other_instate_limited = Column(Float)  # 其他内资持股（受限）
    legal_of_other_instate_limited = Column(Float)  # 其他内资持股（受限）中的境内法人持股
    natural_of_other_instate_limited = Column(Float)  # 其他内资持股（受限）中的境内自然人持股
    outstate_limited = Column(Float)  # 外资持股（受限）
    legal_of_outstate_limited = Column(Float)  # 外资持股（受限）中的境外法人持股
    natural_of_outstate_limited = Column(Float)  # 外资持股（受限）境外自然人持股
    share_trade_total = Column(Float)  # 已流通股份（自由流通股）
    share_rmb = Column(Float)  # 人民币普通股
    share_b = Column(Float)  # 境内上市外资股（B股）
    share_b_limited = Column(Float)  # 限售B股
    share_h = Column(Float)  # 境外上市外资股（H股）
    share_h_limited = Column(Float)  # 限售H股
    share_management = Column(Float)  # 高管股
    share_management_limited = Column(Float)  # 限售高管股
    share_other_trade = Column(Float)  # 其他流通股
    control_shareholder_limited = Column(Float)  # 控股股东、实际控制人(受限)
    core_employee_limited = Column(Float)  # 核心员工(受限)
    individual_fund_limited = Column(Float)  # 个人或基金(受限)
    other_legal_limited = Column(Float)  # 其他法人(受限)
    other_limited = Column(Float)  # 其他(受限)


register_schema(providers=['eastmoney', 'emquantapi', 'joinquant'], db_name='dividend_financing',
                schema_base=DividendFinancingBase)

__all__ = ['FundDividendDetail','DividendFinancing', 'DividendDetail', 'SpoDetail', 'RightsIssueDetail']
