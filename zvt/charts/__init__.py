# -*- coding: utf-8 -*-
from typing import List

import pandas as pd
from pyecharts import options as opts
from pyecharts.charts import Line
from pyecharts.charts.basic_charts.kline import Kline
from pyecharts.options import InitOpts

from zvt.api.common import decode_security_id, get_data
from zvt.api.technical import get_kdata
from zvt.domain import SecurityType
from zvt.utils.time_utils import to_time_str

r_hex = '#dc2624'  # red,       RGB = 220,38,36
dt_hex = '#2b4750'  # dark teal, RGB = 43,71,80
tl_hex = '#45a0a2'  # teal,      RGB = 69,160,162
r1_hex = '#e87a59'  # red,       RGB = 232,122,89
tl1_hex = '#7dcaa9'  # teal,      RGB = 125,202,169
g_hex = '#649E7D'  # green,     RGB = 100,158,125
o_hex = '#dc8018'  # orange,    RGB = 220,128,24
tn_hex = '#C89F91'  # tan,       RGB = 200,159,145
g50_hex = '#6c6d6c'  # grey-50,   RGB = 108,109,108
bg_hex = '#4f6268'  # blue grey, RGB = 79,98,104
g25_hex = '#c7cccf'  # grey-25,   RGB = 199,204,207

default_init_opts = InitOpts(theme="white", page_title='awesome zvt')


def common_data(data_schema, security_id=None, codes=None, level=None, provider='eastmoney', columns=None,
                start_timestamp=None, end_timestamp=None, filters=None, session=None, order=None, limit=None):
    if security_id:
        df = get_data(data_schema=data_schema, security_id=security_id, codes=None, level=level, provider=provider,
                      columns=columns, return_type='df', start_timestamp=start_timestamp,
                      end_timestamp=end_timestamp, filters=filters, session=session, order=order, limit=limit)
        return [df]
    if codes:
        df_list = []
        for code in codes:
            df_list.append(
                get_data(data_schema=data_schema, security_id=None, codes=[code], level=level, provider=provider,
                         columns=columns, return_type='df', start_timestamp=start_timestamp,
                         end_timestamp=end_timestamp, filters=filters, session=session, order=order, limit=limit))
        return df_list


def common_draw(df_list: List[pd.DataFrame], chart_type=Line, columns=[]):
    charts = None
    for df in df_list:
        print(df)
        security_id = df['security_id'][0]
        security_type, _, _ = decode_security_id(security_id)

        xdata = [to_time_str(timestamp) for timestamp in df.index]
        ydata = df.loc[:, columns].values.tolist()

        current_chart = None

        if chart_type == Line:
            current_chart = Line()
            current_chart.add_xaxis(xdata)
            current_chart.add_yaxis(security_id, ydata, is_smooth=True)
            current_chart.set_global_opts(title_opts=opts.TitleOpts(title="Line-smooth"))

        if not charts:
            charts = current_chart
        else:
            charts.overlap(current_chart)

    return charts


def draw_kline(df_list: List[pd.DataFrame]) -> Kline:
    kline = None
    for df in df_list:
        print(df)
        security_id = df['security_id'][0]
        security_type, _, _ = decode_security_id(security_id)

        xdata = [to_time_str(timestamp) for timestamp in df.index]

        if security_type == SecurityType.stock:
            ydata = df.loc[:, ['open', 'close', 'low', 'high']].values.tolist()
        else:
            ydata = df.loc[:, ['open', 'close', 'low', 'high']].values.tolist()

        current_kline = (
            Kline()
                .add_xaxis(xdata)
                .add_yaxis(
                security_id,
                ydata,
                itemstyle_opts=opts.ItemStyleOpts(
                    color="#ec0000",
                    color0="#00da3c",
                    border_color="#8A0000",
                    border_color0="#008F28",
                ),
            )
                .set_global_opts(
                xaxis_opts=opts.AxisOpts(is_scale=True),
                yaxis_opts=opts.AxisOpts(
                    is_scale=True,
                    splitarea_opts=opts.SplitAreaOpts(
                        is_show=True, areastyle_opts=opts.AreaStyleOpts(opacity=1)
                    ),
                ),
                datazoom_opts=[opts.DataZoomOpts()],
                title_opts=opts.TitleOpts(title="Kline-ItemStyle"),
            )
        )

        if not kline:
            kline = current_kline
        else:
            kline.overlap(current_kline)

    return kline


if __name__ == '__main__':
    kdata = get_kdata(security_id='stock_sz_300027', provider='netease')
    draw_kline([kdata])
