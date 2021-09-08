# -*- coding: utf-8 -*-
import logging

import pandas as pd
import requests

from zvt.domain import IndexCategory
from zvt.recorders.consts import DEFAULT_HEADER
from zvt.utils import to_pd_timestamp

logger = logging.getLogger(__name__)

original_page_url = 'http://www.csindex.com.cn/zh-CN/indices/index?class_2=2&class_17=17&class_10=10&class_7=7&is_custom_0=1'

url = 'http://www.csindex.com.cn/zh-CN/indices/index?page=1&page_size=1000&by=asc&order=%E5%8F%91%E5%B8%83%E6%97%B6%E9%97%B4&data_type=json' \
      '&{}&class_7=7&class_10=10&{}&is_custom_0=1'

# 中证指数 抓取 风格指数 行业指数 规模指数
csi_category_map_url = {
    IndexCategory.style: url.format('class_1=1', 'class_19=19'),
    IndexCategory.industry: url.format('class_1=1', 'class_18=18'),
    IndexCategory.scope: url.format('class_1=1', 'class_17=17'),
}

# 上证指数 只取规模指数
sh_category_map_url = {
    IndexCategory.scope: url.format('class_2=2', 'class_17=17')
}


def _get_resp_data(resp: requests.Response):
    resp.raise_for_status()
    return resp.json()['list']


def get_cs_index(index_type='sh', category=IndexCategory.scope):
    if index_type == 'csi':
        category_map_url = csi_category_map_url
    elif index_type == 'sh':
        category_map_url = sh_category_map_url
    else:
        logger.warning(f'not support index type: {index_type}')
        assert False

    url = category_map_url.get(category)

    requests_session = requests.Session()

    resp = requests_session.get(url, headers=DEFAULT_HEADER)

    results = _get_resp_data(resp)
    the_list = []

    logger.info(f'category: {category} ')
    logger.info(f'results: {results} ')
    for i, result in enumerate(results):
        logger.info(f'to {i}/{len(results)}')
        code = result['index_code']
        name = result['indx_sname']
        entity_id = f'index_sh_{code}'
        index_item = {
            'id': entity_id,
            'entity_id': entity_id,
            'timestamp': to_pd_timestamp(result['base_date']),
            'entity_type': 'index',
            'exchange': 'sh',
            'code': code,
            'name': name,
            'category': category.value,
            'list_date': to_pd_timestamp(result['online_date']),
            'base_point': result['base_point'],
            'publisher': 'csindex'
        }
        logger.info(index_item)
        the_list.append(index_item)
    if the_list:
        return pd.DataFrame.from_records(the_list)


if __name__ == '__main__':
    df = get_cs_index()
    print(df)
# the __all__ is generated
__all__ = ['get_cs_index']