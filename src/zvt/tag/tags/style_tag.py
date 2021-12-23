# -*- coding: utf-8 -*-
import logging
from enum import Enum

from zvt.domain import IndexStock
from zvt.tag.tag import StockTagger

# define tag
from zvt.utils import pd_is_not_null
from zvt.utils.time_utils import month_start_date, month_end_date

logger = logging.getLogger(__name__)


class StyleTag(Enum):
    # 成长股
    growth = "growth"
    # 价值股
    value = "value"


index_map_style = {
    # 国证成长（399370）
    # 在国证1000指数样本股中，选取主营业务收入增长率、净利润增长率和净资产收益率综合排名前332只
    "index_sz_399370": StyleTag.growth,
    # 国证价值（399371）
    # 在国证1000指数样本股中，选取每股收益与价格比率、每股经营现金流与价格比率、股息收益率、每股净资产与价格比率综合排名前332只
    "index_sz_399371": StyleTag.value,
}


class StyleTagger(StockTagger):
    def tag(self, timestamp):
        for index_id in index_map_style:
            df = IndexStock.query_data(
                entity_id=index_id, start_timestamp=month_start_date(timestamp), end_timestamp=month_end_date(timestamp)
            )
            if not pd_is_not_null(df):
                logger.error(f"no IndexStock data at {timestamp} for {index_id}")
                continue
            print(df)
            stock_tags = [
                self.get_tag_domain(entity_id=stock_id, timestamp=timestamp) for stock_id in df["stock_id"].tolist()
            ]
            for stock_tag in stock_tags:
                stock_tag.style_tag = index_map_style.get(index_id).value
            self.session.add_all(stock_tags)
            self.session.commit()


if __name__ == "__main__":
    StyleTagger().run()
# the __all__ is generated
__all__ = ["StyleTag", "StyleTagger"]
