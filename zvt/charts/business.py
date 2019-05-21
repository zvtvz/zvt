# -*- coding: utf-8 -*-
from pyecharts.charts import Line

from zvt.api.account import get_account
from zvt.charts import draw_compare


def draw_account(trader_name_list):
    df_list = []
    for trader_name in trader_name_list:
        df_account = get_account(trader_name=trader_name)
        df_list.append(df_account)

    return draw_compare(df_list, chart_type=Line, columns=['all_value'], name='trader_name')


if __name__ == '__main__':
    draw_account(['fooltrader'])
