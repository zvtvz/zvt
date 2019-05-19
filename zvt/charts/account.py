# -*- coding: utf-8 -*-
from pyecharts import options as opts
from pyecharts.charts import Timeline, Pie, Line, Page

from zvt.api.account import get_account, get_position
from zvt.utils.time_utils import to_time_str


def draw_account(trader_name):
    df_account = get_account(trader_name=trader_name)
    df_position = get_position(trader_name=trader_name)

    xdata = [to_time_str(timestamp) for timestamp in df_account.index]
    ydata = df_account.loc[:, 'all_value'].values.tolist()

    line = (
        Line()
            .add_xaxis(xdata)
            .add_yaxis("市值曲线", ydata)
            .set_global_opts(
            title_opts=opts.TitleOpts(title="Grid-Line", pos_top="48%"),
            legend_opts=opts.LegendOpts(pos_top="48%"),
        )
    )

    time_line = Timeline()
    for timestamp in df_position.index:
        positions = zip(df_position.loc[timestamp, ['security_id']].values.tolist(),
                        df_position.loc[timestamp, ['value']].values.tolist())
        security_positions = [(x[0], y[0]) for x, y in positions]
        print(security_positions)
        pie = Pie().add("持仓", security_positions)
        time_line.add(pie, to_time_str(timestamp))

    page = Page()
    page.add(line, time_line)

    return page


if __name__ == '__main__':
    d = draw_account('fooltrader')
    d.render()
