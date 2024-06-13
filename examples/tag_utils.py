# -*- coding: utf-8 -*-
import json
import os
from collections import Counter

from zvt.api.utils import china_stock_code_to_id, get_china_exchange
from zvt.domain import BlockStock, Block, Stock, LimitUpInfo


def get_limit_up_reasons(entity_id):
    info = LimitUpInfo.query_data(
        entity_id=entity_id, order=LimitUpInfo.timestamp.desc(), limit=1, return_type="domain"
    )

    topics = []
    if info and info[0].reason:
        topics = topics + info[0].reason.split("+")
    return topics


def get_concept(code):
    with open(os.path.join(os.path.dirname(__file__), "concept.json")) as f:
        concept_map = json.load(f)
        concepts = [item for sublist in concept_map.values() for item in sublist]
        df = BlockStock.query_data(filters=[BlockStock.stock_code == code, BlockStock.name.in_(concepts)])
        return df["name"].tolist()


def industry_to_tag(industry):
    if industry in ["风电设备", "电池", "光伏设备", "能源金属", "电源设备"]:
        return "赛道"
    if industry in ["半导体", "电子化学品"]:
        return "半导体"
    if industry in ["医疗服务", "中药", "化学制药", "生物制品", "医药商业"]:
        return "医药"
    if industry in ["医疗器械"]:
        return "医疗器械"
    if industry in ["教育"]:
        return "教育"
    if industry in ["贸易行业", "家用轻工", "造纸印刷", "酿酒行业", "珠宝首饰", "美容护理", "食品饮料", "旅游酒店", "商业百货", "纺织服装", "家电行业"]:
        return "大消费"
    if industry in ["小金属", "贵金属", "有色金属", "煤炭行业"]:
        return "资源"
    if industry in ["消费电子", "电子元件"]:
        return "消费电子"
    if industry in ["汽车零部件", "汽车服务", "汽车整车"]:
        return "汽车"
    if industry in ["电机", "通用设备", "专用设备", "仪器仪表"]:
        return "智能机器"
    if industry in ["电网设备", "电力行业"]:
        return "电力"
    if industry in ["光学光电子"]:
        return "VR"
    if industry in ["房地产开发", "房地产服务", "工程建设", "水泥建材", "装修装饰", "装修建材", "工程咨询服务", "钢铁行业", "工程机械"]:
        return "房地产"
    if industry in ["非金属材料", "包装材料", "化学制品", "化肥行业", "化学原料", "化纤行业", "塑料制品", "玻璃玻纤", "橡胶制品"]:
        return "化工"
    if industry in ["交运设备", "船舶制造", "航运港口", "公用事业", "燃气", "航空机场", "环保行业", "石油行业", "铁路公路", "采掘行业"]:
        return "公用"
    if industry in ["证券", "保险", "银行", "多元金融"]:
        return "金融"
    if industry in ["互联网服务", "软件开发", "计算机设备", "游戏", "通信服务", "通信设备"]:
        return "AI"
    if industry in ["文化传媒"]:
        return "传媒"
    if industry in ["农牧饲渔", "农药兽药"]:
        return "农业"
    if industry in ["物流行业"]:
        return "统一大市场"
    if industry in ["航天航空", "船舶制造"]:
        return "军工"
    if industry in ["专业服务"]:
        return "专业服务"


def build_default_tags(codes, provider="em"):
    df_block = Block.query_data(provider=provider, filters=[Block.category == "industry"])
    industry_codes = df_block["code"].tolist()
    tags = []
    for code in codes:
        block_stocks = BlockStock.query_data(
            provider=provider,
            filters=[BlockStock.code.in_(industry_codes), BlockStock.stock_code == code],
            return_type="domain",
        )
        if block_stocks:
            block_stock = block_stocks[0]
            tags.append(
                {
                    "code": block_stock.stock_code,
                    "name": block_stock.stock_name,
                    "tag": industry_to_tag(block_stock.name),
                    "reason": "",
                }
            )
        else:
            print(f"no industry for {code}")

    return tags


def get_main_line_tags():
    with open(os.path.join(os.path.dirname(__file__), "main_line_tags.json")) as f:
        return json.load(f)


def get_main_line_hidden_tags():
    with open(os.path.join(os.path.dirname(__file__), "main_line_hidden_tags.json")) as f:
        return json.load(f)


def replace_tags(old_tag="仪器仪表"):
    with open(os.path.join(os.path.dirname(__file__), "stock_tags.json")) as f:
        stock_tags = json.load(f)
        for stock_tag in stock_tags:
            if stock_tag["tag"] == old_tag:
                df = BlockStock.query_data(filters=[BlockStock.stock_code == stock_tag["code"]])
                blocks = df["name"].tolist()
                for block in blocks:
                    tag = industry_to_tag(industry=block)
                    if tag:
                        stock_tag["tag"] = tag
                        break

        with open("result.json", "w") as json_file:
            json.dump(stock_tags, json_file, indent=2, ensure_ascii=False)


def check_tags():
    with open(os.path.join(os.path.dirname(__file__), "stock_tags.json")) as f:
        stock_tags = json.load(f)
        tags = set()
        hidden_tags = set()
        stocks = []
        final_tags = []
        for stock_tag in stock_tags:
            stock_code = stock_tag["code"]
            if not stock_code.isdigit() or (len(stock_code) != 6):
                print(stock_code)
            tags.add(stock_tag["tag"])
            hidden_tags.add(stock_tag.get("hidden_tag"))
            if stock_code in stocks:
                print(stock_tag)
            else:
                final_tags.append(stock_tag)
            stocks.append(stock_code)

        # with open("result.json", "w") as json_file:
        #     json.dump(final_tags, json_file, indent=2, ensure_ascii=False)

        print(tags)
        print(hidden_tags)
        print(len(stocks))
        count = Counter(stocks)
        duplicates = [item for item, frequency in count.items() if frequency > 1]
        print(duplicates)


def get_hidden_code(code):
    exchange = get_china_exchange(code=code)
    if exchange == "bj":
        return "北交所"


def get_core_tag(codes):
    # 从stock_tags.json读取
    other_codes = []
    with open(os.path.join(os.path.dirname(__file__), "stock_tags.json")) as f:
        stock_tags = json.load(f)
        code_tag_hidden_tag_list = [
            (
                stock_tag["code"],
                stock_tag["tag"],
                stock_tag.get("hidden_tag") if stock_tag.get("hidden_tag") else get_hidden_code(stock_tag["code"]),
            )
            for stock_tag in stock_tags
            if stock_tag["code"] in codes
        ]
        other_codes = [code for code in codes if code not in [item[0] for item in code_tag_hidden_tag_list]]
    for code in other_codes:
        tags = get_limit_up_reasons(entity_id=china_stock_code_to_id(code=code))
        if tags:
            code_tag_hidden_tag_list.append((code, tags[0], None))
        else:
            code_tag_hidden_tag_list.append((code, "未知", get_hidden_code(code)))

    return code_tag_hidden_tag_list


def group_stocks_by_tag(entities, hidden_tags=None):
    code_entities_map = {entity.code: entity for entity in entities}

    tag_stocks = {}
    code_tag_hidden_tag_list = get_core_tag([entity.code for entity in entities])
    for code, tag, hidden_tag in code_tag_hidden_tag_list:
        if hidden_tags and (hidden_tag in hidden_tags):
            tag_stocks.setdefault(hidden_tag, [])
            tag_stocks.get(hidden_tag).append(code_entities_map.get(code))
        if (tag != hidden_tag) or (not hidden_tags):
            tag_stocks.setdefault(tag, [])
            tag_stocks.get(tag).append(code_entities_map.get(code))

    sorted_entities = sorted(tag_stocks.items(), key=lambda x: len(x[1]), reverse=True)

    return sorted_entities


def build_stock_tags_by_block(block_name, tag, hidden_tag):
    block_stocks = BlockStock.query_data(filters=[BlockStock.name == block_name], return_type="domain")
    datas = [
        {
            "code": block_stock.stock_code,
            "name": block_stock.stock_name,
            "tag": tag,
            "hidden_tag": hidden_tag,
            "reason": "",
        }
        for block_stock in block_stocks
    ]

    # Specify the file path where you want to save the JSON data
    file_path = f"{tag}.json"

    # Write JSON data to the file
    with open(file_path, "w") as json_file:
        json.dump(datas, json_file, indent=2, ensure_ascii=False)


def merge_tags(current_tags, added_tags, force_update=False):
    code_tags_map = {item["code"]: item for item in current_tags}

    # Merge
    for added_tag in added_tags:
        code_from_added = added_tag["code"]
        if code_from_added not in code_tags_map:
            current_tags.append(added_tag)
        else:
            # update hidden_tag from added_tag
            if force_update or (not code_tags_map[code_from_added].get("hidden_tag")):
                code_tags_map[code_from_added]["hidden_tag"] = added_tag["hidden_tag"]
    return current_tags


def merge_tags_file(current_tags_file, added_tags_file, result_file, force_update=False):
    # current_tags_file读取
    with open(os.path.join(os.path.dirname(__file__), current_tags_file)) as f:
        current_tags = json.load(f)
    # added_tags_file读取
    with open(os.path.join(os.path.dirname(__file__), added_tags_file)) as f:
        added_tags = json.load(f)

    current_tags = merge_tags(current_tags, added_tags, force_update)
    with open(result_file, "w") as json_file:
        json.dump(current_tags, json_file, indent=2, ensure_ascii=False)


def complete_tags():
    with open(os.path.join(os.path.dirname(__file__), "stock_tags.json")) as f:
        stock_tags = json.load(f)
        current_codes = [stock_tag["code"] for stock_tag in stock_tags]
        df = Stock.query_data(
            provider="em",
            filters=[
                Stock.code.not_in(current_codes),
                Stock.name.not_like("%退%"),
            ],
        )

        codes = df["code"].tolist()
        print(len(codes))
        added_tags = build_default_tags(codes=codes, provider="em")

        with open("result.json", "w") as json_file:
            json.dump(stock_tags + added_tags, json_file, indent=2, ensure_ascii=False)


def refresh_hidden_tags():
    with open(os.path.join(os.path.dirname(__file__), "stock_tags.json")) as f:
        stock_tags = json.load(f)
        for stock_tag in stock_tags:
            if not stock_tag.get("hidden_tag"):
                exchange = get_china_exchange(code=stock_tag["code"])
                if exchange == "bj":
                    stock_tag["hidden_tag"] = "北交所"

        with open("result.json", "w") as json_file:
            json.dump(stock_tags, json_file, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    # build_stock_tags(block_name="化工原料", tag="化工", hidden_tag=None)
    # merge_tags(tags_file="stock_tags.json", hidden_tags_file="化工.json", result_file="result.json", force_update=False)
    # replace_tags(old_tag="仪器仪表")
    # check_tags()
    # complete_tags()
    # refresh_hidden_tags()
    print(get_concept(code="688787"))
