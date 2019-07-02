# -*- coding: utf-8 -*-
import os
from typing import List

import pandas as pd
import plotly
import plotly.graph_objs as go

from zvt.api.common import decode_security_id
from zvt.domain import SecurityType
from zvt.settings import UI_PATH
from zvt.utils.pd_utils import fill_with_same_index, df_is_not_null
from zvt.utils.time_utils import TIME_FORMAT_ISO8601, now_time_str


def get_ui_path(name):
    if name is None:
        name = '{}.html'.format(now_time_str(fmt=TIME_FORMAT_ISO8601))
    return os.path.join(UI_PATH, '{}.html'.format(name))


class Chart(object):
    def __init__(self,
                 category_field: str = 'security_id',
                 # child added arguments
                 figures: List[go._BaseTraceType] = [go.Scatter],
                 modes: List[str] = ['lines'],
                 value_fields: List[str] = ['close'],
                 render: str = 'html',
                 file_name: str = None,
                 width: int = None,
                 height: int = None,
                 title: str = None,
                 keep_ui_state: bool = True) -> None:
        self.figures = figures
        self.modes = modes
        self.category_field = category_field
        self.value_fields = value_fields
        self.render = render
        self.file_name = file_name
        self.width = width
        self.height = height

        if title:
            self.title = title
        else:
            self.title = type(self).__name__.lower()

        self.keep_ui_state = keep_ui_state

        self.data_df: pd.DataFrame = None
        self.annotation_df: pd.DataFrame = None

    def set_data_df(self, df):
        self.data_df = df

    def set_annotation_df(self, df):
        """
        annotation_df should in this format:
                                           flag value  color
        self.trace_field      timestamp

        stock_sz_000338       2019-01-02   buy  100    "#ec0000"

        :param df:
        :type df:
        """
        self.annotation_df = df

    def get_annotation_df(self):
        return self.annotation_df

    def get_data_df(self):
        return self.data_df

    def get_plotly_annotations(self):
        annotations = []

        if df_is_not_null(self.get_annotation_df()):
            for trace_name, df in self.annotation_df.groupby(level=0):
                if df_is_not_null(df):
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

    def get_plotly_data(self):
        if not df_is_not_null(self.get_data_df()):
            return []

        df_list: List[pd.DataFrame] = []
        for _, df_item in self.get_data_df().groupby(self.category_field):
            df = df_item.copy()
            df.reset_index(inplace=True, level=self.category_field)
            df_list.append(df)

        if len(df_list) > 1:
            df_list = fill_with_same_index(df_list=df_list)

        data = []
        for df in df_list:
            series_name = df[df[self.category_field].notna()][self.category_field][0]

            xdata = [timestamp for timestamp in df.index]

            # draw all figures for one category
            for i, figure in enumerate(self.figures):

                if figure == go.Candlestick:
                    security_type, _, _ = decode_security_id(series_name)
                    trace_name = '{}_kdata'.format(series_name)

                    if security_type == SecurityType.stock:
                        open = df.loc[:, 'qfq_open']
                        close = df.loc[:, 'qfq_close']
                        high = df.loc[:, 'qfq_high']
                        low = df.loc[:, 'qfq_low']
                    else:
                        open = df.loc[:, 'open']
                        close = df.loc[:, 'close']
                        high = df.loc[:, 'high']
                        low = df.loc[:, 'low']

                    data.append(go.Candlestick(x=xdata, open=open, close=close, low=low, high=high, name=trace_name))
                elif figure == go.Table:
                    cols = ['timestamp'] + list(df.columns)
                    trace = go.Table(
                        header=dict(values=cols,
                                    fill=dict(color='#C2D4FF'),
                                    align=['left'] * 5),
                        cells=dict(values=[df.index] + [df[col] for col in df.columns],
                                   fill=dict(color='#F5F8FF'),
                                   align=['left'] * 5))

                    data.append(trace)

                else:
                    trace_name = '{}_{}'.format(series_name, self.value_fields[i])

                    ydata = df.loc[:, self.value_fields[i]].values.tolist()
                    data.append(figure(x=xdata, y=ydata, mode=self.modes[i], name=trace_name))

        return data

    def get_plotly_layout(self):
        if self.keep_ui_state:
            uirevision = True
        else:
            uirevision = None

        return go.Layout(showlegend=True,
                         uirevision=uirevision,
                         height=self.height,
                         width=self.width,
                         title=self.title,
                         annotations=self.get_plotly_annotations(),
                         yaxis=dict(
                             autorange=True,
                             fixedrange=False
                         ),
                         xaxis=dict(
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
                                 visible=True
                             ),
                             type='date'
                         ))

    def draw(self):
        if self.render == 'html':
            plotly.offline.plot(figure_or_data={'data': self.get_plotly_data(),
                                                'layout': self.get_plotly_layout()
                                                }, filename=get_ui_path(self.file_name), )
        elif self.render == 'notebook':
            plotly.offline.init_notebook_mode(connected=True)
            plotly.offline.iplot(figure_or_data={'data': self.get_plotly_data(),
                                                 'layout': self.get_plotly_layout()
                                                 })

        return self.get_plotly_data(), self.get_plotly_layout()
