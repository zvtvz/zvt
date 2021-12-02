# -*- coding: utf-8 -*-
import logging
from enum import Enum

from zvt.api import get_recent_report
from zvt.contract import ActorType
from zvt.domain import StockActorSummary
from zvt.tag.dataset.stock_tags import StockTags
from zvt.tag.tag import StockTagger
from zvt.utils import pd_is_not_null

logger = logging.getLogger(__name__)


class ActorTag(Enum):
    # 基金心头好
    fund_love = "fund_love"
    # 基金看不起
    fund_not_care = "fund_not_care"


class ActorTagger(StockTagger):
    def tag(self, timestamp):
        df = get_recent_report(
            data_schema=StockActorSummary,
            timestamp=timestamp,
            filters=[StockActorSummary.actor_type == ActorType.raised_fund.value],
        )
        if not pd_is_not_null(df):
            logger.error(f"no StockActorSummary data at {timestamp}")
            return

        df = df.set_index("entity_id")

        fund_love_ids = df[df["holding_ratio"] >= 0.05 & df["change_ratio"] >= -0.3].index.tolist()
        fund_not_care_ids = df[df["holding_ratio"] < 0.05 | df["change_ratio"] < -0.3].index.tolist()

        fund_love_domains = self.get_tag_domains(
            entity_ids=fund_love_ids, timestamp=timestamp, actor_tag=ActorTag.fund_love.value
        )
        fund_not_care_domains = self.get_tag_domains(
            entity_ids=fund_not_care_ids, timestamp=timestamp, actor_tag=ActorTag.fund_not_care.value
        )
        self.session.add_all(fund_love_domains)
        self.session.add_all(fund_not_care_domains)
        self.session.commit()


if __name__ == "__main__":
    # ActorTagger().run()
    print(StockTags.query_data(start_timestamp="2021-08-31", filters=[StockTags.actor_tag != None]))
# the __all__ is generated
__all__ = ["ActorTag", "ActorTagger"]
