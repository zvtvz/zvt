## 什么是factor

一般来说,人们常把macd,kdj,roe,pe等当作指标,zvt中把他们叫做indicator,甚至什么也不是,就只是普通的value;factor在zvt中有更高层次的抽象.这个会在如何扩展factor里面会做详细说明,你现在只需要知道,zvt里面的factor分为三类:FilterFactor,ScoreFacor,StateFactor.

## TechnicalFactor

> 该factor为计算各种技术指标的算法模板类,基于它可以构造出用于选股和交易的Factor

```
    factor = TechnicalFactor(codes=['000338'], start_timestamp='2018-01-01', end_timestamp='2019-02-01',
                             indicators=['ma', 'ma'],
                             indicators_param=[{'window': 5}, {'window': 10}])
    factor.draw_with_indicators()
```

factor本身是可以draw的,并且可以在notebook中使用:
<p align="center"><img src='./imgs/factor-in-notebook.gif'/></p>

你甚至可以把所有标的的factor都draw成一致的图片,然后用机器学习来对其进行分析,需要做的也只是把codes遍历一遍.

## 技术买卖指标
基于TechnicalFactor你可以构造自己的FilterFactor,比如,均线交叉买卖:
```
class CrossMaFactor(TechnicalFactor):
    def __init__(self,
                 security_list: List[str] = None,
                 security_type: Union[str, SecurityType] = SecurityType.stock,
                 exchanges: List[str] = ['sh', 'sz'],
                 codes: List[str] = None,
                 the_timestamp: Union[str, pd.Timestamp] = None,
                 start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None,
                 columns: List = None, filters: List = None,
                 provider: Union[str, Provider] = 'netease',
                 level: TradingLevel = TradingLevel.LEVEL_1DAY,
                 real_time: bool = False,
                 refresh_interval: int = 10,
                 category_field: str = 'security_id',
                 # child added arguments
                 short_window=5,
                 long_window=10) -> None:
        self.short_window = short_window
        self.long_window = long_window

        super().__init__(security_list, security_type, exchanges, codes, the_timestamp, start_timestamp, end_timestamp,
                         columns, filters, provider, level, real_time, refresh_interval, category_field,
                         indicators=['ma', 'ma'],
                         indicators_param=[{'window': short_window}, {'window': long_window}], valid_window=long_window)

    def compute(self):
        super().compute()
        s = self.depth_df['ma{}'.format(self.short_window)] > self.depth_df['ma{}'.format(self.long_window)]
        self.result_df = s.to_frame(name='score')

    def on_category_data_added(self, category, added_data: pd.DataFrame):
        super().on_category_data_added(category, added_data)
        # TODO:improve it to just computing the added data
        self.compute()
```

其本身也是可以draw的:
```
cross = CrossMaFactor(codes=['000338'], start_timestamp='2018-01-01', end_timestamp='2019-02-01',provider='joinquant')
cross.draw_result(render='notebook')
```
<p align="center"><img src='./imgs/factor-result-in-notebook.gif'/></p>

## ScoreFactor

[**ScoreFactor**](https://github.com/zvtvz/zvt/blob/master/zvt/factors/factor.py#L138)内置了分位数算法(quantile),你可以非常方便的对其进行扩展.

下面展示一个例子:对个股的**营收,利润增速,资金,净资产收益率**进行评分
```
class FinanceGrowthFactor(ScoreFactor):

    def __init__(self,
                 security_list: List[str] = None,
                 security_type: Union[str, SecurityType] = SecurityType.stock,
                 exchanges: List[str] = ['sh', 'sz'],
                 codes: List[str] = None,
                 the_timestamp: Union[str, pd.Timestamp] = None,
                 start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None,
                 columns: List = [FinanceFactor.op_income_growth_yoy, FinanceFactor.net_profit_growth_yoy,
                                  FinanceFactor.rota,
                                  FinanceFactor.roe],
                 filters: List = None,
                 provider: Union[str, Provider] = 'eastmoney',
                 level: TradingLevel = TradingLevel.LEVEL_1DAY,
                 real_time: bool = False,
                 refresh_interval: int = 10,
                 category_field: str = 'security_id',
                 keep_all_timestamp: bool = True,
                 fill_method: str = 'ffill',
                 effective_number: int = None,
                 depth_computing_method='ma',
                 depth_computing_param={'window': '365D', 'on': 'timestamp'},
                 breadth_computing_method='quantile',
                 breadth_computing_param={'score_levels': [0.1, 0.3, 0.5, 0.7, 0.9]}) -> None:
        super().__init__(FinanceFactor, security_list, security_type, exchanges, codes, the_timestamp, start_timestamp,
                         end_timestamp, columns, filters, provider, level, real_time, refresh_interval, category_field,
                         keep_all_timestamp, fill_method, effective_number, depth_computing_method,
                         depth_computing_param, breadth_computing_method, breadth_computing_param)

```

## StateFactor

> 可在该类Factor中实现趋势,震荡,缠论笔,段,中枢之类的状态机