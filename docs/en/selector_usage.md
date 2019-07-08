## what's selector

selector是根据factor来对标的进行综合评价,生成**开多,开空,持多,持空**标的选择器,其比一般的所谓**选股功能**要强大得多.

## 构造自己的selector

### TechnicalSelector

```
class TechnicalSelector(TargetSelector):
    def __init__(self, security_list=None, security_type=SecurityType.stock, exchanges=['sh', 'sz'], codes=None,
                 the_timestamp=None, start_timestamp=None, end_timestamp=None, long_threshold=0.8, short_threshold=-0.8,
                 level=TradingLevel.LEVEL_1DAY,
                 provider='joinquant') -> None:
        super().__init__(security_list, security_type, exchanges, codes, the_timestamp, start_timestamp, end_timestamp,
                         long_threshold, short_threshold, level, provider)

    def init_factors(self, security_list, security_type, exchanges, codes, the_timestamp, start_timestamp,
                     end_timestamp):
        bull_factor = BullFactor(security_list=security_list, security_type=security_type, exchanges=exchanges,
                                 codes=codes, the_timestamp=the_timestamp, start_timestamp=start_timestamp,
                                 end_timestamp=end_timestamp, provider=self.provider, level=self.level)

        self.filter_factors = [bull_factor]

s = TechnicalSelector(codes=SAMPLE_STOCK_CODES, start_timestamp='2018-01-01', end_timestamp='2019-06-30')
s.run()
s.draw()
```

该selector选取macd黄白线在0轴上的标的,选取完成后,可以运行draw来获取选中标的的表格.

<p align="center"><img src='./imgs/technical-selector-in-notebook.gif'/></p>


### FundamentalSelector
```
from zvt.factors.finance_factor import FinanceGrowthFactor
from zvt.selectors.selector import TargetSelector


class FundamentalSelector(TargetSelector):
    def init_factors(self, security_list, security_type, exchanges, codes, the_timestamp, start_timestamp,
                     end_timestamp):
        factor = FinanceGrowthFactor(security_list=security_list, security_type=security_type, exchanges=exchanges,
                                     codes=codes, the_timestamp=the_timestamp, start_timestamp=start_timestamp,
                                     end_timestamp=end_timestamp, keep_all_timestamp=True, provider=self.provider)
        self.score_factors.append(factor)

selector: TargetSelector = FundamentalSelector(start_timestamp='2018-01-01', end_timestamp='2019-06-30')
selector.run()
selector.draw()
```

该selector选取成长性评分在0.8以上的个股.

<p align="center"><img src='./imgs/fundamental-selector-in-notebook.png'/></p>

> 注意:使用到的ScoreFactor是对全市场和历史数据进行运算,比较耗时,但运算结果可以直接进行回测.

### 多factor运算

只需要在init_factors里面继续添加factor即可.