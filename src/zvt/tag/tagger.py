# -*- coding: utf-8 -*-
import logging
from typing import Type

from zvt.contract import Mixin
from zvt.contract import TradableEntity
from zvt.contract.api import get_db_session
from zvt.contract.base_service import OneStateService
from zvt.contract.zvt_info import TaggerState
from zvt.domain import Stock
from zvt.tag.tag_schemas import StockTags

logger = logging.getLogger(__name__)


class Tagger(OneStateService):
    state_schema = TaggerState

    entity_schema: Type[TradableEntity] = None

    data_schema: Type[Mixin] = None

    start_timestamp = "2018-01-01"

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

    def tag(self):
        raise NotImplementedError


class StockTagger(Tagger):
    data_schema = StockTags
    entity_schema = Stock

    def tag(self):
        raise NotImplementedError


# the __all__ is generated
__all__ = ["Tagger", "StockTagger"]
