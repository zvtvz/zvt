# -*- coding: utf-8 -*-

from zvt.utils.pd_utils import pd_is_not_null, fill_with_same_index, normal_index_df, is_normal_df


class NormalData(object):
    table_type_sample = None

    def __init__(self,
                 df,
                 category_field='entity_id',
                 time_field='timestamp',
                 fill_index: bool = False) -> None:
        self.data_df = df
        self.category_field = category_field
        self.time_field = time_field
        self.fill_index = fill_index

        self.entity_ids = []
        self.df_list = []
        self.entity_map_df = {}

        self.normalize()

    def normalize(self):
        """
        normalize data_df to
                                    col1    col2    col3
        entity_id    timestamp

        """
        if pd_is_not_null(self.data_df):
            if not is_normal_df(self.data_df):
                self.data_df = normal_index_df(self.data_df, self.category_field, self.time_field)

            self.entity_ids = self.data_df.index.levels[0].to_list()

            for entity_id in self.entity_ids:
                df = self.data_df.loc[(entity_id,)]
                self.df_list.append(df)
                self.entity_map_df[entity_id] = df

            if len(self.df_list) > 1 and self.fill_index:
                self.df_list = fill_with_same_index(df_list=self.df_list)

    def empty(self):
        return not pd_is_not_null(self.data_df)


__all__ = ['NormalData']
