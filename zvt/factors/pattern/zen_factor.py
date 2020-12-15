# -*- coding: utf-8 -*-
import json
from enum import Enum
from typing import List
from typing import Union, Optional, Type

import numpy as np
import pandas as pd

from zvt.contract import EntityMixin
from zvt.contract import IntervalLevel, AdjustType
from zvt.contract.api import get_schema_by_name, df_to_db, get_db_session
from zvt.contract.data_type import Bean
from zvt.contract.drawer import Rect
from zvt.contract.factor import Accumulator, FactorState
from zvt.contract.factor import Transformer
from zvt.domain import Stock
from zvt.factors import TechnicalFactor
from zvt.factors.algorithm import intersect
from zvt.utils import pd_is_not_null
from zvt.utils import to_time_str
from zvt.utils.time_utils import TIME_FORMAT_ISO8601


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
        return Fenxing(state=fenxing, index=fenxing_index, kdata=one_df.loc[fenxing_index]), start_index, direction
    else:
        print("need add step")
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


def get_ma_zen_factor_schema(entity_type: str,
                             level: Union[IntervalLevel, str] = IntervalLevel.LEVEL_1DAY):
    if type(level) == str:
        level = IntervalLevel(level)

    # ma state stats schema rule
    # 1)name:{SecurityType.value.capitalize()}{IntervalLevel.value.upper()}ZenFactor
    schema_str = '{}{}ZenFactor'.format(entity_type.capitalize(), level.value.capitalize())

    return get_schema_by_name(schema_str)


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

        # list of (timestamp,value)
        self.duans = state.get('duans', [])


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
        if pd_is_not_null(acc_df):
            df = df[df.index > acc_df.index[-1]]
            if pd_is_not_null(df):
                # 遍历的开始位置
                start_index = len(acc_df)

                acc_df = pd.concat([acc_df, df])

                zen_state = state

                acc_df = acc_df.reset_index(drop=True)
            else:
                return acc_df, state
        else:
            acc_df = df
            # 笔的底
            acc_df['bi_di'] = False
            # 笔的顶
            acc_df['bi_ding'] = False
            # 记录笔顶/底分型的值，bi_di取low,bi_ding取high,其他为None,绘图时取有值的连线即为 笔
            acc_df['bi_value'] = np.NAN

            # 记录临时分型，不变
            acc_df['tmp_ding'] = False
            acc_df['tmp_di'] = False
            # 分型的力度
            acc_df['fenxing_power'] = np.NAN

            acc_df['duan_state'] = 'yi'

            # 段的底
            acc_df['duan_di'] = False
            # 段的顶
            acc_df['duan_ding'] = False
            # 记录段顶/底的值，为duan_di时取low,为duan_ding时取high,其他为None,绘图时取有值的连线即为 段
            acc_df['duan_value'] = np.NAN

            # 记录在确定中枢的最后一个段的终点x1，值为Rect(x0,y0,x1,y1)
            acc_df['zhongshu'] = np.NAN

            acc_df = acc_df.reset_index(drop=True)

            zen_state = ZenState(dict(fenxing_list=[], direction=None, can_fenxing=None, can_fenxing_index=None,
                                      opposite_count=0, current_duan_state='yi', duans=[], pre_bi=None, pre_duan=None))

            zen_state.fenxing_list: List[Fenxing] = []

            # 取前11条k线，至多出现一个顶分型+底分型
            # 注:只是一种方便的确定第一个分型的办法，有了第一个分型，后面的处理就比较统一
            # start_index 为遍历开始的位置
            # direction为一个确定分型后的方向，即顶分型后为:down，底分型后为:up
            fenxing, start_index, direction = handle_first_fenxing(acc_df, step=11)
            zen_state.fenxing_list.append(fenxing)
            zen_state.direction = direction

            # list of (timestamp,value)
            zen_state.duans = []

        pre_kdata = acc_df.iloc[start_index - 1]
        pre_index = start_index - 1

        tmp_direction = zen_state.direction

        for index, kdata in acc_df.iloc[start_index:].iterrows():
            # print(f'timestamp: {kdata.timestamp}')
            # 临时方向
            tmp_direction = get_direction(kdata, pre_kdata, current=tmp_direction)

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
                # 第一次反向
                if zen_state.opposite_count == 1:
                    acc_df.loc[pre_index, tmp_fenxing_col] = True
                    acc_df.loc[pre_index, 'fenxing_power'] = fenxing_power(acc_df.loc[pre_index - 1], pre_kdata, kdata,
                                                                           fenxing=tmp_fenxing_col)

                    if pd_is_not_null(zen_state.can_fenxing):
                        # 候选底分型
                        if tmp_direction == Direction.up:
                            # 取小的
                            if pre_kdata['low'] <= zen_state.can_fenxing['low']:
                                zen_state.can_fenxing = pre_kdata
                                zen_state.can_fenxing_index = pre_index

                        # 候选顶分型
                        else:
                            # 取大的
                            if pre_kdata['high'] >= zen_state.can_fenxing['high']:
                                zen_state.can_fenxing = pre_kdata
                                zen_state.can_fenxing_index = pre_index
                    else:
                        zen_state.can_fenxing = pre_kdata
                        zen_state.can_fenxing_index = pre_index

                # 分型确立
                if pd_is_not_null(zen_state.can_fenxing):
                    if zen_state.opposite_count >= 4 or (index - zen_state.can_fenxing_index >= 8):
                        acc_df.loc[zen_state.can_fenxing_index, fenxing_col] = True

                        # 记录笔的值
                        if fenxing_col == 'bi_ding':
                            bi_value = acc_df.loc[zen_state.can_fenxing_index, 'high']
                        else:
                            bi_value = acc_df.loc[zen_state.can_fenxing_index, 'low']
                        acc_df.loc[zen_state.can_fenxing_index, 'bi_value'] = bi_value

                        zen_state.pre_bi = (zen_state.can_fenxing_index, bi_value)

                        zen_state.opposite_count = 0
                        zen_state.direction = zen_state.direction.opposite()
                        zen_state.can_fenxing = None

                        # 确定第一个段
                        if zen_state.fenxing_list != None:
                            zen_state.fenxing_list.append(
                                Fenxing(state=fenxing_col,
                                        kdata=acc_df.loc[zen_state.can_fenxing_index, ['open', 'close', 'high', 'low']],
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

                                    # 记录用于计算中枢的段
                                    zen_state.duans.append((acc_df.loc[duan_index, 'timestamp'], duan_value))

                                    # 计算中枢
                                    if len(zen_state.duans) == 4:
                                        x1 = zen_state.duans[0][0]
                                        x2 = zen_state.duans[3][0]
                                        if zen_state.duans[0][1] < zen_state.duans[1][1]:
                                            # 向下段
                                            range = intersect((zen_state.duans[0][1], zen_state.duans[1][1]),
                                                              (zen_state.duans[2][1], zen_state.duans[3][1]))
                                            if range:
                                                y1, y2 = range
                                                # 记录中枢
                                                acc_df.loc[duan_index, 'zhongshu'] = Rect(x0=x1, x1=x2, y0=y1, y1=y2)
                                                zen_state.duans = zen_state.duans[-1:]
                                            else:
                                                zen_state.duans = zen_state.duans[1:]
                                        else:
                                            # 向上段
                                            range = intersect((zen_state.duans[1][1], zen_state.duans[0][1]),
                                                              (zen_state.duans[3][1], zen_state.duans[2][1]))
                                            if range:
                                                y1, y2 = range
                                                # 记录中枢
                                                acc_df.loc[duan_index, 'zhongshu'] = Rect(x0=x1, x1=x2, y0=y1, y1=y2)
                                                zen_state.duans = zen_state.duans[-1:]
                                            else:
                                                zen_state.duans = zen_state.duans[1:]

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

    def __init__(self, entity_schema: Type[EntityMixin] = Stock, provider: str = None, entity_provider: str = None,
                 entity_ids: List[str] = None, exchanges: List[str] = None, codes: List[str] = None,
                 the_timestamp: Union[str, pd.Timestamp] = None, start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None, columns: List = None, filters: List = None,
                 order: object = None, limit: int = None, level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY,
                 category_field: str = 'entity_id', time_field: str = 'timestamp', computing_window: int = None,
                 keep_all_timestamp: bool = False, fill_method: str = 'ffill', effective_number: int = None,
                 transformer: Transformer = None, accumulator: Accumulator = ZenAccumulator(),
                 need_persist: bool = False, dry_run: bool = False, factor_name: str = None, clear_state: bool = False,
                 adjust_type: Union[AdjustType, str] = None) -> None:
        self.factor_schema = get_ma_zen_factor_schema(entity_type=entity_schema.__name__, level=level)
        super().__init__(entity_schema, provider, entity_provider, entity_ids, exchanges, codes, the_timestamp,
                         start_timestamp, end_timestamp, columns, filters, order, limit, level, category_field,
                         time_field, computing_window, keep_all_timestamp, fill_method, effective_number, transformer,
                         accumulator, need_persist, dry_run, factor_name, clear_state, adjust_type)

    def on_data_loaded(self, data: pd.DataFrame):
        if pd_is_not_null(self.factor_df):
            self.factor_df['zhongshu'] = self.factor_df['zhongshu'].apply(
                lambda x: json.loads(x, object_hook=decode_rect))
        return super().on_data_loaded(data)

    def decode_state(self, state):
        return ZenState(state)

    def persist_factor(self):

        if self.states:
            session = get_db_session(provider='zvt', data_schema=FactorState)
            for entity_id in self.states:
                state = self.states[entity_id]
                if state:
                    domain_id = f'{self.factor_name}_{entity_id}'
                    factor_state: FactorState = session.query(FactorState).get(domain_id)
                    state_str = json.dumps(state, cls=FactorStateEncoder)
                    if factor_state:
                        factor_state.state = state_str
                    else:
                        factor_state = FactorState(id=domain_id, entity_id=entity_id, factor_name=self.factor_name,
                                                   state=state_str)
                        session.add(factor_state)
            session.commit()
        df = self.factor_df.copy()
        df['zhongshu'] = df['zhongshu'].apply(lambda x: json.dumps(x, cls=FactorStateEncoder))

        df_to_db(df=df, data_schema=self.factor_schema, provider='zvt', force_update=False)

    def drawer_factor_df_list(self) -> Optional[List[pd.DataFrame]]:
        bi_value = self.factor_df[['bi_value']].dropna()
        duan_value = self.factor_df[['duan_value']].dropna()
        return [bi_value, duan_value]

    def drawer_rects(self) -> List[Rect]:
        df = self.factor_df[['zhongshu']].dropna()
        return df['zhongshu'].tolist()


if __name__ == '__main__':
    zen = ZenFactor(entity_ids=['stock_sz_000338', 'stock_sz_000001'], level='1d', need_persist=False, clear_state=True)

    print(zen.factor_df)

    zen.move_on(timeout=1)

    print(zen.factor_df)

    zen.draw(show=True)

# the __all__ is generated
__all__ = ['get_ma_zen_factor_schema', 'ZenState', 'ZenAccumulator', 'ZenFactor']
