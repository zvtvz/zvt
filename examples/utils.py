# -*- coding: utf-8 -*-
import json
import logging
import os

import pandas as pd

from zvt.domain import StockNews, Stock, LimitUpInfo
from zvt.utils.time_utils import date_time_by_interval, today

logger = logging.getLogger(__name__)


def get_hot_words_config():
    with open(os.path.join(os.path.dirname(__file__), "hot.json")) as f:
        return json.load(f)


def count_hot_words(text: str):
    text = text.upper()
    hot_words_config = get_hot_words_config()
    word_stats = {}
    topic_stats = {}
    for topic in hot_words_config:
        topic_count = 0
        for word in hot_words_config[topic]:
            word_stats[word] = text.lower().count(word)
            topic_count = topic_count + word_stats[word]
        topic_stats[topic] = topic_count
    return topic_stats, word_stats


def hot_stats(data: pd.Series):
    pass


def group_stocks_by_topic(
    keyword=None, entities=None, hot_words_config=None, start_timestamp=None, days_ago=60, threshold=3
):
    """

    :param keyword:
    :param entities:
    :param hot_words_config: hot words config为二重结构，即 主题:[分支1，分支2,...]的形式
    比如一个有效的item：{"华为":["华为", "mate pro", "星闪", "问界"]}
    :param start_timestamp:
    :param days_ago:
    :param threshold:
    :return:
    """
    if not start_timestamp:
        start_timestamp = date_time_by_interval(today(), -days_ago)
    stock_map = {}

    entity_ids = None
    if entities:
        entity_ids = [entity.entity_id for entity in entities]
    else:
        entities = Stock.query_data(provider="em", return_type="domain")

    for entity in entities:
        stock_map[entity.entity_id] = {"code": entity.code, "name": entity.name}

    filters = None
    if keyword:
        filters = [StockNews.news_title.contains(keyword)]
    df = StockNews.query_data(start_timestamp=start_timestamp, entity_ids=entity_ids, filters=filters)
    df = df.groupby("entity_id")["news_title"].apply(",".join).reset_index()

    if not hot_words_config:
        hot_words_config = get_hot_words_config()

    hot_stocks_map = {}
    topic_count = {}
    word_count = {}
    for _, row in df[["entity_id", "news_title"]].iterrows():
        entity_id = row["entity_id"]
        text = row["news_title"]

        is_hot = False
        for topic in hot_words_config:
            topic_count.setdefault(topic, 0)
            for words in hot_words_config[topic]:
                hot_stocks_map.setdefault(words, [])
                word_count.setdefault(words, 0)
                count = 0
                for word in words.split(","):
                    count = text.lower().count(word) + count
                if count >= threshold:
                    word_count[words] = word_count[words] + 1
                    topic_count[topic] = topic_count[topic] + 1
                    hot_stocks_map[words].append(
                        (f"{stock_map[entity_id]['code']}({stock_map[entity_id]['name']})", count)
                    )
                    is_hot = True
        if not is_hot:
            hot_stocks_map.setdefault("其他", [])
            hot_stocks_map["其他"].append((f"{stock_map[entity_id]['code']}({stock_map[entity_id]['name']})", 0))

    sorted_topics = sorted(topic_count.items(), key=lambda item: item[1], reverse=True)
    sorted_words = sorted(word_count.items(), key=lambda item: item[1], reverse=True)

    result = []
    for topic, count in sorted_topics:
        topic_words = hot_words_config[topic]
        topic_words_stocks = [
            (f"{words}({count})", sorted(hot_stocks_map[words], key=lambda item: item[1], reverse=True))
            for (words, count) in sorted_words
            if words in topic_words
        ]
        result.append((f"{topic}({count})", topic_words_stocks))

    result.append(("其他", [("其他", hot_stocks_map.get("其他", ""))]))

    return result


def msg_group_stocks_by_topic(
    keyword=None, entities=None, hot_words_config=None, start_timestamp=None, days_ago=60, threshold=3
):
    group_info = group_stocks_by_topic(
        keyword=keyword,
        entities=entities,
        hot_words_config=hot_words_config,
        start_timestamp=start_timestamp,
        days_ago=days_ago,
        threshold=threshold,
    )
    msg = ""
    for group in group_info:
        topic = group[0]
        msg = msg + f"^^^^^^ {topic} ^^^^^^\n"
        for topic_word, stocks_count in group[1]:
            msg = msg + f"{topic_word}\n"
            stocks = [f"{stock_count[0]} {stock_count[1]}" for stock_count in stocks_count]
            msg = msg + "\n".join(stocks) + "\n"
    return msg


def get_hot_topics(start_timestamp=None, days_ago=20, limit=15):
    if not start_timestamp:
        start_timestamp = date_time_by_interval(today(), -days_ago)
    df = LimitUpInfo.query_data(start_timestamp=start_timestamp, columns=["reason"])
    df["reason"] = df["reason"].str.split("+")
    result = df["reason"].tolist()
    result = [item for sublist in result for item in sublist]
    result = pd.Series(result)
    result = result.value_counts()
    result = result[:limit].to_dict()
    return result


if __name__ == "__main__":
    # ids = get_top_performance_entities_by_periods(entity_provider="em", data_provider="em")
    #
    # entities = get_entities(provider="em", entity_type="stock", entity_ids=ids, return_type="domain")
    #
    # print(msg_group_stocks_by_topic(entities=entities, threshold=1))
    get_hot_topics(days_ago=10)
