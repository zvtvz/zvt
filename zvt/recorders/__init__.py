# -*- coding: utf-8 -*-

CHINA_STOCK_MAIN_INDEX = [{'id': 'index_cn_000001',
                           'entity_id': 'index_cn_000001',
                           'code': '000001',
                           'name': '上证指数',
                           'timestamp': '1990-12-19',
                           'exchange': 'cn',
                           'entity_type': 'index',
                           'category': 'main'},
                          {'id': 'index_cn_000016',
                           'entity_id': 'index_cn_000016',
                           'code': '000016',
                           'name': '上证50',
                           'timestamp': '2004-01-02',
                           'exchange': 'cn',
                           'entity_type': 'index',
                           'category': 'main'},
                          {'id': 'index_cn_000905',
                           'entity_id': 'index_cn_000905',
                           'code': '000905',
                           'name': '中证500',
                           'timestamp': '2005-01-04',
                           'exchange': 'cn',
                           'entity_type': 'index',
                           'category': 'main'},
                          {'id': 'index_cn_399001',
                           'entity_id': 'index_cn_399001',
                           'code': '399001',
                           'name': '深证成指',
                           'timestamp': '1991-04-03',
                           'exchange': 'cn',
                           'entity_type': 'index',
                           'category': 'main'},
                          {'id': 'index_cn_399106',
                           'entity_id': 'index_cn_399106',
                           'code': '399106',
                           'name': '深证综指',
                           'timestamp': '1991-04-03',
                           'exchange': 'cn',
                           'entity_type': 'index',
                           'category': 'main'},
                          {'id': 'index_cn_399300',
                           'entity_id': 'index_cn_399300',
                           'code': '399300',
                           'name': '沪深300',
                           'timestamp': '2002-01-04',
                           'exchange': 'cn',
                           'entity_type': 'index',
                           'category': 'main'},
                          {'id': 'index_cn_399005',
                           'entity_id': 'index_cn_399005',
                           'code': '399005',
                           'name': '中小板指',
                           'timestamp': '2006-01-24',
                           'exchange': 'cn',
                           'entity_type': 'index',
                           'category': 'main'},
                          {'id': 'index_cn_399006',
                           'entity_id': 'index_cn_399006',
                           'code': '399006',
                           'name': '创业板指',
                           'timestamp': '2010-06-01',
                           'exchange': 'cn',
                           'entity_type': 'index',
                           'category': 'main'},
                          {'id': 'index_cn_000688',
                           'entity_id': 'index_cn_000688',
                           'code': '000688',
                           'name': '科创50',
                           'timestamp': '2019-01-01',
                           'exchange': 'cn',
                           'entity_type': 'index',
                           'category': 'main'},
                          # # 聚宽编码
                          # # 市场通编码	市场通名称
                          # # 310001	沪股通
                          # # 310002	深股通
                          # # 310003	港股通（沪）
                          # # 310004	港股通（深）
                          {'id': 'index_cn_310001',
                           'entity_id': 'index_cn_310001',
                           'code': '310001',
                           'name': '沪股通',
                           'timestamp': '2014-11-17',
                           'exchange': 'cn',
                           'entity_type': 'index',
                           'category': 'main'},
                          {'id': 'index_cn_310002',
                           'entity_id': 'index_cn_310002',
                           'code': '310002',
                           'name': '深股通',
                           'timestamp': '2014-11-17',
                           'exchange': 'cn',
                           'entity_type': 'index',
                           'category': 'main'},
                          {'id': 'index_cn_310003',
                           'entity_id': 'index_cn_310003',
                           'code': '310003',
                           'name': '港股通（沪）',
                           'timestamp': '2014-11-17',
                           'exchange': 'cn',
                           'entity_type': 'index',
                           'category': 'main'},
                          {'id': 'index_cn_310004',
                           'entity_id': 'index_cn_310004',
                           'code': '310004',
                           'name': '港股通（深）',
                           'timestamp': '2014-11-17',
                           'exchange': 'cn',
                           'entity_type': 'index',
                           'category': 'main'}
                          ]


def init_main_index(provider='exchange'):
    from zvt.utils.time_utils import to_pd_timestamp
    import pandas as pd
    from zvt.contract.api import df_to_db
    from zvt.domain import Index

    for item in CHINA_STOCK_MAIN_INDEX:
        item['timestamp'] = to_pd_timestamp(item['timestamp'])
    df = pd.DataFrame(CHINA_STOCK_MAIN_INDEX)
    # print(df)
    df_to_db(df=df, data_schema=Index, provider=provider, force_update=False)
    # delete dirty data
    # del_data(data_schema=Index, provider=provider, filters=[Index.exchange == 'cn'])


# init_main_index(provider='joinquant')
# init_main_index(provider='eastmoney')
# init_main_index(provider='exchange')
# the __all__ is generated
__all__ = ['init_main_index']

# __init__.py structure:
# common code of the package
# export interface in __all__ which contains __all__ of its sub modules

# import all from submodule joinquant
from .joinquant import *
from .joinquant import __all__ as _joinquant_all
__all__ += _joinquant_all

# import all from submodule exchange
from .exchange import *
from .exchange import __all__ as _exchange_all
__all__ += _exchange_all

# import all from submodule em
from .em import *
from .em import __all__ as _em_all
__all__ += _em_all

# import all from submodule consts
from .consts import *
from .consts import __all__ as _consts_all
__all__ += _consts_all

# import all from submodule eastmoney
from .eastmoney import *
from .eastmoney import __all__ as _eastmoney_all
__all__ += _eastmoney_all

# import all from submodule sina
from .sina import *
from .sina import __all__ as _sina_all
__all__ += _sina_all