import pandas as pd

from zvt.api.technical import init_securities
from zvt.domain import Provider
from zvt.utils.time_utils import to_pd_timestamp

CHINA_STOCK_MAIN_INDEX = [{'id': 'index_cn_000001',
                           'code': '000001',
                           'name': '上证指数',
                           'timestamp': '1990-12-19',
                           'exchange': 'cn',
                           'type': 'index',
                           'category': 'main'},
                          {'id': 'index_cn_000016',
                           'code': '000016',
                           'name': '上证50',
                           'timestamp': '2004-01-02',
                           'exchange': 'cn',
                           'type': 'index',
                           'category': 'main'},
                          {'id': 'index_cn_000905',
                           'code': '000905',
                           'name': '中证500',
                           'timestamp': '2005-01-04',
                           'exchange': 'cn',
                           'type': 'index',
                           'category': 'main'},
                          {'id': 'index_cn_399001',
                           'code': '399001',
                           'name': '深证成指',
                           'timestamp': '1991-04-03',
                           'exchange': 'cn',
                           'type': 'index',
                           'category': 'main'},
                          {'id': 'index_cn_399106',
                           'code': '399106',
                           'name': '深证综指',
                           'timestamp': '1991-04-03',
                           'exchange': 'cn',
                           'type': 'index',
                           'category': 'main'},
                          {'id': 'index_cn_399300',
                           'code': '399300',
                           'name': '沪深300',
                           'timestamp': '2002-01-04',
                           'exchange': 'cn',
                           'type': 'index',
                           'category': 'main'},
                          {'id': 'index_cn_399005',
                           'code': '399005',
                           'name': '中小板指',
                           'timestamp': '2006-01-24',
                           'exchange': 'cn',
                           'type': 'index',
                           'category': 'main'},
                          {'id': 'index_cn_399006',
                           'code': '399006',
                           'name': '创业板指',
                           'timestamp': '2010-06-01',
                           'exchange': 'cn',
                           'type': 'index',
                           'category': 'main'}
                          ]


def init_main_index(provider=Provider.EXCHANGE):
    for item in CHINA_STOCK_MAIN_INDEX:
        item['timestamp'] = to_pd_timestamp(item['timestamp'])
    df = pd.DataFrame(CHINA_STOCK_MAIN_INDEX)
    print(df)
    init_securities(df, security_type='index', provider=provider)


if __name__ == '__main__':
    init_main_index()
