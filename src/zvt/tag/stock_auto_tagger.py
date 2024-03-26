# -*- coding: utf-8 -*-
import logging
from enum import Enum
from typing import List

import pandas as pd
import sqlalchemy
from zvt.api import get_recent_report
from zvt.api.selector import get_entity_ids_by_filter
from zvt.contract import ActorType
from zvt.contract.api import get_db_session, df_to_db
from zvt.domain import StockActorSummary, BlockStock, Block, Stock, StockEvents
from zvt.tag.dataset.stock_tags import StockTags, TagsInfo, SubTagsInfo, HiddenTagsInfo
from zvt.tag.tag_utils import industry_to_tag, get_concept_list, get_tags_info, get_sub_tags_info, get_hidden_tags_info
from zvt.tag.tagger import StockTagger
from zvt.utils import pd_is_not_null, is_same_date, count_interval, to_time_str, to_pd_timestamp

logger = logging.getLogger(__name__)


def build_tags_info():
    tags_info = get_tags_info()
    df = pd.DataFrame.from_records(tags_info)
    df_to_db(df=df, data_schema=TagsInfo, provider="zvt", force_update=False)


def build_sub_tags_info():
    tags_info = get_sub_tags_info()
    df = pd.DataFrame.from_records(tags_info)
    df_to_db(df=df, data_schema=SubTagsInfo, provider="zvt", force_update=False)


def build_hidden_tags_info():
    tags_info = get_hidden_tags_info()
    df = pd.DataFrame.from_records(tags_info)
    df_to_db(df=df, data_schema=HiddenTagsInfo, provider="zvt", force_update=False)


class StockAutoTagger(StockTagger):
    def __init__(self, force=False) -> None:
        super().__init__(force)
        datas = StockTags.query_data(limit=1, return_type="domain")
        self.stock_tags_map = {}
        if not datas:
            self.init_default_tags(entity_ids=None)

    def init_default_tags(self, entity_ids=None):
        stocks = Stock.query_data(
            provider="em", entity_ids=entity_ids, return_type="domain", filters=[Stock.timestamp.isnot(None)]
        )
        entity_map = {stock.entity_id: stock for stock in stocks}
        entity_ids = entity_map.keys()
        df_block = Block.query_data(provider="em", filters=[Block.category == "industry"])
        industry_codes = df_block["code"].tolist()
        block_stocks: List[BlockStock] = BlockStock.query_data(
            provider="em",
            filters=[BlockStock.code.in_(industry_codes), BlockStock.stock_id.in_(entity_ids)],
            return_type="domain",
        )
        stock_tags = []
        for block_stock in block_stocks:
            entity = entity_map.get(block_stock.stock_id)
            if entity.id in self.stock_tags_map:
                print(f"ignore {entity.id}")
                continue
            print(f"to {entity.id}")

            tag = industry_to_tag(industry=block_stock.name)
            tag_reason = f"来自行业:{block_stock.name}"

            stock_tag = StockTags(
                id=f"{entity.id}_{to_time_str(entity.timestamp)}",
                entity_id=block_stock.stock_id,
                timestamp=entity.timestamp,
                tag=tag,
                tag_reason=tag_reason,
                tags={tag: tag_reason},
                set_by_user=False,
                latest=True,
            )
            stock_tags.append(stock_tag)
            self.stock_tags_map[entity.id] = stock_tag
        self.session.add_all(stock_tags)
        self.session.commit()

    def build_sub_tags(self, entity_ids):
        for entity_id in entity_ids:
            print(f"to {entity_id}")
            datas = StockTags.query_data(
                entity_id=entity_id, order=StockTags.timestamp.desc(), limit=1, return_type="domain"
            )
            if not datas:
                print(f"ignore no tag:{entity_id}")
                continue
            start_timestamp = max(datas[0].timestamp, to_pd_timestamp("2005-01-01"))
            print(f"start_timestamp: {start_timestamp}")
            current_sub_tag = datas[0].sub_tag
            filters = [StockEvents.event_type == "新增概念", StockEvents.entity_id == entity_id]
            if current_sub_tag:
                print(f"current_sub_tag: {current_sub_tag}")
                filters = filters + [sqlalchemy.not_(StockEvents.level1_content.contains(current_sub_tag))]
            stock_events: List[StockEvents] = StockEvents.query_data(
                provider="em",
                start_timestamp=start_timestamp,
                filters=filters,
                order=StockEvents.timestamp.asc(),
                return_type="domain",
            )
            if not stock_events:
                print(f"no event for {entity_id}")

            for stock_event in stock_events:
                datas: List[StockTags] = StockTags.query_data(
                    entity_id=entity_id, order=StockTags.timestamp.desc(), limit=1, return_type="domain"
                )
                current_stock_tags: StockTags = datas[0]

                event_timestamp = to_pd_timestamp(stock_event.timestamp)
                if stock_event.level1_content:
                    contents = stock_event.level1_content.split("：")
                    if len(contents) < 2:
                        print(f"wrong stock_event:{stock_event.level1_content}")
                    else:
                        sub_tag = contents[1]
                        if sub_tag in get_concept_list(return_checked=True):
                            if stock_event.level2_content:
                                sub_tag_reason = stock_event.level2_content.split("：")[1]
                            else:
                                sub_tag_reason = f"来自概念:{sub_tag}"

                            if current_stock_tags.sub_tags:
                                sub_tags = dict(current_stock_tags.sub_tags)
                            else:
                                sub_tags = {}
                            if is_same_date(event_timestamp, current_stock_tags.timestamp):
                                stock_tag = current_stock_tags
                            else:
                                current_stock_tags.latest = False
                                stock_tag = StockTags(
                                    id=f"{entity_id}_{to_time_str(event_timestamp)}",
                                    entity_id=entity_id,
                                    timestamp=event_timestamp,
                                    tag=current_stock_tags.tag,
                                    tag_reason=current_stock_tags.tag_reason,
                                    tags=current_stock_tags.tags,
                                )
                            sub_tags[sub_tag] = sub_tag_reason
                            stock_tag.sub_tag = sub_tag
                            stock_tag.sub_tag_reason = sub_tag_reason
                            stock_tag.sub_tags = sub_tags
                            stock_tag.latest = True
                            self.session.add(stock_tag)
                            self.session.commit()
                        else:
                            print(f"ignore concept: {sub_tag}")

    def tag(self):
        entity_ids = get_entity_ids_by_filter(
            provider="em", ignore_delist=False, ignore_st=False, ignore_new_stock=False
        )
        for entity_id in entity_ids:
            stock_tags = StockTags.query_data(
                entity_id=entity_id, order=StockTags.timestamp.desc(), limit=1, return_type="domain"
            )
            if not stock_tags:
                self.init_default_tags(entity_ids=[entity_id])
        self.build_sub_tags(entity_ids=entity_ids)


if __name__ == "__main__":
    # entity_ids = get_entity_ids_by_filter(
    #     provider="em", ignore_delist=False, ignore_st=False, ignore_new_stock=False
    # )
    # session = get_db_session(provider="zvt", data_schema=StockTags)
    # for entity_id in entity_ids:
    #     datas = StockTags.query_data(
    #         entity_id=entity_id, order=StockTags.timestamp.desc(), limit=1, return_type="domain"
    #     )
    #     if datas:
    #         stock_tags = datas[0]
    #         stock_tags.latest=True
    #         session.add(stock_tags)
    #         session.commit()
    # StockAutoTagger().tag()
    build_tags_info()
    build_sub_tags_info()
    build_hidden_tags_info()
    # from sqlalchemy import func
    #
    # df = StockTags.query_data(
    #     filters=[func.json_extract(StockTags.sub_tags, '$."麒麟电池"') != None], columns=[StockTags.sub_tags]
    # )
    # print(df)
# the __all__ is generated
__all__ = ["build_tags_info", "build_sub_tags_info", "build_hidden_tags_info", "StockAutoTagger"]
