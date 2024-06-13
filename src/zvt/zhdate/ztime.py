# -*- coding: utf-8 -*-
from zvt.utils.time_utils import to_pd_timestamp, current_date, count_interval
from zvt.zhdate.zhdate import ZhDate


def holiday_distance(timestamp=None, days=15):
    if not timestamp:
        the_date = current_date()
    else:
        the_date = to_pd_timestamp(timestamp)
    # 业绩预告
    month = the_date.month

    infos = [f"现在是{month}月，关注:"]
    if month == 12:
        infos.append("业绩预告期，注意排雷")

        # 元旦
        new_year = to_pd_timestamp(f"{the_date.year + 1}-01-01")
        distance = count_interval(the_date, new_year)
        if 0 < distance < days:
            infos.append(f"距离元旦还有{distance}天")
    if month in (1, 2):
        # 春节
        zh_date = ZhDate(lunar_year=the_date.year, lunar_month=1, lunar_day=1)
        spring_date = zh_date.newyear
        distance = count_interval(the_date, spring_date)
        if 0 < distance < days:
            infos.append(f"距离春节还有{distance}天")

        # 两会
        # 三月初
        lianghui = to_pd_timestamp(f"{the_date.year}-03-01")
        distance = count_interval(the_date, lianghui)
        if 0 < distance < days:
            infos.append(f"距离两会还有{distance}天")

    # 业绩发布
    if month in (3, 4):
        infos.append("业绩发布期，注意排雷")

    # 五一
    if month == 4:
        wuyi = to_pd_timestamp(f"{the_date.year}-05-01")
        distance = count_interval(the_date, wuyi)
        if 0 < distance < days:
            infos.append(f"距离五一还有{distance}天")

    if month == 9:
        # 国庆
        shiyi = to_pd_timestamp(f"{the_date.year}-10-01")
        distance = count_interval(the_date, shiyi)
        if 0 < distance < days:
            infos.append(f"距离国庆还有{distance}天")

    msg = "\n".join(infos)
    msg = msg + "\n"
    print(msg)
    return msg


if __name__ == "__main__":
    holiday_distance()
    # for month in range(1, 13):
    #     holiday_distance(f"2023-{month}-15")
    #     holiday_distance(f"2023-{month}-20")
# the __all__ is generated
__all__ = ["holiday_distance"]
