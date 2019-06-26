# -*- coding: utf-8 -*-
from ..context import init_context

init_context()

import plotly.graph_objs as go
import time

from zvt.api.rules import iterate_timestamps
from zvt.domain import Stock1DKdata, SecurityType, TradingLevel
from zvt.reader.reader import DataReader

from zvt.utils.time_utils import to_time_str


def test_china_stock_reader():
    data_reader = DataReader(codes=['002572', '000338'], data_schema=Stock1DKdata, provider='joinquant',
                             start_timestamp='2019-01-01',
                             end_timestamp='2019-06-10')

    categories = data_reader.get_categories()

    df = data_reader.get_data_df()

    assert 'stock_sz_002572' in categories
    assert 'stock_sz_000338' in categories

    assert ('stock_sz_002572', '2019-01-02') in df.index
    assert ('stock_sz_000338', '2019-01-02') in df.index
    assert ('stock_sz_002572', '2019-06-10') in df.index
    assert ('stock_sz_000338', '2019-06-10') in df.index

    for timestamp in iterate_timestamps(security_type=SecurityType.stock, exchange='sz',
                                        level=TradingLevel.LEVEL_1DAY,
                                        start_timestamp='2019-06-11',
                                        end_timestamp='2019-06-14'):
        data_reader.move_on(to_timestamp=timestamp, timeout=0)

        df = data_reader.get_data_df()

        assert ('stock_sz_002572', timestamp) in df.index
        assert ('stock_sz_000338', to_time_str(timestamp)) in df.index


def test_reader_move_on():
    data_reader = DataReader(codes=['002572', '000338'], data_schema=Stock1DKdata, provider='joinquant',
                             start_timestamp='2019-06-13',
                             end_timestamp='2019-06-14')

    data_reader.move_on(to_timestamp='2019-06-15', timeout=0)
    assert ('stock_sz_002572', '2019-06-15') not in data_reader.get_data_df().index
    assert ('stock_sz_000338', '2019-06-15') not in data_reader.get_data_df().index

    start_time = time.time()
    changed = data_reader.move_on(to_timestamp='2019-06-16', timeout=5)
    assert changed == False
    assert time.time() - start_time > 5


def test_reader_draw():
    data_reader = DataReader(codes=['002572', '000338'], data_schema=Stock1DKdata, provider='joinquant',
                             start_timestamp='2019-01-01',
                             end_timestamp='2019-06-14')
    data_reader.draw(figures=[go.Scatter], render=None)
    data_reader.draw(figures=[go.Candlestick], render=None)
