# -*- coding: utf-8 -*-
import logging
from enum import Enum

from zvt.domain import IndexStock
from zvt.tag.tag import StockTagger
from zvt.utils import pd_is_not_null
from zvt.utils.time_utils import month_start_date, month_end_date

logger = logging.getLogger(__name__)


class MarketValueTag(Enum):
    # 市值前500
    huge = "huge"
    # 500-1000
    medium = "medium"
    # 1000->
    small = "small"


index_map_market_value = {
    # 399311 国证1000指数由A股市场中市值大、流动性好的1000只股票构成，反映A股市场大中盘股票的价格变动趋势。
    # 399400 大中盘指数由巨潮大盘指数样本股与巨潮中盘指数样本股组合而成,国证1000中的前500
    "index_sz_399400": MarketValueTag.huge,
    # 399316 巨潮小盘指数以国证1000指数为样本空间，选取总市值排名在后500名的股票
    "index_sz_399316": MarketValueTag.medium,
    # 399303 国证2000由全部A股扣除国证1000指数样本股后，市值大、流动性好的2000只A股组成，反映A股市场小微盘股票的价格变动趋势。
    "index_sz_399303": MarketValueTag.small,
}


class MarketValueTagger(StockTagger):
    def tag(self, timestamp):
        for index_id in index_map_market_value:
            df = IndexStock.query_data(
                entity_id=index_id, start_timestamp=month_start_date(timestamp), end_timestamp=month_end_date(timestamp)
            )
            if not pd_is_not_null(df):
                logger.error(f"no IndexStock data at {timestamp} for {index_id}")
                continue
            stock_tags = [
                self.get_tag_domain(entity_id=stock_id, timestamp=timestamp) for stock_id in df["stock_id"].tolist()
            ]

            for stock_tag in stock_tags:
                stock_tag.market_value_tag = index_map_market_value.get(index_id).value

            self.session.add_all(stock_tags)
            self.session.commit()


if __name__ == "__main__":
    MarketValueTagger().run()
# the __all__ is generated
__all__ = ["MarketValueTag", "MarketValueTagger"]
