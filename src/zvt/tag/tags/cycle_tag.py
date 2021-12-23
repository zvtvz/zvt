# -*- coding: utf-8 -*-
from enum import Enum

from zvt.domain import Stock, BlockStock, Block
from zvt.tag.dataset.stock_tags import StockTags
from zvt.tag.tag import StockTagger


class CycleTag(Enum):
    # 强周期
    strong_cycle = "strong_cycle"
    # 弱周期
    weak_cycle = "weak_cycle"
    # 非周期，受周期影响不大，比如消费，医药
    non_cycle = "non_cycle"


# 这里用的是东财的行业分类
# 数据来源
# Block.record_data(provider='eastmoney')
# Block.query_data(provider='eastmoney', filters=[Block.category==industry])
# BlockStock.record_data(provider='eastmoney')

# 这不是一个严格的分类，好像也不需要太严格
cycle_map_industry = {
    CycleTag.strong_cycle: [
        "有色金属",
        "水泥建材",
        "化工行业",
        "化纤行业",
        "钢铁行业",
        "煤炭采选",
        "化肥行业",
        "贵金属",
        "船舶制造",
        "房地产",
        "石油行业",
        "港口水运",
        "材料行业",
    ],
    CycleTag.weak_cycle: [
        "电力行业",
        "民航机场",
        "家电行业",
        "旅游酒店",
        "银行",
        "保险",
        "高速公路",
        "电子信息",
        "通讯行业",
        "多元金融",
        "电子元件",
        "国际贸易",
        "珠宝首饰",
        "交运物流",
        "航天航空",
        "交运设备",
        "汽车行业",
        "专用设备",
        "园林工程",
        "造纸印刷",
        "安防设备",
        "装修装饰",
        "木业家具",
        "输配电气",
        "工程建设",
        "包装材料",
        "券商信托",
        "机械行业",
        "金属制品",
        "塑胶制品",
        "环保工程",
        "玻璃陶瓷",
    ],
    CycleTag.non_cycle: [
        "食品饮料",
        "酿酒行业",
        "医疗行业",
        "医药制造",
        "文教休闲",
        "软件服务",
        "商业百货",
        "文化传媒",
        "农牧饲渔",
        "公用事业",
        "纺织服装",
        "综合行业",
        "仪器仪表",
        "电信运营",
        "工艺商品",
        "农药兽药",
    ],
}


def get_cycle_tag(industry_name):
    for cycle_tag in cycle_map_industry:
        if industry_name in cycle_map_industry.get(cycle_tag):
            return cycle_tag.name


class CycleTagger(StockTagger):
    def tag(self, timestamp):
        stock_df = Stock.query_data(filters=[Stock.list_date <= timestamp], index="entity_id")
        block_df = Block.query_data(provider="eastmoney", filters=[Block.category == "industry"], index="entity_id")
        block_ids = block_df.index.tolist()
        block_stock_df = BlockStock.query_data(
            provider="eastmoney",
            entity_ids=block_ids,
            filters=[BlockStock.stock_id.in_(stock_df.index.tolist())],
            index="stock_id",
        )
        block_stock_df["cycle_tag"] = block_stock_df["name"].apply(lambda name: get_cycle_tag(name))
        strong_cycle_stocks = block_stock_df[block_stock_df.cycle_tag == "strong_cycle"]["stock_id"]
        weak_cycle_stocks = block_stock_df[block_stock_df.cycle_tag == "weak_cycle"]["stock_id"]
        non_cycle_stocks = block_stock_df[block_stock_df.cycle_tag == "non_cycle"]["stock_id"]

        strong_cycle_domains = self.get_tag_domains(
            entity_ids=strong_cycle_stocks, timestamp=timestamp, cycle_tag=CycleTag.strong_cycle.value
        )
        weak_cycle_domains = self.get_tag_domains(
            entity_ids=weak_cycle_stocks, timestamp=timestamp, cycle_tag=CycleTag.weak_cycle.value
        )
        non_cycle_domains = self.get_tag_domains(
            entity_ids=non_cycle_stocks, timestamp=timestamp, cycle_tag=CycleTag.non_cycle.value
        )

        self.session.add_all(strong_cycle_domains)
        self.session.add_all(weak_cycle_domains)
        self.session.add_all(non_cycle_domains)
        self.session.commit()


if __name__ == "__main__":
    CycleTagger().run()
    print(StockTags.query_data(start_timestamp="2021-08-31", filters=[StockTags.cycle_tag != None]))
# the __all__ is generated
__all__ = ["CycleTag", "get_cycle_tag", "CycleTagger"]
