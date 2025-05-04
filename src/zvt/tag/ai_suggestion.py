# -*- coding: utf-8 -*-
import json
import logging
import re
from typing import List

import pandas as pd
from openai import OpenAI
from sqlalchemy import func, or_

import zvt.contract.api as contract_api
from zvt import zvt_config
from zvt.domain import StockNews, Stock
from zvt.tag.tag_utils import match_tag
from zvt.utils.time_utils import date_time_by_interval, current_date

logger = logging.getLogger(__name__)


def normalize_tag_suggestions(tag_suggestions):
    for direction in ["up", "down"]:
        if direction in tag_suggestions:
            for item in tag_suggestions[direction]:
                tag_type, tag = match_tag(item["block"])
                item["tag"] = tag
                item["tag_type"] = tag_type
                if item["stocks"]:
                    stocks = Stock.query_data(
                        filters=[Stock.name.in_(item["stocks"])], return_type="dict", provider="em"
                    )
                    if len(stocks) != len(item["stocks"]):
                        logger.warning(
                            f"Stocks not found in zvt:{set(item['stocks']) - set([item['name'] for item in stocks])}"
                        )
                    item["stocks"] = [{"entity_id": item["entity_id"], "name": item["name"]} for item in stocks]
    return tag_suggestions


def set_stock_news_tag_suggestions(stock_news, tag_suggestions, session):
    if stock_news.news_analysis:
        stock_news.news_analysis = dict(stock_news.news_analysis)
    else:
        stock_news.news_analysis = {}

    result = normalize_tag_suggestions(tag_suggestions)
    logger.debug(result)
    stock_news.news_analysis["tag_suggestions"] = result
    session.add(stock_news)
    session.commit()


def build_tag_suggestions(entity_id):
    with contract_api.DBSession(provider="em", data_schema=StockNews)() as session:
        start_date = date_time_by_interval(current_date(), -30)
        datas: List[StockNews] = StockNews.query_data(
            entity_id=entity_id,
            limit=1,
            order=StockNews.timestamp.desc(),
            filters=[
                StockNews.timestamp >= start_date,
                func.json_extract(StockNews.news_analysis, f'$."tag_suggestions"') != None,
            ],
            return_type="domain",
        )
        if datas:
            latest_data = datas[0]
        else:
            latest_data = None

        filters = [
            or_(
                StockNews.news_title.like("%上涨%"),
                StockNews.news_title.like("%拉升%"),
                StockNews.news_title.like("%涨停%"),
                StockNews.news_title.like("%下跌%"),
                StockNews.news_title.like("%跌停%"),
            ),
            StockNews.timestamp >= start_date,
            func.json_extract(StockNews.news_analysis, f'$."tag_suggestions"') == None,
        ]
        if latest_data:
            filters = filters + [
                StockNews.timestamp >= latest_data.timestamp,
                StockNews.news_code != latest_data.news_code,
            ]

        stock_news_list: List[StockNews] = StockNews.query_data(
            entity_id=entity_id,
            session=session,
            order=StockNews.news_code.asc(),
            return_type="domain",
            filters=filters,
        )

        if not stock_news_list:
            logger.info("all stock news has been analyzed")
            return

        example = {
            "up": [{"block": "block_a", "stocks": ["stock_a", "stock_b"]}],
            "down": [{"block": "block_b", "stocks": ["stock_1", "stock_2"]}],
        }

        client = OpenAI(
            api_key=zvt_config["qwen_api_key"],
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

        for stock_news in stock_news_list:
            # same news
            if latest_data and (stock_news.news_code == latest_data.news_code):
                tag_suggestions = latest_data.news_analysis.get("tag_suggestions")
                if tag_suggestions:
                    set_stock_news_tag_suggestions(stock_news, tag_suggestions, session)
                    continue

            news_title = stock_news.news_title
            news_content = stock_news.news_content
            logger.info(news_title)
            logger.info(news_content)

            completion = client.chat.completions.create(
                model="qwen-max",
                messages=[
                    {
                        "role": "system",
                        "content": f"请从新闻标题和内容中识别是上涨还是下跌，提取相应的板块和个股，按照格式: {example} 输出一个 JSON 对象",
                    },
                    {
                        "role": "user",
                        "content": f"新闻标题:{news_title}, 新闻内容:{news_content}",
                    },
                ],
                temperature=0.2,
            )
            content = completion.choices[0].message.content
            content = content.replace("```json", "")
            content = content.replace("```", "")
            content = re.sub(r"\s+", "", content)
            logger.info(f"message content: {content}")
            tag_suggestions = json.loads(content)
            set_stock_news_tag_suggestions(stock_news, tag_suggestions, session)


def extract_info(tag_dict):
    extracted_info = []
    for key, value in tag_dict.items():
        for item in value:
            extracted_info.append({"tag": item["tag"], "stocks": [stock["name"] for stock in item["stocks"]]})
    return extracted_info


def build_tag_suggestions_stats():
    with contract_api.DBSession(provider="em", data_schema=StockNews)() as session:
        start_date = date_time_by_interval(current_date(), -10)
        stock_news_list: List[StockNews] = StockNews.query_data(
            session=session,
            order=StockNews.timestamp.desc(),
            distinct=StockNews.news_code,
            return_type="dict",
            filters=[
                StockNews.timestamp >= start_date,
                func.json_extract(StockNews.news_analysis, f'$."tag_suggestions"') != None,
            ],
        )
        datas = []
        for stock_news in stock_news_list:
            tag_suggestions = stock_news["news_analysis"].get("tag_suggestions")
            if tag_suggestions:
                for key in ("up", "down"):
                    suggestions = tag_suggestions.get(key)
                    if suggestions:
                        datas = datas + [
                            {
                                "tag": item["tag"],
                                "tag_type": item["tag_type"],
                                "entity_ids": [stock["entity_id"] for stock in item["stocks"]],
                                "stock_names": [stock["name"] for stock in item["stocks"]],
                            }
                            for item in suggestions
                        ]
        df = pd.DataFrame.from_records(data=datas)
        grouped_df = (
            df.groupby("tag")
            .agg(
                tag_count=("tag", "count"),
                tag_type=("tag_type", "first"),
                entity_ids=("entity_ids", "sum"),
                stock_names=("stock_names", "sum"),
            )
            .reset_index()
        )
        grouped_df["entity_ids"] = grouped_df["entity_ids"].apply(set).apply(list)
        grouped_df["stock_names"] = grouped_df["stock_names"].apply(set).apply(list)
        grouped_df["entity_ids_count"] = grouped_df["entity_ids"].apply(len)

        sorted_df = grouped_df.sort_values(by=["tag_count", "entity_ids_count"], ascending=[False, False])
        return sorted_df.to_dict(orient="records")


if __name__ == "__main__":
    build_tag_suggestions_stats()
