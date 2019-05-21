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
        datazoom_opts=[opts.DataZoomOpts()],
        title_opts=opts.TitleOpts(title="Kline-ItemStyle"))
    return kline


def get_default_timeline():
    timeline = Timeline(init_opts=get_init_opts())
    timeline.add_schema(is_auto_play=False, axis_type='time', pos_bottom='10%')
    return timeline


def get_ui_path(name):
    if name is None:
        name = '{}.html'.format(now_time_str(fmt=TIME_FORMAT_ISO8601))
    return os.path.join(UI_PATH, name)


def draw_compare(df_list: List[pd.DataFrame], chart_type=Line, columns=[], name='security_id', render='html',
                 file_name=None):
    chart = None

    if chart_type == Line:
        chart = get_default_line()
        assert len(columns) == 1

    xdata = [to_time_str(timestamp) for timestamp in df_list[0].index]

    chart.add_xaxis(xdata)

    for df in df_list:
        name = df[name][0]

        if len(columns) == 1:
            ydata = df.loc[:, columns[0]].values.tolist()

        chart.add_yaxis(name, ydata, is_smooth=True)

    if render == 'html':
        chart.render(get_ui_path(file_name))

    return chart


def draw_kline(df_list: List[pd.DataFrame], render='html', file_name=None) -> Kline:
    kline = None
    for df in df_list:
        security_id = df['security_id'][0]
        security_type, _, _ = decode_security_id(security_id)

        xdata = [to_time_str(timestamp) for timestamp in df.index]

        if security_type == SecurityType.stock:
            ydata = df.loc[:, ['qfq_open', 'qfq_close', 'qfq_low', 'qfq_high']].values.tolist()
        else:
            ydata = df.loc[:, ['open', 'close', 'low', 'high']].values.tolist()

        current_kline = get_default_kline()
        current_kline.add_xaxis(xdata)
        current_kline.add_yaxis(security_id, ydata,
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

    return kline


if __name__ == '__main__':
    kdata = get_kdata(security_id='stock_sz_300027', provider='netease')
    draw_kline([kdata])
