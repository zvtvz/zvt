# -*- coding: utf-8 -*-
import logging
from typing import Type

import pandas as pd

from zvt.contract import Mixin
from zvt.contract import TradableEntity
from zvt.contract.api import get_db_session
from zvt.contract.base import StatefulService
from zvt.contract.zvt_info import TaggerState
from zvt.domain import Stock, Index
from zvt.tag.dataset.stock_tags import StockTags
from zvt.utils import to_time_str, to_pd_timestamp
from zvt.utils.time_utils import TIME_FORMAT_DAY, now_pd_timestamp

logger = logging.getLogger(__name__)


class Tagger(StatefulService):
    state_schema = TaggerState

    entity_schema: Type[TradableEntity] = None

    data_schema: Type[Mixin] = None

    start_timestamp = "2005-01-01"

    def __init__(self, force=False) -> None:
        super().__init__()
        assert self.entity_schema is not None
        assert self.data_schema is not None
        self.force = force
        self.session = get_db_session(provider="zvt", data_schema=self.data_schema)
        if self.state and not self.force:
            logger.info(f"get start_timestamp from state")
            self.start_timestamp = self.state["current_timestamp"]
        logger.info(f"tag start_timestamp: {self.start_timestamp}")

    def tag(self, timestamp):
        raise NotImplementedError

    def get_tag_timestamps(self):
        return pd.date_range(start=self.start_timestamp, end=now_pd_timestamp(), freq="M")

    def get_tag_domain(self, entity_id, timestamp, **fill_kv):
        the_date = to_time_str(timestamp, fmt=TIME_FORMAT_DAY)
        the_id = f"{entity_id}_{the_date}"
        the_domain = self.data_schema.get_one(id=the_id)

        if the_domain:
            for k, v in fill_kv.items():
                exec(f"the_domain.{k}=v")
        else:
            return self.data_schema(id=the_id, entity_id=entity_id, timestamp=to_pd_timestamp(the_date), **fill_kv)
        return the_domain

    def get_tag_domains(self, entity_ids, timestamp, **fill_kv):
        the_date = to_time_str(timestamp, fmt=TIME_FORMAT_DAY)
        ids = [f"{entity_id}_{the_date}" for entity_id in entity_ids]

        the_domains = self.data_schema.query_data(ids=ids, return_type="domain")

        if the_domains:
            for the_domain in the_domains:
                for k, v in fill_kv.items():
                    exec(f"the_domain.{k}=v")

        current_ids = [item.id for item in the_domains]
        need_new_ids = set(ids) - set(current_ids)
        new_domains = [
            self.data_schema(
                id=f"{entity_id}_{the_date}", entity_id=entity_id, timestamp=to_pd_timestamp(the_date), **fill_kv
            )
            for entity_id in need_new_ids
        ]
        return the_domains + new_domains

    def run(self):
        timestamps = self.get_tag_timestamps()
        for timestamp in timestamps:
            logger.info(f"tag to {timestamp}")
            self.tag(timestamp=timestamp)

            self.state = {"current_timestamp": to_time_str(timestamp)}
            self.persist_state()


class StockTagger(Tagger):
    data_schema = StockTags
    entity_schema = Stock

    def tag(self, timestamp):
        raise NotImplementedError


class IndexTagger(Tagger):
    data_schema = StockTags
    entity_schema = Index

    def tag(self, timestamp):
        raise NotImplementedError


# the __all__ is generated
__all__ = ["Tagger", "StockTagger", "IndexTagger"]
