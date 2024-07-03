# -*- coding: utf-8 -*-

import requests

from zvt.utils.time_utils import now_timestamp, to_time_str, TIME_FORMAT_DAY1
from zvt.utils.utils import chrome_copy_header_to_dict

_JKQA_HEADER = chrome_copy_header_to_dict(
    """
Accept: application/json, text/plain, */*
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9,en;q=0.8
Connection: keep-alive
Host: data.10jqka.com.cn
Referer: https://data.10jqka.com.cn/datacenterph/limitup/limtupInfo.html?fontzoom=no&client_userid=cA2fp&share_hxapp=gsc&share_action=webpage_share.1&back_source=wxhy
sec-ch-ua: "Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"
sec-ch-ua-mobile: ?1
sec-ch-ua-platform: "Android"
Sec-Fetch-Dest: empty
Sec-Fetch-Mode: cors
Sec-Fetch-Site: same-origin
User-Agent: Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Mobile Safari/537.36
"""
)


def get_continuous_limit_up(date: str):
    date_str = to_time_str(the_time=date, fmt=TIME_FORMAT_DAY1)
    url = f"https://data.10jqka.com.cn/dataapi/limit_up/continuous_limit_up?filter=HS,GEM2STAR&date={date_str}"
    resp = requests.get(url, headers=_JKQA_HEADER)
    if resp.status_code == 200:
        json_result = resp.json()
        if json_result:
            return json_result["data"]
    raise RuntimeError(f"request jkqa data code: {resp.status_code}, error: {resp.text}")


def get_limit_stats(date: str):
    date_str = to_time_str(the_time=date, fmt=TIME_FORMAT_DAY1)
    url = f"https://data.10jqka.com.cn/dataapi/limit_up/limit_up_pool?page=1&limit=1&field=199112,10,9001,330323,330324,330325,9002,330329,133971,133970,1968584,3475914,9003,9004&filter=HS,GEM2STAR&date={date_str}&order_field=330324&order_type=0&_={now_timestamp()}"
    resp = requests.get(url, headers=_JKQA_HEADER)
    if resp.status_code == 200:
        json_result = resp.json()
        if json_result:
            return {
                "limit_up_count": json_result["data"]["limit_up_count"],
                "limit_down_count": json_result["data"]["limit_down_count"],
            }
    raise RuntimeError(f"request jkqa data code: {resp.status_code}, error: {resp.text}")


def get_limit_up(date: str):
    date_str = to_time_str(the_time=date, fmt=TIME_FORMAT_DAY1)
    url = f"https://data.10jqka.com.cn/dataapi/limit_up/limit_up_pool?field=199112,10,9001,330323,330324,330325,9002,330329,133971,133970,1968584,3475914,9003,9004&filter=HS,GEM2STAR&order_field=330324&order_type=0&date={date_str}"
    return get_jkqa_data(url=url)


def get_limit_down(date: str):
    date_str = to_time_str(the_time=date, fmt=TIME_FORMAT_DAY1)
    url = f"https://data.10jqka.com.cn/dataapi/limit_up/lower_limit_pool?page=1&limit=15&field=199112,10,9001,330323,330324,330325,9002,330329,133971,133970,1968584,3475914,9003,9004&filter=HS,GEM2STAR&order_field=330324&order_type=0&date={date_str}"
    return get_jkqa_data(url=url)


def get_jkqa_data(url, pn=1, ps=200, fetch_all=True, headers=_JKQA_HEADER):
    url = url + f"&page={pn}&limit={ps}&_={now_timestamp()}"
    print(url)
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        json_result = resp.json()
        if json_result and json_result["data"]:
            data: list = json_result["data"]["info"]
            if fetch_all:
                if pn < json_result["data"]["page"]["page"]:
                    next_data = get_jkqa_data(
                        pn=pn + 1,
                        ps=ps,
                        fetch_all=fetch_all,
                    )
                    if next_data:
                        data = data + next_data
                        return data
                    else:
                        return data
                else:
                    return data
            else:
                return data
        return None
    raise RuntimeError(f"request jkqa data code: {resp.status_code}, error: {resp.text}")


if __name__ == "__main__":
    # result = get_limit_up(date="20210716")
    # print(result)
    # result = get_limit_stats(date="20210716")
    # print(result)
    # result = get_limit_down(date="20210716")
    # print(result)
    result = get_continuous_limit_up(date="20210716")
    print(result)


# the __all__ is generated
__all__ = ["get_continuous_limit_up", "get_limit_stats", "get_limit_up", "get_limit_down", "get_jkqa_data"]
