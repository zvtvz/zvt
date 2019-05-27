# -*- coding: utf-8 -*-
from pyecharts.charts import Page, Pie

from zvt.api.account import get_account, get_orders, get_position
from zvt.api.technical import get_kdata
from zvt.charts import draw_kline, get_ui_path, draw_line, get_default_timeline
from zvt.utils.time_utils import to_time_str


def draw_account_list(trader_name_list, render='html'):
    df_list = []
    for trader_name in trader_name_list:
        df_account = get_account(trader_name=trader_name)
        df_list.append(df_account)

    if len(trader_name_list) == 1:
        file_name = trader_name_list[0]
    else:
        file_name = '_vs_'.join(trader_name_list)

    return draw_line(df_list, columns=['all_value'], name_field='trader_name', file_name=file_name,
                     render=render)


def draw_order_signals(trader_name, render='html'):
    df_account = get_account(trader_name=trader_name)
    start_timestamp = df_account['timestamp'][0]
    end_timestamp = df_account['timestamp'][-1]

    df_orders = get_orders(trader_name=trader_name)
    grouped = df_orders.groupby('security_id')

    page = Page()

    for security_id, order_df in grouped:
        kdata = get_kdata(security_id=security_id, provider='netease', start_timestamp=start_timestamp,
                          end_timestamp=end_timestamp)
        mark_points = order_df
        kline = draw_kline(df_list=[kdata], markpoints_list=[mark_points], render=None)

        page.add(kline)

    if render == 'html':
        file_name = '{}_signals'.format(trader_name)
        page.render(get_ui_path(file_name))
    elif render == 'notebook':
        page.render_notebook()

    return page


def draw_positions(trader_name, render='html'):
    df_position = get_position(trader_name=trader_name)

    time_line = get_default_timeline()
    for timestamp in df_position.index:
        securities = df_position.loc[timestamp, ['security_id']].values.tolist()
        positions = zip(securities,
                        df_position.loc[timestamp, ['value']].values.tolist())

        if len(securities) > 1:
            security_positions = [(x[0], y[0]) for x, y in positions]
        else:
            security_positions = [(x, y) for x, y in positions]
        print(security_positions)
        pie = Pie().add('{} positions'.format(trader_name), security_positions)
        time_line.add(pie, to_time_str(timestamp))

    if render == 'html':
        file_name = '{}_positions'.format(trader_name)
        time_line.render(get_ui_path(file_name))
    elif render == 'notebook':
        time_line.render_notebook()

    return time_line


def draw_account_details(trader_name, render='html'):
    page = Page()

    account_summary = draw_account_list([trader_name], render=None)
    # klines = draw_order_signals(trader_name=trader_name, render=None)
    positions = draw_positions(trader_name=trader_name, render=None)

    page.add(account_summary, positions)

    if render == 'html':
        file_name = '{}_details'.format(trader_name)
        page.render(get_ui_path(file_name))
    elif render == 'notebook':
        page.render_notebook()

    return page


if __name__ == '__main__':
    draw_account_list(['fooltrader', 'multipleleveltrader'])
    # draw_account_details('multipleleveltrader')
    # draw_order_signals('multipleleveltrader')
