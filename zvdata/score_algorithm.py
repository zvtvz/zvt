# -*- coding: utf-8 -*-
import logging

import pandas as pd

from zvdata.utils.pd_utils import index_df_with_category_xfield


class Scorer(object):
    logger = logging.getLogger(__name__)

    def compute(self, input_df) -> pd.DataFrame:
        return input_df


class RankScorer(Scorer):
    def __init__(self, ascending=True) -> None:
        self.ascending = ascending

    def compute(self, input_df) -> pd.DataFrame:
        result_df = input_df.groupby(level=1).rank(ascending=self.ascending, pct=True)
        return result_df


class QuantileScorer(Scorer):
    def __init__(self, score_levels=[0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0]) -> None:
        self.score_levels = score_levels

    def compute(self, input_df):
        self.score_levels.sort(reverse=True)

        quantile_df = input_df.groupby(level=1).quantile(self.score_levels)
        quantile_df.index.names = [self.time_field, 'score']

        self.logger.info('factor:{},quantile:\n{}'.format(self.factor_name, quantile_df))

        result_df = input_df.copy()
        result_df.reset_index(inplace=True, level='entity_id')
        result_df['quantile'] = None
        for timestamp in quantile_df.index.levels[0]:
            length = len(result_df.loc[result_df.index == timestamp, 'quantile'])
            result_df.loc[result_df.index == timestamp, 'quantile'] = [quantile_df.loc[
                                                                           timestamp].to_dict()] * length

        self.logger.info('factor:{},df with quantile:\n{}'.format(self.factor_name, result_df))

        # result_df = result_df.set_index(['entity_id'], append=True)
        # result_df = result_df.sort_index(level=[0, 1])
        #
        # self.logger.info(result_df)
        #
        def calculate_score(df, factor_name, quantile):
            original_value = df[factor_name]
            score_map = quantile.get(factor_name)
            min_score = self.score_levels[-1]

            if original_value < score_map.get(min_score):
                return 0

            for score in self.score_levels[:-1]:
                if original_value >= score_map.get(score):
                    return score

        for factor in input_df.columns.to_list():
            result_df[factor] = result_df.apply(lambda x: calculate_score(x, factor, x['quantile']),
                                                axis=1)

        result_df = result_df.reset_index()
        result_df = index_df_with_category_xfield(result_df, category_field=self.category_field,
                                                  xfield=self.time_field)
        result_df = result_df.loc[:, self.factors]

        result_df = result_df.loc[~result_df.index.duplicated(keep='first')]

        self.logger.info('factor:{},df:\n{}'.format(self.factor_name, result_df))

        return result_df
