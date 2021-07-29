# -*- coding: utf-8 -*-
import json
import logging
from enum import Enum
from typing import List
from typing import Union, Optional, Type

import numpy as np
import pandas as pd

from zvt.contract import IntervalLevel, AdjustType
from zvt.contract import TradableEntity
from zvt.contract.api import get_schema_by_name
from zvt.contract.data_type import Bean
from zvt.contract.drawer import Rect
from zvt.contract.factor import Accumulator
from zvt.contract.factor import Transformer
from zvt.contract.normal_data import NormalData
from zvt.domain import Stock
from zvt.factors.technical_factor import TechnicalFactor
from zvt.factors.algorithm import intersect
from zvt.utils import pd_is_not_null, to_string
from zvt.utils import to_time_str
from zvt.utils.time_utils import TIME_FORMAT_ISO8601

logger = logging.getLogger(__name__)


class Direction(Enum):
    up = 'up'
    down = 'down'

    def opposite(self):
        if self == Direction.up:
            return Direction.down
        if self == Direction.down:
            return Direction.up


class Fenxing(Bean):
    def __init__(self, state, kdata, index) -> None:
        self.state = state
        self.kdata = kdata
        self.index = index


class KState(Enum):
    # 顶分型
    bi_ding = 'bi_ding'
    # 底分型
    bi_di = 'bi_di'
    # 临时
    tmp_ding = 'tmp_ding'
    tmp_di = 'tmp_di'
    # 候选(candidate)
    can_ding = 'can_ding'
    can_di = 'can_di'


class DuanState(Enum):
    up = 'up'
    down = 'down'
    # Bardo，中阴阶段,不定，变化,易
    yi = 'yi'


def fenxing_power(left, middle, right, fenxing='tmp_ding'):
    if fenxing == 'tmp_ding':
        a = middle['high'] - middle['close']
        b = middle['high'] - left['high']
        c = middle['high'] - right['high']
        return -(a + b + c) / middle['close']
    if fenxing == 'tmp_di':
        a = abs(middle['low'] - middle['close'])
        b = abs(middle['low'] - left['low'])
        c = abs(middle['low'] - right['low'])
        return (a + b + c) / middle['close']


def a_include_b(a: pd.Series, b: pd.Series) -> bool:
    """
    kdata a includes kdata b

    :param a:
    :param b:
    :return:
    """
    return (a['high'] >= b['high']) and (a['low'] <= b['low'])


def is_including(kdata1, kdata2):
    return a_include_b(kdata1, kdata2) or a_include_b(kdata2, kdata1)


def get_direction(kdata, pre_kdata, current=Direction.up) -> Direction:
    if is_up(kdata, pre_kdata):
        return Direction.up
    if is_down(kdata, pre_kdata):
        return Direction.down

    return current


def is_up(kdata, pre_kdata):
    return kdata['high'] > pre_kdata['high']


def is_down(kdata, pre_kdata):
    return kdata['low'] < pre_kdata['low']


def handle_first_fenxing(one_df, step=11):
    if step >= len(one_df):
        logger.info(f"coult not get fenxing by step {step}, len {len(one_df)}")
        return None, None, None, None

    logger.info(f"try to get first fenxing by step {step}")

    df = one_df.iloc[:step]
    ding_kdata = df[df['high'].max() == df['high']]
    ding_index = int(ding_kdata.index[-1])

    di_kdata = df[df['low'].min() == df['low']]
    di_index = int(di_kdata.index[-1])

    # 确定第一个分型
    if abs(ding_index - di_index) >= 4:
        if ding_index > di_index:
            fenxing = 'bi_di'
            fenxing_index = di_index
            one_df.loc[di_index, 'bi_di'] = True
            # 确定第一个分型后，开始遍历的位置
            start_index = ding_index
            # 目前的笔的方向，up代表寻找 can_ding;down代表寻找can_di
            direction = Direction.up
            interval = ding_index - di_index
        else:
            fenxing = 'bi_ding'
            fenxing_index = ding_index
            one_df.loc[ding_index, 'bi_ding'] = True
            start_index = di_index
            direction = Direction.down
            interval = di_index - ding_index
        return Fenxing(state=fenxing, index=fenxing_index,
                       kdata={
                           'low': float(one_df.loc[fenxing_index]['low']),
                           'high': float(one_df.loc[fenxing_index]['high'])
                       }), start_index, direction, interval
    else:
        logger.info("need add step")
        return handle_first_fenxing(one_df, step=step + 1)


def handle_duan(fenxing_list: List[Fenxing], pre_duan_state='yi'):
    state = fenxing_list[0].state
    # 1笔区间
    bi1_start = fenxing_list[0].kdata
    bi1_end = fenxing_list[1].kdata
    # 3笔区间
    bi3_start = fenxing_list[2].kdata
    bi3_end = fenxing_list[3].kdata

    if state == 'bi_ding':
        # 向下段,下-上-下

        # 第一笔区间
        range1 = (bi1_end['low'], bi1_start['high'])
        # 第三笔区间
        range3 = (bi3_end['low'], bi3_start['high'])

        # 1,3有重叠，认为第一个段出现
        if intersect(range1, range3):
            return 'down'

    else:
        # 向上段，上-下-上

        # 第一笔区间
        range1 = (bi1_start['low'], bi1_end['high'])
        # 第三笔区间
        range3 = (bi3_start['low'], bi3_end['high'])

        # 1,3有重叠，认为第一个段出现
        if intersect(range1, range3):
            return 'up'

    return pre_duan_state


def handle_including(one_df, index, kdata, pre_index, pre_kdata, tmp_direction: Direction):
    # 改kdata
    if a_include_b(kdata, pre_kdata):
        # 长的kdata变短
        if tmp_direction == Direction.up:
            one_df.loc[index, 'low'] = pre_kdata['low']
        else:
            one_df.loc[index, 'high'] = pre_kdata['high']
    # 改pre_kdata
    elif a_include_b(pre_kdata, kdata):
        # 长的pre_kdata变短
        if tmp_direction == Direction.down:
            one_df.loc[pre_index, 'low'] = kdata['low']
        else:
            one_df.loc[pre_index, 'high'] = kdata['high']


class FactorStateEncoder(json.JSONEncoder):
    def default(self, object):
        if isinstance(object, pd.Series):
            return object.to_dict()
        elif isinstance(object, pd.Timestamp):
            return to_time_str(object, fmt=TIME_FORMAT_ISO8601)
        elif isinstance(object, Enum):
            return object.value
        elif isinstance(object, Bean):
            return object.dict()
        else:
            return super().default(object)


def decode_rect(dct):
    return Rect(x0=dct['x0'], y0=dct['y0'], x1=dct['x1'], y1=dct['y1'])


def decode_fenxing(dct):
    return Fenxing(state=dct['state'], kdata=dct['kdata'], index=dct['index'])


def get_zen_factor_schema(entity_type: str,
                          level: Union[IntervalLevel, str] = IntervalLevel.LEVEL_1DAY):
    if type(level) == str:
        level = IntervalLevel(level)

    # z factor schema rule
    # 1)name:{SecurityType.value.capitalize()}{IntervalLevel.value.upper()}ZFactor
    schema_str = '{}{}ZenFactor'.format(entity_type.capitalize(), level.value.capitalize())

    return get_schema_by_name(schema_str)


@to_string
class ZenState(Bean):
    def __init__(self, state: dict = None) -> None:
        super().__init__()

        if not state:
            state = dict()

        # 用于计算未完成段的分型
        self.fenxing_list = state.get('fenxing_list', [])
        fenxing_list = [Fenxing(item['state'], item['kdata'], item['index']) for item in self.fenxing_list]
        self.fenxing_list = fenxing_list

        # 目前的方向
        if state.get('direction'):
            self.direction = Direction(state.get('direction'))
        else:
            self.direction = None

        # 候选分型(candidate)
        self.can_fenxing = state.get('can_fenxing')
        self.can_fenxing_index = state.get('can_fenxing_index')
        # 反方向count
        self.opposite_count = state.get('opposite_count', 0)
        # 目前段的方向
        self.current_duan_state = state.get('current_duan_state', 'yi')

        # 记录用于计算中枢的段
        # list of (timestamp,value)
        self.duans = state.get('duans', [])
        self.bis = state.get('bis', [])

        # 前一个点
        self.pre_bi = state.get('pre_bi')
        self.pre_duan = state.get('pre_duan')


def handle_zhongshu(points: list, acc_df, end_index, zhongshu_col='zhongshu', zhongshu_change_col='zhongshu_change'):
    zhongshu = None
    zhongshu_change = None

    if len(points) == 4:
        x1 = points[0][0]
        x2 = points[3][0]

        if points[0][1] < points[1][1]:
            # 向下段
            range = intersect((points[0][1], points[1][1]),
                              (points[2][1], points[3][1]))
            if range:
                y1, y2 = range
                # 记录中枢
                zhongshu = Rect(x0=x1, x1=x2, y0=y1, y1=y2)
                zhongshu_change = abs(y1 - y2) / y1
                acc_df.loc[end_index, zhongshu_col] = zhongshu
                acc_df.loc[end_index, zhongshu_change_col] = zhongshu_change
                points = points[-1:]
            else:
                points = points[1:]
        else:
            # 向上段
            range = intersect((points[1][1], points[0][1]),
                              (points[3][1], points[2][1]))
            if range:
                y1, y2 = range
                # 记录中枢
                zhongshu = Rect(x0=x1, x1=x2, y0=y1, y1=y2)
                zhongshu_change = abs(y1 - y2) / y1

                acc_df.loc[end_index, zhongshu_col] = zhongshu
                acc_df.loc[end_index, zhongshu_change_col] = zhongshu_change
                points = points[-1:]
            else:
                points = points[1:]
    return points, zhongshu, zhongshu_change


class ZenAccumulator(Accumulator):
    def __init__(self, acc_window: int = 1) -> None:
        """
        算法和概念
        <实体> 某种状态的k线
        [实体] 连续实体排列

        两k线的关系有三种: 上涨，下跌，包含
        上涨: k线高点比之前高，低点比之前高
        下跌: k线低点比之前低，高点比之前低
        包含: k线高点比之前高，低点比之前低;反方向，即被包含
        处理包含关系，长的k线缩短，上涨时，低点取max(low1,low2)；下跌时，高点取min(high1,high2)

        第一个顶(底)分型: 出现连续4根下跌(上涨)k线
        之后开始寻找 候选底(顶)分型，寻找的过程中有以下状态

        <临时顶>: 中间k线比两边的高点高,是一条特定的k线
        <临时底>: 中间k线比两边的高点高,是一条特定的k线

        <候选顶分型>: 连续的<临时顶>取最大
        <候选底分型>:  连续的<临时底>取最小
        任何时刻只能有一个候选，其之前是一个确定的分型

        <上升k线>:
        <下降k线>:
        <连接k线>: 分型之间的k线都可以认为是连接k线，以上为演化过程的中间态
        distance(<候选顶分型>, <连接k线>)>=4 则 <候选顶分型> 变成顶分型
        distance(<候选底分型>, <连接k线>)>=4 则 <候选底分型> 变成底分型

        <顶分型><连接k线><候选底分型>
        <底分型><连接k线><候选顶分型>
        """
        super().__init__(acc_window)

    def acc_one(self, entity_id, df: pd.DataFrame, acc_df: pd.DataFrame, state: dict) -> (pd.DataFrame, dict):
        self.logger.info(f'acc_one:{entity_id}')
        if pd_is_not_null(acc_df):
            df = df[df.index > acc_df.index[-1]]
            if pd_is_not_null(df):
                self.logger.info(f'compute from {df.iloc[0]["timestamp"]}')
                # 遍历的开始位置
                start_index = len(acc_df)

                acc_df = pd.concat([acc_df, df])

                zen_state = ZenState(state)

                acc_df = acc_df.reset_index(drop=True)
                current_interval = acc_df.iloc[start_index - 1]['current_interval']
            else:
                self.logger.info('no need to compute')
                return acc_df, state
        else:
            acc_df = df
            # 笔的底
            acc_df['bi_di'] = False
            # 笔的顶
            acc_df['bi_ding'] = False
            # 记录笔顶/底分型的值，bi_di取low,bi_ding取high,其他为None,绘图时取有值的连线即为 笔
            acc_df['bi_value'] = np.NAN
            # 笔的变化
            acc_df['bi_change'] = np.NAN
            # 笔的斜率
            acc_df['bi_slope'] = np.NAN
            # 持续的周期
            acc_df['bi_interval'] = np.NAN

            # 记录临时分型，不变
            acc_df['tmp_ding'] = False
            acc_df['tmp_di'] = False
            # 分型的力度
            acc_df['fenxing_power'] = np.NAN

            # 目前分型确定的方向
            acc_df['current_direction'] = None
            acc_df['current_change'] = np.NAN
            acc_df['current_interval'] = np.NAN
            acc_df['current_slope'] = np.NAN
            # 最近的一个笔中枢
            # acc_df['current_zhongshu'] = np.NAN
            acc_df['current_zhongshu_change'] = np.NAN
            acc_df['current_zhongshu_y0'] = np.NAN
            acc_df['current_zhongshu_y1'] = np.NAN
            # 目前走势的临时方向 其跟direction的的关系 确定了下一个分型
            acc_df['tmp_direction'] = None
            acc_df['opposite_change'] = np.NAN
            acc_df['opposite_interval'] = np.NAN
            acc_df['opposite_slope'] = np.NAN

            acc_df['duan_state'] = 'yi'

            # 段的底
            acc_df['duan_di'] = False
            # 段的顶
            acc_df['duan_ding'] = False
            # 记录段顶/底的值，为duan_di时取low,为duan_ding时取high,其他为None,绘图时取有值的连线即为 段
            acc_df['duan_value'] = np.NAN
            # 段的变化
            acc_df['duan_change'] = np.NAN
            # 段的斜率
            acc_df['duan_slope'] = np.NAN
            # 持续的周期
            acc_df['duan_interval'] = np.NAN

            # 记录在确定中枢的最后一个段的终点x1，值为Rect(x0,y0,x1,y1)
            acc_df['zhongshu'] = np.NAN
            acc_df['zhongshu_change'] = np.NAN

            acc_df['bi_zhongshu'] = np.NAN
            acc_df['bi_zhongshu_change'] = np.NAN

            acc_df = acc_df.reset_index(drop=True)

            zen_state = ZenState(dict(fenxing_list=[], direction=None, can_fenxing=None, can_fenxing_index=None,
                                      opposite_count=0, current_duan_state='yi', duans=[], pre_bi=None, pre_duan=None))

            zen_state.fenxing_list: List[Fenxing] = []

            # 取前11条k线，至多出现一个顶分型+底分型
            # 注:只是一种方便的确定第一个分型的办法，有了第一个分型，后面的处理就比较统一
            # start_index 为遍历开始的位置
            # direction为一个确定分型后的方向，即顶分型后为:down，底分型后为:up
            fenxing, start_index, direction, current_interval = handle_first_fenxing(acc_df, step=11)
            if not fenxing:
                return None, None

            zen_state.fenxing_list.append(fenxing)
            zen_state.direction = direction

            # list of (timestamp,value)
            zen_state.duans = []
            zen_state.bis = []

        pre_kdata = acc_df.iloc[start_index - 1]
        pre_index = start_index - 1

        tmp_direction = zen_state.direction

        current_zhongshu = None
        current_zhongshu_change = None
        for index, kdata in acc_df.iloc[start_index:].iterrows():
            # print(f'timestamp: {kdata.timestamp}')
            # 临时方向
            tmp_direction = get_direction(kdata, pre_kdata, current=tmp_direction)

            # current states
            current_interval = current_interval + 1
            if zen_state.direction == Direction.up:
                pre_value = acc_df.loc[zen_state.fenxing_list[0].index, 'low']
                current_value = kdata['high']
            else:
                pre_value = acc_df.loc[zen_state.fenxing_list[0].index, 'high']
                current_value = kdata['low']
            acc_df.loc[index, 'current_direction'] = zen_state.direction.value
            acc_df.loc[index, 'current_interval'] = current_interval
            change = (current_value - pre_value) / pre_value
            acc_df.loc[index, 'current_change'] = change
            acc_df.loc[index, 'current_slope'] = change / current_interval
            if current_zhongshu:
                # acc_df.loc[index, 'current_zhongshu'] = current_zhongshu
                acc_df.loc[index, 'current_zhongshu_y0'] = current_zhongshu.y0
                acc_df.loc[index, 'current_zhongshu_y1'] = current_zhongshu.y1
                acc_df.loc[index, 'current_zhongshu_change'] = current_zhongshu_change
            else:
                # acc_df.loc[index, 'current_zhongshu'] = acc_df.loc[index - 1, 'current_zhongshu']
                acc_df.loc[index, 'current_zhongshu_y0'] = acc_df.loc[index - 1, 'current_zhongshu_y0']
                acc_df.loc[index, 'current_zhongshu_y1'] = acc_df.loc[index - 1, 'current_zhongshu_y1']
                acc_df.loc[index, 'current_zhongshu_change'] = acc_df.loc[index - 1, 'current_zhongshu_change']

            # 处理包含关系
            handle_including(one_df=acc_df, index=index, kdata=kdata, pre_index=pre_index, pre_kdata=pre_kdata,
                             tmp_direction=tmp_direction)

            # 根据方向，寻找对应的分型 和 段
            if zen_state.direction == Direction.up:
                tmp_fenxing_col = 'tmp_ding'
                fenxing_col = 'bi_ding'
            else:
                tmp_fenxing_col = 'tmp_di'
                fenxing_col = 'bi_di'

            # 方向一致，延续中
            if tmp_direction == zen_state.direction:
                zen_state.opposite_count = 0
            # 反向，寻找反 分型
            else:
                zen_state.opposite_count = zen_state.opposite_count + 1

                # opposite states
                current_interval = zen_state.opposite_count
                if tmp_direction == Direction.up:
                    pre_value = acc_df.loc[index - zen_state.opposite_count, 'low']
                    current_value = kdata['high']
                else:
                    pre_value = acc_df.loc[index - zen_state.opposite_count, 'high']
                    current_value = kdata['low']
                acc_df.loc[index, 'tmp_direction'] = tmp_direction.value
                acc_df.loc[index, 'opposite_interval'] = current_interval
                change = (current_value - pre_value) / pre_value
                acc_df.loc[index, 'opposite_change'] = change
                acc_df.loc[index, 'opposite_slope'] = change / current_interval

                # 第一次反向
                if zen_state.opposite_count == 1:
                    acc_df.loc[pre_index, tmp_fenxing_col] = True
                    acc_df.loc[pre_index, 'fenxing_power'] = fenxing_power(acc_df.loc[pre_index - 1], pre_kdata, kdata,
                                                                           fenxing=tmp_fenxing_col)

                    if zen_state.can_fenxing is not None:
                        # 候选底分型
                        if tmp_direction == Direction.up:
                            # 取小的
                            if pre_kdata['low'] <= zen_state.can_fenxing['low']:
                                zen_state.can_fenxing = pre_kdata[['low', 'high']]
                                zen_state.can_fenxing_index = pre_index

                        # 候选顶分型
                        else:
                            # 取大的
                            if pre_kdata['high'] >= zen_state.can_fenxing['high']:
                                zen_state.can_fenxing = pre_kdata[['low', 'high']]
                                zen_state.can_fenxing_index = pre_index
                    else:
                        zen_state.can_fenxing = pre_kdata[['low', 'high']]
                        zen_state.can_fenxing_index = pre_index

                # 分型确立
                if zen_state.can_fenxing is not None:
                    if zen_state.opposite_count >= 4 or (index - zen_state.can_fenxing_index >= 8):
                        acc_df.loc[zen_state.can_fenxing_index, fenxing_col] = True

                        # 记录笔的值
                        if fenxing_col == 'bi_ding':
                            bi_value = acc_df.loc[zen_state.can_fenxing_index, 'high']
                        else:
                            bi_value = acc_df.loc[zen_state.can_fenxing_index, 'low']
                        acc_df.loc[zen_state.can_fenxing_index, 'bi_value'] = bi_value

                        # 计算笔斜率
                        if zen_state.pre_bi:
                            change = ((bi_value - zen_state.pre_bi[1]) / zen_state.pre_bi[1])
                            interval = (zen_state.can_fenxing_index - zen_state.pre_bi[0])
                            bi_slope = change / interval
                            acc_df.loc[zen_state.can_fenxing_index, 'bi_change'] = change
                            acc_df.loc[zen_state.can_fenxing_index, 'bi_slope'] = bi_slope
                            acc_df.loc[zen_state.can_fenxing_index, 'bi_interval'] = interval

                        # 记录用于计算笔中枢的笔
                        zen_state.bis.append((acc_df.loc[zen_state.can_fenxing_index, 'timestamp'], bi_value))

                        # 计算笔中枢
                        zen_state.bis, current_zhongshu, current_zhongshu_change = handle_zhongshu(points=zen_state.bis,
                                                                                                   acc_df=acc_df,
                                                                                                   end_index=zen_state.can_fenxing_index,
                                                                                                   zhongshu_col='bi_zhongshu',
                                                                                                   zhongshu_change_col='bi_zhongshu_change')

                        zen_state.pre_bi = (zen_state.can_fenxing_index, bi_value)

                        zen_state.opposite_count = 0
                        zen_state.direction = zen_state.direction.opposite()
                        zen_state.can_fenxing = None

                        # 确定第一个段
                        if zen_state.fenxing_list != None:
                            zen_state.fenxing_list.append(
                                Fenxing(state=fenxing_col,
                                        kdata={
                                            'low': float(acc_df.loc[zen_state.can_fenxing_index]['low']),
                                            'high': float(acc_df.loc[zen_state.can_fenxing_index]['high'])
                                        },
                                        index=zen_state.can_fenxing_index))

                            if len(zen_state.fenxing_list) == 4:
                                duan_state = handle_duan(fenxing_list=zen_state.fenxing_list,
                                                         pre_duan_state=zen_state.current_duan_state)

                                change = duan_state != zen_state.current_duan_state

                                if change:
                                    zen_state.current_duan_state = duan_state

                                    # 确定状态
                                    acc_df.loc[zen_state.fenxing_list[0].index:zen_state.fenxing_list[-1].index,
                                    'duan_state'] = zen_state.current_duan_state

                                    duan_index = zen_state.fenxing_list[0].index
                                    if zen_state.current_duan_state == 'up':
                                        acc_df.loc[duan_index, 'duan_di'] = True
                                        duan_value = acc_df.loc[duan_index, 'low']
                                    else:
                                        duan_index = zen_state.fenxing_list[0].index
                                        acc_df.loc[duan_index, 'duan_ding'] = True
                                        duan_value = acc_df.loc[duan_index, 'high']
                                    # 记录段的值
                                    acc_df.loc[duan_index, 'duan_value'] = duan_value

                                    # 计算段斜率
                                    if zen_state.pre_duan:
                                        change = ((duan_value - zen_state.pre_duan[1]) / zen_state.pre_duan[1])
                                        interval = (duan_index - zen_state.pre_duan[0])
                                        duan_slope = change / interval
                                        acc_df.loc[duan_index, 'duan_change'] = change
                                        acc_df.loc[duan_index, 'duan_slope'] = duan_slope
                                        acc_df.loc[duan_index, 'duan_interval'] = interval

                                    zen_state.pre_duan = (duan_index, duan_value)

                                    # 记录用于计算中枢的段
                                    zen_state.duans.append((acc_df.loc[duan_index, 'timestamp'], duan_value))

                                    # 计算中枢
                                    zen_state.duans, _, _ = handle_zhongshu(points=zen_state.duans, acc_df=acc_df,
                                                                            end_index=duan_index,
                                                                            zhongshu_col='zhongshu',
                                                                            zhongshu_change_col='zhongshu_change')

                                    # 只留最后一个
                                    zen_state.fenxing_list = zen_state.fenxing_list[-1:]
                                else:
                                    # 保持之前的状态并踢出候选
                                    acc_df.loc[
                                        zen_state.fenxing_list[0].index, 'duan_state'] = zen_state.current_duan_state
                                    zen_state.fenxing_list = zen_state.fenxing_list[1:]

            pre_kdata = kdata
            pre_index = index

        acc_df = acc_df.set_index('timestamp', drop=False)
        return acc_df, zen_state


class ZenFactor(TechnicalFactor):
    accumulator = ZenAccumulator()

    def drawer_main_data(self) -> Optional[NormalData]:
        return super().drawer_main_data()

    def __init__(self,
                 entity_schema: Type[TradableEntity] = Stock,
                 provider: str = None,
                 entity_provider: str = None,
                 entity_ids: List[str] = None,
                 exchanges: List[str] = None,
                 codes: List[str] = None,
                 start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None,
                 columns: List = None,
                 filters: List = None,
                 order: object = None,
                 limit: int = None,
                 level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY,
                 category_field: str = 'entity_id',
                 time_field: str = 'timestamp',
                 computing_window: int = None,
                 keep_all_timestamp: bool = False,
                 fill_method: str = 'ffill',
                 effective_number: int = None,
                 transformer: Transformer = None,
                 accumulator: Accumulator = None,
                 need_persist: bool = False,
                 only_compute_factor: bool = False,
                 factor_name: str = None,
                 clear_state: bool = False,
                 only_load_factor: bool = False,
                 adjust_type: Union[AdjustType, str] = None) -> None:
        self.factor_schema = get_zen_factor_schema(entity_type=entity_schema.__name__, level=level)
        super().__init__(entity_schema, provider, entity_provider, entity_ids, exchanges, codes, start_timestamp,
                         end_timestamp, columns, filters, order, limit, level, category_field, time_field,
                         computing_window, keep_all_timestamp, fill_method, effective_number, transformer, accumulator,
                         need_persist, only_compute_factor, factor_name, clear_state, only_load_factor, adjust_type)

    def factor_col_map_object_hook(self) -> dict:
        return {
            'zhongshu': decode_rect,
            'current_zhongshu': decode_rect,
            'bi_zhongshu': decode_rect
        }

    def factor_encoder(self):
        return FactorStateEncoder

    def drawer_factor_df_list(self) -> Optional[List[pd.DataFrame]]:
        bi_value = self.factor_df[['bi_value']].dropna()
        duan_value = self.factor_df[['duan_value']].dropna()
        return [bi_value, duan_value]

    def drawer_rects(self) -> List[Rect]:
        df1 = self.factor_df[['bi_zhongshu']].dropna()
        return df1['bi_zhongshu'].tolist()

    def drawer_sub_df_list(self) -> Optional[List[pd.DataFrame]]:
        # bi_slope = self.factor_df[['bi_slope']].dropna()
        # duan_slope = self.factor_df[['duan_slope']].dropna()
        # power = self.factor_df[['fenxing_power']].dropna()
        # zhongshu_change = self.factor_df[['zhongshu_change']].dropna()
        # return [bi_slope, duan_slope, power, zhongshu_change]
        change1 = self.factor_df[['current_change']].dropna()
        change2 = self.factor_df[['opposite_change']].dropna()
        return [change1, change2]

    def drawer_annotation_df(self) -> Optional[pd.DataFrame]:
        if pd_is_not_null(self.result_df):
            annotation_df = self.result_df.copy()
            annotation_df = annotation_df[annotation_df['score']]
            annotation_df['value'] = self.factor_df.loc[annotation_df.index]['close']
            annotation_df['flag'] = annotation_df['score'].apply(lambda x: order_type_flag(x))
            return annotation_df


def order_type_flag(order_type):
    if order_type:
        return 'B'


class TrendingFactor(ZenFactor):
    def __init__(self,
                 entity_schema: Type[TradableEntity] = Stock,
                 provider: str = None,
                 entity_provider: str = None,
                 entity_ids: List[str] = None,
                 exchanges: List[str] = None,
                 codes: List[str] = None,
                 start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None,
                 columns: List = None,
                 filters: List = None,
                 order: object = None,
                 limit: int = None,
                 level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY,
                 category_field: str = 'entity_id',
                 time_field: str = 'timestamp',
                 computing_window: int = None,
                 keep_all_timestamp: bool = False,
                 fill_method: str = 'ffill',
                 effective_number: int = None,
                 transformer: Transformer = None,
                 accumulator: Accumulator = None,
                 need_persist: bool = False,
                 only_compute_factor: bool = False,
                 factor_name: str = None,
                 clear_state: bool = False,
                 only_load_factor: bool = True,
                 adjust_type: Union[AdjustType, str] = None) -> None:
        super().__init__(entity_schema, provider, entity_provider, entity_ids, exchanges, codes, start_timestamp,
                         end_timestamp, columns, filters, order, limit, level, category_field, time_field,
                         computing_window, keep_all_timestamp, fill_method, effective_number, transformer, accumulator,
                         need_persist, only_compute_factor, factor_name, clear_state, only_load_factor, adjust_type)

    def compute_result(self):
        super().compute_result()
        # 窄幅震荡
        s1 = self.factor_df['current_zhongshu_change'] <= 0.15
        s2 = self.factor_df['close'] > self.factor_df['current_zhongshu_y1'] * 1.1
        s = s1 & s2

        self.result_df = s.to_frame(name='score')

    def drawer_factor_df_list(self) -> Optional[List[pd.DataFrame]]:
        zhongshu_y0 = self.factor_df[['current_zhongshu_y0']].dropna()
        zhongshu_y1 = self.factor_df[['current_zhongshu_y1']].dropna()
        return [zhongshu_y0, zhongshu_y1]

    def drawer_main_df(self) -> Optional[pd.DataFrame]:
        return self.factor_df


class ShakingFactor(ZenFactor):
    # 震荡区间
    shaking_range = 0.15

    def __init__(self,
                 entity_schema: Type[TradableEntity] = Stock,
                 provider: str = None,
                 entity_provider: str = None,
                 entity_ids: List[str] = None,
                 exchanges: List[str] = None,
                 codes: List[str] = None,
                 start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None,
                 columns: List = None,
                 filters: List = None,
                 order: object = None,
                 limit: int = None,
                 level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY,
                 category_field: str = 'entity_id',
                 time_field: str = 'timestamp',
                 computing_window: int = None,
                 keep_all_timestamp: bool = False,
                 fill_method: str = 'ffill',
                 effective_number: int = None,
                 transformer: Transformer = None,
                 accumulator: Accumulator = None,
                 need_persist: bool = False,
                 only_compute_factor: bool = False,
                 factor_name: str = None,
                 clear_state: bool = False,
                 only_load_factor: bool = True,
                 adjust_type: Union[AdjustType, str] = None) -> None:
        super().__init__(entity_schema, provider, entity_provider, entity_ids, exchanges, codes, start_timestamp,
                         end_timestamp, columns, filters, order, limit, level, category_field, time_field,
                         computing_window, keep_all_timestamp, fill_method, effective_number, transformer, accumulator,
                         need_persist, only_compute_factor, factor_name, clear_state, only_load_factor, adjust_type)

    def compute_result(self):
        super().compute_result()
        s1 = self.factor_df['current_zhongshu_change'] >= self.shaking_range
        # 震荡低点
        middle = (self.factor_df['current_zhongshu_y0'] + self.factor_df['current_zhongshu_y1']) / 2
        s2 = self.factor_df['close'] <= middle
        s3 = self.factor_df['close'] >= 0.9 * self.factor_df['current_zhongshu_y0']
        s = s1 & s2 & s3

        self.result_df = s.to_frame(name='score')

    def drawer_annotation_df(self) -> Optional[pd.DataFrame]:
        if pd_is_not_null(self.result_df):
            annotation_df = self.result_df.copy()
            annotation_df = annotation_df[annotation_df['score']]
            annotation_df['value'] = self.factor_df.loc[annotation_df.index]['close']
            annotation_df['flag'] = annotation_df['score'].apply(lambda x: order_type_flag(x))
            return annotation_df

    def drawer_main_df(self) -> Optional[pd.DataFrame]:
        return self.factor_df

    def drawer_factor_df_list(self) -> Optional[List[pd.DataFrame]]:
        zhongshu_y0 = self.factor_df[['current_zhongshu_y0']].dropna()
        zhongshu_y1 = self.factor_df[['current_zhongshu_y1']].dropna()
        return [zhongshu_y0, zhongshu_y1]

class ShowFactor(ZenFactor):

    def __init__(self,
                 entity_schema: Type[TradableEntity] = Stock,
                 provider: str = None,
                 entity_provider: str = None,
                 entity_ids: List[str] = None,
                 exchanges: List[str] = None,
                 codes: List[str] = None,
                 start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None,
                 columns: List = None,
                 filters: List = None,
                 order: object = None,
                 limit: int = None,
                 level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY,
                 category_field: str = 'entity_id',
                 time_field: str = 'timestamp',
                 computing_window: int = None,
                 keep_all_timestamp: bool = False,
                 fill_method: str = 'ffill',
                 effective_number: int = None,
                 transformer: Transformer = None,
                 accumulator: Accumulator = None,
                 need_persist: bool = False,
                 only_compute_factor: bool = False,
                 factor_name: str = None,
                 clear_state: bool = False,
                 only_load_factor: bool = True,
                 adjust_type: Union[AdjustType, str] = None) -> None:
        super().__init__(entity_schema, provider, entity_provider, entity_ids, exchanges, codes, start_timestamp,
                         end_timestamp, columns, filters, order, limit, level, category_field, time_field,
                         computing_window, keep_all_timestamp, fill_method, effective_number, transformer, accumulator,
                         need_persist, only_compute_factor, factor_name, clear_state, only_load_factor, adjust_type)

    def drawer_sub_df_list(self) -> Optional[List[pd.DataFrame]]:
        change1 = self.factor_df[['current_slope']].dropna()
        change2 = self.factor_df[['opposite_slope']].dropna()
        return [change1, change2]


if __name__ == '__main__':
    from zvt.factors.zen.domain import Stock1dZenFactor
    from zvt.domain import Stock1dHfqKdata

    Stock1dHfqKdata.record_data(codes=['000338','601318'])
    zen = ZenFactor(level='1d', need_persist=True, clear_state=False, codes=['000338','601318'])
    zen.draw(show=True)

# the __all__ is generated
__all__ = ['Direction', 'Fenxing', 'KState', 'DuanState', 'fenxing_power', 'a_include_b', 'is_including', 'get_direction', 'is_up', 'is_down', 'handle_first_fenxing', 'handle_duan', 'handle_including', 'FactorStateEncoder', 'decode_rect', 'decode_fenxing',
           'get_zen_factor_schema', 'ZenState', 'handle_zhongshu', 'ZenAccumulator', 'ZenFactor', 'order_type_flag', 'TrendingFactor', 'ShakingFactor']