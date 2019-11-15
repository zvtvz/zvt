# -*- coding: utf-8 -*-
import os

import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots

from zvdata.api import decode_entity_id, get_data
from zvdata.normal_data import NormalData
from zvdata.utils.pd_utils import pd_is_not_null
from zvdata.utils.time_utils import now_time_str, TIME_FORMAT_ISO8601
from zvt import zvt_env
from zvt.domain import Stock1dKdata, Stock1dMaStateStats


class Drawer(object):
    def __init__(self,
                 main_df: pd.DataFrame = None,
                 sub_df: pd.DataFrame = None,
                 main_data: NormalData = None,
                 sub_data: NormalData = None,
                 annotation_df: pd.DataFrame = None) -> None:
        # 主图数据
        if main_data is None:
            main_data = NormalData(main_df)
        self.main_data: NormalData = main_data

        # 副图数据
        if sub_data is None:
            sub_data = NormalData(sub_df)
        self.sub_data: NormalData = sub_data

        # 主图的标记数据
        self.annotation_df = annotation_df

    def _draw(self,
              main_chart='kline',
              sub_chart='bar',
              mode='markers',
              width=None,
              height=None,
              title=None,
              keep_ui_state=True,
              **kwargs):
        if self.sub_data is not None and not self.sub_data.empty():
            subplot = True
            fig = make_subplots(rows=2, cols=1, row_heights=[0.8, 0.2], vertical_spacing=0.08, shared_xaxes=True)
        else:
            subplot = False
            fig = go.Figure()

        traces = []
        sub_traces = []

        for entity_id, df in self.main_data.entity_map_df.items():
            entity_type, _, code = decode_entity_id(entity_id)

            if main_chart == 'kline':
                trace_name = '{}_kdata'.format(code)
                trace = go.Candlestick(x=df.index, open=df['open'], close=df['close'], low=df['low'], high=df['high'],
                                       name=trace_name, **kwargs)
                traces.append(trace)
            elif main_chart == 'scatter':
                for col in df.columns:
                    trace_name = '{}_{}'.format(code, col)
                    ydata = df[col].values.tolist()
                    traces.append(go.Scatter(x=df.index, y=ydata, mode=mode, name=trace_name, **kwargs))

            if subplot:
                # 绘制幅图
                sub_df = self.sub_data.entity_map_df.get(entity_id)
                if pd_is_not_null(sub_df):
                    for col in sub_df.columns:
                        trace_name = '{}_{}'.format(code, col)
                        ydata = sub_df[col].values.tolist()

                        def color(i):
                            if i > 0:
                                return 'red'
                            else:
                                return 'green'

                        colors = [color(i) for i in ydata]
                        bar = go.Bar(x=sub_df.index, y=ydata, name=trace_name, yaxis='y2', marker_color=colors)
                        sub_traces.append(bar)

        if subplot:
            fig.add_traces(traces, rows=[1] * len(traces), cols=[1] * len(traces))
            fig.add_traces(sub_traces, rows=[2] * len(sub_traces), cols=[1] * len(sub_traces))
        else:
            fig.add_traces(traces)

        fig.update_layout(self.gen_plotly_layout(width=width, height=height, title=title, keep_ui_state=keep_ui_state,
                                                 subplot=subplot))

        fig.show()

    def draw_kline(self, width=None, height=None, title=None, keep_ui_state=True, **kwargs):
        return self._draw('kline', width=width, height=height, title=title, keep_ui_state=keep_ui_state, **kwargs)

    def draw_line(self, width=None, height=None, title=None, keep_ui_state=True, **kwargs):
        return self.draw_scatter(mode='lines', width=width, height=height, title=title,
                                 keep_ui_state=keep_ui_state, **kwargs)

    def draw_area(self, width=None, height=None, title=None, keep_ui_state=True, **kwargs):
        return self.draw_scatter(mode='none', width=width, height=height, title=title,
                                 keep_ui_state=keep_ui_state, fill='tonexty', **kwargs)

    def draw_scatter(self, mode='markers', width=None, height=None,
                     title=None, keep_ui_state=True, **kwargs):
        return self._draw('scatter', mode=mode, width=width, height=height, title=title, keep_ui_state=keep_ui_state,
                          **kwargs)

    def draw_table(self, width=None, height=None, title=None, keep_ui_state=True, **kwargs):
        cols = self.main_data.data_df.index.names + self.main_data.data_df.columns.tolist()

        index1 = self.main_data.data_df.index.get_level_values(0).tolist()
        index2 = self.main_data.data_df.index.get_level_values(1).tolist()
        values = [index1] + [index2] + [self.main_data.data_df[col] for col in self.main_data.data_df.columns]

        data = go.Table(
            header=dict(values=cols,
                        fill_color=['#000080', '#000080'] + ['#0066cc'] * len(self.main_data.data_df.columns),
                        align='left',
                        font=dict(color='white', size=13)),
            cells=dict(values=values, fill=dict(color='#F5F8FF'), align='left'), **kwargs)

        fig = go.Figure()
        fig.add_traces([data])
        fig.update_layout(self.gen_plotly_layout(width=width, height=height, title=title, keep_ui_state=keep_ui_state))

        fig.show()

    def gen_plotly_layout(self,
                          width=None,
                          height=None,
                          title=None,
                          keep_ui_state=True,
                          subplot=False,
                          need_range_selector=True,
                          **layout_params):
        if keep_ui_state:
            uirevision = True
        else:
            uirevision = None

        layout = go.Layout(showlegend=True,
                           uirevision=uirevision,
                           height=height,
                           width=width,
                           title=title,
                           annotations=to_annotations(self.annotation_df),
                           yaxis=dict(
                               autorange=True,
                               fixedrange=False,
                               zeroline=False
                           ),
                           **layout_params)

        if subplot:
            layout.yaxis2 = dict(autorange=True,
                                 fixedrange=False,
                                 zeroline=False)

        if need_range_selector and len(self.main_data.data_df) > 500:
            layout.xaxis = dict(
                rangeselector=dict(
                    buttons=list([
                        dict(count=1,
                             label='1m',
                             step='month',
                             stepmode='backward'),
                        dict(count=6,
                             label='6m',
                             step='month',
                             stepmode='backward'),
                        dict(count=1,
                             label='YTD',
                             step='year',
                             stepmode='todate'),
                        dict(count=1,
                             label='1y',
                             step='year',
                             stepmode='backward'),
                        dict(step='all')
                    ])
                ),
                rangeslider=dict(
                    visible=False,
                ),
                type='date'
            )

            # 没有子图，显示rangeslider
            # if not subplot:
            #     layout.xaxis.rangeslider = dict(
            #         autorange=True,
            #         visible=True,
            #         borderwidth=1
            #     )

        return layout


def get_ui_path(name):
    if name is None:
        return os.path.join(zvt_env['ui_path'], '{}.html'.format(now_time_str(fmt=TIME_FORMAT_ISO8601)))
    return os.path.join(zvt_env['ui_path'], f'{name}.html')


def to_annotations(annotation_df: pd.DataFrame):
    """
    annotation_df format:
                                    value    flag    color
    entity_id    timestamp


    :param annotation_df:
    :type annotation_df:
    :return:
    :rtype:
    """
    annotations = []

    if pd_is_not_null(annotation_df):
        for trace_name, df in annotation_df.groupby(level=0):
            if pd_is_not_null(df):
                for (_, timestamp), item in df.iterrows():
                    if 'color' in item:
                        color = item['color']
                    else:
                        color = '#ec0000'

                    value = round(item['value'], 2)
                    annotations.append(dict(
                        x=timestamp,
                        y=value,
                        xref='x',
                        yref='y',
                        text=item['flag'],
                        showarrow=True,
                        align='center',
                        arrowhead=2,
                        arrowsize=1,
                        arrowwidth=2,
                        # arrowcolor='#030813',
                        ax=-10,
                        ay=-30,
                        bordercolor='#c7c7c7',
                        borderwidth=1,
                        bgcolor=color,
                        opacity=0.8
                    ))

    return annotations


if __name__ == '__main__':
    df = get_data(data_schema=Stock1dKdata, provider='joinquant', entity_ids=['stock_sz_000001', 'stock_sz_000002'])
    df1 = get_data(data_schema=Stock1dMaStateStats, provider='zvt', entity_ids=['stock_sz_000001', 'stock_sz_000002'],
                   columns=['current_count'])

    drawer = Drawer(df, df1[['current_count']])
    drawer.draw_kline()
