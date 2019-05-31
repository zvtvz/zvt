# -*- coding: utf-8 -*-
import os
from typing import List

import pandas as pd
from pyecharts import options as opts
from pyecharts.charts import Line, Timeline
from pyecharts.charts.basic_charts.kline import Kline
from pyecharts.globals import ThemeType
from pyecharts.options import InitOpts, TitleOpts

from zvt.api.common import decode_security_id
from zvt.api.technical import get_kdata
from zvt.domain import SecurityType
from zvt.settings import UI_PATH
from zvt.utils.pd_utils import fill_with_same_index
from zvt.utils.time_utils import to_time_str, TIME_FORMAT_ISO8601, now_time_str


def get_init_opts():
    return InitOpts(theme=ThemeType.LIGHT, page_title='awesome zvt')


def get_title_opts():
    return TitleOpts()


def get_default_line():
    line = Line(init_opts=get_init_opts())
    return line


def get_default_kline() -> Kline:
    kline = Kline(init_opts=get_init_opts())
    kline.set_global_opts(
        xaxis_opts=opts.AxisOpts(is_scale=True),
        yaxis_opts=opts.AxisOpts(
            is_scale=True,
            splitarea_opts=opts.SplitAreaOpts(
                is_show=True, areastyle_opts=opts.AreaStyleOpts(opacity=1)
            ),
        ),
        datazoom_opts=[opts.DataZoomOpts()])
    return kline


def get_default_timeline():
    timeline = Timeline(init_opts=get_init_opts())
    timeline.add_schema(is_auto_play=False, axis_type='time', pos_bottom='10%')
    return timeline


def get_ui_path(name):
    if name is None:
        name = '{}.html'.format(now_time_str(fmt=TIME_FORMAT_ISO8601))
    return os.path.join(UI_PATH, '{}.html'.format(name))


def common_draw(df_list: List[pd.DataFrame], chart_type=Line, columns=[], name_field='security_id', render='html',
                file_name=None):
    if len(df_list) > 1:
        df_list = fill_with_same_index(df_list=df_list)

    chart = None

    if chart_type == Line:
        chart = get_default_line()
        assert len(columns) == 1

    xdata = [to_time_str(timestamp) for timestamp in df_list[0].index]

    chart.add_xaxis(xdata)

    for df in df_list:
        series_name = df[df[name_field].notna()][name_field][0]

        if len(columns) == 1:
            ydata = df.loc[:, columns[0]].values.tolist()

        chart.add_yaxis(series_name, ydata, is_smooth=True,
                        markpoint_opts=opts.MarkPointOpts(
                            data=[opts.MarkPointItem(type_="min"), opts.MarkPointItem(type_="max")]))

        if render == 'html':
            chart.render(get_ui_path(file_name))
        elif render == 'notebook':
            chart.render_notebook()

    return chart


def draw_line(df_list: List[pd.DataFrame], columns=[], name_field='security_id', render='html',
              file_name=None):
    return common_draw(df_list=df_list, chart_type=Line, columns=columns, name_field=name_field, render=render,
                       file_name=file_name)


def draw_kline(df_list: List[pd.DataFrame], markpoints_list: List[pd.DataFrame] = None, render='html',
               file_name=None) -> Kline:
    if len(df_list) > 1:
        df_list = fill_with_same_index(df_list=df_list)

    kline = None
    for idx, df in enumerate(df_list):
        security_id = df[df.security_id.notna()]['security_id'][0]
        security_type, _, _ = decode_security_id(security_id)

        xdata = [to_time_str(timestamp) for timestamp in df.index]

        if security_type == SecurityType.stock:
            ydata = df.loc[:, ['qfq_open', 'qfq_close', 'qfq_low', 'qfq_high']].values.tolist()
        else:
            ydata = df.loc[:, ['open', 'close', 'low', 'high']].values.tolist()

        current_kline = get_default_kline()
        current_kline.add_xaxis(xdata)

        # markpoint
        markpoint_opts = None
        if markpoints_list:
            mark_points = markpoints_list[idx]
            if mark_points is not None and not mark_points.empty:
                mark_point_items = []
                for timestamp, item in mark_points.iterrows():
                    if to_time_str(timestamp) in df.index:

                        if item['order_type'] == 'order_long':
                            flag_name = 'buy'
                            symbol = 'arrow'
                            color = "#ec0000"

                        if item['order_type'] == 'order_close_long':
                            flag_name = 'sell'
                            symbol = 'pin'
                            color = "#00da3c"

                        value = round(item['order_price'], 2)

                        mark_point_items.append(
                            opts.MarkPointItem(name=flag_name, coord=[to_time_str(timestamp), value],
                                               value=value, symbol=symbol, symbol_size=20))

                    markpoint_opts = opts.MarkPointOpts(data=mark_point_items, symbol_size=20)

        current_kline.add_yaxis(security_id, ydata,
                                markpoint_opts=markpoint_opts,
                                itemstyle_opts=opts.ItemStyleOpts(
                                    color="#ec0000",
                                    color0="#00da3c",
                                    border_color="#8A0000",
                                    border_color0="#008F28"))

        if not kline:
            kline = current_kline
        else:
            kline.overlap(current_kline)

    if render == 'html':
        kline.render(get_ui_path(file_name))
    elif render == 'notebook':
        kline.render_notebook()

    return kline


if __name__ == '__main__':
    kdata1 = get_kdata(security_id='stock_sz_000338', provider='netease')
    kdata2 = get_kdata(security_id='stock_sz_000778', provider='netease')

    df_list = fill_with_same_index([kdata1, kdata2])
    assert len(df_list[0]) == len(df_list[1])
    print(df_list[0])
    print(df_list[1])

    draw_kline(df_list, file_name='test_kline.html')
