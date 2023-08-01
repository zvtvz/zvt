# -*- coding: utf-8 -*-
import json
import logging
import os
import pprint

import eastmoneypy
import pandas as pd

from zvt.api.stats import get_top_performance_entities_by_periods
from zvt.contract.api import get_entities
from zvt.domain import StockNews
from zvt.utils import next_date, today

logger = logging.getLogger(__name__)


def add_to_eastmoney(codes, group, entity_type="stock", over_write=True):
    if over_write:
        try:
            eastmoneypy.del_group(group_name=group)
        except:
            pass
    try:
        eastmoneypy.create_group(group_name=group)
    except:
        pass

    for code in codes:
        eastmoneypy.add_to_group(code=code, entity_type=entity_type, group_name=group)


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
            word_stats[word] = text.count(word)
            topic_count = topic_count + word_stats[word]
        topic_stats[topic] = topic_count
    return topic_stats, word_stats


def hot_stats(data: pd.Series):
    pass


def group_stocks_by_topic(entities, start_timestamp=None):
    if not start_timestamp:
        start_timestamp = next_date(today(), -180)
    stock_map = {}
    for entity in entities:
        stock_map[entity.entity_id] = {"code": entity.code, "name": entity.name}
    df = StockNews.query_data(start_timestamp=start_timestamp, entity_ids=[entity.entity_id for entity in entities])
    df = df.groupby("entity_id")["news_title"].apply(",".join).reset_index()

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
                for word in words.split():
                    count = text.count(word)
                    if count > 0:
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

    result.append(("其他", [("其他", hot_stocks_map["其他"])]))

    return result


if __name__ == "__main__":
    ids = get_top_performance_entities_by_periods(entity_provider="em", data_provider="em")

    entities = get_entities(provider="em", entity_type="stock", entity_ids=ids, return_type="domain")

    group_info = group_stocks_by_topic(entities=entities)
    info = ""
    for group in group_info:
        topic = group[0]
        info = info + f"^^^^^^ {topic} ^^^^^^\n"
        for topic_word, stocks_count in group[1]:
            info = info + f"{topic_word}\n"
            stocks = [f"{stock_count[0]} {stock_count[1]}" for stock_count in stocks_count]
            info = info + "\n".join(stocks) + "\n"

    print(info)
