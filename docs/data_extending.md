## 数据扩展要点

* zvt里面只有两种数据，EntityMixin和Mixin

  EntityMixin为投资标的信息，Mixin为其发生的事。任何一个投资品种，首先是定义EntityMixin，然后是其相关的Mixin。
  比如Stock(EntityMixin),及其相关的BalanceSheet,CashFlowStatement(Mixin)等。

* zvt的数据可以记录(record_data方法)
  
  记录数据可以通过扩展以下类来实现：

  * Recorder
    
    最基本的类，实现了关联data_schema和recorder的功能。记录EntityMixin一般继承该类。
  
  * RecorderForEntities
    
    实现了初始化需要记录的**投资标的列表**的功能，有了标的，才能记录标的发生的事。

  * TimeSeriesDataRecorder
    
    实现了增量记录，实时和非实时数据处理的功能。

  * FixedCycleDataRecorder

    实现了计算固定周期数据剩余size的功能。

  * TimestampsDataRecorder

    实现记录时间集合可知的数据记录功能。

继承Recorder必须指定data_schema和provider两个字段，系统通过python meta programing的方式对data_schema和recorder class进行了关联:
```
class Meta(type):
    def __new__(meta, name, bases, class_dict):
        cls = type.__new__(meta, name, bases, class_dict)
        # register the recorder class to the data_schema
        if hasattr(cls, 'data_schema') and hasattr(cls, 'provider'):
            if cls.data_schema and issubclass(cls.data_schema, Mixin):
                print(f'{cls.__name__}:{cls.data_schema.__name__}')
                cls.data_schema.register_recorder_cls(cls.provider, cls)
        return cls


class Recorder(metaclass=Meta):
    logger = logging.getLogger(__name__)

    # overwrite them to setup the data you want to record
    provider: str = None
    data_schema: Mixin = None
```


下面以**个股估值数据**为例对具体步骤做一个说明。

## 1. 定义数据
在domain package(或者其子package)下新建一个文件(module)valuation.py，内容如下：
```
# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, Float
from sqlalchemy.ext.declarative import declarative_base

from zvdata import Mixin
from zvdata.contract import register_schema

ValuationBase = declarative_base()


class StockValuation(ValuationBase, Mixin):
    __tablename__ = 'stock_valuation'

    code = Column(String(length=32))
    name = Column(String(length=32))
    # 总股本(股)
    capitalization = Column(Float)
    # 公司已发行的普通股股份总数(包含A股，B股和H股的总股本)
    circulating_cap = Column(Float)
    # 市值
    market_cap = Column(Float)
    # 流通市值
    circulating_market_cap = Column(Float)
    # 换手率
    turnover_ratio = Column(Float)
    # 静态pe
    pe = Column(Float)
    # 动态pe
    pe_ttm = Column(Float)
    # 市净率
    pb = Column(Float)
    # 市销率
    ps = Column(Float)
    # 市现率
    pcf = Column(Float)


class EtfValuation(ValuationBase, Mixin):
    __tablename__ = 'etf_valuation'

    code = Column(String(length=32))
    name = Column(String(length=32))
    # 静态pe
    pe = Column(Float)
    # 动态pe
    pe_ttm = Column(Float)
    # 市净率
    pb = Column(Float)
    # 市销率
    ps = Column(Float)
    # 市现率
    pcf = Column(Float)


register_schema(providers=['joinquant'], db_name='valuation', schema_base=ValuationBase)

__all__ = ['StockValuation', 'EtfValuation']

```
将其分解为以下步骤：
### 1.1 数据库base
```
ValuationBase = declarative_base()
```
一个数据库可有多个table(schema),table(schema)应继承自该类

### 1.2 table(schema)的定义
```
class StockValuation(ValuationBase, Mixin):
    __tablename__ = 'stock_valuation'

    code = Column(String(length=32))
    name = Column(String(length=32))
    # 总股本(股)
    capitalization = Column(Float)
    # 公司已发行的普通股股份总数(包含A股，B股和H股的总股本)
    circulating_cap = Column(Float)
    # 市值
    market_cap = Column(Float)
    # 流通市值
    circulating_market_cap = Column(Float)
    # 换手率
    turnover_ratio = Column(Float)
    # 静态pe
    pe = Column(Float)
    # 动态pe
    pe_ttm = Column(Float)
    # 市净率
    pb = Column(Float)
    # 市销率
    ps = Column(Float)
    # 市现率
    pcf = Column(Float)


class EtfValuation(ValuationBase, Mixin):
    __tablename__ = 'etf_valuation'

    code = Column(String(length=32))
    name = Column(String(length=32))
    # 静态pe
    pe = Column(Float)
    # 动态pe
    pe_ttm = Column(Float)
    # 市净率
    pb = Column(Float)
    # 市销率
    ps = Column(Float)
    # 市现率
    pcf = Column(Float)
```
这里定义了两个table(schema),继承ValuationBase表明其隶属的数据库，继承Mixin让其获得zvt统一的字段和方法。
schema里面的__tablename__为表名。
### 1.3 注册数据
```
register_schema(providers=['joinquant'], db_name='valuation', schema_base=ValuationBase)

__all__ = ['StockValuation', 'EtfValuation']
```
register_schema会将数据注册到zvt的数据系统中，providers为数据的提供商列表，db_name为数据库名字标识，schema_base为上面定义的数据库base。

__all__为该module定义的数据结构，为了使得整个系统的数据依赖干净明确，所有的module都应该手动定义该字段。


## 2 实现相应的recorder
```
# -*- coding: utf-8 -*-

import pandas as pd
from jqdatasdk import auth, logout, query, valuation, get_fundamentals_continuously

from zvdata.api import df_to_db
from zvdata.recorder import TimeSeriesDataRecorder
from zvdata.utils.time_utils import now_pd_timestamp, now_time_str, to_time_str
from zvt import zvt_config
from zvt.domain import Stock, StockValuation, EtfStock
from zvt.recorders.joinquant.common import to_jq_entity_id


class JqChinaStockValuationRecorder(TimeSeriesDataRecorder):
    entity_provider = 'joinquant'
    entity_schema = Stock

    # 数据来自jq
    provider = 'joinquant'

    data_schema = StockValuation

    def __init__(self, entity_type='stock', exchanges=['sh', 'sz'], entity_ids=None, codes=None, batch_size=10,
                 force_update=False, sleeping_time=5, default_size=2000, real_time=False, fix_duplicate_way='add',
                 start_timestamp=None, end_timestamp=None, close_hour=0, close_minute=0) -> None:
        super().__init__(entity_type, exchanges, entity_ids, codes, batch_size, force_update, sleeping_time,
                         default_size, real_time, fix_duplicate_way, start_timestamp, end_timestamp, close_hour,
                         close_minute)
        auth(zvt_config['jq_username'], zvt_config['jq_password'])

    def on_finish(self):
        super().on_finish()
        logout()

    def record(self, entity, start, end, size, timestamps):
        q = query(
            valuation
        ).filter(
            valuation.code == to_jq_entity_id(entity)
        )
        count: pd.Timedelta = now_pd_timestamp() - start
        df = get_fundamentals_continuously(q, end_date=now_time_str(), count=count.days + 1, panel=False)
        df['entity_id'] = entity.id
        df['timestamp'] = pd.to_datetime(df['day'])
        df['code'] = entity.code
        df['name'] = entity.name
        df['id'] = df['timestamp'].apply(lambda x: "{}_{}".format(entity.id, to_time_str(x)))
        df = df.rename({'pe_ratio_lyr': 'pe',
                        'pe_ratio': 'pe_ttm',
                        'pb_ratio': 'pb',
                        'ps_ratio': 'ps',
                        'pcf_ratio': 'pcf'},
                       axis='columns')

        df['market_cap'] = df['market_cap'] * 100000000
        df['circulating_cap'] = df['circulating_cap'] * 100000000
        df['capitalization'] = df['capitalization'] * 10000
        df['circulating_cap'] = df['circulating_cap'] * 10000
        df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)

        return None

__all__ = ['JqChinaStockValuationRecorder']
```

# 3. 获得的能力

# 4. recorder原理
将各provider提供(或者自己爬取)的数据**变成**符合data schema的数据需要做好以下几点:  
* 初始化要抓取的标的  
可抓取单标的来调试，然后抓取全量标的
* 能够从上次抓取的地方接着抓  
减少不必要的请求，增量抓取
* 封装常用的请求方式  
对时间序列数据的请求，无非start,end,size,time list的组合
* 能够自动去重
* 能够设置抓取速率
* 提供抓取完成的回调函数  
方便数据校验和多provider数据补全

流程图如下：
<p align="center"><img src='./imgs/recorder.png'/></p>