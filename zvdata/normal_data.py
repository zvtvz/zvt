# -*- coding: utf-8 -*-
import enum
from typing import List

import numpy as np
import pandas as pd

from zvdata.utils.pd_utils import df_is_not_null, fill_with_same_index, normal_index_df


class TableType(enum.Enum):
    single_single_single = 'single_single_single'
    single_single_multiple = 'single_single_multiple'
    single_multiple_single = 'single_multiple_single'
    single_multiple_multiple = 'single_multiple_multiple'

    multiple_single_single = 'multiple_single_single'
    multiple_single_multiple = 'multiple_single_multiple'
    multiple_multiple_single = 'multiple_multiple_single'
    multiple_multiple_multiple = 'multiple_multiple_multiple'


class IntentType(enum.Enum):
    not_much_meaning = 'not_much_meaning'
    # for one entity
    compare_self = 'compare_self'
    composite_self = 'composite_self'
    distribute_self = 'distribute_self'

    # multiple entities
    compare_to_other = 'compare_to_other'


class ChartType(enum.Enum):
    line = 'line'
    scatter = 'scatter'
    bar = 'bar'
    area = 'area'

    pie = 'pie'
    polar = 'polar'

    histogram = 'histogram'


intent_map_charts = {
    IntentType.not_much_meaning: [ChartType.bar],
    IntentType.compare_self: [ChartType.line, ChartType.bar, ChartType.scatter, ChartType.area],
    IntentType.composite_self: [ChartType.pie, ChartType.polar],
    IntentType.distribute_self: [ChartType.histogram],

    IntentType.compare_to_other: [ChartType.line, ChartType.bar, ChartType.scatter, ChartType.area]
}


class NormalData(object):
    table_type_sample = None

    def __init__(self,
                 df,
                 annotation_df=None,
                 category_field='entity_id',
                 index_field='timestamp',
                 is_timeseries: bool = True,
                 fill_index: bool = False) -> None:
        self.data_df = df
        self.annotation_df: pd.DataFrame = annotation_df
        self.category_field = category_field
        self.index_field = index_field
        self.is_timeseries = is_timeseries
        self.fill_index = fill_index

        self.entity_ids = []
        self.df_list = []
        self.entity_map_df = {}

        self.normalize()

    def is_normalized(self):
        if df_is_not_null(self.data_df):
            names = self.data_df.index.names

            if len(names) == 2 and names[0] == self.category_field and names[1] == self.index_field:
                return True

        return False

    def normalize(self):
        """
        normalize data_df to
                                    col1    col2    col3
        entity_id    index_field

        """
        if df_is_not_null(self.data_df):
            if not self.is_normalized():
                self.data_df = normal_index_df(self.data_df, category_field=self.category_field,
                                               xfield=self.index_field, is_timeseries=self.is_timeseries)

            self.entity_ids = self.data_df.index.levels[0].to_list()

            for entity_id in self.entity_ids:
                df = self.data_df.loc[(entity_id,)]
                self.df_list.append(df)
                self.entity_map_df[entity_id] = df

            if len(self.df_list) > 1 and self.fill_index:
                self.df_list = fill_with_same_index(df_list=self.df_list)

    def add_data(self, entity_id, df):
        self.entity_map_df[entity_id] = self.entity_map_df[entity_id].append(df)

        self.data_df = self.data_df.append(df)
        self.data_df.sort_index(level=[0, 1])

    def empty(self):
        return not df_is_not_null(self.data_df)

    def get_table_type(self):
        if self.entity_size == 1:
            a = 'single'
        else:
            a = 'multiple'

        if self.row_count == 1:
            b = 'single'
        else:
            b = 'multiple'

        if self.column_size == 1:
            c = 'single'
        else:
            c = 'multiple'

        return f'{a}_{b}_{c}'

    def get_intents(self) -> List[IntentType]:
        table_type = TableType(self.get_table_type())

        # single entity
        if table_type == TableType.single_single_single:
            return [IntentType.not_much_meaning]

        if table_type == TableType.single_single_multiple:
            return [IntentType.compare_self, IntentType.composite_self]

        if table_type == TableType.single_multiple_single:
            return [IntentType.compare_self, IntentType.distribute_self]

        if table_type == TableType.single_multiple_multiple:
            return [IntentType.compare_self]

        # multiple entity
        if table_type == TableType.multiple_single_single:
            return [IntentType.compare_to_other]

        if table_type == TableType.multiple_single_multiple:
            return [IntentType.compare_to_other]

        if table_type == TableType.multiple_multiple_single:
            return [IntentType.compare_to_other]

        if table_type == TableType.multiple_multiple_multiple:
            return [IntentType.compare_to_other]

    @staticmethod
    def get_charts_by_intent(intent) -> List[ChartType]:
        charts = intent_map_charts.get(IntentType(intent))

        if charts is None:
            charts = [ChartType.line, ChartType.bar, ChartType.scatter, ChartType.area]

        return charts

    @staticmethod
    def sample(table_type: TableType = TableType.multiple_multiple_single):

        if NormalData.table_type_sample is None:
            NormalData.table_type_sample = {
                TableType.single_single_single: NormalData._sample(entity_ids=['jack'], row_size=1,
                                                                   columns=['score']),
                TableType.single_single_multiple: NormalData._sample(entity_ids=['jack'], row_size=1),
                TableType.single_multiple_single: NormalData._sample(entity_ids=['jack'], columns=['score']),
                TableType.single_multiple_multiple: NormalData._sample(entity_ids=['jack']),

                TableType.multiple_single_single: NormalData._sample(row_size=1, columns=['math']),
                TableType.multiple_single_multiple: NormalData._sample(row_size=1),
                TableType.multiple_multiple_single: NormalData._sample(columns=['math']),
                TableType.multiple_multiple_multiple: NormalData._sample()
            }

        return NormalData.table_type_sample.get(table_type)

    @staticmethod
    def _sample(entity_ids: List[str] = ['jack', 'helen', 'kris'],
                x_field: str = 'timestamp',
                row_size: int = 10,
                is_timeseries: bool = True,
                columns: List[str] = ['math', 'physics', 'programing']):
        dfs = pd.DataFrame()
        for entity in entity_ids:
            if x_field is not None and is_timeseries:
                df = pd.DataFrame(np.random.randint(low=0, high=100, size=(row_size, len(columns))), columns=columns)
                df[x_field] = pd.date_range(end='1/1/2018', periods=row_size)
            else:
                df = pd.DataFrame(np.random.randint(low=0, high=100, size=(row_size, len(columns))), columns=columns)

            df['entity_id'] = entity
            dfs = dfs.append(df)

        dfs = normal_index_df(df=dfs, xfield=x_field, is_timeseries=is_timeseries)

        return dfs

    def is_empty(self):
        return not df_is_not_null(self.data_df)
