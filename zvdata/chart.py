# -*- coding: utf-8 -*-
import os

import dash_table
import plotly
import plotly.graph_objs as go

from zvdata.api import decode_entity_id
from zvdata.domain import context
from zvdata.normal_data import NormalData, TableType
from zvdata.utils.pd_utils import df_is_not_null
from zvdata.utils.time_utils import now_time_str, TIME_FORMAT_ISO8601
from zvdata.utils.utils import to_positive_number


def get_ui_path(name):
    if name is None:
        return os.path.join(context['ui_path'], '{}.html'.format(now_time_str(fmt=TIME_FORMAT_ISO8601)))
    return os.path.join(context['ui_path'], f'{name}.html')


class Drawer(object):
    def __init__(self, data: NormalData = None) -> None:
        self.normal_data: NormalData = data

    def refresh_data(self, data: NormalData = None):
        self.normal_data = data

    def get_plotly_annotations(self):
        annotation_df = self.normal_data.annotation_df
        annotations = []

        if df_is_not_null(annotation_df):
            for trace_name, df in annotation_df.groupby(level=0):
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

    def get_plotly_layout(self,
                          width=None,
                          height=None,
                          title=None,
                          keep_ui_state=True,
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
                           annotations=self.get_plotly_annotations(),
                           yaxis=dict(
                               autorange=True,
                               fixedrange=False,
                               zeroline=False
                           ),
                           **layout_params)
        if self.normal_data.is_timeseries and need_range_selector and len(self.normal_data.data_df) > 500:
            layout.xaxis = dict(
                domain=[0.2, 0.9],
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
            )
        return layout

    def show(self, plotly_data, plotly_layout=None, annotation_df=None, render='html', file_name=None, width=None,
             height=None, title=None, keep_ui_state=True, **layout_params):
        if plotly_layout is None:
            plotly_layout = self.get_plotly_layout(width=width, height=height, title=title, keep_ui_state=keep_ui_state,
                                                   **layout_params)

        # TODO:better way to add annotation
        if annotation_df:
            self.normal_data.annotation_df = annotation_df

        if render == 'html':
            plotly.offline.plot(figure_or_data={'data': plotly_data,
                                                'layout': plotly_layout
                                                }, filename=get_ui_path(file_name))

        elif render == 'notebook':
            plotly.offline.init_notebook_mode(connected=True)
            plotly.offline.iplot(figure_or_data={'data': plotly_data,
                                                 'layout': plotly_layout
                                                 })

        else:
            return plotly_data, plotly_layout

    def draw(self, chart: str, plotly_layout=None, annotation_df=None, render='html', file_name=None, width=None,
             height=None, title=None, keep_ui_state=True, property_map=None, **kwargs):

        func_name = f'self.draw_{chart}'
        draw_func = eval(func_name)

        return draw_func(plotly_layout=plotly_layout, annotation_df=annotation_df, render=render, file_name=file_name,
                         width=width, height=height, title=title, keep_ui_state=keep_ui_state,
                         property_map=property_map, **kwargs)

    def draw_compare(self, chart: str, plotly_layout=None, annotation_df=None, render='html', file_name=None,
                     width=None, height=None, title=None, keep_ui_state=True, property_map=None, **kwargs):
        data = []
        layout_params = {}
        for entity_id, df in self.normal_data.entity_map_df.items():
            _, _, code = decode_entity_id(entity_id)
            for col in df.columns:
                trace_name = '{}_{}'.format(code, col)
                ydata = df.loc[:, col].values.tolist()

                # set y axis
                yaxis, layout, col_chart = self.get_yaxis_layout_chart(col, property_map)
                if yaxis and layout:
                    layout_params[f'yaxis{yaxis[-1]}'] = layout

                if not col_chart:
                    col_chart = chart

                if col_chart == 'line':
                    trace = go.Scatter(x=df.index, y=ydata, mode='lines', name=trace_name, yaxis=yaxis, **kwargs)
                elif col_chart == 'scatter':
                    trace = go.Scatter(x=df.index, y=ydata, mode='markers', name=trace_name, yaxis=yaxis, **kwargs)
                elif col_chart == 'area':
                    trace = go.Scatter(x=df.index, y=ydata, mode='none', fill='tonexty', name=trace_name, yaxis=yaxis,
                                       **kwargs)
                elif col_chart == 'bar':
                    trace = go.Bar(x=df.index, y=ydata, name=trace_name, yaxis=yaxis, **kwargs)

                data.append(trace)

        return self.show(plotly_data=data, plotly_layout=plotly_layout, annotation_df=annotation_df, render=render,
                         file_name=file_name, width=width,
                         height=height, title=title, keep_ui_state=keep_ui_state, **layout_params)

    def draw_line(self, plotly_layout=None, annotation_df=None, render='html', file_name=None, width=None, height=None,
                  title=None, keep_ui_state=True, property_map=None, **kwargs):
        return self.draw_scatter(mode='lines', plotly_layout=plotly_layout, annotation_df=annotation_df, render=render,
                                 file_name=file_name,
                                 width=width, height=height, title=title, keep_ui_state=keep_ui_state,
                                 property_map=property_map, **kwargs)

    def draw_area(self, plotly_layout=None, annotation_df=None, render='html', file_name=None, width=None, height=None,
                  title=None, keep_ui_state=True, property_map=None, **kwargs):
        return self.draw_scatter(mode='none', fill='tonexty', plotly_layout=plotly_layout, annotation_df=annotation_df,
                                 render=render,
                                 file_name=file_name,
                                 width=width, height=height, title=title, keep_ui_state=keep_ui_state,
                                 property_map=property_map, **kwargs)

    def get_yaxis_layout_chart(self, col, property_map):
        yaxis = None
        chart = None
        if property_map:
            props = property_map.get(col)
            if props:
                if props.get('y_axis') != 'y1':
                    yaxis = props.get('y_axis')

                chart = props.get('chart')

        layout = None

        if yaxis:
            i = int(yaxis[-1])
            if i % 2 == 1:
                layout = dict(
                    title=col,
                    titlefont=dict(
                        color="#ff7f0e"
                    ),
                    tickfont=dict(
                        color="#ff7f0e"
                    ),
                    autorange=True,
                    fixedrange=False,
                    zeroline=False,
                    anchor="free",
                    overlaying="y",
                    side="left",
                    position=0.05 * (i - 1)
                )
            else:
                layout = dict(
                    title=col,
                    titlefont=dict(
                        color="#d62728"
                    ),
                    tickfont=dict(
                        color="#d62728"
                    ),
                    autorange=True,
                    fixedrange=False,
                    zeroline=False,
                    anchor="free",
                    overlaying="y",
                    side="right",
                    position=1.0 - 0.05 * (i - 1)
                )

        return yaxis, layout, chart

    def draw_scatter(self, mode='markers', plotly_layout=None, annotation_df=None, render='html', file_name=None,
                     width=None, height=None,
                     title=None, keep_ui_state=True, property_map=None, **kwargs):
        data = []
        layout_params = {}
        for entity_id, df in self.normal_data.entity_map_df.items():
            _, _, code = decode_entity_id(entity_id)
            for col in df.columns:
                trace_name = '{}_{}'.format(code, col)
                ydata = df.loc[:, col].values.tolist()

                # set y axis
                yaxis, layout = self.get_yaxis_layout_chart(col, property_map)
                if yaxis and layout:
                    layout_params[f'yaxis{yaxis[-1]}'] = layout

                data.append(go.Scatter(x=df.index, y=ydata, mode=mode, name=trace_name, yaxis=yaxis, **kwargs))

        return self.show(plotly_data=data, plotly_layout=plotly_layout, annotation_df=annotation_df, render=render,
                         file_name=file_name, width=width,
                         height=height, title=title, keep_ui_state=keep_ui_state, **layout_params)

    def draw_bar(self, x='columns', plotly_layout=None, annotation_df=None, render='html', file_name=None, width=None,
                 height=None,
                 title=None, keep_ui_state=True, property_map=None, **kwargs):
        data = []
        layout_params = {}
        for entity_id, df in self.normal_data.entity_map_df.items():
            _, _, code = decode_entity_id(entity_id)
            for col in df.columns:
                trace_name = '{}_{}'.format(code, col)
                ydata = df.loc[:, col].values.tolist()

                # set y axis
                yaxis, layout = self.get_yaxis_layout_chart(col, property_map)
                if yaxis and layout:
                    layout_params[f'yaxis{yaxis[-1]}'] = layout

                data.append(go.Bar(x=df.index, y=ydata, name=trace_name, yaxis=yaxis, **kwargs))

        return self.show(plotly_data=data, plotly_layout=plotly_layout, annotation_df=annotation_df, render=render,
                         file_name=file_name, width=width,
                         height=height, title=title, keep_ui_state=keep_ui_state, **layout_params)

    def draw_pie(self, plotly_layout=None, annotation_df=None, render='html', file_name=None, width=None, height=None,
                 title=None, keep_ui_state=True, property_map=None, **kwargs):
        data = []
        for entity_id, df in self.normal_data.entity_map_df.items():
            for _, row in df.iterrows():
                row = row.apply(lambda x: to_positive_number(x))
                data.append(go.Pie(name=entity_id, labels=df.columns.tolist(), values=row.tolist(), **kwargs))
                # just support one pie now
                # TODO: group by entity
                break

        return self.show(plotly_data=data, plotly_layout=plotly_layout, annotation_df=annotation_df, render=render,
                         file_name=file_name, width=width,
                         height=height, title=title, keep_ui_state=keep_ui_state)

    def draw_polar(self, plotly_layout=None, annotation_df=None, render='html', file_name=None, width=None, height=None,
                   title=None, keep_ui_state=True, property_map=None, **kwargs):
        data = []
        for entity_id, df in self.normal_data.entity_map_df.items():
            for _, row in df.iterrows():
                row = row.apply(lambda x: to_positive_number(x))

                trace = go.Scatterpolar(
                    r=row.to_list(),
                    theta=df.columns.tolist(),
                    fill='toself',
                    name=entity_id,
                    **kwargs
                )
                data.append(trace)
                # just support one pie now
                # TODO: group by entity
                break

        return self.show(plotly_data=data, plotly_layout=plotly_layout, annotation_df=annotation_df, render=render,
                         file_name=file_name, width=width,
                         height=height, title=title, keep_ui_state=keep_ui_state)

    def draw_histogram(self, plotly_layout=None, annotation_df=None, render='html', file_name=None, width=None,
                       height=None,
                       title=None, keep_ui_state=True, property_map=None, **kwargs):
        data = []
        annotations = []
        for entity_id, df in self.normal_data.entity_map_df.items():
            _, _, code = decode_entity_id(entity_id)

            for col in df.columns:
                trace_name = '{}_{}'.format(code, col)
                x = df[col].tolist()
                trace = go.Histogram(
                    x=x,
                    name=trace_name,
                    histnorm='probability',
                    **kwargs
                )
                annotation = dict(
                    x=x[-1],
                    y=0,
                    xref='x',
                    yref='y',
                    text=f'current:{x[-1]}',
                    showarrow=True,
                    align='center',
                    arrowhead=2,
                    arrowsize=1,
                    arrowwidth=2,
                    # arrowcolor='#030813',
                    # ax=-0.02,
                    # ay=-0.02,
                    bordercolor='#c7c7c7',
                    borderwidth=1,
                    opacity=0.8
                )
                data.append(trace)
                annotations.append(annotation)
            # just support one entity
            break

        if keep_ui_state:
            uirevision = True
        else:
            uirevision = None

        layout = go.Layout(showlegend=True,
                           uirevision=uirevision,
                           height=height,
                           width=width,
                           title=title,
                           annotations=annotations,
                           barmode='overlay')

        return self.show(plotly_data=data, plotly_layout=layout, render=render, file_name=file_name, width=width,
                         height=height, title=title, keep_ui_state=keep_ui_state)

    def draw_kline(self, plotly_layout=None, annotation_df=None, render='html', file_name=None, width=None, height=None,
                   title=None, keep_ui_state=True, indicators=[], property_map=None, **kwargs):
        data = []
        for entity_id, df in self.normal_data.entity_map_df.items():
            entity_type, _, code = decode_entity_id(entity_id)

            trace_name = '{}_kdata'.format(code)

            if entity_type == 'stock':
                open = df.loc[:, 'qfq_open']
                close = df.loc[:, 'qfq_close']
                high = df.loc[:, 'qfq_high']
                low = df.loc[:, 'qfq_low']
            else:
                open = df.loc[:, 'open']
                close = df.loc[:, 'close']
                high = df.loc[:, 'high']
                low = df.loc[:, 'low']

            data.append(
                go.Candlestick(x=df.index, open=open, close=close, low=low, high=high, name=trace_name, **kwargs))

            # append indicators
            for indicator in indicators:
                if indicator in df.columns:
                    trace_name = '{}_{}'.format(code, indicator)
                    ydata = df.loc[:, indicator].values.tolist()
                    data.append(go.Scatter(x=df.index, y=ydata, mode='lines', name=trace_name))

        return self.show(plotly_data=data, plotly_layout=plotly_layout, annotation_df=annotation_df, render=render,
                         file_name=file_name, width=width,
                         height=height, title=title, keep_ui_state=keep_ui_state)

    def draw_table(self, plotly_layout=None, annotation_df=None, render='html', file_name=None, width=None, height=None,
                   title=None, keep_ui_state=True, property_map=None, **kwargs):
        cols = self.normal_data.data_df.index.names + self.normal_data.data_df.columns.tolist()

        index1 = self.normal_data.data_df.index.get_level_values(0).tolist()
        index2 = self.normal_data.data_df.index.get_level_values(1).tolist()
        values = [index1] + [index2] + [self.normal_data.data_df[col] for col in self.normal_data.data_df.columns]

        data = go.Table(
            header=dict(values=cols,
                        fill_color=['#000080', '#000080'] + ['#0066cc'] * len(self.normal_data.data_df.columns),
                        align='left',
                        font=dict(color='white', size=13)),
            cells=dict(values=values, fill=dict(color='#F5F8FF'), align='left'), **kwargs)

        return self.show(plotly_data=[data], plotly_layout=plotly_layout, annotation_df=annotation_df, render=render,
                         file_name=file_name, width=width,
                         height=height, title=title, keep_ui_state=keep_ui_state)

    def draw_data_table(self, id=None):
        cols = self.normal_data.data_df.index.names + self.normal_data.data_df.columns.tolist()

        df = self.normal_data.data_df.reset_index()

        return dash_table.DataTable(
            id=id,
            columns=[{'name': i, 'id': i} for i in cols],
            data=df.to_dict('records'),
            filter_action="native",
            sort_action="native",
            sort_mode='multi',
            row_selectable='multi',
            selected_rows=[],
            page_action='native',
            page_current=0,
            page_size=5,
        )


if __name__ == '__main__':
    for table_type in TableType:
        drawer = Drawer(data=NormalData(NormalData.sample(table_type=table_type)))
        drawer.draw_table()
