# -*- coding: utf-8 -*-
from sqlalchemy import String, Column, Float

from zvt.contract import Mixin


class KdataCommon(Mixin):
    provider = Column(String(length=32))
    code = Column(String(length=32))
    name = Column(String(length=32))
    # Enum constraint is not extendable
    # level = Column(Enum(IntervalLevel, values_callable=enum_value))
    level = Column(String(length=32))

    # 如果是股票，代表前复权数据
    # 开盘价
    open = Column(Float)
    # 收盘价
    close = Column(Float)
    # 最高价
    high = Column(Float)
    # 最低价
    low = Column(Float)
    # 成交量
    volume = Column(Float)
    # 成交金额
    turnover = Column(Float)


class TickCommon(Mixin):
    provider = Column(String(length=32))
    code = Column(String(length=32))
    name = Column(String(length=32))
    level = Column(String(length=32))

    order = Column(String(length=32))
    price = Column(Float)
    volume = Column(Float)
    turnover = Column(Float)
    direction = Column(String(length=32))
    order_type = Column(String(length=32))


class BlockKdataCommon(KdataCommon):
    pass


class IndexKdataCommon(KdataCommon):
    provider = Column(String(length=32))
    code = Column(String(length=32))
    name = Column(String(length=32))


class FundCommon(Mixin):
    provider = Column(String(length=32))
    code = Column(String(length=32))
    name = Column(String(length=32))



class FundNetValueCommon(FundCommon):
    provider = Column(String(length=32))
    code = Column(String(length=32))
    name = Column(String(length=32))

    net_value = Column(Float)  # 单位净值
    sum_value = Column(Float)  # 累计净值
    factor = Column(Float)  # 复权因子
    acc_factor = Column(Float)  # 累计复权因子
    refactor_net_value = Column(Float)  # 累计复权净值


class EtfKdataCommon(KdataCommon):
    turnover_rate = Column(Float)

    # ETF 累计净值（货币 ETF 为七日年化)
    cumulative_net_value = Column(Float)
    # ETF 净值增长率
    change_pct = Column(Float)


class StockKdataCommon(KdataCommon):
    # 涨跌幅
    change_pct = Column(Float)
    # 换手率
    turnover_rate = Column(Float)


class StockFactorCommon(Mixin):
    provider = Column(String(length=32))
    code = Column(String(length=32))
    name = Column(String(length=32))
    # Enum constraint is not extendable
    # level = Column(Enum(IntervalLevel values_callable=enum_value))


class StockBasicsFactorCommon(StockFactorCommon):
    """
    基础科目及衍生类因子
    """
    # 管理费用TTM
    administration_expense_ttm = Column(Float)
    # 资产减值损失TTM
    asset_impairment_loss_ttm = Column(Float)
    # 现金流市值比
    cash_flow_to_price_ratio = Column(Float)
    # 流通市值
    circulating_market_cap = Column(Float)
    # 息税前利润
    EBIT = Column(Float)
    # 息税折旧摊销前利润
    EBITDA = Column(Float)
    # 金融资产
    financial_assets = Column(Float)
    # 财务费用TTM
    financial_expense_ttm = Column(Float)
    # 金融负债
    financial_liability = Column(Float)
    # 销售商品提供劳务收到的现金
    goods_sale_and_service_render_cash_ttm = Column(Float)
    # 毛利TTM
    gross_profit_ttm = Column(Float)
    # 带息流动负债
    interest_carry_current_liability = Column(Float)
    # 无息流动负债
    interest_free_current_liability = Column(Float)
    # 市值
    market_cap = Column(Float)
    # 净债务
    net_debt = Column(Float)
    # 筹资活动现金流量净额TTM
    net_finance_cash_flow_ttm = Column(Float)
    # 净利息费用
    net_interest_expense = Column(Float)
    # 投资活动现金流量净额TTM
    net_invest_cash_flow_ttm = Column(Float)
    # 经营活动现金流量净额TTM
    net_operate_cash_flow_ttm = Column(Float)
    # 净利润TTM
    net_profit_ttm = Column(Float)
    # 净运营资本
    net_working_capital = Column(Float)
    # 营业外收支净额TTM
    non_operating_net_profit_ttm = Column(Float)
    # 非经常性损益
    non_recurring_gain_loss = Column(Float)
    # 归属于母公司股东的净利润TTM
    np_parent_company_owners_ttm = Column(Float)
    # 经营活动净收益
    OperateNetIncome = Column(Float)
    # 经营性资产
    operating_assets = Column(Float)
    # 营业成本TTM
    operating_cost_ttm = Column(Float)
    # 经营性负债
    operating_liability = Column(Float)
    # 营业利润TTM
    operating_profit_ttm = Column(Float)
    # 营业收入TTM
    operating_revenue_ttm = Column(Float)
    # 留存收益
    retained_earnings = Column(Float)
    # 营收市值比
    sales_to_price_ratio = Column(Float)
    # 销售费用TTM
    sale_expense_ttm = Column(Float)
    # 营业总成本TTM
    total_operating_cost_ttm = Column(Float)
    # 营业总收入TTM
    total_operating_revenue_ttm = Column(Float)
    # 利润总额TTM
    total_profit_ttm = Column(Float)
    # 价值变动净收益TTM
    value_change_profit_ttm = Column(Float)


class StockEmotionFactorCommon(StockFactorCommon):
    """
    情绪类因子
    """
    AR = Column(Float)  # 人气指标
    ARBR = Column(Float)  # ARBR
    ATR14 = Column(Float)  # 14日均幅指标
    ATR6 = Column(Float)  # 6日均幅指标
    BR = Column(Float)  # 意愿指标
    DAVOL10 = Column(Float)  # 10日平均换手率与120日平均换手率之比
    DAVOL20 = Column(Float)  # 20日平均换手率与120日平均换手率之比
    DAVOL5 = Column(Float)  # 5日平均换手率与120日平均换手率
    MAWVAD = Column(Float)  # 因子WVAD的6日均值
    money_flow_20 = Column(Float)  # 20日资金流量
    PSY = Column(Float)  # 心理线指标
    turnover_volatility = Column(Float)  # 换手率相对波动率
    TVMA20 = Column(Float)  # 20日成交金额的移动平均值
    TVMA6 = Column(Float)  # 6日成交金额的移动平均值
    TVSTD20 = Column(Float)  # 20日成交金额的标准差
    TVSTD6 = Column(Float)  # 6日成交金额的标准差
    VDEA = Column(Float)  # 计算VMACD因子的中间变量
    VDIFF = Column(Float)  # 计算VMACD因子的中间变量
    VEMA10 = Column(Float)  # 成交量的10日指数移动平均
    VEMA12 = Column(Float)  # 12日成交量的移动平均值
    VEMA26 = Column(Float)  # 成交量的26日指数移动平均
    VEMA5 = Column(Float)  # 成交量的5日指数移动平均
    VMACD = Column(Float)  # 成交量指数平滑异同移动平均线
    VOL10 = Column(Float)  # 10日平均换手率
    VOL120 = Column(Float)  # 120日平均换手率
    VOL20 = Column(Float)  # 20日平均换手率
    VOL240 = Column(Float)  # 120日平均换手率
    VOL5 = Column(Float)  # 5日平均换手率
    VOL60 = Column(Float)  # 60日平均换手率
    VOSC = Column(Float)  # 成交量震荡
    VR = Column(Float)  # 成交量比率（Volume Ratio）
    VROC12 = Column(Float)  # 12日量变动速率指标
    VROC6 = Column(Float)  # 6日量变动速率指标
    VSTD10 = Column(Float)  # 10日成交量标准差
    VSTD20 = Column(Float)  # 20日成交量标准差
    WVAD = Column(Float)  # 威廉变异离散量


class StockGrowthFactorCommon(StockFactorCommon):
    """
    成长类因子
    """
    financing_cash_growth_rate = Column(Float)  # 筹资活动产生的现金流量净额增长率
    net_asset_growth_rate = Column(Float)  # 净资产增长率
    net_operate_cashflow_growth_rate = Column(Float)  # 经营活动产生的现金流量净额增长率
    net_profit_growth_rate = Column(Float)  # 净利润增长率
    np_parent_company_owners_growth_rate = Column(Float)  # 归属母公司股东的净利润增长率
    operating_revenue_growth_rate = Column(Float)  # 营业收入增长率
    PEG = Column(Float)  # PEG
    total_asset_growth_rate = Column(Float)  # 总资产增长率
    total_profit_growth_rate = Column(Float)  # 利润总额增长率


class StockMomentumFactorCommon(StockFactorCommon):
    """
    动量类因子
    """
    arron_down_25 = Column(Float)  # 利润总额增长率Aroon指标下轨
    arron_up_25 = Column(Float)  # 利润总额增长率	Aroon指标上轨
    BBIC = Column(Float)  # 利润总额增长率BBI 动量
    bear_power = Column(Float)  # 利润总额增长率	空头力道
    BIAS10 = Column(Float)  # 利润总额增长率	10日乖离率
    BIAS20 = Column(Float)  # 利润总额增长率	20日乖离率
    BIAS5 = Column(Float)  # 利润总额增长率	5日乖离率
    BIAS60 = Column(Float)  # 利润总额增长率60日乖离率
    bull_power = Column(Float)  # 利润总额增长率多头力道
    CCI10 = Column(Float)  # 利润总额增长率10日顺势指标
    CCI15 = Column(Float)  # 利润总额增长率15日顺势指标
    CCI20 = Column(Float)  # 利润总额增长率20日顺势指标
    CCI88 = Column(Float)  # 利润总额增长率88日顺势指标
    CR20 = Column(Float)  # 利润总额增长率CR指标
    fifty_two_week_close_rank = Column(Float)  # 利润总额增长率当前价格处于过去1年股价的位置
    MASS = Column(Float)  # 利润总额增长率梅斯线
    PLRC12 = Column(Float)  # 利润总额增长率12日收盘价格与日期线性回归系数
    PLRC24 = Column(Float)  # 利润总额增长率24日收盘价格与日期线性回归系数
    PLRC6 = Column(Float)  # 利润总额增长率6日收盘价格与日期线性回归系数
    Price1M = Column(Float)  # 利润总额增长率当前股价除以过去一个月股价均值再减1
    Price1Y = Column(Float)  # 利润总额增长率当前股价除以过去一年股价均值再减1
    Price3M = Column(Float)  # 利润总额增长率当前股价除以过去三个月股价均值再减1
    Rank1M = Column(Float)  # 利润总额增长率1减去 过去一个月收益率排名与股票总数的比值
    ROC12 = Column(Float)  # 利润总额增长率12日变动速率（Price Rate of Change）
    ROC120 = Column(Float)  # 利润总额增长率120日变动速率（Price Rate of Change）
    ROC20 = Column(Float)  # 利润总额增长率20日变动速率（Price Rate of Change）
    ROC6 = Column(Float)  # 利润总额增长率6日变动速率（Price Rate of Change）
    ROC60 = Column(Float)  # 利润总额增长率60日变动速率（Price Rate of Change）
    single_day_VPT = Column(Float)  # 利润总额增长率单日价量趋势
    single_day_VPT_12 = Column(Float)  # 利润总额增长率	单日价量趋势12均值
    single_day_VPT_6 = Column(Float)  # 利润总额增长率	单日价量趋势6日均值
    TRIX10 = Column(Float)  # 利润总额增长率10日终极指标TRIX
    TRIX5 = Column(Float)  # 利润总额增长率5日终极指标TRIX
    Volume1M = Column(Float)  # 利润总额增长率当前交易量相比过去1个月日均交易量 与过去过去20日日均收益率乘积


class StockPershareFactorCommon(StockFactorCommon):
    """
    每股指标因子
    """
    capital_reserve_fund_per_share = Column(Float)  # 每股资本公积金
    cashflow_per_share_ttm = Column(Float)  # 每股现金流量净额，根据当时日期来获取最近变更日的总股本
    cash_and_equivalents_per_share = Column(Float)  # 每股现金及现金等价物余额
    eps_ttm = Column(Float)  # 每股收益TTM
    net_asset_per_share = Column(Float)  # 每股净资产
    net_operate_cash_flow_per_share = Column(Float)  # 每股经营活动产生的现金流量净额
    operating_profit_per_share = Column(Float)  # 每股营业利润
    operating_profit_per_share_ttm = Column(Float)  # 每股营业利润TTM
    operating_revenue_per_share = Column(Float)  # 每股营业收入
    operating_revenue_per_share_ttm = Column(Float)  # 每股营业收入TTM
    retained_earnings_per_share = Column(Float)  # 每股留存收益
    retained_profit_per_share = Column(Float)  # 每股未分配利润
    surplus_reserve_fund_per_share = Column(Float)  # 每股盈余公积金
    total_operating_revenue_per_share = Column(Float)  # 每股营业总收入
    total_operating_revenue_per_share_ttm = Column(Float)  # 每股营业总收入TTM


class StockQualityFactorCommon(StockFactorCommon):
    """
    质量类因子
    """
    ACCA = Column(Float)  # 现金流资产比和资产回报率之差
    accounts_payable_turnover_days = Column(Float)  # 应付账款周转天数
    accounts_payable_turnover_rate = Column(Float)  # 应付账款周转率
    account_receivable_turnover_days = Column(Float)  # 应收账款周转天数
    account_receivable_turnover_rate = Column(Float)  # 应收账款周转率
    adjusted_profit_to_total_profit = Column(Float)  # 扣除非经常损益后的净利润/净利润
    admin_expense_rate = Column(Float)  # 管理费用与营业总收入之比
    asset_turnover_ttm = Column(Float)  # 经营资产周转率TTM
    cash_rate_of_sales = Column(Float)  # 经营活动产生的现金流量净额与营业收入之比
    cash_to_current_liability = Column(Float)  # 现金比率
    cfo_to_ev = Column(Float)  # 经营活动产生的现金流量净额与企业价值之比TTM
    current_asset_turnover_rate = Column(Float)  # 流动资产周转率TTM
    current_ratio = Column(Float)  # 流动比率(单季度)
    debt_to_asset_ratio = Column(Float)  # 债务总资产比
    debt_to_equity_ratio = Column(Float)  # 产权比率
    debt_to_tangible_equity_ratio = Column(Float)  # 有形净值债务率
    DEGM = Column(Float)  # 毛利率增长
    DEGM_8y = Column(Float)  # 长期毛利率增长
    DSRI = Column(Float)  # 应收账款指数
    equity_to_asset_ratio = Column(Float)  # 股东权益比率
    equity_to_fixed_asset_ratio = Column(Float)  # 股东权益与固定资产比率
    equity_turnover_rate = Column(Float)  # 股东权益周转率
    financial_expense_rate = Column(Float)  # 财务费用与营业总收入之比
    fixed_assets_turnover_rate = Column(Float)  # 固定资产周转率
    fixed_asset_ratio = Column(Float)  # 固定资产比率
    GMI = Column(Float)  # 毛利率指数
    goods_service_cash_to_operating_revenue_ttm = Column(Float)  # 销售商品提供劳务收到的现金与营业收入之比
    gross_income_ratio = Column(Float)  # 销售毛利率
    intangible_asset_ratio = Column(Float)  # 无形资产比率
    inventory_turnover_days = Column(Float)  # 存货周转天数
    inventory_turnover_rate = Column(Float)  # 存货周转率
    invest_income_associates_to_total_profit = Column(Float)  # 对联营和合营公司投资收益/利润总额
    long_debt_to_asset_ratio = Column(Float)  # 长期借款与资产总计之比
    long_debt_to_working_capital_ratio = Column(Float)  # 长期负债与营运资金比率
    long_term_debt_to_asset_ratio = Column(Float)  # 长期负债与资产总计之比
    LVGI = Column(Float)  # 财务杠杆指数
    margin_stability = Column(Float)  # 盈利能力稳定性
    maximum_margin = Column(Float)  # 最大盈利水平
    MLEV = Column(Float)  # 市场杠杆
    net_non_operating_income_to_total_profit = Column(Float)  # 营业外收支利润净额/利润总额
    net_operate_cash_flow_to_asset = Column(Float)  # 总资产现金回收率
    net_operate_cash_flow_to_net_debt = Column(Float)  # 经营活动产生现金流量净额/净债务
    net_operate_cash_flow_to_operate_income = Column(Float)  # 经营活动产生的现金流量净额与经营活动净收益之比
    net_operate_cash_flow_to_total_current_liability = Column(Float)  # 现金流动负债比
    net_operate_cash_flow_to_total_liability = Column(Float)  # 经营活动产生的现金流量净额/负债合计
    net_operating_cash_flow_coverage = Column(Float)  # 净利润现金含量
    net_profit_ratio = Column(Float)  # 销售净利率
    net_profit_to_total_operate_revenue_ttm = Column(Float)  # 净利润与营业总收入之比
    non_current_asset_ratio = Column(Float)  # 非流动资产比率
    OperatingCycle = Column(Float)  # 营业周期
    operating_cost_to_operating_revenue_ratio = Column(Float)  # 销售成本率
    operating_profit_growth_rate = Column(Float)  # 营业利润增长率
    operating_profit_ratio = Column(Float)  # 营业利润率
    operating_profit_to_operating_revenue = Column(Float)  # 营业利润与营业总收入之比
    operating_profit_to_total_profit = Column(Float)  # 经营活动净收益/利润总额
    operating_tax_to_operating_revenue_ratio_ttm = Column(Float)  # 销售税金率
    profit_margin_ttm = Column(Float)  # 销售利润率TTM
    quick_ratio = Column(Float)  # 速动比率
    rnoa_ttm = Column(Float)  # 经营资产回报率TTM
    ROAEBITTTM = Column(Float)  # 总资产报酬率
    roa_ttm = Column(Float)  # 资产回报率TTM
    roa_ttm_8y = Column(Float)  # 长期资产回报率TTM
    roe_ttm = Column(Float)  # 权益回报率TTM
    roe_ttm_8y = Column(Float)  # 长期权益回报率TTM
    roic_ttm = Column(Float)  # 投资资本回报率TTM
    sale_expense_to_operating_revenue = Column(Float)  # 营业费用与营业总收入之比
    SGAI = Column(Float)  # 销售管理费用指数
    SGI = Column(Float)  # 营业收入指数
    super_quick_ratio = Column(Float)  # 超速动比率
    total_asset_turnover_rate = Column(Float)  # 总资产周转率
    total_profit_to_cost_ratio = Column(Float)  # 成本费用利润率


class StockRiskFactorCommon(StockFactorCommon):
    """
    风险类因子
    """
    Kurtosis120 = Column(Float)  # 个股收益的120日峰度
    Kurtosis20 = Column(Float)  # 个股收益的20日峰度
    Kurtosis60 = Column(Float)  # 个股收益的60日峰度
    sharpe_ratio_120 = Column(Float)  # 120日夏普比率
    sharpe_ratio_20 = Column(Float)  # 20日夏普比率
    sharpe_ratio_60 = Column(Float)  # 60日夏普比率
    Skewness120 = Column(Float)  # 个股收益的120日偏度
    Skewness20 = Column(Float)  # 个股收益的20日偏度
    Skewness60 = Column(Float)  # 个股收益的60日偏度
    Variance120 = Column(Float)  # 120日收益方差
    Variance20 = Column(Float)  # 20日收益方差
    Variance60 = Column(Float)  # 60日收益方差


class StockStyleFactorCommon(StockFactorCommon):
    """
    风险因子 - 风格因子
    """
    average_share_turnover_annual = Column(Float)  # 年度平均月换手率
    average_share_turnover_quarterly = Column(Float)  # 季度平均平均月换手率
    beta = Column(Float)  # BETA
    book_leverage = Column(Float)  # 账面杠杆
    book_to_price_ratio = Column(Float)  # 市净率因子
    cash_earnings_to_price_ratio = Column(Float)  # 现金流量市值比
    cube_of_size = Column(Float)  # 市值立方因子
    cumulative_range = Column(Float)  # 收益离差
    daily_standard_deviation = Column(Float)  # 日收益率标准差
    debt_to_assets = Column(Float)  # 资产负债率
    earnings_growth = Column(Float)  # 5年盈利增长率
    earnings_to_price_ratio = Column(Float)  # 利润市值比
    earnings_yield = Column(Float)  # 盈利预期因子
    growth = Column(Float)  # 成长因子
    historical_sigma = Column(Float)  # 残差历史波动率
    leverage = Column(Float)  # 杠杆因子
    liquidity = Column(Float)  # 流动性因子
    long_term_predicted_earnings_growth = Column(Float)  # 预期长期盈利增长率
    market_leverage = Column(Float)  # 市场杠杆
    momentum = Column(Float)  # 动量因子
    natural_log_of_market_cap = Column(Float)  # 对数总市值
    non_linear_size = Column(Float)  # 非线性市值因子
    predicted_earnings_to_price_ratio = Column(Float)  # 预期市盈率
    raw_beta = Column(Float)  # RAW BETA
    relative_strength = Column(Float)  # 相对强弱
    residual_volatility = Column(Float)  # 残差波动因子
    sales_growth = Column(Float)  # 5年营业收入增长率
    share_turnover_monthly = Column(Float)  # 月换手率
    short_term_predicted_earnings_growth = Column(Float)  # 预期短期盈利增长率
    size = Column(Float)  # 市值因子


class StockTechnicalFactorCommon(StockFactorCommon):
    """
    技术指标因子
    """
    boll_down = Column(Float)  # 下轨线（布林线）指标
    boll_up = Column(Float)  # 上轨线（布林线）指标
    EMA5 = Column(Float)  # 5日指数移动均线
    EMAC10 = Column(Float)  # 10日指数移动均线
    EMAC12 = Column(Float)  # 12日指数移动均线
    EMAC120 = Column(Float)  # 120日指数移动均线
    EMAC20 = Column(Float)  # 20日指数移动均线
    EMAC26 = Column(Float)  # 26日指数移动均线
    MAC10 = Column(Float)  # 10日移动均线
    MAC120 = Column(Float)  # 120日移动均线
    MAC20 = Column(Float)  # 20日移动均线
    MAC5 = Column(Float)  # 5日移动均线
    MAC60 = Column(Float)  # 60日移动均线
    MACDC = Column(Float)  # 平滑异同移动平均线
    MFI14 = Column(Float)  # 资金流量指标


from zvt.domain.quotes.block import *
from zvt.domain.quotes.stock import *
from zvt.domain.quotes.etf import *
from zvt.domain.quotes.fund import *
from zvt.domain.quotes.index import *
from zvt.domain.quotes.trade_day import *

