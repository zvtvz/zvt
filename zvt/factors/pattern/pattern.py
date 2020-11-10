# -*- coding: utf-8 -*-
from enum import Enum
from typing import List, Union

import pandas as pd

from zvt.api import get_kdata
from zvt.contract import EntityMixin
from zvt.contract import IntervalLevel, AdjustType
from zvt.domain import Stock
from zvt.factors import Transformer, TechnicalFactor, Accumulator
from zvt.factors.algorithm import intersect
from zvt.utils import pd_is_not_null


class Direction(Enum):
    up = 'up'
    down = 'down'

    def opposite(self):
        if self == Direction.up:
            return Direction.down
        if self == Direction.down:
            return Direction.up


class Fenxing(object):
    def __init__(self, state, kdata, index) -> None:
        super().__init__()
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
    print(f"gen first fenxing by step {step}")
    df = one_df.iloc[:step]
    ding_kdata = df[df['high'].max() == df['high']]
    ding_index = ding_kdata.index[-1]

    di_kdata = df[df['low'].min() == df['low']]
    di_index = di_kdata.index[-1]

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
        else:
            fenxing = 'bi_ding'
            fenxing_index = ding_index
            one_df.loc[ding_index, 'bi_ding'] = True
            start_index = di_index
            direction = Direction.down
        return (Fenxing(state=fenxing, index=fenxing_index, kdata=one_df.loc[fenxing_index]), start_index, direction)
    else:
        print("need add step")
        handle_first_fenxing(one_df, step=step + 1)


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


class ZenTransformer(Transformer):
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

    def __init__(self) -> None:
        super().__init__()
        self.entity_duan_intervals = {}

    def transform_one(self, entity_id, df: pd.DataFrame) -> pd.DataFrame:
        # 记录段区间
        if entity_id not in self.entity_duan_intervals:
            self.entity_duan_intervals[entity_id] = []

        df = df.reset_index(drop=False)
        # 笔的底
        df['bi_di'] = False
        # 笔的顶
        df['bi_ding'] = False

        # 记录临时分型，不变
        df['tmp_ding'] = False
        df['tmp_di'] = False

        df['duan_state'] = 'yi'

        # 段的底
        df['duan_di'] = False
        # 段的顶
        df['duan_ding'] = False

        fenxing_list: List[Fenxing] = []

        # 取前11条k线，至多出现一个顶分型+底分型
        # 注:只是一种方便的确定第一个分型的办法，有了第一个分型，后面的处理就比较统一
        # start_index 为遍历开始的位置
        # direction为一个确定分型后的方向，即顶分型后为:down，底分型后为:up
        fenxing, start_index, direction = handle_first_fenxing(df, step=11)
        fenxing_list.append(fenxing)
        # 临时方向
        tmp_direction = direction
        # 候选分型(candidate)
        can_fenxing = None
        can_fenxing_index = None
        # 正向count
        count = 0
        # 反方向count
        opposite_count = 0
        # 目前段的方向
        current_duan_state = 'yi'

        pre_kdata = df.iloc[start_index - 1]
        pre_index = start_index - 1
        for index, kdata in df.iloc[start_index:].iterrows():
            print(f'timestamp: {kdata.timestamp}')
            # 临时方向
            tmp_direction = get_direction(kdata, pre_kdata, current=tmp_direction)

            # 处理包含关系
            handle_including(one_df=df, index=index, kdata=kdata, pre_index=pre_index, pre_kdata=pre_kdata,
                             tmp_direction=tmp_direction)

            # 根据方向，寻找对应的分型 和 段
            if direction == Direction.up:
                tmp_fenxing_col = 'tmp_ding'
                fenxing_col = 'bi_ding'
            else:
                tmp_fenxing_col = 'tmp_di'
                fenxing_col = 'bi_di'

            # 方向一致，延续中
            if tmp_direction == direction:
                opposite_count = 0
            # 反向，寻找反 分型
            else:
                opposite_count = opposite_count + 1
                # 第一次反向
                if opposite_count == 1:
                    df.loc[pre_index, tmp_fenxing_col] = True

                    if pd_is_not_null(can_fenxing):
                        # 候选底分型
                        if tmp_direction == Direction.up:
                            # 取小的
                            if pre_kdata['low'] <= can_fenxing['low']:
                                can_fenxing = pre_kdata
                                can_fenxing_index = pre_index

                        # 候选顶分型
                        else:
                            # 取大的
                            if pre_kdata['high'] >= can_fenxing['high']:
                                can_fenxing = pre_kdata
                                can_fenxing_index = pre_index
                    else:
                        can_fenxing = pre_kdata
                        can_fenxing_index = pre_index

                # 分型确立
                if pd_is_not_null(can_fenxing):
                    if opposite_count >= 4 or (index - can_fenxing_index >= 8):
                        df.loc[can_fenxing_index, fenxing_col] = True
                        opposite_count = 0
                        direction = direction.opposite()
                        can_fenxing = None

                        # 确定第一个段
                        if fenxing_list != None:
                            fenxing_list.append(Fenxing(state=fenxing_col, kdata=df.loc[can_fenxing_index],
                                                        index=can_fenxing_index))

                            if len(fenxing_list) == 4:
                                duan_state = handle_duan(fenxing_list=fenxing_list,
                                                         pre_duan_state=current_duan_state)

                                change = duan_state != current_duan_state

                                if change:
                                    current_duan_state = duan_state

                                    # 确定状态
                                    df.loc[fenxing_list[0].index:fenxing_list[-1].index,
                                    'duan_state'] = current_duan_state

                                    if current_duan_state == 'up':
                                        df.loc[fenxing_list[0].index, 'duan_di'] = True
                                    else:
                                        df.loc[fenxing_list[0].index, 'duan_ding'] = True
                                    # 只留最后一个
                                    fenxing_list = fenxing_list[-1:]
                                else:
                                    # 保持之前的状态并踢出候选
                                    df.loc[fenxing_list[0].index, 'duan_state'] = current_duan_state
                                    fenxing_list = fenxing_list[1:]

            pre_kdata = kdata
            pre_index = index

        return df


class ZenFactor(TechnicalFactor):

    def __init__(self, entity_schema: EntityMixin = Stock, provider: str = None, entity_provider: str = None,
                 entity_ids: List[str] = None, exchanges: List[str] = None, codes: List[str] = None,
                 the_timestamp: Union[str, pd.Timestamp] = None, start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None, columns: List = None, filters: List = None,
                 order: object = None, limit: int = None, level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY,
                 category_field: str = 'entity_id', time_field: str = 'timestamp', computing_window: int = None,
                 keep_all_timestamp: bool = False, fill_method: str = 'ffill', effective_number: int = None,
                 transformer: Transformer = ZenTransformer(), accumulator: Accumulator = None,
                 need_persist: bool = False, dry_run: bool = False, adjust_type: Union[AdjustType, str] = None) -> None:
        super().__init__(entity_schema, provider, entity_provider, entity_ids, exchanges, codes, the_timestamp,
                         start_timestamp, end_timestamp, columns, filters, order, limit, level, category_field,
                         time_field, computing_window, keep_all_timestamp, fill_method, effective_number, transformer,
                         accumulator, need_persist, dry_run, adjust_type)


if __name__ == '__main__':
    from zvt.drawer.drawer import Drawer

    df = get_kdata(entity_ids=['stock_sz_000338'], columns=['entity_id', 'timestamp', 'high', 'low', 'open', 'close'],
                   index=['entity_id', 'timestamp'], end_timestamp='2009-01-01')
    one_df = df[['high', 'low']]
    t = ZenTransformer()
    one_df = t.transform_one('stock_sz_000338', one_df)

    print(one_df)

    #     annotation_df format:
    #                                     value    flag    color
    #     entity_id    timestamp

    # 处理分型
    bi_ding = one_df[one_df.bi_ding][['timestamp', 'high']]
    bi_di = one_df[one_df.bi_di][['timestamp', 'low']]

    df1 = bi_ding.rename(columns={"high": "value"})
    df1['flag'] = '顶分型'

    df2 = bi_di.rename(columns={"low": "value"})
    df2['flag'] = '底分型'

    flag_df: pd.DataFrame = pd.concat([df1, df2])
    flag_df = flag_df.sort_values(by=['timestamp'])
    flag_df['entity_id'] = 'stock_sz_000338'
    flag_df = flag_df.set_index(['entity_id', 'timestamp'])

    # 处理段
    up = one_df[one_df.duan_di][['timestamp', 'low']]
    down = one_df[one_df.duan_ding][['timestamp', 'high']]
    df1 = up.rename(columns={"low": "value"})
    df2 = down.rename(columns={"high": "value"})

    duan_df: pd.DataFrame = pd.concat([df1, df2])
    duan_df = duan_df.sort_values(by=['timestamp'])
    duan_df['entity_id'] = 'stock_sz_000338'
    duan_df = duan_df.set_index(['entity_id', 'timestamp'])

    # 处理中枢
    rects = []
    duans = []
    for index, item in duan_df.iterrows():
        if len(duans) == 4:
            x = duans[0][0]
            x1 = duans[3][0]
            if duans[0][1] < duans[1][1]:
                y, y1 = intersect((duans[0][1], duans[1][1]), (duans[2][1], duans[3][1]))
            else:
                y, y1 = intersect((duans[1][1], duans[0][1]), (duans[3][1], duans[2][1]))
            rects.append(((x, y), (x1, y1)))
            duans = []
        else:
            duans.append((index[1], item.value))

    drawer = Drawer(main_df=df, factor_df_list=[flag_df[['value']], duan_df], annotation_df=flag_df)
    fig = drawer.draw_kline(show=False)

    for rect in rects:
        fig.add_shape(type="rect",
                      x0=rect[0][0], y0=rect[0][1], x1=rect[1][0], y1=rect[1][1],
                      line=dict(
                          color="RoyalBlue",
                          width=2,
                      ),
                      fillcolor="LightSkyBlue",
                      )
    fig.update_shapes(dict(xref='x', yref='y'))
    fig.show()
# the __all__ is generated
__all__ = ['Direction', 'Fenxing', 'KState', 'DuanState', 'a_include_b', 'is_including', 'get_direction', 'is_up',
           'is_down', 'handle_first_fenxing', 'handle_duan', 'handle_including', 'ZenTransformer', 'ZenFactor']
