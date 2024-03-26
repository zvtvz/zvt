# -*- coding: utf-8 -*-
import json
import os
from collections import Counter

from zvt.api import china_stock_code_to_id, get_china_exchange
from zvt.api.selector import get_entity_ids_by_filter
from zvt.api.tag import tag_stock, get_stock_tags, get_limit_up_reasons
from zvt.contract.api import get_entities
from zvt.domain import BlockStock, Block, Stock
from zvt.utils import current_date, next_date, pd_is_not_null, to_time_str


def get_industry_list():
    df = Block.query_data(
        filters=[Block.category == "industry"], columns=[Block.name], return_type="df", order=Block.timestamp.desc()
    )
    return df["name"].tolist()


def get_concept_list(return_checked=True):
    checked_list = [
        "低空经济",
        "AIPC",
        "可控核聚变",
        "AI手机",
        "英伟达概念",
        "Sora概念",
        "飞行汽车(eVTOL)",
        "PEEK材料概念",
        "小米汽车",
        "多模态AI",
        "高带宽内存",
        "短剧互动游戏",
        "新型工业化",
        "星闪概念",
        "BC电池",
        "SPD概念",
        "减肥药",
        "机器人执行器",
        "高压快充",
        "空间计算",
        "裸眼3D",
        "混合现实",
        "存储芯片",
        "液冷概念",
        "光通信模块",
        "数据要素",
        "算力概念",
        "MLOps概念",
        "时空大数据",
        "同步磁阻电机",
        "数字水印",
        "AI芯片",
        "CPO概念",
        "ChatGPT概念",
        "电子后视镜",
        "毫米波概念",
        "蒙脱石散",
        "血氧仪",
        "第四代半导体",
        "熊去氧胆酸",
        "PLC概念",
        "数据确权",
        "抗原检测",
        "抗菌面料",
        "跨境电商",
        "人造太阳",
        "复合集流体",
        "AIGC概念",
        "Web3.0",
        "供销社概念",
        "创新药",
        "信创",
        "熔盐储能",
        "Chiplet概念",
        "减速器",
        "轮毂电机",
        "TOPCon电池",
        "光伏高速公路",
        "钒电池",
        "钙钛矿电池",
        "汽车一体化压铸",
        "麒麟电池",
        "机器人概念",
        "汽车热管理",
        "F5G概念",
        "超超临界发电",
        "千金藤素",
        "新型城镇化",
        "户外露营",
        "肝炎概念",
        "统一大市场",
        "托育服务",
        "跨境支付",
        "气溶胶检测",
        "东数西算",
        "重组蛋白",
        "数字经济",
        "新冠检测",
        "新冠药物",
        "地下管网",
        "虚拟数字人",
        "DRG/DIP",
        "动力电池回收",
        "EDR概念",
        "IGBT概念",
        "数据安全",
        "预制菜概念",
        "培育钻石",
        "发电机概念",
        "华为欧拉",
        "磷化工",
        "国资云概念",
        "元宇宙概念",
        "碳基材料",
        "工业母机",
        "抽水蓄能",
        "激光雷达",
        "NFT概念",
        "机器视觉",
        "华为昇腾",
        "空间站概念",
        "储能",
        "钠离子电池",
        "盐湖提锂",
        "CAR-T细胞疗法",
        "换电概念",
        "华为汽车",
        "核污染防治",
        "工业气体",
        "光伏建筑一体化",
        "碳化硅",
        "被动元件",
        "磁悬浮概念",
        "汽车芯片",
        "固态电池",
        "碳交易",
        "6G概念",
        "虚拟电厂",
        "鸿蒙概念",
        "第三代半导体",
        "刀片电池",
        "氦气概念",
        "MicroLED",
        "EDA概念",
        "装配建筑",
        "汽车拆解",
        "疫苗冷链",
        "辅助生殖",
        "长寿药",
        "中芯概念",
        "免税概念",
        "北交所概念",
        "数据中心",
        "天基互联",
        "特高压",
        "半导体概念",
        "氮化镓",
        "降解塑料",
        "HIT电池",
        "转基因",
        "流感",
        "传感器",
        "云游戏",
        "MiniLED",
        "CRO",
        "阿兹海默",
        "无线耳机",
        "MLCC",
        "医疗美容",
        "农业种植",
        "鸡肉概念",
        "智慧政务",
        "光刻胶",
        "数字货币",
        "PCB",
        "ETC",
        "垃圾分类",
        "青蒿素",
        "人造肉",
        "电子烟",
        "氢能源",
        "超级真菌",
        "数字孪生",
        "边缘计算",
        "工业大麻",
        "纳米银",
        "华为概念",
        "电子竞技",
        "体外诊断",
        "知识产权",
        "互联医疗",
        "工业互联",
        "小米概念",
        "新零售",
        "大飞机",
        "雄安新区",
        "共享经济",
        "精准医疗",
        "钛白粉",
        "无线充电",
        "草甘膦",
        "网红直播",
        "车联网",
        "新能源车",
        "国产芯片",
        "单抗概念",
        "区块链",
        "工业4.0",
        "人工智能",
        "增强现实",
        "无人驾驶",
        "虚拟现实",
        "5G概念",
        "一带一路",
        "量子通信",
        "赛马概念",
        "体育产业",
        "人脑工程",
        "无人机",
        "超级电容",
        "充电桩",
        "全息技术",
        "免疫治疗",
        "基因测序",
        "氟化工",
        "燃料电池",
        "智能家居",
        "超导概念",
        "独家药品",
        "病毒防治",
        "彩票概念",
        "国家安防",
        "电商概念",
        "苹果概念",
        "婴童概念",
        "智能电视",
        "网络安全",
        "养老概念",
        "特斯拉",
        "智能机器",
        "智能穿戴",
        "互联金融",
        "北斗导航",
        "通用航空",
        "3D打印",
        "石墨烯",
        "中药概念",
        "食品安全",
        "风能",
        "智能电网",
        "太阳能",
        "水利建设",
        "稀土永磁",
        "核能核电",
        "锂电池",
        "创投",
    ]
    if return_checked:
        return checked_list

    df = Block.query_data(
        filters=[Block.category == "concept"], columns=[Block.name], return_type="df", order=Block.timestamp.desc()
    )
    return df["name"].tolist()


_industry_to_tag_mapping = {
    ("风电设备", "电池", "光伏设备", "能源金属", "电源设备"): "新能源",
    ("半导体", "电子化学品"): "半导体",
    ("医疗服务", "中药", "化学制药", "生物制品", "医药商业"): "医药",
    ("医疗器械",): "医疗器械",
    ("教育",): "教育",
    ("贸易行业", "家用轻工", "造纸印刷", "酿酒行业", "珠宝首饰", "美容护理", "食品饮料", "旅游酒店", "商业百货", "纺织服装", "家电行业"): "大消费",
    ("小金属", "贵金属", "有色金属", "煤炭行业"): "资源",
    ("消费电子", "电子元件", "光学光电子"): "消费电子",
    ("汽车零部件", "汽车服务", "汽车整车"): "汽车",
    ("电机", "通用设备", "专用设备", "仪器仪表"): "智能机器",
    ("电网设备", "电力行业"): "电力",
    ("房地产开发", "房地产服务", "工程建设", "水泥建材", "装修装饰", "装修建材", "工程咨询服务", "钢铁行业", "工程机械"): "房地产",
    ("非金属材料", "包装材料", "化学制品", "化肥行业", "化学原料", "化纤行业", "塑料制品", "玻璃玻纤", "橡胶制品"): "化工",
    ("交运设备", "船舶制造", "航运港口", "公用事业", "燃气", "航空机场", "环保行业", "石油行业", "铁路公路", "采掘行业"): "公用",
    ("证券", "保险", "银行", "多元金融"): "金融",
    ("互联网服务", "软件开发", "计算机设备", "游戏", "通信服务", "通信设备"): "AI",
    ("文化传媒",): "传媒",
    ("农牧饲渔", "农药兽药"): "农业",
    ("物流行业",): "物流",
    ("航天航空", "船舶制造"): "军工",
    ("专业服务",): "专业服务",
}


def get_tags_info():
    timestamp = "2024-03-25"
    entity_id = "admin"
    return [
        {
            "id": f"admin_{to_time_str(timestamp)}_{tag}",
            "entity_id": entity_id,
            "timestamp": timestamp,
            "tag": tag,
            "tag_reason": f"来自这些行业:{','.join(industries)}",
        }
        for industries, tag in _industry_to_tag_mapping.items()
    ]


def get_sub_tags_info():
    timestamp = "2024-03-25"
    entity_id = "admin"
    return [
        {
            "id": f"admin_{to_time_str(timestamp)}_{tag}",
            "entity_id": entity_id,
            "timestamp": timestamp,
            "tag": tag,
            "tag_reason": tag,
        }
        for tag in get_concept_list(return_checked=True)
    ]


_hidden_tags = {
    "中字头": "央企，国资委控股",
    "核心资产": "高ROE 高现金流 高股息 低应收 低资本开支 低财务杠杆 有增长",
    "高股息": "高股息",
    "微盘股": "市值50亿以下",
    "次新股": "上市未满两年",
}


def get_hidden_tags_info():
    timestamp = "2024-03-25"
    entity_id = "admin"
    return [
        {
            "id": f"admin_{to_time_str(timestamp)}_{tag}",
            "entity_id": entity_id,
            "timestamp": timestamp,
            "tag": tag,
            "tag_reason": tag_reason,
        }
        for tag, tag_reason in _hidden_tags.items()
    ]


def industry_to_tag(industry):
    for key, value in _industry_to_tag_mapping.items():
        if industry in key:
            return value
    return "未知行业"


def check_industry_list_consistency():
    all_industries = get_industry_list()
    using_industries = []
    for key in _industry_to_tag_mapping.keys():
        for item in key:
            using_industries.append(item)
    if sorted(all_industries) == sorted(using_industries):
        print(set(all_industries) - set(using_industries))
        print("failed")
        assert False
    print("ok")


if __name__ == "__main__":
    check_industry_list_consistency()
    print(get_tags_info())
# the __all__ is generated
__all__ = [
    "get_industry_list",
    "get_concept_list",
    "get_tags_info",
    "get_sub_tags_info",
    "get_hidden_tags_info",
    "industry_to_tag",
    "check_industry_list_consistency",
]
