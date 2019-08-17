# -*- coding: utf-8 -*-
from ..context import init_context

init_context()

import plotly.graph_objs as go
import time

from zvt.api.rules import iterate_timestamps
from zvt.domain import Stock1dKdata

from zvt.utils.time_utils import to_time_str

from zvdata.reader import DataReader
from zvdata.structs import IntervalLevel


def test_china_stock_reader():
    data_reader = DataReader(codes=['002572', '000338'], data_schema=Stock1dKdata, provider='joinquant',
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

    for timestamp in iterate_timestamps(entity_type='stock', exchange='sz',
                                        level=IntervalLevel.LEVEL_1DAY,
                                        start_timestamp='2019-06-11',
                                        end_timestamp='2019-06-14'):
        data_reader.move_on(to_timestamp=timestamp, timeout=0)

        df = data_reader.get_data_df()

        assert ('stock_sz_002572', timestamp) in df.index
        assert ('stock_sz_000338', to_time_str(timestamp)) in df.index

    data_reader.data_drawer().draw_table()
    data_reader.data_drawer().draw_kline()


def test_reader_move_on():
    data_reader = DataReader(codes=['002572', '000338'], data_schema=Stock1dKdata, provider='joinquant',
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
    data_reader = DataReader(codes=['002572', '000338'], data_schema=Stock1dKdata, provider='joinquant',
                             start_timestamp='2019-01-01',
                             end_timestamp='2019-06-14')
    data_reader.data_drawer().draw_table()
    data_reader.data_drawer().draw_kline()
