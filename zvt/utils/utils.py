# -*- coding: utf-8 -*-
import logging
import numbers
from decimal import *
from enum import Enum

import pandas as pd

from zvt.utils.time_utils import to_time_str

getcontext().prec = 16

logger = logging.getLogger(__name__)

none_values = ['不变', '--', '-', '新进']
zero_values = ['不变', '--', '-', '新进']


def first_item_to_float(the_list):
    return to_float(the_list[0])


def second_item_to_float(the_list):
    return to_float(the_list[1])


def add_func_to_value(the_map, the_func):
    for k, v in the_map.items():
        the_map[k] = (v, the_func)
    return the_map


def to_float(the_str, default=None):
    if not the_str:
        return default
    if the_str in none_values:
        return None

    if '%' in the_str:
        return pct_to_float(the_str)
    try:
        scale = 1.0
        if the_str[-2:] == '万亿':
            the_str = the_str[0:-2]
            scale = 1000000000000
        elif the_str[-1] == '亿':
            the_str = the_str[0:-1]
            scale = 100000000
        elif the_str[-1] == '万':
            the_str = the_str[0:-1]
            scale = 10000
        if not the_str:
            return default
        return float(Decimal(the_str.replace(',', '')) * Decimal(scale))
    except Exception as e:
        logger.error('the_str:{}'.format(the_str))
        logger.exception(e)
        return default


def pct_to_float(the_str, default=None):
    if the_str in none_values:
        return None

    try:
        return float(Decimal(the_str.replace('%', '')) / Decimal(100))
    except Exception as e:
        logger.exception(e)
        return default


def json_callback_param(the_str):
    json_str = the_str[the_str.index("(") + 1:the_str.index(")")].replace('null', 'None')
    return eval(json_str)


def fill_domain_from_dict(the_domain, the_dict: dict, the_map: dict = None, default_func=lambda x: x):
    """
    use field map and related func to fill properties from the dict to the domain


    :param the_domain:
    :type the_domain: DeclarativeMeta
    :param the_dict:
    :type the_dict: dict
    :param the_map:
    :type the_map: dict
    :param default_func:
    :type default_func: function
    """
    if not the_map:
        the_map = {}
        for k in the_dict:
            the_map[k] = (k, default_func)

    for k, v in the_map.items():
        if isinstance(v, tuple):
            field_in_dict = v[0]
            the_func = v[1]
        else:
            field_in_dict = v
            the_func = default_func

        the_value = the_dict.get(field_in_dict)
        if the_value is not None:
            to_value = the_value
            if to_value in none_values:
                setattr(the_domain, k, None)
            else:
                result_value = the_func(to_value)
                setattr(the_domain, k, result_value)
                exec('the_domain.{}=result_value'.format(k))


SUPPORT_ENCODINGS = ['GB2312', 'GBK', 'GB18030', 'UTF-8']


def read_csv(f, encoding, sep=None, na_values=None):
    encodings = [encoding] + SUPPORT_ENCODINGS
    for encoding in encodings:
        try:
            if sep:
                return pd.read_csv(f, sep=sep, encoding=encoding, na_values=na_values)
            else:
                return pd.read_csv(f, encoding=encoding, na_values=na_values)
        except UnicodeDecodeError as e:
            logger.warning('read_csv failed by using encoding:{}'.format(encoding), e)
            f.seek(0)
            continue
    return None


def marshal_object_for_ui(object):
    if isinstance(object, Enum):
        return object.value

    if isinstance(object, pd.Timestamp):
        return to_time_str(object)

    return object


def chrome_copy_header_to_dict(src):
    lines = src.split('\n')
    header = {}
    if lines:
        for line in lines:
            try:
                index = line.index(':')
                key = line[:index]
                value = line[index + 1:]
                if key and value:
                    header.setdefault(key.strip(), value.strip())
            except Exception:
                pass
    return header


def to_positive_number(number):
    if isinstance(number, numbers.Number):
        return abs(number)

    return 0


def multiple_number(number, factor):
    try:
        return number * factor
    except:
        return number


def add_to_map_list(the_map, key, value):
    result = []
    if key in the_map:
        result = the_map[key]
    else:
        the_map[key] = result

    if value not in result:
        result.append(value)


def iterate_with_step(data, sub_size=100):
    size = len(data)
    if size >= sub_size:
        step_count = int(size / sub_size)
        if size % sub_size:
            step_count = step_count + 1
    else:
        step_count = 1

    for step in range(step_count):
        if type(data) == pd.DataFrame or type(data) == pd.Series:
            yield data.iloc[sub_size * step:sub_size * (step + 1)]
        else:
            yield data[sub_size * step:sub_size * (step + 1)]


# the __all__ is generated
__all__ = ['first_item_to_float', 'second_item_to_float', 'add_func_to_value', 'to_float', 'pct_to_float',
           'json_callback_param', 'fill_domain_from_dict', 'read_csv', 'marshal_object_for_ui',
           'chrome_copy_header_to_dict', 'to_positive_number', 'multiple_number', 'add_to_map_list']
