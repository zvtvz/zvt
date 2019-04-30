# -*- coding: utf-8 -*-
import pandas as pd

from zvt.api.common import common_filter
from zvt.domain.account import SimAccount


def get_account(trader_name=None, model_name=None, return_type='df', start_timestamp=None, end_timestamp=None,
                filters=None, session=None, order=None, limit=None):
    try:
        data_schema = SimAccount
        query = session.query(data_schema)

        query = query.filter(data_schema.trader_name == trader_name, data_schema.model_name == model_name)

        query = common_filter(query, data_schema=data_schema, start_timestamp=start_timestamp,
                              end_timestamp=end_timestamp, filters=filters, order=order, limit=limit)
        if return_type == 'df':
            return pd.read_sql(query.statement, query.session.bind)
        elif return_type == 'domain':
            return query.all()
        elif return_type == 'dict':
            return [item.as_dict() for item in query.all()]
    except Exception:
        raise
